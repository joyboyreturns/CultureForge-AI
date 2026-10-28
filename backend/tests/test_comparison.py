"""The native comparisons must be honest, and the provenance allowlist real."""
from __future__ import annotations

from backend import comparison
from backend.providers import safe_query


class StubProvider:
    """A provider that records what it was asked and answers with a fixture."""

    def __init__(self, envelope, rows=None):
        self.envelope = envelope
        self._rows = rows or []
        self.calls = []

    def rows(self, envelope):
        return self._rows

    def tag_id(self, row):
        return row.get('id')

    def _affinity(self, row):
        value = row.get('affinity')
        return float(value) if isinstance(value, (int, float)) else None

    def run_workflow_cached(self, operation, payload):
        self.calls.append((operation, payload))
        return self.envelope, False, 1

    def _trace_event(self, step, workflow, envelope, result_count):
        from backend.models import TraceEvent
        return TraceEvent(id=f'trace-{workflow}', step=step, workflow=workflow, resultCount=result_count)


def test_the_provenance_allowlist_drops_everything_it_does_not_know():
    query = {
        'filter.type': 'urn:entity:place',
        'signal.location.query': 'Brooklyn, New York',
        'signal.interests.tags': ['urn:tag:interests:qloo:food_design'],
        'some_unexpected_field': 'should not be shown',
        'authorization': 'should never be shown',
    }
    kept = safe_query(query)
    assert kept['filter.type'] == 'urn:entity:place'
    assert kept['signal.location.query'] == 'Brooklyn, New York'
    assert 'some_unexpected_field' not in kept
    assert 'authorization' not in kept


def test_the_allowlist_covers_every_query_key_the_app_sends():
    """If the app starts sending a new key, the allowlist must be updated too."""
    from backend.providers import SAFE_QUERY_KEYS
    for key in (
        'filter.query', 'feature.semantic_search',
        'filter.type', 'filter.location.query', 'signal.location.query',
        'take', 'feature.explainability',
        'signal.interests.tags', 'operator.signal.interests.tags',
        'signal.interests.entities', 'signal.demographics.gender',
        'signal.demographics.age', 'filter.tags', 'operator.filter.tags',
        'filter.results.entities',
        'a.signal.interests.entities', 'b.signal.interests.entities',
    ):
        assert key in SAFE_QUERY_KEYS, key


def test_the_rank_workflow_is_asked_without_a_limit(monkeypatch):
    """The Qloo rank workflow rejects unknown fields, including `limit`."""
    stub = StubProvider({'status': 'ok', 'results': []})
    monkeypatch.setattr(comparison, 'QlooHarnessProvider', lambda *a, **k: stub)

    comparison.rank_entities(['entity-1'], signal_location='Brooklyn, New York', demographic='millennials')

    operation, payload = stub.calls[0]
    assert operation == 'rank'
    assert 'limit' not in payload
    assert payload['demographic'] == 'millennials'
    assert payload['signal_location'] == 'Brooklyn, New York'


def test_the_rank_workflow_reports_the_signal_qloo_actually_sent(monkeypatch):
    """The converted demographic must be shown, not assumed."""
    from backend.models import TraceEvent

    class TracingProvider(StubProvider):
        def _trace_event(self, step, workflow, envelope, result_count):
            return TraceEvent(
                id='trace-rank', step=step, workflow=workflow, resultCount=result_count,
                request={'method': 'GET', 'path': '/v2/insights', 'query': {
                    'signal.demographics.age': '30_to_34,35_to_44',
                    'signal.demographics.gender': 'female',
                    'filter.type': 'urn:entity:place',
                }},
            )

    stub = TracingProvider({'status': 'ok', 'results': []})
    monkeypatch.setattr(comparison, 'QlooHarnessProvider', lambda *a, **k: stub)

    result = comparison.rank_entities(['entity-1'], signal_location='Brooklyn, New York', demographic='millennials')

    assert result['signalsUsed']['signal.demographics.age'] == '30_to_34,35_to_44'
    assert result['signalsUsed']['signal.demographics.gender'] == 'female'


