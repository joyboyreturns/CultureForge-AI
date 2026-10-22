"""The agent loop, with a fake model and a fake Qloo: nothing reaches a network.

The fake model returns a scripted sequence of structured answers; the fake
provider answers each workflow from fixed envelopes and records the calls.
"""
from __future__ import annotations

import json
import time

import pytest

from backend import agent, reasoning
from backend.models import (AgentAnalysis, AgentClaim, AgentStepPlan, Concept, Delivery, Evidence,
                            GenerateResponse, ProjectRequest, ProvenanceMetadata)
from backend.providers import QlooHarnessError

PLACE_A, PLACE_B, PLACE_C = 'urn-place-a', 'urn-place-b', 'urn-place-c'
TAG = 'urn:tag:interests:qloo:local_arts'


@pytest.fixture
def response():
    concept = Concept(
        id='direction-a', name='Neighbourhood table', tagline='A place to gather',
        description='Build the direction around this returned place.', budget='TBD',
        investment='Not estimated', signals=['local arts'], accent='#fff', image='',
        evidenceIds=['ev-place-a'], decisions=[{
            'id': 'decision-a', 'field': 'offering', 'proposal': 'Use this place',
            'evidenceIds': ['ev-place-a'], 'ruleId': 'anchor-culture', 'origin': 'cultureforge_rule'}])
    return GenerateResponse(
        projectId='cf-one', project=ProjectRequest(
            businessType='Hospitality', audience='creative locals', location='Brooklyn',
            budget='TBD', objectives=[]), concepts=[concept], signals=[], dataMode='live',
        conceptMode='evidence_composed', notice='Evidence-backed result.',
        provenance=ProvenanceMetadata(source='Qloo API', resolved_tags=[TAG]),
        evidence=[Evidence(id='ev-place-a', kind='entity', label='North Room', entityId=PLACE_A),
                  Evidence(id='ev-place-b', kind='entity', label='South Hall', entityId=PLACE_B),
                  Evidence(id='ev-tag-0', kind='tag', label='Local arts', tagId=TAG)],
        trace=[], delivery=Delivery(kind='fresh', transportRequests=2))


class FakeQloo:
    def __init__(self, fail_on: dict | None = None):
        self.calls: list[tuple[str, dict]] = []
        self.fail_on = fail_on or {}

    def run_workflow_cached(self, operation, payload):
        self.calls.append((operation, payload))
        if operation in self.fail_on:
            raise self.fail_on[operation]
        if operation == 'rank':
            return {'results': [{'entity_id': PLACE_B, 'name': 'South Hall'},
                                {'entity_id': PLACE_A, 'name': 'North Room'}]}, False, 1
        if operation == 'entity_tags':
            return {'results': [{'id': 'urn:tag:ambience:qloo:lively', 'name': 'Lively'}]}, False, 1
        if operation == 'recommend':
            return {'results': [{'entity_id': PLACE_C, 'name': 'East Studio'}]}, True, 0
        return {'results': []}, False, 1


def script(monkeypatch, *answers):
    """Make the model return these answers in order; an exception is raised."""
    queue = list(answers)
    calls = []

    def fake(prompt, payload, output_model, **kwargs):
        calls.append({'prompt': prompt, 'payload': payload, 'model': output_model, **kwargs})
        answer = queue.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer
    monkeypatch.setattr(reasoning, 'call_structured', fake)
    monkeypatch.setattr(reasoning, 'configured', lambda: True)
    return calls


def plan(tool, reason='Sharpen the anchor.', **arguments):
    return AgentStepPlan(tool=tool, arguments=arguments, question='Does the anchor hold?', reason=reason)


def analysis(*claims, recommended='direction-a'):
    return AgentAnalysis(claims=list(claims), recommendedDirectionId=recommended,
                         summary='The anchor ranks below its alternative for this profile.',
                         whatWouldChangeTheConclusion='A different profile or location.')


