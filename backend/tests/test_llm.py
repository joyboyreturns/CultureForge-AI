"""The free naming layer: the guard, the budget, and the refusal to spend.

No network is touched here. The point of these tests is that the model can
never make the app show a number Qloo did not return, and can never make it
spend money.
"""
from __future__ import annotations

import pytest

from backend import llm


EVIDENCE = [
    {'id': 'ev-entity-2', 'kind': 'entity', 'label': 'Whitney Museum of American Art',
     'description': 'A museum of American art in New York City.',
     'popularity': 0.7311, 'affinity': 0.51, 'rating': 4.5, 'priceLevel': 2},
]


def test_a_number_qloo_returned_somewhere_else_is_still_dropped():
    """A number that exists in the evidence does not license the model here.

    The place is rated 4.5 and has a popularity of 0.7311. Neither of those
    makes "the 4.5 rated museum" a true statement about a *different* place,
    and neither licenses a service time. The guard is strict: no numbers in
    a model-written name or tagline, unless the name is a name Qloo returned.
    """
    answer = {'directions': [{'index': 0, 'name': 'The Reading Room',
                              'tagline': 'A room for the 4.5 rated museum'}]}
    usable, dropped = llm.validate_directions(answer, EVIDENCE)
    assert usable[0]['name'] == 'The Reading Room'
    assert usable[0]['tagline'] is None
    assert len(dropped) == 1


def test_a_name_that_is_a_qloo_name_may_keep_its_digits():
    """The exception: the model's name is exactly a name Qloo returned."""
    answer = {'directions': [{'index': 0, 'name': 'Whitney Museum of American Art',
                              'tagline': 'A room for it'}]}
    usable, dropped = llm.validate_directions(answer, EVIDENCE)
    assert usable[0]['name'] == 'Whitney Museum of American Art'
    assert dropped == []


def test_a_number_the_model_invented_is_dropped():
    """The rule the codebase holds to: no number Qloo did not return."""
    answer = {'directions': [{'index': 0, 'name': 'The 9000 Square Foot Room',
                              'tagline': 'A good line'}]}
    usable, dropped = llm.validate_directions(answer, EVIDENCE)
    # The name carries the invented number, so it goes.
    assert usable[0]['name'] is None
    # The tagline does not, so it stays.
    assert usable[0]['tagline'] == 'A good line'
    assert len(dropped) == 1


def test_a_direction_with_nothing_usable_is_not_returned():
    answer = {'directions': [{'index': 0, 'name': '9000', 'tagline': '12', 'rationale': '3'}]}
    usable, dropped = llm.validate_directions(answer, EVIDENCE)
    assert usable == {}
    assert dropped


def test_a_citation_is_dropped():
    answer = {'directions': [{'index': 0, 'name': 'The Reading Room',
                              'tagline': 'See https://example.com for more',
                              'rationale': 'A model that has drifted into citing its sources.'}]}
    usable, _dropped = llm.validate_directions(answer, EVIDENCE)
    assert usable[0]['tagline'] is None
    assert usable[0]['name'] == 'The Reading Room'


def test_an_answer_that_is_not_json_is_not_used():
    with pytest.raises(llm.LlmUnavailable):
        llm._parse_json('I think the name should be the Reading Room.')


def test_json_wrapped_in_a_fence_is_read():
    parsed = llm._parse_json('```json\n{"directions": [{"index": 0, "name": "A"}]}\n```')
    assert parsed['directions'][0]['name'] == 'A'


def test_a_placeholder_is_not_used():
    """A free model sometimes answers "...". That is a refusal, not a name."""
    answer = {'directions': [{'index': 0, 'name': '...', 'tagline': '...',
                              'rationale': '...'}]}
    usable, dropped = llm.validate_directions(answer, EVIDENCE)
    assert usable == {}, 'a placeholder must not reach the screen'


def test_a_placeholder_field_is_dropped_but_the_rest_stays():
    answer = {'directions': [{'index': 0, 'name': '...', 'tagline': 'A real tagline here.',
                              'rationale': 'A real reason why this audience fits this place here.'}]}
    usable, _dropped = llm.validate_directions(answer, EVIDENCE)
    assert usable[0]['name'] is None
    assert usable[0]['tagline'] == 'A real tagline here.'