def test_a_comparison_needs_both_sides():
    import pytest
    from backend.providers import QlooHarnessError
    with pytest.raises(QlooHarnessError):
        comparison.compare_audiences([], ['entity-1'])
    with pytest.raises(QlooHarnessError):
        comparison.compare_audiences(['entity-1'], [])


def test_the_shared_tags_carry_the_score_and_the_hit_counts(monkeypatch):
    envelope = {'status': 'ok', 'results': {
        'tags': [{
            'tag_id': 'urn:tag:interests:qloo:food_design', 'name': 'Food design',
            'popularity': 0.93,
            'query': {'score': 0.7311, 'a.signal.interests.entities': ['a1', 'a2'],
                      'b.signal.interests.entities': ['b1']},
        }],
        'a': [{'tag_id': 'urn:tag:interests:qloo:food_design', 'name': 'Food design', 'popularity': 0.9}],
        'b': [{'tag_id': 'urn:tag:interests:qloo:coffee', 'name': 'Coffee', 'popularity': 0.8}],
        'matchEntities': [{'entity_id': 'a1'}, {'entity_id': 'b1'}],
    }}
    stub = StubProvider(envelope)
    monkeypatch.setattr(comparison, 'QlooHarnessProvider', lambda *a, **k: stub)

    result = comparison.compare_audiences(['a1', 'a2'], ['b1'])

    shared = result['shared'][0]
    assert shared['label'] == 'Food design'
    assert shared['score'] == 0.7311
    assert shared['groupAHits'] == 2
    assert shared['groupBHits'] == 1
    assert result['matchedEntities'] == 2
    assert len(result['groupA']) == 1 and len(result['groupB']) == 1


# ---------------------------------------------------------------------------
# Recomposition
#
# The check that the answer really depends on the evidence. Removing a venue
# must change the answer, not just the list it was on.
# ---------------------------------------------------------------------------

class RecomposeProvider:
    """A provider whose ``generate`` composes from the rows it is handed.

    It uses the real composer, so a test that removes a venue and finds it
    still in a description is a real failure and not an artefact of the stub.
    """

    def __init__(self, tag_rows, place_rows):
        self.tag_rows = tag_rows
        self.place_rows = place_rows
        self.seen: list[tuple] = []

    def rows(self, envelope):
        rows = envelope.get('results')
        return rows if isinstance(rows, list) else []

    def tag_id(self, row):
        value = row.get('id') or row.get('tag_id')
        return value if isinstance(value, str) and value.startswith('urn:tag:') else None

    def _affinity(self, row):
        value = row.get('affinity')
        return float(value) if value is not None else None

    def generate(self, project, tag_result=None, recommendations=None,
                 seed_tag_ids=None, allow_naming=True, bridge_held_only=False):
        self.seen.append({
            'tag_result': tag_result,
            'recommendations': recommendations,
            'allow_naming': allow_naming,
            'bridge_held_only': bridge_held_only,
        })
        from backend.concept_composer import compose
        from backend.models import Delivery, GenerateResponse, ProvenanceMetadata

        tags = [{'id': tag} for tag in (self.tag_id(row) for row in self.rows(tag_result)) if tag]
        entities = []
        for row in self.rows(recommendations):
            properties = row.get('properties') or {}
            entities.append({
                'entity_id': row.get('entity_id') or row.get('id'),
                'name': row.get('name'),
                'description': properties.get('description', ''),
                'short_description': properties.get('short_description', ''),
                'image': '',
                'popularity': row.get('popularity', 0.0),
                'affinity': self._affinity(row) or 0.0,
                'business_rating': properties.get('business_rating'),
                'price_level': properties.get('price_level'),
            })
        composed = compose(
            business_type=project.businessType, audience=project.audience,
            location=project.location, budget=project.budget,
            tags=tags, entities=entities, evidence_index={},
            tag_evidence_ids={tag: f'ev-tag-{index}' for index, tag in enumerate(t['id'] for t in tags)},
            entity_evidence_ids={
                entity['entity_id']: f'ev-entity-{index + len(tags)}'
                for index, entity in enumerate(entities)
            },
            trace_id='trace-recommend',
        )
        evidence = []
        for index, tag in enumerate(tags):
            evidence.append({'id': f'ev-tag-{index}', 'kind': 'tag', 'label': tag['id'],
                             'tagId': tag['id']})
        for index, entity in enumerate(entities):
            evidence.append({'id': f'ev-entity-{index + len(tags)}', 'kind': 'entity',
                             'label': entity['name'], 'entityId': entity['entity_id'],
                             'description': entity['description']})
        return GenerateResponse(
            projectId='cf-test', project=project,
            concepts=[{
                'id': f'live-{index}', 'name': f'Direction {index}', 'tagline': '',
                'description': ' '.join(d['proposal'] for d in c.decisions),
                'evidenceIds': list(c.evidence_ids), 'decisions': [dict(d) for d in c.decisions],
                'signals': [], 'accent': '', 'image': '',
                'budget': project.budget, 'investment': '',
            } for index, c in enumerate(composed)],
            signals=[], dataMode='live', conceptMode='evidence_composed', notice='',
            provenance=ProvenanceMetadata(source='Qloo API', resolved_tags=[t['id'] for t in tags]),
            evidence=evidence, trace=[],
            delivery=Delivery(kind='cache', transportRequests=0),
        )


