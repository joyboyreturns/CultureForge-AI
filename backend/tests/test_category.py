"""Deterministic category-resolution and evidence-class tests (synthetic text, no network)."""
import pytest

from backend.category import head_phrase, resolve
from backend.outcome import INSUFFICIENT, SUPPORTED, build_outcome
from backend.providers import brief_category_payload, select_category_tag
from backend.relevance import assess, classify_brief

SCENARIOS = [
    ('Where should I open an ice cream parlour in Paris?', 'frozen_dessert', 'ice cream'),
    ('Artisan bakery in Tokyo', 'bakery', 'bakery'),
    ('Specialty coffee shop in Bengaluru', 'coffee', 'coffee shop'),
    ('Independent bookstore in London', 'books', 'bookstore'),
    ('Record store in Brooklyn', 'records', 'record store'),
    ('Boutique hotel in Kyoto', 'hotel', 'boutique hotel'),
    ('Vegan restaurant in Berlin', 'food', 'restaurant'),
    ('Fitness studio in Singapore', 'wellness', 'gym'),
    ('Flower shop in Amsterdam', 'florist', 'florist'),
    ('Pet café in Seoul', 'pet_cafe', 'pet cafe'),
    ('Neapolitan pizza restaurant in Toronto', 'pizza', 'pizza'),
    ('A pizza store in Toronto', 'pizza', 'pizza'),
]


@pytest.mark.parametrize('idea,family,query', SCENARIOS)
def test_each_judge_scenario_resolves_its_own_category(idea, family, query):
    assert classify_brief('Retail', idea, '').family == family
    if family not in ('food', 'wellness'):
        assert brief_category_payload(idea)['query'] == query


def test_question_frames_and_places_are_stripped():
    assert head_phrase('Where should I open an ice cream parlour in Paris?') == 'ice cream parlour'


@pytest.mark.parametrize('idea,expected', [('glacier artisanal', 'frozen_dessert'), ('ジェラート', None), ('花屋', 'florist'),
                                           ('boulangerie', 'bakery'), ('Gelateria', 'frozen_dessert')])
def test_synonyms_and_other_languages(idea, expected):
    assert (resolve(idea).id or None) == expected or resolve(idea).status == 'open_vocabulary'


def test_ambiguity_is_not_guessed():
    assert resolve('Bakery and bookstore').status == 'unresolved'
    assert resolve('Gelato and coffee bar').status == 'unresolved'
    assert resolve('Shop').status == 'unresolved'
    assert resolve('').status == 'unresolved'


def test_an_unfamiliar_business_is_looked_up_not_rejected_or_widened():
    result = resolve('Kombucha taproom')
    assert result.status == 'open_vocabulary' and result.query == 'kombucha taproom'


def test_museums_are_context_not_ice_cream_competitors():
    base = dict(business_type='Food & beverage', idea='Ice cream parlour', audience='', location='Paris',
                returned_location='Paris, France')
    museum = assess(name="Musée d'Orsay", description='A museum of impressionist art.', **base)
    shop = assess(name='Berthillon', description='Famous ice cream and sorbet maker.', **base)
    assert museum['evidenceClass'] == 'cultural_attraction' and not museum['anchorEligible']
    assert shop['evidenceClass'] == 'direct_business' and shop['anchorEligible']
    other = assess(name='Berthillon', description='ice cream', **{**base, 'returned_location': 'Montreal, Quebec'})
    assert other['evidenceClass'] == 'unverified_geography'


def test_category_tag_is_chosen_only_from_returned_identifiers():
    env = {'results': [{'id': 'urn:tag:setting:qloo:ice_cream_parlor', 'name': 'Ice Cream Parlor'},
                       {'id': 'urn:tag:category:qloo:ice_cream', 'name': 'Ice Cream'}]}
    assert select_category_tag(env, 'ice cream') == 'urn:tag:category:qloo:ice_cream'
    assert select_category_tag({'results': []}, 'ice cream') is None


def test_boutique_hotel_resolves_by_returned_words():
    env = {'results': [{'id': 'urn:tag:category:qloo:boutique_hotel', 'name': 'Boutique Hotels'}]}
    assert select_category_tag(env, 'boutique hotel') == 'urn:tag:category:qloo:boutique_hotel'  # plural is the same word
    assert select_category_tag({'results': [{'id': 'urn:tag:category:qloo:hotel_bar', 'name': 'Hotel Bar'}]}, 'boutique hotel') is None


class _Item:
    def __init__(self, kind, cls):
        self.kind, self.relevance = kind, {'evidenceClass': cls}


