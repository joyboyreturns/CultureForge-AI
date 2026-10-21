"""The evidence test: the checks, the verdicts, and the order they leave.

No network is touched here. The point of these tests is that the test can
come back with a no, and that when it does, the order changes.
"""
from __future__ import annotations

import pytest

from backend import challenge
from backend.models import Concept, Evidence, GenerateResponse, ProjectRequest, ProvenanceMetadata


def _evidence(places: list[tuple[str, str]]) -> list[Evidence]:
    """The places, as ``(id, name)`` pairs."""
    return [Evidence(id=f'ev-entity-{index}', kind='entity', label=name, entityId=entity_id)
            for index, (entity_id, name) in enumerate(places)]


def _response(evidence: list[Evidence], concepts: list[Concept]) -> GenerateResponse:
    return GenerateResponse(
        projectId='cf-test', project=ProjectRequest(
            businessType='Food & beverage', audience='Design-conscious Gen Z',
            location='Brooklyn, New York', budget='$25k – $50k', objectives=[]),
        concepts=concepts, signals=[], dataMode='live', conceptMode='evidence_composed',
        notice='', provenance=ProvenanceMetadata(source='Qloo API',
                                                 resolved_tags=['urn:tag:interests:qloo:modern_restaurant_design']),
        evidence=evidence, trace=[],
    )


def _concept(concept_id: str, name: str, cited: list[str]) -> Concept:
    return Concept(
        id=concept_id, name=name, tagline='', description='', budget='$25k – $50k',
        investment='', signals=[], accent='', image='', evidenceIds=cited,
    )


class FakeProvider:
    """A provider that answers the two checks with fixed envelopes."""

    def __init__(self, rank_rows: list[dict], compare: dict):
        self.rank_rows = rank_rows
        self.compare = compare
        self.calls: list[tuple[str, dict]] = []

    def run_workflow_cached(self, operation, payload):
        self.calls.append((operation, payload))
        if operation == 'rank':
            return {'status': 'ok', 'results': self.rank_rows}, False, 1
        return {'status': 'ok', 'results': self.compare}, False, 1

    @staticmethod
    def rows(envelope):
        rows = envelope.get('results')
        return rows if isinstance(rows, list) else []

    @staticmethod
    def _affinity(row):
        value = row.get('affinity')
        return float(value) if value is not None else None


def test_a_signal_family_is_cultural_and_a_type_family_is_not():
    assert challenge._is_cultural_signal({'tag_id': 'urn:tag:ambience:qloo:energetic'})
    assert challenge._is_cultural_signal({'tag_id': 'urn:tag:good_for:qloo:nightlife'})
    assert challenge._is_cultural_signal({'tag_id': 'urn:tag:cuisine:qloo:bar_food'})
    assert not challenge._is_cultural_signal({'tag_id': 'urn:tag:genre:place:park'})
    assert not challenge._is_cultural_signal({'tag_id': 'urn:tag:category:place:tourist_attraction'})
    assert not challenge._is_cultural_signal({'tag_id': 'urn:tag:service_type:qloo:dine_in'})
    # An unknown family is plain, so the rule can say no.
    assert not challenge._is_cultural_signal({'tag_id': 'urn:tag:something_new:place:thing'})


