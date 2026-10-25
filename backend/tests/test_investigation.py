"""Investigation replays retain provenance and recover from a failed facet."""
from datetime import datetime, timezone

from backend.evidence_store import canonical_key
from backend.investigation import investigate, _call_for
from backend.models import ProjectRequest
from backend.providers import QlooHarnessError, QlooHarnessProvider


def project():
    return ProjectRequest(businessType='Food & beverage', businessIdea='Bakery',
                          audience='Morning commuters', location='Tokyo, Japan',
                          budget='$25k – $50k', objectives=[])


def test_held_investigation_reports_zero_wait_and_original_acquisition(store):
    brief = project()
    operation, payload = _call_for('describe', QlooHarnessProvider(), 'place-1', ['place-1'], brief.location)
    acquired = 1760000000.0
    store.seed(canonical_key(operation, payload), {
        'status': 'ok', 'results': [{'entity_id': 'place-1', 'name': 'Returned bakery'}],
        'execution': {'duration_ms': 8500},
    }, acquired)

    report = investigate(brief, 'direction-1', ['place-1'], brief.location, ['describe'])

    tool = report['tools'][0]
    assert tool['cached'] is True
    assert tool['durationMs'] == 0
    assert tool['originalDurationMs'] == 8500
    assert 'original call took 8.5s' in tool['detail']
    assert tool['acquiredAt'] == datetime.fromtimestamp(acquired, timezone.utc).isoformat()
    assert report['transportRequests'] == 0
    assert report['describe']['name'] == 'Returned bakery'


def test_one_failed_facet_does_not_hide_another_facets_answer(store, monkeypatch):
    brief = project()

    def workflow(self, operation, payload):
        if operation == 'entity_tags':
            raise QlooHarnessError('Qloo rate limited this request.', code='RATE_LIMITED')
        return {'status': 'ok', 'results': [{'entity_id': 'place-1', 'name': 'Returned bakery'}],
                'execution': {'duration_ms': 1200}}, False, 1

    monkeypatch.setattr(QlooHarnessProvider, 'run_workflow_cached', workflow)
    report = investigate(brief, None, ['place-1'], brief.location, ['tags', 'describe'])

    assert [tool['status'] for tool in report['tools']] == ['error', 'ok']
    assert 'rate limited' in report['limitations'][0]
    assert report['describe']['name'] == 'Returned bakery'
    assert report['tools'][1]['durationMs'] == 1200
    assert report['tools'][1]['originalDurationMs'] is None
    assert report['transportRequests'] == 1
