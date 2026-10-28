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
    interpret_idea = QlooHarnessProvider.interpret_idea
    confirmed_tag_envelope = QlooHarnessProvider.confirmed_tag_envelope
    _cached_tag_rows = staticmethod(QlooHarnessProvider._cached_tag_rows)

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


# --- how an idea that cannot be resolved ends: a typed question with working ways out ---------------------------
def _idea_project(idea):
    return ProjectRequest(businessType='Retail', businessIdea=idea, audience='Design-conscious Gen Z',
                          location='Tokyo, Japan', budget='$25k – $50k', objectives=['x'])


def test_an_unsupported_category_asks_instead_of_substituting(monkeypatch):
    # the same envelope answers every find_tags: an audience seed, and a category tag that is not a sneaker store
    envelope = {'status': 'ok', 'results': [{'id': 'urn:tag:interests:qloo:design', 'name': 'Design'},
                                            {'id': 'urn:tag:category:place:shoe_store', 'name': 'Shoe Store'}]}
    provider = _install(monkeypatch, StubProvider(envelope, {'status': 'ok', 'results': [{'name': 'x'}]}))
    run = research.ResearchRun(_idea_project('Vintage sneaker store'))
    research._execute(run, allowance=8)
    assert run.status == research.STATUS_CLARIFY and run.clarification['code'] == 'UNSUPPORTED_CATEGORY'
    assert run.clarification['field'] == 'businessIdea'
    assert run.clarification['actions'] == [], 'a rewrite that was already searched and failed is not offered again'
    assert provider.workflow_calls == 3, 'audience, the specific search and its one broader search; no places requested'


def test_an_idea_that_names_no_business_asks_before_spending_a_category_or_places_request(monkeypatch):
    envelope = {'status': 'ok', 'results': [{'id': 'urn:tag:interests:qloo:design', 'name': 'Design'}]}
    provider = _install(monkeypatch, StubProvider(envelope, {'status': 'ok', 'results': [{'name': 'x'}]}))
    run = research.ResearchRun(_idea_project('a place for stuff'))
    research._execute(run, allowance=8)
    assert run.clarification['code'] == 'AMBIGUOUS_IDEA' and provider.workflow_calls == 1


def test_a_category_without_local_places_is_not_called_an_unsupported_category(monkeypatch):
    envelope = {'status': 'ok', 'results': [{'id': 'urn:tag:interests:qloo:design', 'name': 'Design'},
                                            {'id': 'urn:tag:category:place:bakery', 'name': 'Bakery'}]}
    _install(monkeypatch, StubProvider(envelope, {'status': 'ok', 'results': []}))
    run = research.ResearchRun(ProjectRequest(businessType='Food & beverage', businessIdea='Bakery',
                                              audience='Design-conscious Gen Z', location='Tokyo, Japan',
                                              budget='$25k – $50k', objectives=['x']))
    research._execute(run, allowance=8)
    assert run.clarification['code'] == 'CATEGORY_NO_PLACES' and run.clarification['field'] == 'location'
    assert 'gap in Qloo' in run.clarification['reason']


def test_a_run_with_no_direction_does_not_spend_the_agent(monkeypatch):
    """Observed live (Denver bouldering, Mexico City bookshop cafe): 5 Qloo requests and ~100 s of agent
    loop on a brief that composed nothing. The honest answer should arrive without them."""
    tag_envelope = {'status': 'ok', 'operation': 'find_tags', 'results': [{'id': 'urn:tag:x:qloo:y'}]}
    rec_envelope = {'status': 'ok', 'operation': 'recommend',
                    'results': [{'entity_id': 'urn:place:far', 'name': 'Far Gym'}]}
    empty = GenerateResponse(
        projectId='cf-run', project=PROJECT, concepts=[], signals=[], dataMode='live',
        conceptMode='evidence_composed', notice='did not support a relevant business direction',
        evidence=[Evidence(id='ev-place-a', kind='entity', label='Far Gym', entityId='urn:place:far')],
        trace=[], delivery=Delivery(kind='fresh', transportRequests=1))
    _install(monkeypatch, StubProvider(tag_envelope, rec_envelope, empty))

    def forbidden(*_args, **_kwargs):
        raise AssertionError('the agent must not run when there is no direction')
    monkeypatch.setattr(research, 'run_agent', forbidden)
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=None)
    assert run.status == research.STATUS_COMPLETE and run.result['concepts'] == []
    assert run.result['agent']['status'] == 'skipped' and 'did not run' in run.result['agent']['stoppingReason']
    skipped = [event for event in run.events if event['step'] == 'agent-plan']
    assert skipped and skipped[0]['status'] == 'skipped'


