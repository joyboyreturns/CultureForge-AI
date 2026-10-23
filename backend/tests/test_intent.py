"""Business intent, tag resolution, hybrids, failures and caching. Offline: Qloo is scripted, never called."""
from __future__ import annotations

import json
import threading
import time

import pytest

from backend import category as taxonomy
from backend import config, intent as business_intent, llm, relevance
from backend.evidence_store import canonical_key, get_store
from backend.intent import interpret, validate_proposal
from backend.intent_report import held_tag, idea_alternatives, resolve_tag
from backend.models import ProjectRequest
from backend.providers import QlooHarnessError, QlooHarnessProvider, rank_category_tag


# --------------------------------------------------------------------------- the intent
@pytest.mark.parametrize('idea,ids', [
    ('A bakery combined with a bookstore in Paris', ['bakery', 'books']),
    ('Coffee shop with a coworking space', ['coffee', 'coworking']),
    ('Ice cream parlour and gaming lounge', ['frozen_dessert', 'gaming']),
    ('Vegan restaurant with a bakery', ['restaurant', 'bakery']),
    ('Bookstore that also serves specialty coffee', ['books', 'coffee']),
])
def test_a_hybrid_keeps_every_business(idea, ids):
    result = interpret(idea)
    assert result.hybrid and [c.categoryId for c in result.components] == ids


@pytest.mark.parametrize('idea', ['Fish and chips shop in Leeds', 'Wine and cheese shop', 'Bakery with outdoor seating',
                                  'Bakery and bakery', 'Vegan restaurant in Berlin'])
def test_ordinary_phrases_are_not_hybrids(idea):
    assert not interpret(idea).hybrid


def test_a_feature_after_with_is_disclosed_not_researched():
    result = interpret('Bakery with outdoor seating in Rome')
    assert [c.categoryId for c in result.components] == ['bakery']
    assert any('outdoor seating' in line for line in result.substitutions)


def test_specialisations_are_kept_on_the_component():
    assert interpret('Vegan restaurant in Berlin').primary.modifiers == ['vegan']
    assert interpret('Specialty coffee shop in Melbourne').primary.modifiers == ['specialty']
    assert interpret('Gluten-free bakery').primary.modifiers == ['gluten-free']
    assert interpret('Sustainable fashion boutique').primary.modifiers == ['sustainable']


def test_a_vintage_sneaker_store_is_looked_up_whole_then_without_the_specialisation_never_as_another_category():
    primary = interpret('Vintage sneaker store in Tokyo').primary
    assert primary.status == 'open_vocabulary' and primary.categoryId == ''
    assert primary.queries == ['vintage sneaker store', 'sneaker store'] and primary.modifiers == ['vintage']


def test_bubble_tea_is_discovered_not_mapped():
    primary = interpret('Bubble tea shop in Los Angeles').primary
    assert primary.status == 'open_vocabulary' and primary.queries == ['bubble tea shop']


def test_existing_canonical_handling_is_unchanged_and_costs_one_find_tags():
    primary = interpret('Ice cream parlour in Bengaluru').primary
    assert (primary.categoryId, primary.queries) == ('frozen_dessert', ['ice cream'])


def test_a_board_game_cafe_asks_for_itself_first_and_arcade_is_a_disclosed_fallback():
    assert interpret('Board game café in London').primary.queries == ['board game café', 'arcade']


def test_an_unnameable_idea_asks_for_clarification():
    result = interpret('a place for stuff')
    assert result.ambiguous and result.clarification and not result.hybrid


def test_idea_alternatives_use_only_the_founders_words():
    hybrid = idea_alternatives(interpret('Bakery combined with a bookstore'))
    assert {o['value'].casefold() for o in hybrid} == {'bakery', 'bookstore'}
    plain = idea_alternatives(interpret('Vegan restaurant'))
    assert plain and plain[0]['value'].casefold() == 'restaurant'
    assert idea_alternatives(interpret('Vegan restaurant'), tried=('restaurant',)) == []