def test_every_model_in_the_chain_is_free():
    """A paid model in the chain would be billed. There is no budget for that."""
    for model in llm.FREE_MODELS:
        assert model == 'openrouter/free' or model.endswith(':free'), model
    for model in llm.FALLBACK_CHAIN:
        assert model == 'openrouter/free' or model.endswith(':free'), model
    assert llm.FALLBACK_CHAIN[0] == llm.DEFAULT_MODEL


def test_the_fallback_chain_fits_openrouters_limit():
    """OpenRouter rejects a `models` array with more than three entries."""
    assert len(llm.FALLBACK_CHAIN) <= 3


def test_the_request_caps_the_reasoning(monkeypatch):
    """A reasoning model given the whole budget answers with nothing."""
    sent: list[dict] = []

    def fake_post(payload, timeout):
        sent.append(payload)
        return {'model': 'test/free', 'choices': [{'message': {'content': '{"directions": []}'}}]}

    monkeypatch.setattr(llm, '_post', fake_post)
    llm._ask_model({'businessType': 'x'}, [], 5)

    assert sent, 'the model was asked'
    assert sent[0]['reasoning'] == {'max_tokens': llm.REASONING_MAX_TOKENS}
    assert sent[0]['max_tokens'] == llm.DEFAULT_MAX_TOKENS


def test_a_gone_model_falls_through_to_the_next(monkeypatch):
    """A free model can be withdrawn at any time."""
    tried: list[str] = []

    def fake_post(payload, timeout):
        tried.append(payload['model'])
        if len(tried) == 1:
            raise llm.LlmUnavailable('The model refused the request (404).',
                                     code='LLM_REJECTED', details={'status': 404})
        return {'model': 'test/free', 'choices': [{'message': {'content': '{"directions": []}'}}]}

    monkeypatch.setattr(llm, '_post', fake_post)
    answer, model, served = llm._ask_model({'businessType': 'x'}, [], 5)

    assert len(tried) >= 2, 'the next model got the request'
    assert model == 'test/free'
    # The refused attempt served nothing, so only the one that answered is
    # counted against the tier.
    assert served == 1


def test_a_model_that_answers_with_nothing_falls_through(monkeypatch):
    """A reasoning model that spends its budget thinking answers with nothing."""
    tried: list[str] = []

    def fake_post(payload, timeout):
        tried.append(payload['model'])
        if len(tried) == 1:
            raise llm.LlmUnavailable('The model returned an empty answer.',
                                     code='LLM_EMPTY', details={'raw': 'it reasoned'})
        return {'model': 'test/free', 'choices': [{'message': {'content': '{"directions": []}'}}]}

    monkeypatch.setattr(llm, '_post', fake_post)
    _answer, model, _spent = llm._ask_model({'businessType': 'x'}, [], 5)

    assert len(tried) >= 2
    assert model == 'test/free'


def test_a_paid_model_is_refused(monkeypatch):
    monkeypatch.setenv('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4')
    assert llm._model() == llm.DEFAULT_MODEL
    monkeypatch.setenv('OPENROUTER_MODEL', 'minimax/minimax-m3.1-flash:free')
    assert llm._model() == 'minimax/minimax-m3.1-flash:free'


def test_without_a_key_nothing_is_attempted(monkeypatch):
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    names, report = llm.name_directions({}, [], [])
    assert names == {}
    assert report['used'] is False
    assert report['attempted'] is False
    assert 'key' in report['reason'].lower()


def test_the_suite_never_reaches_the_model():
    """The free tier is 50 requests a day, and a test must not spend one."""
    assert llm.is_configured() is False, (
        'the suite reached the model layer: the conftest fixture that keeps it '
        'off has been overridden')


def test_the_budget_guard_stops_the_calls(monkeypatch, tmp_path):
    """The free tier is finite, and the guard sits at it."""
    log = tmp_path / 'llm_calls.json'
    monkeypatch.setattr(llm, 'BUDGET_LOG_PATH', log)
    monkeypatch.setenv('LLM_MAX_CALLS_PER_HOUR', '1')
    monkeypatch.setenv('LLM_MAX_CALLS_PER_DAY', '1')
    llm._check_budget()
    llm._record_call()
    with pytest.raises(llm.LlmUnavailable) as caught:
        llm._check_budget()
    assert caught.value.code == 'LLM_QUOTA_EXHAUSTED'