def test_a_held_agent_report_costs_the_run_nothing(monkeypatch):
    """Observed live: a free replay of a held brief reported 2 upstream requests, borrowed from the steps
    that an earlier run had paid for."""
    from backend.models import AgentStep
    tag_envelope = {'status': 'ok', 'operation': 'find_tags', 'results': [{'id': 'urn:tag:x:qloo:y'}]}
    rec_envelope = {'status': 'ok', 'operation': 'recommend', 'results': [{'entity_id': 'urn:place:a', 'name': 'A'}]}
    concept = Concept(id='d', name='N', tagline='t', description='d', budget='TBD', investment='x', signals=[], accent='#fff',
                      image='', evidenceIds=['ev-place-a'], decisions=[{'id': 'x', 'field': 'f', 'proposal': 'p',
                                                                        'evidenceIds': ['ev-place-a'], 'ruleId': 'r'}])
    generated = GenerateResponse(
        projectId='cf-run', project=PROJECT, concepts=[concept], signals=[], dataMode='live', conceptMode='evidence_composed',
        notice='n', evidence=[Evidence(id='ev-place-a', kind='entity', label='A', entityId='urn:place:a')], trace=[],
        delivery=Delivery(kind='cache', transportRequests=0))
    provider = _install(monkeypatch, StubProvider(tag_envelope, rec_envelope, generated))
    provider.generate = lambda project, **_kw: generated.model_copy(deep=True)  # the run edits its delivery
    earlier = AgentStep(index=1, tool='rank', status='ok', detail='Fetched rank.', upstreamRequests=2)
    monkeypatch.setattr(research, 'run_agent', lambda *a, **k: AgentReport(
        mode='frontier_ai', status='complete', stoppingReason='held', modelCalls=0, cached=True, steps=[earlier]))
    run = research.ResearchRun(PROJECT)
    research._execute(run, allowance=None)
    held_requests = run.transport_requests - 2  # the stub provider's own find_tags + recommend
    assert held_requests == 0
    assert run.result['delivery']['transportRequests'] == run.transport_requests


def test_confirmed_seeds_retain_cached_names_and_popularities(monkeypatch, store):
    from backend.evidence_store import canonical_key
    from backend.providers import brief_tags_payload

    store.put(canonical_key('find_tags', brief_tags_payload(PROJECT.businessType, PROJECT.audience)), {
        'operation': 'find_tags', 'status': 'ok',
        'results': [{'id': 'urn:tag:x:qloo:y', 'name': 'Food design', 'popularity': 0.91}],
    })
    rec_envelope = {'status': 'ok', 'operation': 'recommend', 'results': [{'entity_id': 'urn:place:a', 'name': 'A'}]}
    generated = GenerateResponse(
        projectId='cf-run', project=PROJECT, concepts=[], signals=[], dataMode='live',
        conceptMode='evidence_composed', notice='n', evidence=[], trace=[],
        delivery=Delivery(kind='cache', transportRequests=0))
    captured_tags = {}

    class CapturingProvider(StubProvider):
        def generate(self, project, **kwargs):
            if kwargs.get('tag_result') is not None:
                captured_tags['envelope'] = kwargs['tag_result']
            return generated.model_copy(deep=True)

    _install(monkeypatch, CapturingProvider({}, rec_envelope, generated))
    run = research.ResearchRun(PROJECT)
    run.seed_tag_ids = ['urn:tag:x:qloo:y']
    research._execute(run, allowance=None)
    assert captured_tags['envelope']['results'] == [{'id': 'urn:tag:x:qloo:y', 'name': 'Food design', 'popularity': 0.91}]

