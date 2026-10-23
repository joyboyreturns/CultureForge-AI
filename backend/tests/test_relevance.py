"""Synthetic policy fixtures; these are never served as Qloo evidence."""
import json
from pathlib import Path

from backend.concept_composer import compose
from backend.providers import brief_category_payload, brief_places_payload
from backend.relevance import VERSION, assess, classify_brief


def assessment(name, description='', **kwargs):
    return assess(business_type='Food & beverage', idea='Artisan bakery',
                  audience='Early-morning commuters who love artisan bread',
                  location='Tokyo, Japan', name=name, description=description, **kwargs)


def test_a_museum_or_hotel_is_not_bakery_evidence():
    for name in ('Mori Art Museum', 'The Ritz-Carlton, Tokyo'):
        result = assessment(name)
        assert not result['anchorEligible']
        assert result['relationship'] == 'indirect'
        assert result['reasons']


def test_direct_reference_is_a_rule_assessment_not_a_fit_score():
    result = assessment('Bread counter', 'A sourdough bakery.', returned_location='Tokyo, Japan')
    assert result['anchorEligible']
    assert result['geography'] == 'text_match'
    assert result['confidence'] == 'rule_assessment_only'
    assert not any(isinstance(value, float) for value in result.values())


def test_missing_geography_is_not_replaced_by_query_location():
    assert assessment('Bakery')['geography'] == 'unknown'


def test_other_city_is_an_explicit_geographic_gap():
    result = assessment('Bakery', returned_location='Honolulu, Hawaii')
    assert result['geography'] == 'unverified'
    assert 'Honolulu' in ' '.join(result['reasons'])


def test_cultural_bridge_never_becomes_a_local_anchor():
    result = assessment('Bread', kind='crossdomain')
    assert result['relationship'] == 'indirect'
    assert not result['anchorEligible']


def test_missing_identifier_cannot_support_a_direction():
    assert not assessment('Bakery', has_identifier=False)['anchorEligible']


def test_exact_words_prevent_false_category_matches():
    assert not assessment('Breadth of culture museum')['anchorEligible']


def test_documented_category_filter_is_explicit_and_optional():
    filtered = brief_places_payload(['urn:tag:interests:qloo:bread'], 'Tokyo', 'Artisan bakery')
    assert filtered['include_tags'] == ['bakery']
    assert filtered['include_tags_operator'] == 'intersection'
    assert 'include_tags' not in brief_places_payload([], 'Tokyo')


def test_ambiguous_category_labels_use_only_an_exact_returned_identifier(store):
    from backend.evidence_store import canonical_key
    from backend.providers import brief_category_payload, select_category_tag
    envelope = {'status': 'ok', 'results': [
        {'id': 'urn:tag:industry:qloo:bakery', 'name': 'Bakery'},
        {'id': 'urn:tag:cuisine:qloo:bakery', 'name': 'Bakery'},
        {'id': 'urn:tag:cuisine:qloo:bakery_pastries', 'name': 'Bakery & Pastries'}]}
    store.put(canonical_key('find_tags', brief_category_payload('Artisan bakery')), envelope)
    payload = brief_places_payload([], 'Tokyo', 'Artisan bakery')
    assert payload['include_tags'] == ['urn:tag:cuisine:qloo:bakery']
    assert select_category_tag(envelope, 'unknown') is None


def bakery_concepts(entities, audience='Early-morning commuters who love artisan bread'):
    return compose(business_type='Food & beverage', business_idea='Artisan bakery',
                   audience=audience, location='Tokyo', budget='Not estimated',
                   tags=[{'id': 'urn:tag:service_type:place:artisan_bread'}],
                   entities=entities, evidence_index={},
                   tag_evidence_ids={'urn:tag:service_type:place:artisan_bread': 'tag'},
                   entity_evidence_ids={e['entity_id']: e['entity_id'] for e in entities},
                   trace_id='retrieval')


def test_bakery_directions_differ_by_occasion_and_use_only_relevant_anchors():
    entities = [{'entity_id': 'museum', 'name': 'Art Museum', 'popularity': 1},
                {'entity_id': 'bakery-a', 'name': 'Sourdough Bakery', 'price_level': 1},
                {'entity_id': 'bakery-b', 'name': 'Bread Workshop', 'business_rating': 4.5}]
    concepts = bakery_concepts(entities)
    assert len(concepts) == 2
    assert {c.evidence_ids[0] for c in concepts} == {'bakery-a', 'bakery-b'}
    assert len({c.offering for c in concepts}) == 2
    assert all('Art Museum' not in c.description for c in concepts)
    assert all('Artisan bakery' in c.description for c in concepts)
    assert all('tag' in next(d for d in c.decisions if d['field'] == 'positioning')['evidenceIds'] for c in concepts)


def test_missing_relevant_places_abstains_and_removal_can_destroy_a_direction():
    assert not bakery_concepts([{'entity_id': 'museum', 'name': 'Art Museum'}])
    assert len(bakery_concepts([{'entity_id': 'bakery', 'name': 'Bread Bakery'}])) == 1
    assert not bakery_concepts([])


