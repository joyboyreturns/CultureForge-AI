"""The research agent must clarify rather than guess, and must respect its budget."""
from __future__ import annotations

from backend import research
from backend.models import ProjectRequest
from backend.providers import QlooHarnessError

PROJECT = ProjectRequest(
    businessType='Food & beverage', audience='Design-conscious Gen Z',
    location='Brooklyn, New York', budget='$25k – $50k', objectives=['x'],
)


class StubProvider:
    """A provider that answers with whatever the test tells it to."""

    def __init__(self, tag_envelope, rec_envelope, generate=None):
        self.tag_envelope = tag_envelope
        self.rec_envelope = rec_envelope
        self.generate_result = generate
        self.workflow_calls = 0

    def rows(self, envelope):
        return envelope.get('results', []) or []

    def tag_id(self, row):
        return row.get('id')

    def run_workflow_cached(self, operation, payload):
        self.workflow_calls += 1
        envelope = self.tag_envelope if operation == 'find_tags' else self.rec_envelope
        return envelope, False, 1

    def generate(self, project):
        if self.generate_result is None:
            raise QlooHarnessError('stub')
        return self.generate_result


def _install(monkeypatch, provider):
    monkeypatch.setattr(research, 'QlooHarnessProvider', lambda *a, **k: provider)
    return provider


def test_needs_input_becomes_a_clarification(monkeypatch):
    provider = _install(monkeypatch, StubProvider({'status': 'needs_input'}, {}))
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=3)
    assert run.status == research.STATUS_CLARIFY
    assert run.clarification['field'] == 'audience'


def test_no_resolved_tags_becomes_a_clarification(monkeypatch):
    provider = _install(monkeypatch, StubProvider({'status': 'ok', 'results': []}, {}))
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=3)
    assert run.status == research.STATUS_CLARIFY
    assert 'cultural tags' in run.clarification['reason']


def test_no_local_evidence_becomes_a_clarification(monkeypatch):
    tag_envelope = {'status': 'ok', 'results': [{'id': 'urn:tag:x:qloo:y'}]}
    provider = _install(monkeypatch, StubProvider(tag_envelope, {'status': 'ok', 'results': []}))
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=3)
    assert run.status == research.STATUS_CLARIFY
    assert run.clarification['field'] == 'location'
    assert 'Brooklyn, New York' in run.clarification['reason'], 'the message names the location that failed'
    assert run.clarification['suggestion'] is None, 'nothing is suggested when nothing is known'


def test_a_known_location_is_offered_as_the_way_out(monkeypatch, store):
    """A location Qloo cannot resolve must not be a dead end.

    When the store already holds places for the same signals somewhere else,
    that location is offered. It is evidence, not a guess, and taking it
    spends no request, because the evidence is already held.
    """
    from backend.evidence_store import canonical_key

    tag_envelope = {'status': 'ok', 'results': [{'id': 'urn:tag:x:qloo:y'}]}
    provider = _install(monkeypatch, StubProvider(tag_envelope, {'status': 'ok', 'results': []}))

    store.put(canonical_key('recommend', {'signal_tags': ['urn:tag:x:qloo:y'], 'signal_location': 'Brooklyn, New York'}), {
        'operation': 'recommend', 'status': 'ok',
        'results': [{'entity_id': 'a', 'name': 'Somewhere'}],
        'query_intent': {'signals': {'location': 'Brooklyn, New York', 'tags': ['urn:tag:x:qloo:y']}},
    })

    # The founder asked for a neighbourhood Qloo cannot resolve.
    run = research.ResearchRun(PROJECT.model_copy(update={'location': 'Greenpoint, Brooklyn'}))
    research._execute(run, allowance=3)

    assert run.status == research.STATUS_CLARIFY
    assert 'Greenpoint, Brooklyn' in run.clarification['reason']
    assert run.clarification['suggestion'] == 'Brooklyn, New York'


def test_the_run_stops_at_its_allowance(monkeypatch):
    tag_envelope = {'status': 'ok', 'results': [{'id': 'urn:tag:x:qloo:y'}]}
    provider = _install(monkeypatch, StubProvider(tag_envelope, {'status': 'ok', 'results': [{}]}))
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=1)
    assert run.status == research.STATUS_FAILED
    assert 'allowance' in run.error


def test_a_provider_failure_is_reported_not_crashed(monkeypatch):
    class Broken(StubProvider):
        def run_workflow_cached(self, operation, payload):
            raise QlooHarnessError('Qloo rejected the request.')

    _install(monkeypatch, Broken({}, {}))
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=3)
    assert run.status == research.STATUS_FAILED
    assert run.error


def test_the_run_records_real_trace_events(monkeypatch):
    tag_envelope = {'status': 'ok', 'operation': 'find_tags',
                    'results': [{'id': 'urn:tag:x:qloo:y'}],
                    'execution': {'duration_ms': 1234, 'correlation_id': 'exec-abc'}}
    rec_envelope = {'status': 'ok', 'operation': 'recommend', 'results': [{}],
                    'execution': {'duration_ms': 21000, 'correlation_id': 'exec-def'}}
    _install(monkeypatch, StubProvider(tag_envelope, rec_envelope))
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=3)
    steps = [event['step'] for event in run.events]
    assert 'resolve-audience' in steps
    assert 'retrieve-evidence' in steps
    first = run.events[0]
    assert first['durationMs'] == 1234
    assert first['correlationId'] == 'exec-abc'