def test_insufficient_evidence_states_what_is_missing_and_a_way_forward():
    cat = classify_brief('Retail', 'Ice cream parlour', '')
    out = build_outcome(category=cat, evidence=[_Item('entity', 'cultural_attraction')], concepts=[])
    assert out['state'] == INSUFFICIENT
    assert any('attractions' in m.lower() for m in out['missing']) and out['recovery']
    ok = build_outcome(category=cat, evidence=[_Item('entity', 'direct_business')], concepts=[object()])
    assert ok['state'] == SUPPORTED


def test_a_dish_family_tag_is_accepted_when_it_is_the_only_exact_label():
    env = {'results': [{'id': 'urn:tag:specialty_dish:place:pizza', 'name': 'Pizza'},
                       {'id': 'urn:tag:specialty_dish:place:pizzas', 'name': 'Pizzas'}]}
    assert select_category_tag(env, 'pizza') == 'urn:tag:specialty_dish:place:pizza'


def test_a_matching_business_in_another_city_cannot_anchor():
    out = assess(business_type='Food & beverage', idea='Pizza restaurant', audience='', location='Toronto, Canada',
                 name="Pizza 4P's", description='Pizza restaurant', returned_location='Ho Chi Minh City, Vietnam')
    assert out['relationship'] == 'direct' and out['evidenceClass'] == 'unverified_geography'
    assert not out['anchorEligible']


def test_a_modified_head_is_looked_up_whole_and_matches_on_its_distinctive_word():
    r = resolve('Yoga cafe')
    assert r.status == 'open_vocabulary' and r.terms == ('yoga',)
    base = dict(business_type='Food & beverage', idea='Yoga cafe', audience='', location='Toronto',
                returned_location='Toronto, Ontario')
    assert not assess(name='Plain Cafe', description='A coffee shop', **base)['anchorEligible']
    assert assess(name='Yoga House', description='yoga and tea', **base)['anchorEligible']
    assert resolve('Sushi restaurant').status == 'open_vocabulary'


def test_suburbs_reported_under_their_own_council_still_match_their_metro():
    from backend.providers import _returned_location
    place = {'city': 'City of Yarra', 'name': 'Fitzroy', 'metro': 'Melbourne', 'country': 'Australia',
             'admin1_region': 'Victoria'}
    text = _returned_location(place)
    assert text == 'City of Yarra, Melbourne, Victoria' and 'Australia' not in text
    out = assess(business_type='Food & beverage', idea='Specialty coffee shop', audience='', location='Melbourne, Australia',
                 name='Seven Seeds Coffee Roasters', description='Specialty coffee roasters', returned_location=text)
    assert out['geography'] == 'text_match' and out['anchorEligible']


def test_place_namespaced_categories_beat_qloo_namespace_tags_and_shop_equals_store():
    env = {'results': [{'id': 'urn:tag:cuisine:qloo:bubble_tea_shop', 'name': 'Bubble Tea Shop'},
                       {'id': 'urn:tag:category:place:bubble_tea_store', 'name': 'Bubble tea store'},
                       {'id': 'urn:tag:amenity:qloo:bubble_tea_shop', 'name': 'Bubble Tea Shop'}]}
    assert select_category_tag(env, 'bubble tea shop') == 'urn:tag:category:place:bubble_tea_store'


def test_a_well_referenced_category_with_no_matching_recipe_gets_a_narrow_honest_direction():
    from backend.concept_composer import compose
    entities = [{'entity_id': f'e{i}', 'name': f'Boba House {i}', 'description': 'A bubble tea shop.',
                 'popularity': 0.5, 'affinity': 0.5 + i / 100, 'relevance': {'anchorEligible': True}} for i in range(3)]
    out = compose(business_type='Food & beverage', business_idea='Bubble tea shop', audience='Gen Z',
                  location='Los Angeles', budget='', tags=[{'id': 'urn:tag:customer_segment:qloo:gen_z'}], entities=entities,
                  evidence_index={}, tag_evidence_ids={}, entity_evidence_ids={f'e{i}': f'ev{i}' for i in range(3)},
                  trace_id='t')
    assert len(out) == 1 and out[0].name == 'The Local Reference Study'
    assert 'not established' in out[0].offering and out[0].evidence_ids
    one = compose(business_type='Food & beverage', business_idea='Bubble tea shop', audience='Gen Z',
                  location='Los Angeles', budget='', tags=[], entities=entities[:1], evidence_index={},
                  tag_evidence_ids={}, entity_evidence_ids={'e0': 'ev0'}, trace_id='t')
    assert one == []


def test_the_narrow_fallback_is_promising_not_supported():
    class D:
        decisions = [{'ruleId': 'category-reference-study'}]
    cat = classify_brief('Retail', 'Bubble tea shop', '')
    out = build_outcome(category=cat, evidence=[_Item('entity', 'direct_business')], concepts=[D()])
    assert out['state'] == 'promising_unverified' and out['missing']