def test_other_briefs_follow_their_own_categories():
    for business_type, idea, suitable, unsuitable in (
        ('Retail', 'Vinyl record shop', 'Independent record store', 'Luxury hotel'),
        ('Wellness', 'Yoga studio', 'Yoga and meditation studio', 'Art museum'),
        ('Retail', 'Ceramics studio', 'Pottery workshop', 'Concert hall'),
    ):
        def check(name):
            return assess(business_type=business_type, idea=idea, audience='Local regulars',
                          location='London', name=name, description='')['anchorEligible']
        assert check(suitable)
        assert not check(unsuitable)


def test_sequential_removal_never_resurrects_an_earlier_removed_place(store, recommend_places):
    from backend.comparison import recompose
    from backend.evidence_store import canonical_key
    from backend.models import ProjectRequest
    from backend.providers import brief_tags_payload
    project = ProjectRequest(businessType='Food & beverage', audience='Design regulars',
                             location='Brooklyn, New York', budget='Not estimated')
    tags = ['urn:tag:interests:qloo:food_design']
    store.put(canonical_key('find_tags', brief_tags_payload(project.businessType, project.audience)),
              {'status': 'ok', 'results': [{'id': tag} for tag in tags]})
    store.put(canonical_key('recommend', brief_places_payload(tags, project.location)), recommend_places)
    rows = recommend_places['results']
    removed = next(row['entity_id'] for row in rows if row['name'] == 'The Bell House')
    retained = [row['entity_id'] for row in rows if row['entity_id'] != removed]
    second = recompose(project, retain_entity_ids=retained, exclude_entity_ids=[retained[0]])
    assert removed not in {item['entityId'] for item in second['evidence']}
    assert second['concepts'] == []


def test_recomposition_keeps_the_founders_confirmed_seed_subset(store, recommend_places):
    from backend.comparison import recompose
    from backend.evidence_store import canonical_key
    from backend.models import ProjectRequest
    from backend.providers import brief_tags_payload
    project = ProjectRequest(businessType='Food & beverage', audience='Design regulars',
                             location='Brooklyn, New York', budget='Not estimated')
    tags = ['urn:tag:interests:qloo:food_design', 'urn:tag:interests:qloo:community', 'urn:tag:interests:qloo:mindful']
    store.put(canonical_key('find_tags', brief_tags_payload(project.businessType, project.audience)),
              {'status': 'ok', 'results': [{'id': tag} for tag in tags]})
    store.put(canonical_key('recommend', brief_places_payload(tags[:2], project.location)), recommend_places)
    answer = recompose(project, seed_tag_ids=tags[:2])
    assert {item['tagId'] for item in answer['evidence'] if item['kind'] == 'tag'} == set(tags[:2])


def family(business_type, idea, audience='Local regulars'):
    return classify_brief(business_type, idea, audience).family


def test_a_specific_idea_is_never_widened_to_a_broader_category():
    # Ice cream is its own category, not food.
    for idea in ('Best ice cream parlour in Paris', 'Gelato shop', 'Frozen yogurt'):
        assert family('Food & beverage', idea) == 'frozen_dessert'
    # A gaming cafe is gaming, not coffee.
    for idea in ('Gaming cafe', 'Board game cafe', 'Internet cafe'):
        assert family('Entertainment', idea) == 'gaming'
        assert family('Food & beverage', idea) == 'gaming'
    # A medical store is pharmacy under every business type, never wellness or hospitality.
    for business_type in ('Wellness', 'Hospitality', 'Retail', 'Food & beverage'):
        assert family(business_type, 'Medical store') == 'pharmacy'
    assert family('Retail', 'Hospital') == 'clinic'


def test_an_idea_the_rules_do_not_recognise_stays_unknown_and_says_why():
    for idea in ('Shop', 'Venue'):
        category = classify_brief('Food & beverage', idea, 'Local regulars')
        assert category.family == '' and category.specificity == 'unknown', idea
        assert idea in category.reason
        assert 'not widened' in category.reason


def test_a_hybrid_is_read_for_its_first_business_and_the_second_is_kept_by_the_intent():
    from backend.intent import interpret
    assert classify_brief('Food & beverage', 'Bakery and bookstore', 'Local regulars').family == 'bakery'
    assert [c.categoryId for c in interpret('Bakery and bookstore').components] == ['bakery', 'books']


def test_a_head_noun_resolves_only_with_neutral_modifiers():
    assert family('Food & beverage', 'Specialty coffee cafe') == 'coffee'
    assert family('Food & beverage', 'Artisan bakery') == 'bakery'
    assert family('Food & beverage', 'Artisan bread') == 'bakery'
    assert family('Wellness', 'Yoga studio') == 'wellness'
    assert family('Retail', 'Vinyl record shop') == 'records'
    assert family('Retail', 'Ceramics studio') == 'ceramics'
    assert family('Food & beverage', 'Vegan cafe') == 'coffee'