def test_the_verdicts_can_be_different_for_different_directions(monkeypatch):
    """The whole point: one direction passes, another is contested."""
    places = [('id-1', 'Union Square Park'), ('id-2', 'The Bell House'),
              ('id-3', 'Whitney Museum'), ('id-4', 'Brooklyn Steel'), ('id-5', 'Brooklyn Bridge Park')]
    evidence = _evidence(places)
    concepts = [
        _concept('live-1', 'The Artful Pour', ['ev-entity-2']),
        _concept('live-2', 'The Bell Table', ['ev-entity-1']),
    ]
    response = _response(evidence, concepts)

    provider = FakeProvider(
        # The Bell House first, the museum last.
        rank_rows=[{'entity_id': 'id-2', 'name': 'The Bell House', 'affinity': 0.95},
                   {'entity_id': 'id-1', 'name': 'Union Square Park', 'affinity': 0.9},
                   {'entity_id': 'id-4', 'name': 'Brooklyn Steel', 'affinity': 0.85},
                   {'entity_id': 'id-5', 'name': 'Brooklyn Bridge Park', 'affinity': 0.8},
                   {'entity_id': 'id-3', 'name': 'Whitney Museum', 'affinity': 0.7}],
        compare={
            'tags': [{'name': 'Place', 'query': {'score': 0.7}}],
            'a': [{'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'},
                  {'name': 'Bar', 'tag_id': 'urn:tag:genre:place:restaurant:bar'}],
            'b': [],
        })
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    result = challenge.challenge_directions(response.project, response)

    by_id = {entry['directionId']: entry for entry in result['directions']}
    assert by_id['live-2']['verdict'] == challenge.SUPPORTED
    assert by_id['live-1']['verdict'] == challenge.CONTESTED
    # The order the evidence leaves is not the order they arrived in.
    assert result['order'] == ['live-2', 'live-1']