def test_a_refusal_is_not_charged(monkeypatch, tmp_path):
    """A model that is withdrawn or busy serves nothing, so it costs nothing."""
    log = tmp_path / 'llm_calls.json'
    monkeypatch.setattr(llm, 'BUDGET_LOG_PATH', log)
    llm._check_budget()          # the check spends nothing
    assert not log.exists() or llm._read_calls() == []
    llm._record_call()           # only a request that reached a model counts
    assert len(llm._read_calls()) == 1


def test_a_refusing_model_is_skipped_on_the_next_brief(monkeypatch, tmp_path):
    """The failover is instant, because the refusal is remembered."""
    health = tmp_path / 'llm_models.json'
    monkeypatch.setattr(llm, 'MODEL_HEALTH_PATH', health)
    monkeypatch.setattr(llm, 'BUDGET_LOG_PATH', tmp_path / 'llm_calls.json')

    first, second = llm.FALLBACK_CHAIN[0], llm.FALLBACK_CHAIN[1]
    assert llm.healthy_models()[0] == first

    llm._mark_unhealthy(first, 429)
    assert llm.healthy_models()[0] == second, 'the refusing model is asked last'
    assert first in llm.healthy_models(), 'but it is still in the chain'

    llm._mark_healthy(first)
    assert llm.healthy_models()[0] == first


def test_a_withdrawn_model_is_skipped_for_longer(monkeypatch, tmp_path):
    health = tmp_path / 'llm_models.json'
    monkeypatch.setattr(llm, 'MODEL_HEALTH_PATH', health)
    llm._mark_unhealthy(llm.FALLBACK_CHAIN[0], 404)
    stored = llm._read_health()[llm.FALLBACK_CHAIN[0]]
    assert stored['until'] - stored['until'] + 12 * 60 * 60 >= 12 * 60 * 60 - 1
    assert llm.healthy_models()[0] != llm.FALLBACK_CHAIN[0]


def test_the_health_reads_a_half_written_file(monkeypatch, tmp_path):
    """A file that is being written while it is read must not break /api/health."""
    health = tmp_path / 'llm_models.json'
    monkeypatch.setattr(llm, 'MODEL_HEALTH_PATH', health)
    health.write_text('{"cohere/north-mini-code:free": {"good": 1', encoding='utf-8')
    state = llm.status()
    assert state['models'], 'the models are still listed'
    assert state['budget']['dayLimit'] > 0


def test_a_model_entry_without_a_cooldown_is_read(monkeypatch, tmp_path):
    """A model that only has an outcome recorded has no cooldown to read."""
    health = tmp_path / 'llm_models.json'
    monkeypatch.setattr(llm, 'MODEL_HEALTH_PATH', health)
    llm._mark_outcome('cohere/north-mini-code:free', usable=True, duration_ms=4000)
    state = llm.status()
    entry = next(m for m in state['models'] if m['id'] == 'cohere/north-mini-code:free')
    assert entry['answering'] is True
    assert entry['until'] is None
    assert entry['good'] == 1


def test_a_model_in_cooldown_is_asked_last_and_then_retried(monkeypatch, tmp_path):
    """A model in cooldown is not dropped — it is asked last, and comes back."""
    health = tmp_path / 'llm_models.json'
    monkeypatch.setattr(llm, 'MODEL_HEALTH_PATH', health)
    learned = 'minimax/minimax-m3.1-flash:free'

    llm._mark_outcome(learned, usable=True, duration_ms=4000)
    assert llm.healthy_models()[0] == learned, 'the learned model comes first'

    llm._mark_unhealthy(learned, 404)
    order = llm.healthy_models()
    assert learned in order, 'it is still in the chain'
    assert order[-1] == learned, 'but it is asked last while it is refusing'


def test_the_model_that_answered_well_is_asked_first(monkeypatch, tmp_path):
    """The router picks at random. The backend does not have to."""
    health = tmp_path / 'llm_models.json'
    monkeypatch.setattr(llm, 'MODEL_HEALTH_PATH', health)
    first, second = llm.FALLBACK_CHAIN[0], llm.FALLBACK_CHAIN[1]

    llm._mark_outcome(second, usable=True, duration_ms=4000)
    assert llm.healthy_models()[0] == second, 'the model that answered well comes first'

    llm._mark_outcome(first, usable=False, duration_ms=21000)
    assert llm.healthy_models()[0] == second, 'the model that answered with nothing goes last'