def test_a_valid_run_plans_acts_observes_and_cites(monkeypatch, response, store):
    calls = script(monkeypatch,
                   plan('rank', options=[PLACE_A, PLACE_B], demographic='millennials'),
                   plan('entity_tags', entities=[PLACE_B]),
                   plan('finish', reason='The evidence answers the question.'),
                   analysis(AgentClaim(statement='South Hall outranks North Room for this profile.',
                                       citations=[PLACE_B, PLACE_A], directionId='direction-a'),
                            AgentClaim(statement='South Hall carries a lively ambience tag.',
                                       citations=[PLACE_B, 'urn:tag:ambience:qloo:lively'])))
    qloo = FakeQloo()
    events = []
    report = agent.run_agent(response, {}, {}, None, time.time() + 60, events.append, provider=qloo)

    assert report.mode == 'frontier_ai' and report.status == 'complete'
    assert [step.tool for step in report.steps] == ['rank', 'entity_tags', 'finish']
    assert [operation for operation, _ in qloo.calls] == ['rank', 'entity_tags']
    # The server built the rank request, with the brief's location.
    assert qloo.calls[0][1] == {'options': [PLACE_A, PLACE_B], 'option_type': 'place',
                                'signal_location': 'Brooklyn', 'demographic': 'millennials'}
    assert len(report.analysis['claims']) == 2 and report.rejectedClaims == []
    assert report.analysis['claims'][0]['citations'][0] == {'id': PLACE_B, 'label': 'South Hall'}
    assert report.modelCalls == 4
    assert [event.step for event in events] == ['agent-step-1', 'agent-step-2', 'agent-step-3', 'agent-analysis']
    # The tag the second step observed was citable in the analysis.
    assert calls[-1]['model'] is AgentAnalysis


def test_an_uncited_or_numeric_claim_is_rejected_and_the_rest_kept(monkeypatch, response, store):
    script(monkeypatch, plan('rank', options=[PLACE_A, PLACE_B]), plan('finish'),
           analysis(AgentClaim(statement='South Hall outranks North Room here.', citations=[PLACE_B, PLACE_A]),
                    AgentClaim(statement='A rival venue nearby draws the same crowd.', citations=['urn-invented']),
                    AgentClaim(statement='North Room would capture forty percent, or 40%.', citations=[PLACE_A])))
    report = agent.run_agent(response, {}, {}, None, time.time() + 60, provider=FakeQloo())
    assert len(report.analysis['claims']) == 1
    reasons = [item['reason'] for item in report.rejectedClaims]
    assert any('not in this run' in reason for reason in reasons)
    assert any('number' in reason for reason in reasons)


def test_when_every_claim_fails_validation_the_rules_answer_stands(monkeypatch, response, store):
    events = []
    script(monkeypatch, plan('rank', options=[PLACE_A, PLACE_B]), plan('finish'),
           analysis(AgentClaim(statement='An unseen venue dominates.', citations=['urn-invented'])))
    report = agent.run_agent(response, {}, {}, None, time.time() + 60, events.append, provider=FakeQloo())
    assert report.mode == 'rules' and report.status == 'limited'
    assert 'rule composer' in report.stoppingReason
    assert events[-1].step == 'agent-analysis' and events[-1].status == 'error'


def test_malformed_model_output_falls_back_and_says_so(monkeypatch, response, store):
    events = []
    script(monkeypatch, reasoning.AnalysisUnavailable('The analysis model could not return a valid structured answer.'))
    qloo = FakeQloo()
    report = agent.run_agent(response, {}, {}, None, time.time() + 60, events.append, provider=qloo)
    assert report.mode == 'rules' and report.status == 'limited'
    assert 'valid plan' in report.stoppingReason and 'rule composer' in report.stoppingReason
    assert qloo.calls == []
    assert events[0].status == 'error'


def test_a_429_mid_loop_stops_the_tools_but_not_the_analysis(monkeypatch, response, store):
    script(monkeypatch,
           plan('rank', options=[PLACE_A, PLACE_B]),
           plan('entity_tags', entities=[PLACE_A]),
           analysis(AgentClaim(statement='South Hall outranks North Room here.', citations=[PLACE_B])))
    qloo = FakeQloo(fail_on={'entity_tags': QlooHarnessError('Qloo rate limited this key.', code='RATE_LIMITED')})
    report = agent.run_agent(response, {}, {}, None, time.time() + 60, provider=qloo)
    assert [step.status for step in report.steps] == ['ok', 'error']
    assert 'RATE_LIMITED' in report.stoppingReason
    assert report.mode == 'frontier_ai' and report.analysis['claims']
    assert [operation for operation, _ in qloo.calls] == ['rank', 'entity_tags']