def test_with_no_idea_the_audience_only_chooses_a_distinctive_compatible_family():
    assert family('Retail', '', 'Independent vinyl collectors') == 'records'
    assert family('Food & beverage', '', 'gamers who love coffee') == 'food'
    assert family('Food & beverage', '', 'Design-conscious Gen Z & young professionals') == 'food'
    assert family('Retail', '', 'ice cream lovers') == ''
    assert family('Wellness', '', 'Mindful professionals') == 'wellness'


def test_the_broad_business_type_is_a_labelled_fallback_only_when_the_idea_is_blank():
    category = classify_brief('Food & beverage', '', 'Young families')
    assert (category.family, category.source, category.specificity) == ('food', 'business_type', 'broad')
    assert classify_brief('Food & beverage', 'Kombucha taproom', '').source == 'idea'


def test_assessment_states_how_the_category_was_read():
    result = assess(business_type='Food & beverage', idea='Best ice cream parlour in Paris', audience='Food explorers',
                    location='Paris, France', name='Café de Flore', description='A historic café, restaurant and bar.')
    assert result['category'] == 'frozen_dessert'
    assert result['categorySource'] == 'idea'
    assert result['categorySpecificity'] == 'specific'
    assert result['categoryMatched'] == 'ice cream parlour'
    assert 'ice cream' in result['reasons'][0]
    assert result['relationship'] == 'indirect'
    assert not result['anchorEligible']


def test_an_unrecognised_idea_gives_no_anchor_even_next_to_café_text():
    result = assess(business_type='Food & beverage', idea='Shop', audience='Food explorers',
                    location='Tokyo', name='Café de Flore', description='A historic café, restaurant and bar.')
    assert result['category'] == 'unknown'
    assert result['categorySpecificity'] == 'unknown'
    assert result['relationship'] == 'unknown'
    assert not result['anchorEligible']


def test_the_prepared_briefs_keep_the_category_they_were_written_for():
    briefs = json.loads((Path(__file__).resolve().parents[2] / 'shared' / 'demoBriefs.json').read_text())['briefs']
    expected = {
        'brooklyn-gen-z-cafe': ('food', 'business_type'), 'seattle-family-cafe': ('food', 'business_type'),
        'london-mindful-wellness': ('wellness', 'business_type'), 'lisbon-local-stay': ('hospitality', 'business_type'),
        'austin-live-music': ('music', 'business_type'), 'chicago-vinyl-retail': ('records', 'audience'),
        'los-angeles-slow-fashion': ('fashion', 'audience'), 'tokyo-ceramics-studio': ('ceramics', 'audience'),
        'tokyo-morning-bakery': ('bakery', 'idea'), 'paris-ice-cream': ('frozen_dessert', 'idea'),
        'melbourne-specialty-coffee': ('coffee', 'idea'),
    }
    seen = {}
    for brief in briefs:
        project = brief['project']
        category = classify_brief(project['businessType'], project.get('businessIdea', ''), project['audience'])
        seen[brief['id']] = (category.family, category.source)
    assert seen == expected


def test_the_category_version_is_bumped_for_the_new_rules():
    assert VERSION == 'relevance-3'


def test_a_category_with_no_label_sends_no_category_filter_to_qloo():
    # A hybrid filters on its first business; the second is retrieved separately (see test_intent.py).
    assert brief_category_payload('Bakery and bookstore')['query'] == 'bakery'
    assert brief_category_payload('Shop') is None
    assert brief_category_payload('Ice cream parlour')['query'] == 'ice cream'
    assert brief_category_payload('Where should I open an ice cream parlour in Paris?')['query'] == 'ice cream'
    assert brief_category_payload('Artisan bakery')['query'] == 'bakery'


def test_an_unfamiliar_business_matches_on_what_the_place_is_not_on_its_menu():
    """Observed live (Boise, "tea house"): six drive-thru coffee shops were 'direct' because their menu said tea."""
    from backend import relevance

    def verdict(name, description, location='Boise, Idaho'):
        return relevance.assess(business_type='Food & beverage', idea='tea house', audience='slow-living tea drinkers',
                                location='Boise, Idaho', name=name, description=description, returned_location=location)
    drive_thru = verdict('Dutch Bros Coffee', 'Fun drive-thru coffee shop offering customized espresso drinks, cold brew, Rebel energy drinks, tea and quick grab-and-go snacks.')
    assert drive_thru['relationship'] == 'indirect' and not drive_thru['anchorEligible']
    garden = verdict('Portland Japanese Garden', 'Serene 5.5-acre Japanese garden featuring varied garden styles, waterfall, teahouse and mountain views.', 'Portland, Oregon')
    assert not garden['anchorEligible']
    for name, text in [('Leaf & Kettle', 'Quiet tea house offering single-origin oolong and a small food menu.'),
                       ('Boise Boba', 'Casual boba and tea cafe serving bubble tea, coffee, and offering takeout.'),
                       ('Tea Room 208', 'A calm tea room where regulars stay for hours.')]:
        assert verdict(name, text)['relationship'] == 'direct', name
