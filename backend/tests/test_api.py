"""The HTTP surface: status codes, error shapes, and the contract the UI relies on."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend.models import GenerateResponse


@pytest.fixture
def client():
    return TestClient(main.app, raise_server_exceptions=False)


def test_health_reports_the_provider(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ok'
    assert body['dataMode'] in {'live', 'mock'}


def test_the_health_alias_works(client):
    assert client.get('/health').status_code == 200


def test_authorized_partner_cors_preflight_is_allowed(client):
    response = client.options('/api/health', headers={'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'GET', 'Access-Control-Request-Headers': 'Authorization'})
    assert response.status_code == 200
    assert 'authorization' in response.headers['access-control-allow-headers'].lower()


def test_validation_errors_are_readable(client):
    """The UI renders `detail` directly, so it must be a string, not a list."""
    response = client.post('/api/projects/generate', json={'businessType': 'Nope', 'audience': 'x'})
    assert response.status_code == 422
    detail = response.json()['detail']
    assert isinstance(detail, str)
    assert 'businessType' in detail


def test_a_valid_request_answers_with_the_contract(client, monkeypatch):
    from backend.providers import MockCultureProvider

    monkeypatch.setattr(main, 'get_provider', lambda: MockCultureProvider())
    response = client.post('/api/projects/generate', json={
        'businessType': 'Food & beverage', 'audience': 'Design-conscious Gen Z',
        'location': 'Brooklyn, New York', 'budget': '$25k – $50k',
        'objectives': ['Build a loyal community'],
    })
    assert response.status_code == 200
    body = GenerateResponse.model_validate(response.json())
    assert body.conceptMode == 'sample'
    assert body.evidence == []
    assert body.trace == []


def test_the_compare_endpoint_refuses_without_a_live_provider(client, monkeypatch):
    from backend.providers import MockCultureProvider

    monkeypatch.setattr(main, 'get_provider', lambda: MockCultureProvider())
    response = client.post('/api/projects/compare', json={
        'project': {'businessType': 'Food & beverage', 'audience': 'Gen Z',
                    'location': 'Brooklyn, New York', 'budget': '$25k', 'objectives': []},
        'audience': 'Mindful professionals',
    })
    assert response.status_code == 409
    assert 'Qloo' in response.json()['detail']


def _challenge_probe_body():
    return {
        'project': {'businessType': 'Food & beverage', 'audience': 'Gen Z',
                    'location': 'Brooklyn, New York', 'budget': '$25k', 'objectives': []},
        'directionId': 'direction-a',
        'revision': {
            'evidence': [
                {'id': 'place-a', 'kind': 'entity', 'label': 'Anchor Place',
                 'entityId': 'entity-a', 'entityType': 'place'},
                {'id': 'tag-a', 'kind': 'tag', 'label': 'Food design',
                 'tagId': 'urn:tag:interests:qloo:food_design'},
            ],
            'concepts': [{
                'id': 'direction-a', 'name': 'Direction A', 'tagline': 'A tagline',
                'description': 'A direction', 'budget': 'small', 'investment': 'pilot',
                'signals': ['food design'], 'accent': 'green', 'image': '',
                'evidenceIds': ['place-a'],
            }],
            'resolvedTags': ['urn:tag:interests:qloo:food_design'],
        },
    }


def test_challenge_probe_route_returns_probe_result_without_live_call(client, monkeypatch):
    from backend.providers import QlooHarnessProvider

    expected = {'outcome': 'unresolved', 'transportRequests': 1, 'replacements': []}
    monkeypatch.setattr(main, 'get_provider', lambda: QlooHarnessProvider())
    monkeypatch.setattr(main, 'challenge_probe', lambda request, provider: expected)

    response = client.post('/api/projects/challenge-probe', json=_challenge_probe_body())

    assert response.status_code == 200
    assert response.json() == expected


def test_challenge_probe_route_rejects_malformed_or_unknown_fields(client):
    malformed = _challenge_probe_body()
    malformed['revision']['resolvedTags'] = 'not-a-list'
    assert client.post('/api/projects/challenge-probe', json=malformed).status_code == 422

    unknown = _challenge_probe_body()
    unknown['qlooQuery'] = {'filter.exclude.entities': 'entity-a'}
    assert client.post('/api/projects/challenge-probe', json=unknown).status_code == 422


def test_challenge_probe_route_refuses_sample_provider(client, monkeypatch):
    from backend.providers import MockCultureProvider

    monkeypatch.setattr(main, 'get_provider', lambda: MockCultureProvider())
    response = client.post('/api/projects/challenge-probe', json=_challenge_probe_body())
    assert response.status_code == 409
    assert 'Qloo' in response.json()['detail']


def test_evidence_analysis_request_is_typed_and_opt_in(client, monkeypatch):
    malformed = client.post('/api/projects/analyze', json={
        'project': {'businessType': 'Food & beverage', 'audience': 'Gen Z',
                    'location': 'Brooklyn', 'budget': '$25k', 'objectives': []},
        'evidence': 'not-a-list', 'concepts': [],
    })
    assert malformed.status_code == 422
    assert malformed.json()['detail']

    monkeypatch.setattr(main, 'analyze_evidence', lambda _request: (_ for _ in ()).throw(
        main.AnalysisUnavailable('Evidence analysis is disabled.')))
    disabled = client.post('/api/projects/analyze', json={
        'project': {'businessType': 'Food & beverage', 'audience': 'Gen Z',
                    'location': 'Brooklyn', 'budget': '$25k', 'objectives': []},
        'evidence': [], 'concepts': [],
    })
    assert disabled.status_code == 503
    assert 'disabled' in disabled.json()['detail']


def test_snapshots_round_trip_over_http(client):
    payload = {'projectId': 'cf-test', 'concepts': [], 'note': 'shared'}
    created = client.post('/api/explorations/share', json=payload)
    assert created.status_code == 201
    assert created.headers.get('Location', '').startswith('/api/snapshots/')
    snapshot_id = created.json()['snapshotId']
    assert snapshot_id.startswith('snap-')

    read = client.get(f'/api/snapshots/{snapshot_id}')
    assert read.status_code == 200
    assert read.json()['projectId'] == 'cf-test'


def test_a_missing_snapshot_is_a_404(client):
    assert client.get('/api/snapshots/snap-nope').status_code == 404


def test_an_unknown_research_run_is_a_404(client):
    assert client.get('/api/research/runs/run-nope').status_code == 404


# ---------------------------------------------------------------------------
# The operator routes
#
# There is no account system behind them, so they are closed to anyone who
# is not the operator. A partner's key is not an operator credential:
# authentication is not authorisation.
# ---------------------------------------------------------------------------

def test_the_operator_routes_are_closed_to_a_remote_caller(client):
    for method, path, body in (
        ('post', '/api/workspaces', {'name': 'Someone Else'}),
        ('post', '/api/workspaces/ws-nope/keys', {}),
        ('get', '/api/workspaces/ws-nope/keys', None),
        ('delete', '/api/workspaces/ws-nope/keys/key-nope', None),
    ):
        response = getattr(client, method)(path, json=body) if body is not None \
            else getattr(client, method)(path)
        assert response.status_code in (401, 403), f'{method} {path} -> {response.status_code}'


def test_the_operator_routes_open_with_the_operator_token(client, monkeypatch):
    monkeypatch.setenv('CULTUREFORGE_OPERATOR_TOKEN', 'operator-secret')
    response = client.post('/api/workspaces', json={'name': 'A Partner'},
                            headers={'x-operator-token': 'operator-secret'})
    assert response.status_code == 201
    # And a wrong token is refused.
    refused = client.post('/api/workspaces', json={'name': 'A Partner'},
                           headers={'x-operator-token': 'wrong'})
    assert refused.status_code == 401


def test_a_key_cannot_be_revoked_from_another_workspace(client, monkeypatch):
    """The workspace in the path has to be the one that owns the key."""
    monkeypatch.setenv('CULTUREFORGE_OPERATOR_TOKEN', 'operator-secret')
    headers = {'x-operator-token': 'operator-secret'}
    workspace = client.post('/api/workspaces', json={'name': 'Mine'}, headers=headers).json()
    other = client.post('/api/workspaces', json={'name': 'Theirs'}, headers=headers).json()
    issued = client.post(f"/api/workspaces/{workspace['id']}/keys", json={}, headers=headers).json()

    refused = client.delete(f"/api/workspaces/{other['id']}/keys/{issued['id']}", headers=headers)
    assert refused.status_code == 404
    # And the right workspace can.
    allowed = client.delete(f"/api/workspaces/{workspace['id']}/keys/{issued['id']}", headers=headers)
    assert allowed.status_code == 204


def test_a_malformed_workflow_body_is_a_readable_422(client):
    """A string where a list was meant must not reach the provider."""
    for path, body in (
        ('/api/qloo/entity-tags', {'entities': 'a-string-not-a-list'}),
        ('/api/qloo/trends', {'entities': ['a'], 'startDate': 'not-a-date'}),
        ('/api/qloo/describe', {'entity': 'x', 'limit': 'not-a-number'}),
    ):
        response = client.post(path, json=body)
        assert response.status_code == 422, f'{path} -> {response.status_code}'
        assert response.json()['detail']


def test_interest_cells_are_capped_at_what_the_harness_accepts(client):
    """The Qloo harness rejects more than 20 where_popular cells; ask for more and it is a 422 here."""
    response = client.post('/api/qloo/where-popular', json={'entity': 'x', 'within': 'Brooklyn', 'limit': 21})
    assert response.status_code == 422


def test_operator_bodies_are_typed(client):
    """A workspace or key request of the wrong shape is a 422, like every other body."""
    assert client.post('/api/workspaces', json={'name': ''}).status_code == 422
    assert client.post('/api/workspaces', json={'name': 'x', 'surprise': 1}).status_code == 422
    assert client.post('/api/workspaces/w/keys', json={'scopes': ['admin']}).status_code == 422


def test_an_unexpected_error_is_still_the_one_envelope_with_a_request_id(client, monkeypatch):
    import backend.chat as chat_module

    def boom(_request):
        raise RuntimeError('boom')
    monkeypatch.setattr(chat_module, 'ask', boom)
    body = {'project': {'businessType': 'Retail', 'audience': 'collectors', 'location': 'Paris', 'budget': 'b'},
            'question': 'Which place anchors it?'}
    response = client.post('/api/chat', json=body)
    assert response.status_code == 500
    payload = response.json()
    assert payload['error']['code'] == 'INTERNAL_ERROR' and payload['error']['retryable'] is True
    assert payload['requestId'].startswith('req-') and 'boom' not in response.text
