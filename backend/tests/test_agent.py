from __future__ import annotations

import time

import pytest

from backend import agent
from backend.models import (AgentAction, Concept, Delivery, Evidence,
                            EvidenceAnalysisResult, GenerateResponse, ProjectRequest)


@pytest.fixture
def response():
    concept = Concept(
        id='direction-a', name='Neighbourhood table', tagline='A place to gather',
        description='Build the direction around this returned place.', budget='TBD',
        investment='Not estimated', signals=['local arts'], accent='#fff', image='',
        evidenceIds=['ev-place-a'], decisions=[{
            'id': 'decision-a', 'field': 'anchor', 'proposal': 'Use this place',
            'evidenceIds': ['ev-place-a'], 'ruleId': 'anchor-culture',
        }])
    return GenerateResponse(
        projectId='cf-one', project=ProjectRequest(
            businessType='Hospitality', audience='creative locals', location='Brooklyn',
            budget='TBD', objectives=[]), concepts=[concept], signals=[], dataMode='live',
        conceptMode='evidence_composed', notice='Evidence-backed result.',
        evidence=[Evidence(id='ev-place-a', kind='entity', label='North Room', entityId='urn:place:north')],
        trace=[], delivery=Delivery(kind='fresh', transportRequests=2))


def reflection():
    return EvidenceAnalysisResult(
        directions=[], recommendationRationale='The direction remains a hypothesis.',
        whatWouldChangeTheConclusion='A new result from another audience.', model='Frontier AI')


def test_agent_executes_one_valid_removal_from_this_runs_exact_evidence(response, monkeypatch, store):
    monkeypatch.setattr(agent.reasoning, 'configured', lambda: True)
    action = AgentAction(operation='remove_anchor', directionId='direction-a', evidenceId='ev-place-a',
                         question='Does the direction survive without its place?',
                         reason='The current direction cites one returned place.')
    monkeypatch.setattr(agent.reasoning, 'call_structured', lambda *_args: action)
    contexts = []
    monkeypatch.setattr(agent.reasoning, 'analyze', lambda _request, agent_context=None:
                        contexts.append(agent_context) or reflection())
    envelopes = {
        'tags': {'operation': 'find_tags', 'results': [{'id': 'urn:tag:art'}]},
        'places': {'operation': 'recommend', 'results': [{'entity_id': 'urn:place:north'}]},
    }
    calls = []
    def fake_recompose(project, **kwargs):
        calls.append((project, kwargs))
        return {'concepts': [], 'evidence': [], 'notice': 'held evidence'}
    monkeypatch.setattr(agent, 'recompose', fake_recompose)

    report = agent.run_agent(response, envelopes['tags'], envelopes['places'], 1,
                              time.time() + 30)

    assert report.mode == 'frontier_ai' and report.status == 'complete'
    assert len(calls) == 1
    assert calls[0][1]['tag_envelope'] is envelopes['tags']
    assert calls[0][1]['recommend_envelope'] is envelopes['places']
    assert calls[0][1]['exclude_entity_ids'] == ['urn:place:north']
    assert response.concepts[0].description == 'Build the direction around this returned place.'
    assert report.observation.upstreamRequests == 0
    assert report.observation.result['after'] is None
    assert contexts[0]['observation']['result']['after'] is None
    assert report.modelCalls == 2


def test_agent_rejects_fabricated_tool_ids_without_execution(response, monkeypatch, store):
    monkeypatch.setattr(agent.reasoning, 'configured', lambda: True)
    monkeypatch.setattr(agent.reasoning, 'call_structured', lambda *_args: AgentAction(
        operation='remove_anchor', directionId='direction-a', evidenceId='invented',
        question='Remove the selected place?', reason='It might change the result.'))
    monkeypatch.setattr(agent, 'recompose', lambda *_args, **_kwargs: pytest.fail('invalid tool must not execute'))

    report = agent.run_agent(response, {'results': []}, {'results': []}, 1,
                              time.time() + 30)

    assert report.mode == 'rules' and report.status == 'limited'
    assert 'do not belong' in report.stoppingReason
    assert report.observation is None


def test_agent_stops_without_retry_when_planner_is_unavailable(response, monkeypatch, store):
    monkeypatch.setattr(agent.reasoning, 'configured', lambda: True)
    attempts = []
    def unavailable(*_args):
        attempts.append(1)
        raise agent.reasoning.AnalysisUnavailable('Gateway unavailable.')
    monkeypatch.setattr(agent.reasoning, 'call_structured', unavailable)

    report = agent.run_agent(response, {'results': []}, {'results': []}, 1,
                              time.time() + 30)

    assert len(attempts) == 1
    assert report.status == 'limited' and report.mode == 'rules'
    assert report.modelCalls == 1  # one request was attempted; no retry followed
    assert 'Gateway unavailable' in report.stoppingReason


def test_agent_disabled_preserves_rules_result_without_model_call(response, monkeypatch, store):
    monkeypatch.setattr(agent.reasoning, 'configured', lambda: False)
    monkeypatch.setattr(agent.reasoning, 'call_structured', lambda *_args: pytest.fail('must not call the model'))

    events = []
    report = agent.run_agent(response, {'results': []}, {'results': []}, 1,
                              time.time() + 30, events.append)

    assert report.mode == 'rules' and report.status == 'skipped'
    assert report.modelCalls == 0
    assert events[0].status == 'skipped'


def test_frontier_ai_request_includes_the_pydantic_output_schema(monkeypatch, tmp_path):
    import json
    from backend import reasoning

    monkeypatch.setattr(reasoning, '_reserve', lambda: None)
    monkeypatch.setenv('AI_GATEWAY_MODEL', 'test/frontier-model')
    monkeypatch.setenv('AI_GATEWAY_API_KEY', 'test-only-placeholder')
    captured = {}

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return json.dumps({'choices': [{'message': {'content': json.dumps({
                'operation': 'finish', 'reason': 'The evidence already answers this question.'})}}]}).encode()

    def fake_urlopen(request, timeout):
        captured['body'] = json.loads(request.data)
        captured['timeout'] = timeout
        return Response()

    monkeypatch.setattr(reasoning.urllib.request, 'urlopen', fake_urlopen)
    action = reasoning.call_structured('Choose one action.', {'evidence': []}, AgentAction)

    schema_prompt = captured['body']['messages'][0]['content']
    assert '"operation"' in schema_prompt and 'remove_anchor' in schema_prompt
    assert action.operation == 'finish'
    assert captured['body']['response_format'] == {'type': 'json_object'}
    assert captured['timeout'] == reasoning.TIMEOUT_SECONDS