def test_a_direction_with_only_type_tags_is_unproven(monkeypatch):
    """A type is not a cultural signal, and its absence is not evidence against.

    The anchor differs from the other retrieved places only by its type. That
    is neither a cultural signal nor a contradiction, so the verdict is
    unproven — not a confident negative.
    """
    places = [('id-1', 'Union Square Park'), ('id-2', 'The Bell House'), ('id-3', 'Whitney Museum')]
    evidence = _evidence(places)
    concepts = [_concept('live-1', 'The River Bench', ['ev-entity-0'])]
    response = _response(evidence, concepts)

    provider = FakeProvider(
        rank_rows=[{'entity_id': 'id-1', 'name': 'Union Square Park', 'affinity': 0.9},
                   {'entity_id': 'id-2', 'name': 'The Bell House', 'affinity': 0.8},
                   {'entity_id': 'id-3', 'name': 'Whitney Museum', 'affinity': 0.7}],
        compare={'tags': [{'name': 'Place', 'query': {'score': 0.7}}],
                 'a': [{'name': 'Park', 'tag_id': 'urn:tag:category:place:park'}],
                 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    result = challenge.challenge_directions(response.project, response)
    entry = result['directions'][0]
    assert entry['verdict'] == challenge.UNPROVEN
    assert 'unproven' in entry['reason']


def test_too_few_places_is_unproven(monkeypatch):
    """Two places are not a market."""
    evidence = _evidence([('id-1', 'Union Square Park'), ('id-2', 'The Bell House')])
    concepts = [_concept('live-1', 'The Artful Pour', ['ev-entity-0'])]
    response = _response(evidence, concepts)

    provider = FakeProvider([], {})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    result = challenge.challenge_directions(response.project, response)
    entry = result['directions'][0]
    assert entry['verdict'] == challenge.UNPROVEN
    assert 'not enough' in entry['reason']


def test_the_coverage_is_disclosed(monkeypatch):
    places = [('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C'), ('id-4', 'D'), ('id-5', 'E')]
    evidence = _evidence(places)
    concepts = [_concept('live-1', 'One', ['ev-entity-0', 'ev-entity-1'])]
    response = _response(evidence, concepts)
    provider = FakeProvider(
        rank_rows=[{'entity_id': f'id-{index}', 'name': name, 'affinity': 0.5}
                   for index, name in enumerate(['A', 'B', 'C', 'D', 'E'])],
        compare={'tags': [], 'a': [], 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    result = challenge.challenge_directions(response.project, response)
    coverage = result['directions'][0]['coverage']
    assert coverage['venuesRetrieved'] == 5
    assert coverage['venuesCited'] == 2
    assert 'do not measure demand' in coverage['note'] or 'not demand' in coverage['note']


def test_the_profile_that_was_ranked_is_reported(monkeypatch):
    """The studio shows the signal that was sent, not a mystery."""
    evidence = _evidence([('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')])
    concepts = [_concept('live-1', 'One', ['ev-entity-0'])]
    response = _response(evidence, concepts)
    provider = FakeProvider([{'entity_id': 'id-1', 'name': 'A', 'affinity': 0.5}], {'tags': [], 'a': [], 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    result = challenge.challenge_directions(response.project, response)
    assert result['profile']['demographic']
    rank_call = next(payload for operation, payload in provider.calls if operation == 'rank')
    assert rank_call['demographic'] == result['profile']['demographic']
    assert 'signal_location' in rank_call


def test_the_demographic_is_read_from_the_audience():
    """The phrase is read from the founder's own words, and it is honest about it."""
    assert challenge.guess_demographic('Design-conscious Gen Z') == ('gen z', True)
    assert challenge.guess_demographic('young families') == ('young adults', True)
    assert challenge.guess_demographic('retirees in the suburbs') == ('seniors', True)
    assert challenge.guess_demographic('millennials') == ('millennials', True)
    assert challenge.guess_demographic('women in their thirties') == ('women 35-44', True)
    # No demographic was named, so the default is used and *says* it is one.
    assert challenge.guess_demographic('designers') == ('millennials', False)


def test_the_demographic_is_matched_on_whole_words():
    """A word inside another word is not a word.

    "restaurant" contains "rest", and "managers" contains "man". Matching on
    substrings is how a brief about restaurants ends up profiled as "men".
    """
    assert challenge.guess_demographic('Restaurant regulars') == ('millennials', False)
    assert challenge.guess_demographic('Warehouse managers') == ('millennials', False)
    assert challenge.guess_demographic('The ageing crowd') == ('millennials', False)


def test_the_verdict_states_what_it_is_about(monkeypatch):
    """A verdict on the anchor is not a verdict on the business."""
    evidence = _evidence([('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')])
    concepts = [_concept('live-1', 'One', ['ev-entity-0'])]
    response = _response(evidence, concepts)
    provider = FakeProvider([{'entity_id': 'id-1', 'name': 'A', 'affinity': 0.5}], {'tags': [], 'a': [], 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    result = challenge.challenge_directions(response.project, response)
    entry = result['directions'][0]
    assert result['scope'] == challenge.VERDICT_SCOPE
    assert result['policyVersion'] == challenge.POLICY_VERSION
    assert entry['scope'] == challenge.VERDICT_SCOPE
    # The claim, its falsifier and its unproven condition travel with the verdict.
    assert 'A' in entry['claim']
    assert entry['falsifier']
    assert entry['unprovenIf']
    assert entry['anchor']['label'] == 'A'
    # And the alternatives are the other places it could be held to.
    assert {alternative['label'] for alternative in entry['alternatives']} == {'B', 'C'}


def test_a_direction_can_be_held_to_a_different_place(monkeypatch):
    """Change the assumption, and the answer follows."""
    evidence = _evidence([('id-1', 'Union Square Park'), ('id-2', 'The Bell House'),
                          ('id-3', 'Whitney Museum')])
    concepts = [_concept('live-1', 'One', ['ev-entity-0'])]
    response = _response(evidence, concepts)
    provider = FakeProvider(
        rank_rows=[{'entity_id': 'id-2', 'name': 'The Bell House', 'affinity': 0.9},
                   {'entity_id': 'id-3', 'name': 'Whitney Museum', 'affinity': 0.8},
                   {'entity_id': 'id-1', 'name': 'Union Square Park', 'affinity': 0.7}],
        compare={'tags': [{'name': 'Place', 'query': {'score': 0.7}}],
                 'a': [{'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'}],
                 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    # The default anchor is the first place the direction cites.
    default = challenge.challenge_directions(response.project, response)['directions'][0]
    assert default['anchor']['label'] == 'Union Square Park'
    assert default['verdict'] == challenge.CONTESTED

    # Held to a different place, the same claim answers differently.
    reanchored = challenge.challenge_directions(
        response.project, response, anchor_entity_id='id-2')['directions'][0]
    assert reanchored['anchor']['label'] == 'The Bell House'
    assert reanchored['verdict'] == challenge.SUPPORTED


def test_the_comparison_set_is_every_other_retrieved_place(monkeypatch):
    """Cited or not: the universe of comparators does not change with the anchor.

    If the comparison used only the places a direction does not cite, then
    changing the anchor would change two assumptions at once — the anchor and
    the comparator set — and the two answers would not be comparable.
    """
    places = [('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C'), ('id-4', 'D')]
    evidence = _evidence(places)
    concepts = [_concept('live-1', 'One', ['ev-entity-0', 'ev-entity-1'])]
    response = _response(evidence, concepts)
    provider = FakeProvider(
        rank_rows=[{'entity_id': f'id-{index}', 'name': name, 'affinity': 0.5}
                   for index, name in enumerate(['A', 'B', 'C', 'D'])],
        compare={'tags': [], 'a': [], 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    default = challenge.challenge_directions(response.project, response)['directions'][0]
    reanchored = challenge.challenge_directions(
        response.project, response, anchor_entity_id='id-3')['directions'][0]

    compare_calls = [payload for operation, payload in provider.calls
                     if operation == 'compare_audiences']
    first, second = compare_calls[0], compare_calls[1]
    assert set(first['group_b']) == {'id-2', 'id-3', 'id-4'}
    assert set(second['group_b']) == {'id-1', 'id-2', 'id-4'}
    # Same size, same universe: only the anchor moved.
    assert len(first['group_b']) == len(second['group_b'])
    assert default['coverage']['venuesCompared'] == 4
    assert reanchored['coverage']['venuesCompared'] == 4


def test_a_tag_returned_for_both_sides_is_never_called_exclusive(monkeypatch):
    """The comparison response is a bounded list. Absence is not proof.

    A tag that comes back for the anchor may also come back for the other
    places. The screen may not say the anchor alone has it.
    """
    places = [('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')]
    evidence = _evidence(places)
    concepts = [_concept('live-1', 'One', ['ev-entity-0'])]
    response = _response(evidence, concepts)
    provider = FakeProvider(
        rank_rows=[{'entity_id': 'id-1', 'name': 'A', 'affinity': 0.9},
                   {'entity_id': 'id-2', 'name': 'B', 'affinity': 0.8},
                   {'entity_id': 'id-3', 'name': 'C', 'affinity': 0.7}],
        compare={'tags': [{'name': 'Live Music Venue',
                           'tag_id': 'urn:tag:activities:place:live_music_venue',
                           'query': {'score': 0.6}}],
                 'a': [{'name': 'Live Music Venue',
                        'tag_id': 'urn:tag:activities:place:live_music_venue'},
                       {'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'}],
                 'b': [{'name': 'Live Music Venue',
                        'tag_id': 'urn:tag:activities:place:live_music_venue'}]})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    entry = challenge.challenge_directions(response.project, response)['directions'][0]
    detail = entry['checks'][1]['detail']
    assert 'the other places lack them' in detail
    assert 'do not' not in detail.split('it does not establish')[0].replace('do not establish', '')
    # The shared tag is reported as shared, not as an exclusive trait.
    assert 'also returned' in detail.lower()


def test_a_re_anchored_direction_is_labelled_as_a_counterfactual(monkeypatch):
    """The badge says which place was tested, and that the idea was not rebuilt."""
    evidence = _evidence([('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')])
    concepts = [_concept('live-1', 'One', ['ev-entity-0'])]
    response = _response(evidence, concepts)
    provider = FakeProvider(
        rank_rows=[{'entity_id': 'id-2', 'name': 'B', 'affinity': 0.9},
                   {'entity_id': 'id-1', 'name': 'A', 'affinity': 0.8},
                   {'entity_id': 'id-3', 'name': 'C', 'affinity': 0.7}],
        compare={'tags': [], 'a': [], 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    default = challenge.challenge_directions(response.project, response)['directions'][0]
    assert default['isCounterfactual'] is False
    assert default['originalAnchor'] is None

    reanchored = challenge.challenge_directions(
        response.project, response, anchor_entity_id='id-2')['directions'][0]
    assert reanchored['isCounterfactual'] is True
    assert reanchored['originalAnchor']['entityId'] == 'id-1'
