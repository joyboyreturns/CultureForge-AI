"""The evidence store must survive a restart, collapse duplicates, and expire."""
from __future__ import annotations

import threading
import time

from backend.evidence_store import EvidenceStore, canonical_key, transport_request_count


def test_canonical_key_is_stable_and_order_independent():
    a = canonical_key('find_tags', {'query': 'coffee', 'limit': 3})
    b = canonical_key('find_tags', {'limit': 3, 'query': 'coffee'})
    c = canonical_key('find_tags', {'query': 'tea', 'limit': 3})
    assert a == b
    assert a != c


def test_a_stored_envelope_survives_a_new_store_instance(store, tmp_path):
    key = canonical_key('find_tags', {'query': 'coffee'})
    store.put(key, {'status': 'ok', 'results': []}, transport_requests=2)
    # A brand new store over the same directory, as after a restart.
    reopened = EvidenceStore(directory=tmp_path)
    assert reopened.get(key) is not None
    assert reopened.transport_requests(key) == 2


def test_entries_expire(store):
    key = canonical_key('find_tags', {'query': 'old'})
    store.put(key, {'status': 'ok'}, 1)
    assert store.get(key, ttl_seconds=3600) is not None
    assert store.get(key, ttl_seconds=-1) is None


def test_snapshots_round_trip(store):
    store.save_snapshot('snap-1', {'projectId': 'cf-1', 'concepts': []})
    assert store.get_snapshot('snap-1')['projectId'] == 'cf-1'
    assert store.get_snapshot('snap-missing') is None


def test_concurrent_callers_collapse_into_one(store):
    """Two threads asking for the same evidence must produce one upstream call."""
    from backend.evidence_store import cached_call

    calls = []
    key = canonical_key('recommend', {'x': 1})

    def slow() -> dict:
        calls.append(1)
        time.sleep(0.2)
        return {'status': 'ok', 'results': []}

    results = []
    threads = [threading.Thread(target=lambda: results.append(cached_call(key, slow)))
               for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(calls) == 1, 'the upstream call must happen once'
    assert len(results) == 4
    for envelope, was_cached, _requests in results:
        assert envelope['status'] == 'ok'


def test_transport_requests_counts_the_real_http_calls():
    envelope = {'provenance': {'requests': [{'path': '/v2/insights'}, {'path': '/v2/tags'}]}}
    assert transport_request_count(envelope) == 2
    assert transport_request_count({'provenance': {}}) == 1


def test_evidence_that_was_already_held_costs_nothing(store):
    """A cached brief must report zero upstream requests, not the key's lifetime total."""
    from backend.evidence_store import cached_call

    key = canonical_key('recommend', {'x': 'cached'})
    calls = []

    def upstream() -> dict:
        calls.append(1)
        return {'status': 'ok', 'results': []}

    envelope, was_cached, requests = cached_call(key, upstream)
    assert requests == 1
    assert was_cached is False

    envelope, was_cached, requests = cached_call(key, upstream)
    assert requests == 0, 'the second call spent nothing upstream'
    assert was_cached is True
    assert len(calls) == 1, 'no second upstream call'

    # The key's lifetime total is still tracked, for the quota guard.
    assert store.transport_requests(key) == 1


def test_the_provider_reports_zero_for_a_cached_workflow(monkeypatch, store):
    """A run that reuses held evidence must not claim to have spent a request."""
    from backend.providers import QlooHarnessProvider

    provider = QlooHarnessProvider()
    payload = {'query': 'a cached brief', 'limit': 3}
    key = canonical_key('find_tags', payload)
    store.put(key, {'status': 'ok', 'results': []}, transport_requests=1)

    envelope, was_cached, requests = provider.run_workflow_cached('find_tags', payload)

    assert was_cached is True
    assert requests == 0
    assert envelope['status'] == 'ok'