# ----------------------------------------------------------------- the model's proposal
GOOD = {'components': [{'phrase': 'tattoo parlour', 'search': 'tattoo parlor'}], 'ambiguous': False, 'clarification': ''}


@pytest.mark.parametrize('bad', [
    None, 'text', [], {}, {'components': []},
    {'components': [{'phrase': 'x', 'search': 'tattoo'}] * 4},
    {'components': [{'phrase': 'tattoo parlour', 'search': 'urn:tag:category:place:tattoo'}]},
    {'components': [{'phrase': 'tattoo parlour', 'search': 'tattoo; DROP'}]},
    {'components': [{'phrase': 'tattoo parlour', 'search': 'tattoo', 'tagId': 'urn:tag:x'}]},
    {**GOOD, 'filter.type': 'urn:entity:place'},
    {**GOOD, 'clarification': 'x' * 200},
])
def test_a_malformed_or_hostile_proposal_is_rejected(bad):
    assert validate_proposal(bad) is None


def test_a_valid_proposal_is_accepted_and_normalised():
    assert validate_proposal(GOOD)['components'][0]['search'] == 'tattoo parlor'


def _enable_model(monkeypatch, answer=None, error=None):
    calls = []
    monkeypatch.setattr(llm, 'is_configured', lambda: True)

    def ask(brief, directions, timeout, before_request=None, after_request=None, messages=None):
        calls.append(messages)
        if error:
            raise error
        return answer, 'test-model', 1
    monkeypatch.setattr(llm, '_ask_model', ask)
    return calls


def test_the_model_is_asked_once_only_when_rules_cannot_read_the_idea(monkeypatch):
    calls = _enable_model(monkeypatch, {'components': [{'phrase': 'thing', 'search': 'thing'}]})
    provider = QlooHarnessProvider()
    provider.interpret_idea('Ice cream parlour')
    provider.interpret_idea('Bubble tea shop')
    assert calls == []
    reading, event = provider.interpret_idea('a place for stuff')
    assert len(calls) == 1 and event.status == 'ok' and reading.source == 'model'
    provider.interpret_idea('a place for stuff')          # held now: no second request
    assert len(calls) == 1


def test_a_failed_or_invalid_model_reading_falls_back_to_rules_and_is_not_held(monkeypatch):
    _enable_model(monkeypatch, error=llm.LlmUnavailable('down', code='LLM_TIMEOUT'))
    reading, event = QlooHarnessProvider().interpret_idea('a place for stuff')
    assert reading.ambiguous and reading.source == 'rules' and event.status == 'skipped'
    assert get_store().get(business_intent.llm_key('a place for stuff')) is None
    _enable_model(monkeypatch, {'components': [{'phrase': 'x y', 'search': 'urn:tag:category:place:x'}]})
    reading, event = QlooHarnessProvider().interpret_idea('a place for stuff')
    assert reading.source == 'rules' and 'validation' in event.detail


# --------------------------------------------------------------------------- tags
def _tags(*pairs):
    return {'status': 'ok', 'results': [{'id': i, 'name': n} for i, n in pairs]}


def test_exact_near_and_no_match_are_distinguished_by_name_only():
    exact = _tags(('urn:tag:category:place:bakery', 'Bakery'))
    near = _tags(('urn:tag:category:place:bubble_tea_shop_and_cafe', 'Bubble Tea Shop and Cafe'))
    assert rank_category_tag(exact, 'bakery')[:2] == ('urn:tag:category:place:bakery', 'exact')
    assert rank_category_tag(near, 'bubble tea shop')[:2] == ('urn:tag:category:place:bubble_tea_shop_and_cafe', 'near')
    assert rank_category_tag(_tags(('urn:tag:category:place:shoe_store', 'Shoe Store')), 'sneaker store') == (None, None, None)


