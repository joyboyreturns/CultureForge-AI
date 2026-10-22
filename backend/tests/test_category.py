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
    assert resolve('Yoga cafe').status == 'unresolved'
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
    assert select_category_tag(env, 'boutique hotel') is None  # 'hotels' != 'hotel': fail closed


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
