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


def test_a_repeated_brief_reports_that_it_spent_nothing(monkeypatch, recommend_places):
    """The delivery is the product's receipt. A replay must read zero, not unknown.

    The brief is answered twice from the same evidence. The second answer is
    served from the provider's own cache, so it costs no upstream request, and
    the delivery has to say so rather than leave the cost blank.
    """
    from backend.models import ProjectRequest
    from backend.providers import QlooHarnessProvider

    find_tags = {
        'status': 'ok',
        'results': [
            {'id': 'urn:tag:customer_segment:qloo:gen_z_foodies', 'name': 'Gen Z Foodies', 'popularity': 0.97},
            {'id': 'urn:tag:interests:qloo:modern_restaurant_design', 'name': 'Modern Restaurant Design', 'popularity': 0.98},
            {'id': 'urn:tag:interests:qloo:food_design', 'name': 'Food Design', 'popularity': 0.93},
        ],
        'execution': {'duration_ms': 1},
        'provenance': {'endpoint': 'stub', 'requests': []},
    }

    provider = QlooHarnessProvider()
    calls: list[str] = []

    def fake(operation, payload):
        calls.append(operation)
        if operation == 'find_tags':
            return find_tags, False, 1
        return recommend_places, False, 1

    monkeypatch.setattr(provider, 'run_workflow_cached', fake)

    project = ProjectRequest(
        businessType='Food & beverage', audience='Design-conscious Gen Z',
        location='Brooklyn, New York', budget='$25k – $50k',
        objectives=['Build a loyal community'],
    )

    first = provider.generate(project)
    assert first.delivery is not None
    assert first.delivery.kind == 'fresh'
    assert first.delivery.transportRequests == 2

    second = provider.generate(project)
    assert second.delivery is not None
    assert second.delivery.kind == 'cache'
    assert second.delivery.transportRequests == 0
    assert calls == ['find_tags', 'recommend'], 'the replay must not call Qloo again'


def test_a_reused_step_does_not_claim_the_original_calls_duration():
    """A held envelope carries the time of the call that fetched it.

    If a run that reused that evidence reported that duration, a free and
    instant answer would look like it waited on the network for twenty
    seconds. The step's own duration is zero, and the original time is stated
    in the detail rather than presented as this run's latency.
    """
    from backend.providers import mark_reused
    from backend.models import TraceEvent

    event = TraceEvent(id='t1', step='retrieve-evidence', workflow='recommend', status='ok',
                       durationMs=23299, resultCount=5, evidenceIds=[])
    mark_reused(event)

    assert event.durationMs == 0
    assert '23.3s' in (event.detail or ''), 'the original duration is still stated'
    assert 'no time waiting' in (event.detail or '')


def test_a_fresh_step_keeps_the_duration_of_the_call_that_made_it():
    """A step that really called the API reports the time it really took."""
    from backend.providers import QlooHarnessProvider

    envelope = {
        'status': 'ok', 'results': [],
        'execution': {'duration_ms': 23299, 'correlation_id': 'abc'},
        'provenance': {'endpoint': '/v2/insights', 'requests': []},
    }
    event = QlooHarnessProvider._trace_event('retrieve-local-evidence', 'recommend', envelope, 0)

    assert event.durationMs == 23299
    assert event.correlationId == 'abc'