def test_invalid_or_foreign_tag_ids_are_never_selected():
    junk = _tags(('bakery', 'Bakery'), ('urn:tag', 'Bakery'), ('urn:tag:genre', 'Bakery'),
                 ('urn:tag:amenity:qloo:bakery', 'Bakery'), ('urn:entity:place', 'Bakery'))
    assert rank_category_tag(junk, 'bakery') == (None, None, None)
    assert rank_category_tag({}, 'bakery') == (None, None, None)
    assert rank_category_tag({'results': 'oops'}, 'bakery') == (None, None, None)


class Script:
    """Scripted find_tags / recommend answers that behave like the cached workflow (and count requests)."""

    def __init__(self, monkeypatch, tags=None, places=None, fail=None):
        self.tags, self.places, self.fail, self.calls = tags or {}, places or {}, fail or {}, []
        monkeypatch.setattr(QlooHarnessProvider, 'run_workflow_cached',
                            lambda provider, operation, payload: self.run(provider, operation, payload))

    def run(self, provider, operation, payload):
        key = canonical_key(operation, payload)
        store = get_store()
        held = store.get(key)
        if held is not None:
            return held, True, 0
        self.calls.append((operation, payload))
        if operation == 'find_tags':
            if payload.get('limit') == 3:
                envelope = _tags(('urn:tag:interests:qloo:design', 'Design'))
            else:
                if payload['query'] in self.fail:
                    raise QlooHarnessError('limit', code=self.fail[payload['query']], retryable=True)
                envelope = {'status': 'ok', 'results': self.tags.get(payload['query'], [])}
        else:
            tag = (payload.get('include_tags') or [''])[0]
            if tag in self.fail:
                raise QlooHarnessError('limit', code=self.fail[tag], retryable=True)
            rows = self.places.get((tag, 'tags' if payload.get('signal_tags') else 'only'),
                                   self.places.get((tag, 'any'), []))
            envelope = {'status': 'ok', 'results': rows}
        store.put(key, envelope, 1)
        return envelope, False, 1


def _place(entity_id, name, description='', city='Paris'):
    return {'entity_id': entity_id, 'name': name, 'properties': {'description': description, 'geocode': {'city': city}}}


def _project(idea, location='Paris, France'):
    return ProjectRequest(businessType='Food & beverage', businessIdea=idea, audience='Design-minded locals',
                          location=location, budget='$25k – $50k', objectives=['x'])


BAKERY = ('urn:tag:category:place:bakery', 'Bakery')
BOOKS = ('urn:tag:category:place:bookstore', 'Bookstore')


def test_a_single_exact_category_costs_the_baseline_and_no_more(monkeypatch):
    script = Script(monkeypatch, tags={'bakery': _tags(BAKERY)['results']},
                    places={(BAKERY[0], 'any'): [_place('e1', 'Boulangerie Utopie', 'A bakery')]})
    response = QlooHarnessProvider().generate(_project('Artisan bakery in Paris'), allow_naming=False)
    ops = [op for op, _ in script.calls]
    assert ops == ['find_tags', 'find_tags', 'recommend']          # audience, category, places: unchanged
    entry = response.intent.evidence[0]
    assert entry['state'] == 'exact' and entry['tag']['id'] == BAKERY[0] and not response.intent.hybrid
    assert [m['word'] for m in entry['modifiers']] == ['artisan']


def test_a_specialisation_is_disclosed_with_a_count_of_what_was_returned(monkeypatch):
    Script(monkeypatch, tags={'restaurant': _tags(('urn:tag:category:place:restaurant', 'Restaurant'))['results']},
           places={('urn:tag:category:place:restaurant', 'any'): [
               _place('r1', 'Lucky Leaf', 'Vegan kitchen', 'Berlin'), _place('r2', 'Schnitzel Haus', 'Austrian', 'Berlin')]})
    response = QlooHarnessProvider().generate(_project('Vegan restaurant in Berlin', 'Berlin, Germany'), allow_naming=False)
    note = next(line for line in response.intent.substitutions if 'vegan-specific' in line)
    assert note.startswith('Showing general restaurant evidence; vegan-specific relevance is not verified')
    assert '1 of 2 returned places mention "vegan"' in note


