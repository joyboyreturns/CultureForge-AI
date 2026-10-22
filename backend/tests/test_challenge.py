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


# ---------------------------------------------------------------------------
# anchor-fit-5: the written rule, its confidence and its sensitivity
# ---------------------------------------------------------------------------

def test_the_rank_rule_is_thirds_and_reduces_to_first_and_last_on_small_samples():
    assert [challenge.rank_band(p, 2) for p in (1, 2)] == ['mixed', 'mixed']
    assert [challenge.rank_band(p, 3) for p in (1, 2, 3)] == ['pass', 'mixed', 'fail']
    assert [challenge.rank_band(p, 5) for p in (1, 2, 4, 5)] == ['pass', 'mixed', 'mixed', 'fail']
    assert [challenge.rank_band(p, 10) for p in range(1, 11)] == (
        ['pass'] * 3 + ['mixed'] * 4 + ['fail'] * 3)
    assert challenge.rank_band(1, 1) == 'mixed'


def test_confidence_follows_sample_size_and_stability_and_is_never_high():
    assert challenge.confidence_label(2, True)[0] == 'none'
    assert challenge.confidence_label(5, True)[0] == 'low'
    assert challenge.confidence_label(10, True)[0] == 'moderate'
    assert challenge.confidence_label(10, False)[0] == 'low'
    assert all(challenge.confidence_label(n, s)[0] != 'high' for n in range(12) for s in (True, False))


def _ten(monkeypatch, anchor_index: int, demographic: str = ''):
    places = [(f'id-{n}', f'Place {n}') for n in range(1, 11)]
    evidence = _evidence(places)
    concept = _concept('d-1', 'Direction', [f'ev-entity-{anchor_index}'])
    response = _response(evidence, [concept])
    provider = FakeProvider(
        rank_rows=[{'entity_id': f'id-{n}', 'name': f'Place {n}', 'affinity': 1 - n / 20} for n in range(1, 11)],
        compare={'tags': [], 'a': [{'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'}], 'b': []})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)
    return challenge.challenge_directions(response.project, response, demographic_override=demographic or None), provider


def test_a_top_third_anchor_with_a_cultural_tag_is_supported_with_moderate_confidence(monkeypatch):
    result, _provider = _ten(monkeypatch, anchor_index=1)  # Place 2 ranks 2 of 10
    entry = result['directions'][0]
    assert entry['verdict'] == challenge.SUPPORTED
    index = entry['index']
    assert index['policy'] == 'anchor-fit-5' == result['policyVersion']
    assert (index['rankCheck'], index['tagCheck'], index['sampleSize']) == ('pass', 'pass', 10)
    assert index['confidence'] == 'moderate'
    assert index['sensitivity']['stable'] is True
    assert 'positions 1-3' in entry['checks'][0]['detail']


def test_a_borderline_anchor_is_low_confidence_because_one_removal_changes_it(monkeypatch):
    result, _provider = _ten(monkeypatch, anchor_index=3)  # Place 4 ranks 4 of 10: mixed
    index = result['directions'][0]['index']
    assert index['rankCheck'] == 'mixed'
    # Removing any place above it moves it to 3 of 9: the top band.
    assert index['sensitivity']['stable'] is False
    assert {change['rankCheck'] for change in index['sensitivity']['changesWhenRemoved']} == {'pass'}
    assert index['confidence'] == 'low'
    assert result['directions'][0]['verdict'] == challenge.UNPROVEN


def test_a_bottom_third_anchor_is_contested_and_the_alternatives_are_listed(monkeypatch):
    result, provider = _ten(monkeypatch, anchor_index=8)  # Place 9 ranks 9 of 10
    entry = result['directions'][0]
    assert entry['verdict'] == challenge.CONTESTED
    alternatives = entry['index']['sensitivity']['alternativeAnchors']
    assert len(alternatives) == 9
    assert [alt['rankCheck'] for alt in alternatives[:3]] == ['pass'] * 3
    # The sensitivity is computed from the one ranking: no extra rank call.
    assert [operation for operation, _ in provider.calls].count('rank') == 1


