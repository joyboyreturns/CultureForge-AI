"""The composer is the claim that Qloo decides the answer. Test it hard."""
from __future__ import annotations

from backend.concept_composer import compose

DESIGN_TAGS = [
    'urn:tag:target_audience:qloo:design_enthusiasts',
    'urn:tag:customer_segment:qloo:design_conscious_professionals',
    'urn:tag:target_audience:qloo:aspiring_designers',
]
MINDFUL_TAGS = [
    'urn:tag:customer_segment:qloo:mindful_professionals',
    'urn:tag:interests:qloo:mindful_living',
    'urn:tag:customer_segment:qloo:mindfulness_practitioners',
]
INDEPENDENT_TAGS = [
    'urn:tag:artist:qloo:independent',
    'urn:tag:customer_segment:qloo:independent_creators',
    'urn:tag:lifestyle:qloo:supporting_independent_creators',
]


def _compose(tags, entities):
    tag_ids = {tag: f'ev-tag-{i}' for i, tag in enumerate(tags)}
    entity_ids = {e['entity_id']: f'ev-entity-{i}' for i, e in enumerate(entities)}
    return compose(
        business_type='Food & beverage', audience='test', location='Brooklyn, New York',
        budget='$25k', tags=[{'id': t} for t in tags], entities=entities,
        evidence_index={}, tag_evidence_ids=tag_ids, entity_evidence_ids=entity_ids,
        trace_id='trace-1',
    )


def test_composer_returns_three_directions(entities):
    concepts = _compose(DESIGN_TAGS, entities)
    assert len(concepts) == 3


def test_the_audience_changes_the_directions(entities):
    """The exit gate: same venues, different audience, different directions."""
    design = [c.name for c in _compose(DESIGN_TAGS, entities)]
    mindful = [c.name for c in _compose(MINDFUL_TAGS, entities)]
    independent = [c.name for c in _compose(INDEPENDENT_TAGS, entities)]
    assert design[0] != mindful[0], 'the leading direction must follow the audience'
    assert design[0] != independent[0]
    assert 'The Slow Hour' in mindful
    assert 'Independent Makers Guild' in independent


def test_every_concept_cites_real_evidence(entities):
    for concept in _compose(DESIGN_TAGS, entities):
        assert concept.evidence_ids, 'a concept must cite something'
        for decision in concept.decisions:
            assert decision['evidenceIds'], 'a decision must name its evidence'
            assert decision['origin'] == 'cultureforge_rule'


def test_evidence_ids_resolve_to_the_entities_that_were_returned(entities):
    known = {f'ev-entity-{i}' for i in range(len(entities))}
    for concept in _compose(DESIGN_TAGS, entities):
        for evidence_id in concept.evidence_ids:
            assert evidence_id in known


def test_the_directions_are_different_from_one_another(entities):
    concepts = _compose(DESIGN_TAGS, entities)
    names = {c.name for c in concepts}
    assert len(names) == len(concepts)
    primary = {c.evidence_ids[0] for c in concepts}
    assert len(primary) > 1, 'the directions should not all rest on the same venue'


def test_a_brief_with_no_cultural_signal_falls_back_to_the_brief_and_says_so(entities):
    """No audience tag matched, so only the business type can unlock a direction.

    That is allowed, but it must be labelled honestly rather than pretending
    the evidence supported it.
    """
    concepts = _compose(['urn:tag:weather:qloo:rain'], entities)
    assert concepts, 'the brief alone can still unlock a direction'
    for concept in concepts:
        assert 'brief' in concept.rationale
        assert 'Unlocked by rain' not in concept.rationale
    # And the directions the audience WOULD have unlocked are absent.
    assert 'The Design Floor' not in {c.name for c in concepts}


def test_a_concept_states_what_the_evidence_does_not_establish(entities):
    for concept in _compose(DESIGN_TAGS, entities):
        assert concept.limitations
        assert any('interpretation' in line for line in concept.limitations)


def test_missing_prices_do_not_become_an_affordability_claim(entities):
    from backend.concept_composer import RECIPES

    recipe = next(item for item in RECIPES if item.rule_id == 'everyday-value')
    assert 'have not been measured' in recipe.offering
    assert 'most accessible' not in recipe.offering
    assert all('locally' not in concept.description for concept in _compose(DESIGN_TAGS, entities))


def test_a_priced_organisation_cannot_outrank_an_unpriced_place():
    from backend.concept_composer import FACET_ACCESSIBLE, _facet_rank

    organisation = {'entity_id': 'org', 'description': 'Nonprofit organization managing a park.', 'price_level': 1}
    place = {'entity_id': 'place', 'description': 'A community meeting room.', 'price_level': None}
    assert _facet_rank(FACET_ACCESSIBLE, [organisation, place])[0]['entity_id'] == 'place'


# ---------------------------------------------------------------------------
# The rules that decide which evidence unlocks which direction
# ---------------------------------------------------------------------------

def test_a_matcher_is_a_whole_word_not_a_fragment():
    """"restaurant" is not "rest".

    The slow-ritual direction used to be unlocked by any tag containing the
    letters "rest", which meant a brief about restaurants produced a
    direction about rest. The matcher has to be a word.
    """
    from backend.concept_composer import _matches, RECIPES

    slow = next(recipe for recipe in RECIPES if recipe.rule_id == 'slow-ritual')
    score, hits = _matches(slow, ['modern restaurant design'], 'Food & beverage')
    assert hits == []
    assert score == 0.0

    # And the tag it was meant to catch still works.
    score, hits = _matches(slow, ['mindful dining'], 'Food & beverage')
    assert hits == ['mindful dining']
    assert score > 0


def test_an_organisation_is_not_the_place_a_direction_is_built_around():
    """A park-managing nonprofit is not a dining room.

    It stays in the evidence, because Qloo returned it and hiding that
    would be its own kind of lie. It does not become the anchor.
    """
    places = [
        {'entity_id': 'id-park', 'name': 'Brooklyn Bridge Park Corporation',
         'description': 'Nonprofit organization managing a waterfront park on Brooklyn’s East River.',
         'short_description': '', 'image': '', 'popularity': 0.0, 'affinity': 0.88,
         'business_rating': 5.0, 'price_level': None},
        {'entity_id': 'id-steel', 'name': 'Brooklyn Steel',
         'description': 'Converted Williamsburg warehouse hosting lively, large-capacity concerts.',
         'short_description': '', 'image': '', 'popularity': 0.999, 'affinity': 0.88,
         'business_rating': 4.6, 'price_level': None},
    ]
    concepts = _compose(DESIGN_TAGS, places)
    assert concepts
    for concept in concepts:
        assert 'Brooklyn Bridge Park Corporation' not in concept.description
        assert 'Brooklyn Bridge Park Corporation' not in concept.image_alt
    # And it is disclosed, not hidden.
    assert any('organisation' in line for concept in concepts for line in concept.limitations)