def test_a_broader_category_is_used_only_when_disclosed_and_costs_one_more_find_tags(monkeypatch):
    shoe = ('urn:tag:category:place:sneaker_store', 'Sneaker Store')
    script = Script(monkeypatch, tags={'sneaker store': _tags(shoe)['results']},
                    places={(shoe[0], 'any'): [_place('s1', 'Atmos', 'Sneakers', 'Tokyo')]})
    response = QlooHarnessProvider().generate(_project('Vintage sneaker store in Tokyo', 'Tokyo, Japan'), allow_naming=False)
    assert [p['query'] for op, p in script.calls if op == 'find_tags' and p.get('limit') == 10] == ['vintage sneaker store', 'sneaker store']
    entry = response.intent.evidence[0]
    assert entry['state'] == 'broader' and entry['queriesTried'] == ['vintage sneaker store', 'sneaker store']
    assert any('broadening is CultureForge' in line for line in response.intent.substitutions)


def test_no_matching_tag_is_an_unsupported_category_and_nothing_else_is_substituted(monkeypatch):
    script = Script(monkeypatch, tags={'vintage sneaker store': _tags(('urn:tag:category:place:shoe_store', 'Shoe Store'))['results']})
    with pytest.raises(QlooHarnessError) as caught:
        QlooHarnessProvider().generate(_project('Vintage sneaker store in Tokyo', 'Tokyo, Japan'), allow_naming=False)
    assert caught.value.code == 'UNSUPPORTED_CATEGORY' and caught.value.details['tried'] == ['vintage sneaker store', 'sneaker store']
    assert 'recommend' not in [op for op, _ in script.calls]


def test_a_tag_that_exists_but_returns_no_places_is_its_own_state(monkeypatch):
    Script(monkeypatch, tags={'bakery': _tags(BAKERY)['results']})
    with pytest.raises(QlooHarnessError) as caught:
        QlooHarnessProvider().generate(_project('Bakery in Paris'), allow_naming=False)
    assert caught.value.code == 'NO_EVIDENCE' and caught.value.details['reason'] == 'category_no_places'
    assert caught.value.details['tag'] == BAKERY[0]


@pytest.mark.parametrize('code', ['RATE_LIMITED', 'UPSTREAM_TIMEOUT', 'UPSTREAM_UNAUTHENTICATED', 'UPSTREAM_MALFORMED'])
def test_a_provider_failure_is_never_read_as_an_unsupported_category(monkeypatch, code):
    Script(monkeypatch, fail={'bakery': code})
    with pytest.raises(QlooHarnessError) as caught:
        QlooHarnessProvider().generate(_project('Bakery in Paris'), allow_naming=False)
    assert caught.value.code == code
    # nothing was held as "unsupported"
    assert get_store().get(canonical_key('find_tags', {'query': 'bakery', 'limit': 10})) is None


# --------------------------------------------------------------------------- hybrids
def _hybrid(monkeypatch, books_places=None, **extra):
    shared = _place('shared-1', 'Shakespeare and Company', 'Bookshop with a bakery counter')
    return Script(monkeypatch,
                  tags={'bakery': _tags(BAKERY)['results'], 'bookstore': _tags(BOOKS)['results']},
                  places={(BAKERY[0], 'any'): [_place('b1', 'Du Pain et des Idées', 'A bakery'), shared],
                          (BOOKS[0], 'any'): books_places if books_places is not None else [shared, _place('k1', 'Librairie', 'Bookshop')]},
                  **extra)


def test_a_hybrid_retrieves_each_business_separately_within_its_budget(monkeypatch):
    script = _hybrid(monkeypatch)
    response = QlooHarnessProvider().generate(_project('A bakery combined with a bookstore in Paris'), allow_naming=False)
    intent = response.intent
    assert intent.hybrid and [e['phrase'] for e in intent.evidence] == ['bakery', 'bookstore']
    assert [e['state'] for e in intent.evidence] == ['exact', 'exact']
    baseline = 3                                                  # audience, category, places
    assert len(script.calls) - baseline <= 2                      # + find_tags and recommend for the second business
    assert intent.overlap['established'] and intent.overlap['sharedPlaces'][0]['entityId'] == 'shared-1'
    assert 'does not show demand' in intent.overlap['statement']