def test_a_chosen_profile_is_sent_and_reported_as_chosen(monkeypatch):
    result, provider = _ten(monkeypatch, anchor_index=1, demographic='seniors')
    rank_payload = next(payload for operation, payload in provider.calls if operation == 'rank')
    assert rank_payload['demographic'] == 'seniors'
    assert result['profile']['source'] == 'chosen'
    assert result['profile']['proposed'] == 'gen z'
    assert 'you chose' in result['directions'][0]['checks'][0]['detail']


def test_an_unknown_profile_is_refused_before_any_request(monkeypatch):
    provider = FakeProvider(rank_rows=[], compare={})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)
    response = _response(_evidence([('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')]),
                         [_concept('d', 'D', ['ev-entity-0'])])
    with pytest.raises(challenge.QlooHarnessError):
        challenge.challenge_directions(response.project, response, demographic_override='everyone')
    assert provider.calls == []


def test_the_profile_is_proposed_before_the_test_and_costs_nothing():
    from fastapi.testclient import TestClient

    import backend.main as main

    client = TestClient(main.app)
    named = client.post('/api/profile/propose', json={'audience': 'Design-conscious Gen Z'}).json()
    assert (named['demographic'], named['named']) == ('gen z', True)
    default = client.post('/api/profile/propose', json={'audience': 'Bicycle couriers'}).json()
    assert (default['demographic'], default['named']) == ('millennials', False)
    assert 'seniors' in default['choices']
    bad = client.post('/api/projects/challenge', json={
        'project': {'businessType': 'Retail', 'audience': 'x y', 'location': 'Paris', 'budget': 'b'},
        'demographic': 'everyone'})
    assert bad.status_code == 422


def test_the_evidence_policy_document_states_this_policy():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / 'docs' / 'EVIDENCE_POLICY.md').read_text(encoding='utf-8')
    assert challenge.POLICY_VERSION in text
    for phrase in ('total // 3', 'MINIMUM_VENUES', 'leave-one-out', 'not demand'):
        assert phrase in text, phrase


# ---------------------------------------------------------------------------
# When Qloo cannot answer part of the test
# ---------------------------------------------------------------------------

class FlakyProvider(FakeProvider):
    """Answers some workflows and raises for the rest."""

    def __init__(self, fail: set, error: Exception, rank_rows, compare):
        super().__init__(rank_rows, compare)
        self.fail, self.error = fail, error

    def run_workflow_cached(self, operation, payload):
        if operation in self.fail:
            raise self.error
        return super().run_workflow_cached(operation, payload)


def _small_case(monkeypatch, fail, error):
    places = [('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C'), ('id-4', 'D'), ('id-5', 'E')]
    response = _response(_evidence(places), [_concept('d-1', 'Direction', ['ev-entity-0'])])
    rank_rows = [{'entity_id': f'id-{n}', 'name': chr(64 + n), 'affinity': 1 - n / 10} for n in range(1, 6)]
    compare = {'tags': [], 'a': [{'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'}], 'b': []}
    provider = FlakyProvider(set(fail), error, rank_rows, compare)
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)
    return response


def test_a_rate_limited_ranking_leaves_the_tag_check_and_the_direction_unproven(monkeypatch):
    error = challenge.QlooHarnessError('Qloo rate limited this key.', code='RATE_LIMITED', retryable=True)
    response = _small_case(monkeypatch, {'rank'}, error)
    result = challenge.challenge_directions(response.project, response)
    entry = result['directions'][0]
    assert entry['verdict'] == challenge.UNPROVEN
    assert entry['problems'] == [{'check': 'rank', 'code': 'RATE_LIMITED',
                                  'message': 'Qloo rate limited this key.', 'retryable': True}]
    assert entry['completion'] == {'rank': 'failed', 'compare': 'complete',
                                   'completedChecks': 1, 'totalChecks': 2}
    assert 'could not be run (RATE_LIMITED)' in entry['checks'][0]['detail']
    assert entry['checks'][1]['result'] == 'pass'   # the tag check still ran
    assert result['summary'].startswith('Qloo could not answer 1 of the checks (RATE_LIMITED)')