def test_a_quick_model_is_asked_before_a_slow_one(monkeypatch, tmp_path):
    health = tmp_path / 'llm_models.json'
    monkeypatch.setattr(llm, 'MODEL_HEALTH_PATH', health)
    first, second = llm.FALLBACK_CHAIN[0], llm.FALLBACK_CHAIN[1]
    llm._mark_outcome(first, usable=True, duration_ms=20000)
    llm._mark_outcome(second, usable=True, duration_ms=3000)
    assert llm.healthy_models()[0] == second, 'the quick one comes first'


def test_the_model_is_never_shown_a_number():
    """The strongest guard: the prompt cannot quote what it was never shown."""
    brief = {
        'businessType': 'Food & beverage',
        'audience': 'Design-conscious Gen Z',
        'location': 'Brooklyn, New York',
        'budget': '$25k – $50k',
        'signals': ['design focused'],
    }
    directions = [{
        'index': 0,
        'currentName': 'The Design Floor',
        'currentTagline': 'A space that behaves like the thing it sells.',
        'currentPositioning': 'For an audience that treats taste as the primary signal of quality.',
        'venues': [{'name': 'Whitney Museum of American Art', 'role': 'primary',
                    'description': 'A museum of American art in New York City.'}],
    }]
    prompt = llm._build_user_prompt(brief, directions)
    for number in ('0.7311', '0.51', '4.5'):
        assert number not in prompt
    # The budget band is the founder's own, and it is fine to see it.
    assert '25k' in prompt
    assert 'Whitney Museum of American Art' in prompt


# ---------------------------------------------------------------------------
# The provider, end to end
# ---------------------------------------------------------------------------

def _stub_qloo(monkeypatch, provider, recommend_places):
    """Make the provider's Qloo calls return the captured fixture."""
    find_tags = {
        'status': 'ok',
        'results': [
            {'id': 'urn:tag:customer_segment:qloo:gen_z_foodies', 'name': 'Gen Z Foodies', 'popularity': 0.97},
            {'id': 'urn:tag:interests:qloo:modern_restaurant_design', 'name': 'Modern Restaurant Design', 'popularity': 0.98},
            {'id': 'urn:tag:interests:qloo:food_design', 'name': 'Food Design', 'popularity': 0.93},
        ],
        'execution': {'duration_ms': 1},
        'provenance': {'endpoint': 'stub', 'requests': []},
    }

    def fake(operation, payload):
        if operation == 'find_tags':
            return find_tags, False, 1
        return recommend_places, False, 1

    monkeypatch.setattr(provider, 'run_workflow_cached', fake)


def test_the_model_names_the_directions(monkeypatch, store, recommend_places):
    """The model writes the words; the rules keep the evidence."""
    from backend.models import ProjectRequest
    from backend.providers import QlooHarnessProvider

    monkeypatch.setattr(llm, 'is_configured', lambda: True)
    seen: list[dict] = []

    def fake_name(brief, directions, evidence):
        seen.append({'brief': brief, 'directions': directions, 'evidence': evidence})
        return {0: {'name': 'The Whitney Reading Room',
                    'tagline': 'A room that behaves like the art behind it.'}}, \
               {'used': True, 'attempted': True, 'model': 'openrouter/free', 'reason': None, 'dropped': []}

    monkeypatch.setattr(llm, 'name_directions', fake_name)

    provider = QlooHarnessProvider()
    _stub_qloo(monkeypatch, provider, recommend_places)
    project = ProjectRequest(
        businessType='Food & beverage', audience='Design-conscious Gen Z',
        location='Brooklyn, New York', budget='$25k – $50k',
        objectives=['Build a loyal community'],
    )
    response = provider.generate(project)

    assert response.concepts, 'the evidence still composes directions'
    assert response.concepts[0].name == 'The Whitney Reading Room'
    assert response.concepts[0].tagline == 'A room that behaves like the art behind it.'
    # The rationale is grounded in the evidence, not written by the model.
    assert 'Unlocked by' in (response.concepts[0].audienceRationale or '')
    # The evidence is untouched: the rules still chose it.
    assert response.concepts[0].evidenceIds
    assert response.evidence
    # The step is visible in the trace, and says who did the naming.
    step = next(event for event in response.trace if event.step == 'name-the-directions')
    assert step.status == 'ok'
    assert 'openrouter/free' in (step.detail or '')
    # The model was given the venues, and no numbers.
    assert seen[0]['directions'][0]['venues']
    entity = next(item for item in seen[0]['evidence'] if item.kind == 'entity')
    assert entity.popularity is not None