def test_overlap_is_not_manufactured_when_no_place_is_shared(monkeypatch):
    _hybrid(monkeypatch, books_places=[_place('k1', 'Librairie', 'Bookshop')])
    intent = QlooHarnessProvider().generate(_project('Bakery and bookstore in Paris'), allow_naming=False).intent
    assert intent.overlap['established'] is False and intent.overlap['statement'].startswith('Overlap not established')


def test_a_hybrid_with_evidence_for_one_component_says_which(monkeypatch):
    _hybrid(monkeypatch, books_places=[])
    intent = QlooHarnessProvider().generate(_project('Bakery and bookstore in Paris'), allow_naming=False).intent
    assert [e['state'] for e in intent.evidence] == ['exact', 'tag_no_places']
    assert intent.overlap['established'] is False and 'bookstore' in intent.overlap['statement']


def test_a_rate_limit_on_the_second_business_leaves_the_first_intact(monkeypatch):
    _hybrid(monkeypatch, fail={'bookstore': 'RATE_LIMITED'})
    response = QlooHarnessProvider().generate(_project('Bakery and bookstore in Paris'), allow_naming=False)
    assert [e['state'] for e in response.intent.evidence] == ['exact', 'provider_error']
    assert response.intent.evidence[1]['code'] == 'RATE_LIMITED' and response.evidence


def test_held_evidence_for_a_hybrid_is_free_and_never_fetches_on_an_explicit_recomposition(monkeypatch):
    script = _hybrid(monkeypatch)
    provider = QlooHarnessProvider()
    first = provider.generate(_project('Bakery and bookstore in Paris'), allow_naming=False)
    spent = len(script.calls)
    again = QlooHarnessProvider().generate(_project('Bakery and bookstore in Paris'), allow_naming=False)
    assert len(script.calls) == spent and again.intent.evidence[1]['state'] == 'exact'
    # a recomposition from explicit envelopes may not spend: a cold second business is "not retrieved"
    get_store()._cache.clear()
    script2 = Script(monkeypatch, tags={'bakery': _tags(BAKERY)['results']},
                     places={(BAKERY[0], 'any'): [_place('b1', 'Du Pain', 'A bakery')]})
    tags_env = _tags(('urn:tag:interests:qloo:design', 'Design'))
    rec_env = {'status': 'ok', 'results': [_place('b1', 'Du Pain', 'A bakery')]}
    cold = QlooHarnessProvider().generate(_project('Bakery and bookstore in Paris'), tag_result=tags_env,
                                          recommendations=rec_env, allow_naming=False)
    assert cold.intent.evidence[1]['state'] == 'not_retrieved' and script2.calls == []
    assert first.intent.hybrid


# ------------------------------------------------------------------------ the cache
def _put_recommend(payload, rows, age_seconds):
    store = get_store()
    key = canonical_key('recommend', payload)
    store.put(key, {'status': 'ok', 'results': rows}, 1)
    store._cache[key]['storedAt'] = time.time() - age_seconds
    return key


NEG_PAYLOAD = {'target_type': 'place', 'signal_location': 'Paris', 'limit': 10, 'include_tags': ['urn:tag:category:place:x'],
               'include_tags_operator': 'intersection', 'signal_tags': ['urn:tag:interests:qloo:design']}