def test_removing_a_venue_rebuilds_the_directions_without_it(monkeypatch):
    """The removal happens before the composition, not after it.

    Filtering the composer's output afterwards would leave the removed
    venue's name, photograph and decisions in place while the answer claimed
    to have been rebuilt.
    """
    from backend.models import ProjectRequest

    tag_rows = [{'id': 'urn:tag:interests:qloo:food_design', 'name': 'Food design',
                 'popularity': 0.9}]
    place_rows = [
        {'entity_id': 'id-museum', 'name': 'Whitney Museum of American Art',
         'properties': {'description': 'Museum dedicated to 20th-century American art.'}},
        {'entity_id': 'id-bar', 'name': 'The Bell House',
         'properties': {'description': 'Bar and performance venue in a former warehouse.'}},
        {'entity_id': 'id-park', 'name': 'Brooklyn Bridge Park Corporation',
         'properties': {'description': 'Nonprofit organization managing a waterfront park.'}},
    ]
    provider = RecomposeProvider(tag_rows, place_rows)

    from backend.evidence_store import canonical_key

    class StubStore:
        """Answers with the tag envelope or the place envelope, by key."""

        def __init__(self):
            self.keys = {}

        def get(self, key):
            return self.keys.get(key)

    store = StubStore()
    store.keys[canonical_key('find_tags', {'query': 'Food & beverage Design-conscious Gen Z',
                                           'limit': 3})] = {'status': 'ok', 'results': tag_rows}
    store.keys[canonical_key('recommend', {
        'target_type': 'place', 'signal_tags': ['urn:tag:interests:qloo:food_design'],
        'signal_location': 'Brooklyn, New York', 'limit': 10,
    })] = {'status': 'ok', 'results': place_rows}

    monkeypatch.setattr(comparison, 'QlooHarnessProvider', lambda *a, **k: provider)
    project = ProjectRequest(businessType='Food & beverage', audience='Design-conscious Gen Z',
                             location='Brooklyn, New York', budget='$25k – $50k', objectives=[])

    result = comparison.recompose(project, evidence_store=store,
                                  exclude_entity_ids=['id-museum'])

    # The held rows the composer was handed no longer contain the venue.
    handed = provider.seen[0]['recommendations']
    assert 'id-museum' not in [row.get('entity_id') for row in handed.get('results', [])]
    # No model was asked to name anything, and the bridge was read, not fetched.
    assert provider.seen[0]['allow_naming'] is False
    assert provider.seen[0]['bridge_held_only'] is True
    # And nothing in the answer still points at it.
    assert 'Whitney' not in ' '.join(concept['description'] for concept in result['concepts'])
    assert 'Whitney' not in ' '.join(
        evidence.get('label') or '' for evidence in result['evidence'])


