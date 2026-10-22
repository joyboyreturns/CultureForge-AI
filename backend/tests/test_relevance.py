"""Synthetic policy fixtures; these are never served as Qloo evidence."""
from backend.concept_composer import compose
from backend.providers import brief_places_payload
from backend.relevance import assess


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