def test_a_verified_empty_result_expires_on_its_own_shorter_ttl(monkeypatch):
    calls = []
    monkeypatch.setattr(QlooHarnessProvider, '_run_workflow',
                        lambda self, op, payload: calls.append(op) or {'status': 'ok', 'results': [{'name': 'fresh'}]})
    provider = QlooHarnessProvider()
    _put_recommend(NEG_PAYLOAD, [], age_seconds=config.negative_ttl_seconds() - 60)
    assert provider.run_workflow_cached('recommend', NEG_PAYLOAD)[1] is True and calls == []
    _put_recommend(NEG_PAYLOAD, [], age_seconds=config.negative_ttl_seconds() + 60)
    envelope, cached, _ = provider.run_workflow_cached('recommend', NEG_PAYLOAD)
    assert cached is False and calls == ['recommend'] and envelope['results'][0]['name'] == 'fresh'


def test_a_positive_answer_keeps_the_ordinary_ttl(monkeypatch):
    monkeypatch.setattr(QlooHarnessProvider, '_run_workflow', lambda self, op, payload: pytest.fail('refetched'))
    _put_recommend(NEG_PAYLOAD, [{'name': 'x'}], age_seconds=config.negative_ttl_seconds() + 60)
    assert QlooHarnessProvider().run_workflow_cached('recommend', NEG_PAYLOAD)[1] is True


def test_negative_keys_do_not_leak_across_cities_tags_or_audiences():
    keys = {canonical_key('recommend', p) for p in (
        NEG_PAYLOAD,
        {**NEG_PAYLOAD, 'signal_location': 'Lyon'},
        {**NEG_PAYLOAD, 'include_tags': ['urn:tag:category:place:y']},
        {**NEG_PAYLOAD, 'signal_tags': ['urn:tag:interests:qloo:other']},
        {k: v for k, v in NEG_PAYLOAD.items() if k != 'signal_tags'})}
    assert len(keys) == 5


def test_a_transient_failure_is_never_held_as_an_empty_answer(monkeypatch):
    def boom(self, op, payload):
        raise QlooHarnessError('limited', code='RATE_LIMITED', retryable=True)
    monkeypatch.setattr(QlooHarnessProvider, '_run_workflow', boom)
    with pytest.raises(QlooHarnessError):
        QlooHarnessProvider().run_workflow_cached('recommend', NEG_PAYLOAD)
    assert get_store().get(canonical_key('recommend', NEG_PAYLOAD)) is None