def test_the_names_are_held_so_a_repeat_costs_nothing(monkeypatch, store, recommend_places):
    """The free tier is 50 a day. A brief that was named before is free."""
    from backend.models import ProjectRequest
    from backend.providers import QlooHarnessProvider

    monkeypatch.setattr(llm, 'is_configured', lambda: True)
    calls: list[int] = []

    def fake_name(brief, directions, evidence):
        calls.append(1)
        return {0: {'name': 'The Whitney Reading Room', 'tagline': 'A room.'}}, \
               {'used': True, 'attempted': True, 'model': 'openrouter/free', 'reason': None, 'dropped': []}

    monkeypatch.setattr(llm, 'name_directions', fake_name)

    project = ProjectRequest(
        businessType='Food & beverage', audience='Design-conscious Gen Z',
        location='Brooklyn, New York', budget='$25k – $50k',
        objectives=['Build a loyal community'],
    )
    first = QlooHarnessProvider()
    _stub_qloo(monkeypatch, first, recommend_places)
    first.generate(project)

    # A second provider has an empty in-memory cache, so the naming has to be
    # found in the evidence store rather than asked for again.
    second = QlooHarnessProvider()
    _stub_qloo(monkeypatch, second, recommend_places)
    response = second.generate(project)

    assert calls == [1], 'the model was asked once'
    assert response.concepts[0].name == 'The Whitney Reading Room'
    step = next(event for event in response.trace if event.step == 'name-the-directions')
    assert 'held' in (step.detail or '').lower()


def test_a_failure_is_not_held(monkeypatch, store, recommend_places):
    """A model that could not answer must not be cached as the empty answer."""
    from backend.models import ProjectRequest
    from backend.providers import QlooHarnessProvider

    monkeypatch.setattr(llm, 'is_configured', lambda: True)
    calls: list[int] = []

    def fake_name(brief, directions, evidence):
        calls.append(1)
        return {}, {'used': False, 'attempted': True, 'model': None,
                    'reason': 'The model refused the request (429).', 'dropped': []}

    monkeypatch.setattr(llm, 'name_directions', fake_name)

    project = ProjectRequest(
        businessType='Food & beverage', audience='Design-conscious Gen Z',
        location='Brooklyn, New York', budget='$25k – $50k',
        objectives=['Build a loyal community'],
    )
    first = QlooHarnessProvider()
    _stub_qloo(monkeypatch, first, recommend_places)
    first.generate(project)

    second = QlooHarnessProvider()
    _stub_qloo(monkeypatch, second, recommend_places)
    second.generate(project)

    assert calls == [1, 1], 'the second run tried again instead of reading a held failure'


def test_without_a_model_the_rules_still_name_the_directions(monkeypatch, store, recommend_places):
    """No key, no model, no change in what the founder gets."""
    from backend.models import ProjectRequest
    from backend.providers import QlooHarnessProvider

    monkeypatch.setattr(llm, 'is_configured', lambda: False)
    provider = QlooHarnessProvider()
    _stub_qloo(monkeypatch, provider, recommend_places)
    project = ProjectRequest(
        businessType='Food & beverage', audience='Design-conscious Gen Z',
        location='Brooklyn, New York', budget='$25k – $50k',
        objectives=['Build a loyal community'],
    )
    response = provider.generate(project)

    assert response.concepts
    assert response.concepts[0].name != ''
    assert response.concepts[0].audienceRationale, 'the rule engine still explains the direction'
    step = next(event for event in response.trace if event.step == 'name-the-directions')
    assert step.status == 'skipped'
    assert 'rule engine' in (step.detail or '')


def test_a_claim_about_a_locality_qloo_did_not_establish_is_dropped():
    """Qloo returned a city. It did not return a neighbourhood.

    A tagline that says a place is "in the neighbourhood" is making a claim
    the evidence does not carry, so it goes — the same way an invented
    number goes.
    """
    answer = {'directions': [{'index': 0, 'name': 'The Reading Room',
                              'tagline': 'Meet the neighbourhood where the gallery comes alive.'}]}
    usable, dropped = llm.validate_directions(answer, EVIDENCE)
    assert usable[0]['name'] == 'The Reading Room'
    assert usable[0]['tagline'] is None
    assert len(dropped) == 1
    assert 'locality' in dropped[0]
