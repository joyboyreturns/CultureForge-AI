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