def test_identical_concurrent_requests_make_one_upstream_call(monkeypatch):
    calls = []

    def slow(self, op, payload):
        calls.append(op)
        time.sleep(0.2)
        return {'status': 'ok', 'results': [{'id': 'urn:tag:category:place:bakery', 'name': 'Bakery'}]}
    monkeypatch.setattr(QlooHarnessProvider, '_run_workflow', slow)
    out = []
    threads = [threading.Thread(target=lambda: out.append(QlooHarnessProvider().run_workflow_cached(
        'find_tags', {'query': 'bakery', 'limit': 10}))) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(calls) == 1 and sum(request for _, _, request in out) == 1


# ---------------------------------------------------------------------- relevance
def _assess(idea, name, description):
    return relevance.assess(business_type='Retail', idea=idea, audience='', location='Tokyo', name=name,
                            description=description, returned_location='Tokyo, Japan')


def test_a_vintage_cinema_is_not_a_vintage_sneaker_shop_but_a_sneaker_shop_is():
    assert not _assess('Vintage sneaker store', 'Vintage Cinema Tokyo', 'A vintage movie theatre')['anchorEligible']
    assert _assess('Vintage sneaker store', 'Kicks Lab', 'Rare sneakers and streetwear')['anchorEligible']


def test_bubble_tea_needs_both_product_words():
    assert _assess('Bubble tea shop', 'Boba Bar', 'Bubble tea and snacks')['evidenceClass'] == 'direct_business'
    assert _assess('Bubble tea shop', 'Quiet Tea House', 'Loose leaf tea')['evidenceClass'] != 'direct_business'


def test_a_place_in_the_right_city_but_the_wrong_business_cannot_anchor():
    result = _assess('Bakery', 'Tokyo Tower', 'An observation tower in Tokyo')
    assert result['evidenceClass'] != 'direct_business' and not result['anchorEligible']


# ----------------------------------------------------- one definition of a category
def test_the_two_category_tables_cannot_drift_apart():
    broad = {'food', 'hospitality'}                       # business-type fallbacks with no founder-facing term
    assert set(relevance.FAMILIES) - broad <= set(taxonomy.CATEGORIES)
    for phrases, family in relevance.SPECIFIC_PHRASES.items():
        assert family in taxonomy.CATEGORIES and phrases in taxonomy.terms_for(family)
    for family in set(relevance.FAMILIES) & set(taxonomy.CATEGORIES):
        words = lambda terms: {w for t in terms for w in t.split()}  # noqa: E731
        assert words(relevance.FAMILIES[family]) & words(taxonomy.terms_for(family)), family
    for cid, spec in taxonomy.CATEGORIES.items():
        assert set(spec.get('narrow', ())) <= set(spec['terms']), cid
        assert spec['query'], cid


def test_held_tag_reads_the_store_and_spends_nothing():
    component = interpret('Vintage sneaker store').primary
    resolution, complete = held_tag(component)
    assert resolution.tag is None and complete is False
    get_store().put(canonical_key('find_tags', {'query': 'vintage sneaker store', 'limit': 10}), {'status': 'ok', 'results': []}, 1)
    get_store().put(canonical_key('find_tags', {'query': 'sneaker store', 'limit': 10}),
                    _tags(('urn:tag:category:place:sneaker_store', 'Sneaker Store')), 1)
    resolution, complete = held_tag(component)
    assert complete and resolution.quality == 'broader' and resolution.tag.endswith('sneaker_store')


def test_the_json_intent_has_no_free_form_fields_a_client_could_inject():
    dumped = json.dumps(interpret('Bakery and bookstore').model_dump())
    assert 'urn:' not in dumped


def test_a_model_read_category_judges_places_by_the_categorys_own_words(monkeypatch):
    """Observed live (Mexico City, "bookshop cafe"): ten returned bookshops, none direct.

    The model reading carried only the typed word "bookshop", so Qloo's own "bookstore" and
    "Librerías" text never matched and every real bookshop was demoted to indirect.
    """
    from backend import relevance
    _enable_model(monkeypatch, {'components': [{'phrase': 'bookshop', 'search': 'bookstore'},
                                               {'phrase': 'cafe', 'search': 'coffee shop'}]})
    QlooHarnessProvider().interpret_idea('bookshop cafe')
    places = {
        'Librerías El Sótano': "Large Mexican bookstore offering a broad selection of fiction, non-fiction and regular cultural events in a central Coyoacán location.",
        'Cafebrería El Péndulo San Ángel': 'Bookstore-café and restaurant blending curated books, gifts and on-site dining.',
    }
    for name, text in places.items():
        verdict = relevance.assess(business_type='Retail', idea='bookshop cafe', audience='readers',
                                   location='Mexico City, Mexico', name=name, description=text,
                                   returned_location='Mexico City')
        assert verdict['evidenceClass'] == 'direct_business' and verdict['anchorEligible'], name
    # The same bookstore returned for another country still cannot anchor: geography is unchanged.
    far = relevance.assess(business_type='Retail', idea='bookshop cafe', audience='readers',
                           location='Mexico City, Mexico', name='Librería Puro Verso',
                           description='Independent Montevideo bookstore on Av. 18 de Julio.',
                           returned_location='Montevideo')
    assert far['evidenceClass'] == 'unverified_geography' and not far['anchorEligible']


def test_an_unsupported_three_word_idea_offers_its_own_shorter_form_as_a_way_out():
    """Observed live (Singapore, "film camera shop"): Qloo had no such tag and the reader was offered nothing."""
    from backend.intent_report import idea_alternatives
    reading = interpret('film camera shop')
    offered = idea_alternatives(reading, tried=('film camera shop',))
    assert [option['value'] for option in offered] == ['camera shop']
    assert idea_alternatives(reading, tried=('film camera shop', 'camera shop')) == []
    assert idea_alternatives(interpret('camera shop'), tried=('camera shop',)) == []