def test_an_unobserved_identifier_is_rejected_without_a_call(monkeypatch, response, store):
    script(monkeypatch, plan('describe', entity='urn-made-up'), plan('finish'),
           analysis(AgentClaim(statement='North Room is the cited anchor.', citations=[PLACE_A])))
    qloo = FakeQloo()
    report = agent.run_agent(response, {}, {}, None, time.time() + 60, provider=qloo)
    assert report.steps[0].status == 'rejected' and 'not observed' in report.steps[0].detail
    assert qloo.calls == []


def test_judging_is_bounded_by_steps_and_dev_by_its_allowances(monkeypatch, response, store):
    monkeypatch.setenv('RUN_PROFILE', 'judging')
    script(monkeypatch, *([plan('recommend', target_type='artist', signal_tags=[TAG])] * agent.MAX_STEPS),
           analysis(AgentClaim(statement='East Studio shares the audience tag.', citations=[PLACE_C, TAG])))
    report = agent.run_agent(response, {}, {}, None, time.time() + 60, provider=FakeQloo())
    assert len(report.steps) == agent.MAX_STEPS
    assert 'limit of 8 steps' in report.stoppingReason

    # dev: one live Qloo workflow left, and a model allowance of ten a day.
    monkeypatch.setenv('RUN_PROFILE', 'dev')
    store._cache.clear()
    script(monkeypatch, plan('rank', options=[PLACE_A, PLACE_B]), plan('entity_tags', entities=[PLACE_A]),
           analysis(AgentClaim(statement='South Hall outranks North Room here.', citations=[PLACE_B])))
    qloo = FakeQloo()
    report = agent.run_agent(response, {}, {}, 1, time.time() + 60, provider=qloo)
    assert [step.status for step in report.steps] == ['ok', 'skipped']
    assert [operation for operation, _ in qloo.calls] == ['rank']
    assert 'allowance' in report.stoppingReason


def test_a_repeated_run_of_the_same_evidence_is_held(monkeypatch, response, store):
    script(monkeypatch, plan('finish'),
           analysis(AgentClaim(statement='North Room is the cited anchor.', citations=[PLACE_A])))
    first = agent.run_agent(response, {}, {}, None, time.time() + 60, provider=FakeQloo())
    assert first.mode == 'frontier_ai'
    script(monkeypatch)  # an empty script: any model call would fail the test
    again = agent.run_agent(response, {}, {}, None, time.time() + 60, provider=FakeQloo())
    assert again.cached is True and again.modelCalls == 0 and again.analysis == first.analysis


def test_without_a_model_nothing_is_attempted(response):
    events = []
    report = agent.run_agent(response, {}, {}, 1, time.time() + 30, events.append)
    assert report.mode == 'rules' and report.status == 'skipped' and report.modelCalls == 0
    assert events[0].status == 'skipped'


def test_the_planning_request_carries_the_schema_and_a_small_budget(monkeypatch, response, store):
    monkeypatch.setattr(reasoning, '_reserve', lambda: None)
    monkeypatch.setattr(reasoning, 'configured', lambda: True)
    monkeypatch.setenv('AI_GATEWAY_MODEL', 'test/frontier-model')
    monkeypatch.setenv('AI_GATEWAY_API_KEY', 'test-only-placeholder')
    sent = []

    class Answer:
        def __init__(self, content):
            self.content = content
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return json.dumps({'choices': [{'message': {'content': json.dumps(self.content)}}]}).encode()

    def fake_urlopen(request, timeout):
        sent.append((json.loads(request.data), timeout))
        return Answer({'tool': 'finish', 'arguments': {}, 'reason': 'Nothing more to learn.'}) if len(sent) == 1 \
            else Answer({'claims': [{'statement': 'North Room is the cited anchor.', 'citations': [PLACE_A]}],
                         'summary': 'The cited anchor stands.', 'whatWouldChangeTheConclusion': 'Another place.'})
    monkeypatch.setattr(reasoning.urllib.request, 'urlopen', fake_urlopen)

    report = agent.run_agent(response, {}, {}, None, time.time() + 60, provider=FakeQloo())
    plan_body, plan_timeout = sent[0]
    assert plan_body['reasoning'] == {'effort': 'low'} and plan_body['max_tokens'] == 1200 and plan_timeout == 45
    assert '"tool"' in plan_body['messages'][0]['content']  # the schema travels with the prompt
    assert 'test-only-placeholder' not in json.dumps(plan_body)
    assert report.mode == 'frontier_ai'
