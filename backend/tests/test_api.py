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


def test_snapshots_round_trip_over_http(client):
    payload = {'projectId': 'cf-test', 'concepts': [], 'note': 'shared'}
    created = client.post('/api/explorations/share', json=payload)
    assert created.status_code == 200
    snapshot_id = created.json()['snapshotId']
    assert snapshot_id.startswith('snap-')

    read = client.get(f'/api/snapshots/{snapshot_id}')
    assert read.status_code == 200
    assert read.json()['projectId'] == 'cf-test'


def test_a_missing_snapshot_is_a_404(client):
    assert client.get('/api/snapshots/snap-nope').status_code == 404


def test_an_unknown_research_run_is_a_404(client):
    assert client.get('/api/research/runs/run-nope').status_code == 404