def test_agent_recomposition_uses_exact_run_envelopes_without_cache_lookup(monkeypatch):
    from backend.models import ProjectRequest

    tag_envelope = {'status': 'ok', 'results': [
        {'id': 'urn:tag:interests:qloo:founder_selected', 'name': 'Founder selected'}]}
    places = [
        {'entity_id': 'id-one', 'name': 'North Room', 'properties': {'description': 'Community art room.'}},
        {'entity_id': 'id-two', 'name': 'South Hall', 'properties': {'description': 'Local performance hall.'}},
    ]
    recommend_envelope = {'status': 'ok', 'results': places}
    provider = RecomposeProvider(tag_envelope['results'], places)
    monkeypatch.setattr(comparison, 'QlooHarnessProvider', lambda *a, **k: provider)

    class EmptyStore:
        def get(self, _key):
            return None

    project = ProjectRequest(businessType='Hospitality', audience='Founder-selected community',
                             location='Brooklyn', budget='TBD', objectives=[])
    result = comparison.recompose(
        project, evidence_store=EmptyStore(), exclude_entity_ids=['id-one'],
        tag_envelope=tag_envelope, recommend_envelope=recommend_envelope)

    assert provider.seen[0]['tag_result']['results'][0]['id'] == 'urn:tag:interests:qloo:founder_selected'
    assert [row['entity_id'] for row in provider.seen[0]['recommendations']['results']] == ['id-two']
    assert all('North Room' not in c['description'] for c in result['concepts'])


def test_recompose_handles_subset_seed_tags_from_an_earlier_removal(monkeypatch):
    """When an earlier step removed one of three tags, basis.evidence sends only the remaining two."""
    from backend.evidence_store import canonical_key
    from backend.models import ProjectRequest

    tag_rows = [
        {'id': 'urn:tag:interests:qloo:food_design', 'name': 'Food design'},
        {'id': 'urn:tag:interests:qloo:coffee', 'name': 'Coffee'},
        {'id': 'urn:tag:interests:qloo:bakery', 'name': 'Bakery'},
    ]
    place_rows = [
        {'entity_id': 'id-one', 'name': 'North Bakery', 'properties': {'description': 'Bakery and pastry shop.'}},
        {'entity_id': 'id-two', 'name': 'South Bakery', 'properties': {'description': 'Artisan bread bakery.'}},
    ]
    provider = RecomposeProvider(tag_rows, place_rows)
    monkeypatch.setattr(comparison, 'QlooHarnessProvider', lambda *a, **k: provider)

    class StubStore:
        def __init__(self):
            self.keys = {}

        def get(self, key):
            return self.keys.get(key)

    store = StubStore()
    store.keys[canonical_key('find_tags', {'query': 'Food & beverage Design-conscious Gen Z',
                                           'limit': 3})] = {'status': 'ok', 'results': tag_rows}
    store.keys[canonical_key('recommend', {
        'target_type': 'place',
        'signal_tags': [r['id'] for r in tag_rows],
        'filter_location': 'Brooklyn, New York', 'limit': 10,
    })] = {'status': 'ok', 'results': place_rows}

    project = ProjectRequest(businessType='Food & beverage', audience='Design-conscious Gen Z',
                             location='Brooklyn, New York', budget='$25k – $50k', objectives=[])
    result = comparison.recompose(
        project, evidence_store=store, exclude_entity_ids=['id-one'],
        seed_tag_ids=['urn:tag:interests:qloo:food_design', 'urn:tag:interests:qloo:coffee'],
    )
    assert [row['entity_id'] for row in provider.seen[0]['recommendations']['results']] == ['id-two']
    assert result['dropped'] == 1

