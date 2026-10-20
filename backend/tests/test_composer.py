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
