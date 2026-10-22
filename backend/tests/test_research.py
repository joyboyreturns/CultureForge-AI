"""The research agent must clarify rather than guess, and must respect its budget."""
from __future__ import annotations

from backend import research
from backend.models import (AgentReport, Concept, Delivery, Evidence, GenerateResponse,
                            ProjectRequest, TraceEvent)
from backend.providers import QlooHarnessError, QlooHarnessProvider

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

    recommend_places = QlooHarnessProvider.recommend_places

    def tag_id(self, row):
        return row.get('id')

    def run_workflow_cached(self, operation, payload):
        self.workflow_calls += 1
        envelope = self.tag_envelope if operation == 'find_tags' else self.rec_envelope
        return envelope, False, 1

    def generate(self, project, **_kwargs):
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


def test_bounded_agent_is_part_of_the_completed_research_run(monkeypatch):
    tag_envelope = {'status': 'ok', 'operation': 'find_tags',
                    'results': [{'id': 'urn:tag:x:qloo:y'}]}
    rec_envelope = {'status': 'ok', 'operation': 'recommend',
                    'results': [{'entity_id': 'urn:place:north', 'name': 'North Room'}]}
    concept = Concept(
        id='direction-a', name='Neighbourhood table', tagline='A place to gather',
        description='Build the direction around a returned place.', budget='TBD',
        investment='Not estimated', signals=['local arts'], accent='#fff', image='',
        evidenceIds=['ev-place-a'], decisions=[{
            'id': 'decision-a', 'field': 'anchor', 'proposal': 'Use this place',
            'evidenceIds': ['ev-place-a'], 'ruleId': 'anchor-culture',
        }])
    generated = GenerateResponse(
        projectId='cf-run', project=PROJECT, concepts=[concept], signals=[],
        dataMode='live', conceptMode='evidence_composed', notice='Evidence-backed result.',
        evidence=[Evidence(id='ev-place-a', kind='entity', label='North Room', entityId='urn:place:north')],
        trace=[], delivery=Delivery(kind='fresh', transportRequests=2))
    provider = StubProvider(tag_envelope, rec_envelope, generated)
    _install(monkeypatch, provider)

    def execute_agent(answer, actual_tags, actual_places, remaining_allowance, deadline, on_event):
        # The initial answer must be available while the slow controller is
        # still running, with no completed analysis claimed in the preview.
        snapshot = run.snapshot()
        assert snapshot['status'] == 'running'
        assert snapshot['partialResult']['concepts']
        assert snapshot['result'] is None
        assert snapshot['timings']['firstConceptMs'] >= snapshot['timings']['firstEvidenceMs']
        assert answer is generated
        assert actual_tags is tag_envelope and actual_places is rec_envelope
        assert remaining_allowance == 1
        event = TraceEvent(id='agent-test', step='agent-plan', status='ok', detail='Selected a bounded test.')
        on_event(event)
        from backend.models import AgentStep
        live = AgentStep(index=1, tool='rank', status='ok', detail='Fetched rank.', upstreamRequests=2)
        return AgentReport(mode='frontier_ai', status='complete', stoppingReason='One action completed.',
                           modelCalls=2, steps=[live])

    monkeypatch.setattr(research, 'run_agent', execute_agent)
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=3)

    assert run.status == research.STATUS_COMPLETE
    assert run.timings['completeMs'] >= run.timings['firstConceptMs']
    assert run.result['agent']['mode'] == 'frontier_ai'
    assert 'agent-plan' in [event['step'] for event in run.result['trace']]
    assert 'agent-plan' in [event['step'] for event in run.events]
    # The answer states the whole run's cost: what the run fetched, what
    # generate() fetched, and the agent's live workflows. Here the stub run
    # fetched 2 and the agent 2; the stub generate() fetched nothing more.
    assert run.result['delivery']['transportRequests'] == run.transport_requests
    assert run.transport_requests >= 2 and run.result['delivery']['kind'] == 'fresh'