def test_a_failed_comparison_is_unproven_not_contested_and_not_supported(monkeypatch):
    error = challenge.QlooHarnessError('Qloo could not be reached.', code='PROVIDER_UNAVAILABLE', retryable=True)
    response = _small_case(monkeypatch, {'compare_audiences'}, error)
    entry = challenge.challenge_directions(response.project, response)['directions'][0]
    assert entry['verdict'] == challenge.UNPROVEN
    assert entry['problems'][0]['check'] == 'compare'
    assert 'tag comparison could not be run' in entry['checks'][1]['detail']


def test_when_qloo_answers_nothing_at_all_it_is_the_stated_error_not_a_screen_of_unproven(monkeypatch):
    error = challenge.QlooHarnessError('Qloo rate limited this key.', code='RATE_LIMITED', retryable=True)
    response = _small_case(monkeypatch, {'rank', 'compare_audiences'}, error)
    with pytest.raises(challenge.QlooHarnessError) as caught:
        challenge.challenge_directions(response.project, response)
    assert caught.value.code == 'RATE_LIMITED'


@pytest.mark.parametrize('anchor_index', [0, 1])
def test_two_ranked_places_cannot_settle_a_larger_retrieved_sample(monkeypatch, anchor_index):
    evidence = _evidence([('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')])
    response = _response(evidence, [_concept('d', 'Direction', [f'ev-entity-{anchor_index}'])])
    provider = FakeProvider(
        rank_rows=[{'entity_id': 'id-1'}, {'entity_id': 'id-2'}],
        compare={'a': [{'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'}]})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    entry = challenge.challenge_directions(response.project, response)['directions'][0]
    assert entry['verdict'] == challenge.UNPROVEN
    assert entry['index']['rankCheck'] == 'mixed'
    assert entry['index']['confidence'] == 'none'
    assert 'Fewer than 3 places were ranked' in entry['reason']
    assert entry['completion'] == {'rank': 'insufficient_sample', 'compare': 'complete',
                                   'completedChecks': 1, 'totalChecks': 2}


def test_duplicate_and_unrequested_rank_rows_do_not_inflate_the_sample(monkeypatch):
    evidence = _evidence([('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')])
    response = _response(evidence, [_concept('d', 'Direction', ['ev-entity-0'])])
    provider = FakeProvider(
        rank_rows=[{'entity_id': 'outside'}, {'entity_id': 'id-1'},
                   {'entity_id': 'id-1'}, {'entity_id': 'id-2'}],
        compare={'a': [{'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'}]})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)

    entry = challenge.challenge_directions(response.project, response)['directions'][0]
    assert entry['verdict'] == challenge.UNPROVEN
    assert entry['index']['sampleSize'] == 2
    assert entry['checks'][0]['metric']['position'] == 1


def test_one_rate_limited_anchor_does_not_block_another_anchor_comparison(monkeypatch):
    evidence = _evidence([('id-1', 'A'), ('id-2', 'B'), ('id-3', 'C')])
    response = _response(evidence, [_concept('a', 'A direction', ['ev-entity-0']),
                                    _concept('b', 'B direction', ['ev-entity-1'])])

    class OneFailedAnchor(FakeProvider):
        def run_workflow_cached(self, operation, payload):
            if operation == 'compare_audiences' and payload['group_a'] == ['id-1']:
                self.calls.append((operation, payload))
                raise challenge.QlooHarnessError('Rate limited A.', code='RATE_LIMITED', retryable=True)
            return super().run_workflow_cached(operation, payload)

    provider = OneFailedAnchor(
        rank_rows=[{'entity_id': 'id-2'}, {'entity_id': 'id-1'}, {'entity_id': 'id-3'}],
        compare={'a': [{'name': 'Nightlife', 'tag_id': 'urn:tag:good_for:qloo:nightlife'}]})
    monkeypatch.setattr(challenge, 'QlooHarnessProvider', lambda: provider)
    result = challenge.challenge_directions(response.project, response)
    by_id = {entry['directionId']: entry for entry in result['directions']}
    assert by_id['a']['verdict'] == challenge.UNPROVEN
    assert by_id['a']['completion']['compare'] == 'failed'
    assert by_id['b']['verdict'] == challenge.SUPPORTED
    assert by_id['b']['completion']['completedChecks'] == 2
    assert [payload['group_a'] for op, payload in provider.calls if op == 'compare_audiences'] == [
        ['id-1'], ['id-2']]
