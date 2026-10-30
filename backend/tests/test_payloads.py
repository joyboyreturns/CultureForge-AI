"""Payload builders and error mapping: the two edges where Qloo meets this app.

A changed payload changes its cache key, which silently invalidates every
prewarmed brief, so the builders are pinned to a snapshot. And every harness
failure must map to a stated code and an HTTP status, never a crash.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import backend.main as main
from backend import providers as p
from backend.providers import QLOO_CAPABILITIES, QlooHarnessError, QlooHarnessProvider

SNAPSHOT = json.loads((Path(__file__).resolve().parent.parent / 'fixtures' / 'payload_snapshots.json').read_text())

BUILT = {
    'brief_tags_payload': ('find_tags', p.brief_tags_payload('Food & beverage', 'Design-conscious Gen Z')),
    'brief_places_payload': ('recommend', p.brief_places_payload(['urn:tag:a', 'urn:tag:b'], 'Brooklyn, New York')),
    'bridge_payload': ('recommend', p.bridge_payload(['urn:tag:a'], 'artist')),
    'describe_payload': ('describe', p.describe_payload('North Room', 'place')),
    'describe_payload_untyped': ('describe', p.describe_payload('North Room')),
    'entity_tags_payload': ('entity_tags', p.entity_tags_payload(['e1', 'e2', 'e3', 'e4', 'e5', 'e6'], 'place', 10)),
    'where_popular_payload': ('where_popular', p.where_popular_payload('e1', 'Brooklyn, New York', None, 20)),
    'audience_demographics_payload': ('audience_demographics', p.audience_demographics_payload('e1', 'place', 5)),
    'trends_payload': ('trends', p.trends_payload(['e1', 'e2'], 'place', '2026-07-01', '2026-10-01', 10)),
}


@pytest.mark.parametrize('name', sorted(BUILT))
def test_each_builder_matches_its_snapshot(name):
    assert BUILT[name][1] == SNAPSHOT[name], f'{name} changed: every held cache entry for it goes cold'


@pytest.mark.parametrize('name', sorted(BUILT))
def test_each_builder_sends_only_fields_its_workflow_accepts(name):
    operation, payload = BUILT[name]
    spec = QLOO_CAPABILITIES[operation]
    allowed = set(spec['required']) | set(spec['optional']) | ({spec['entityTypeField']} - {None})
    assert set(payload) <= allowed, set(payload) - allowed
    assert set(spec['required']) <= set(payload)
    if 'limit' in payload:
        assert spec['acceptsLimit'] and 1 <= payload['limit'] <= 20  # the harness caps results at 20


def test_entity_lists_never_exceed_the_harness_cap():
    assert len(p.entity_tags_payload([f'e{n}' for n in range(30)])['entities']) == 5
    assert len(p.trends_payload([f'e{n}' for n in range(30)], 'place', 'a', 'b')['entities']) == 5


def test_fresh_place_retrieval_constrains_results_not_the_audience_location(store):
    payload = p.brief_places_retrieval_payload(['urn:tag:food'], 'Berlin, Germany')
    assert payload['filter_location'] == 'Berlin, Germany'
    assert 'signal_location' not in payload


def test_legacy_evidence_replays_under_its_own_key_and_modern_evidence_wins(store):
    tags, location = ['urn:tag:food'], 'Berlin, Germany'
    modern = p.brief_places_payload(tags, location)
    legacy = {k: v for k, v in modern.items() if k != 'filter_location'}
    legacy['signal_location'] = location
    store.put(p.canonical_key('recommend', legacy), {'results': [{'name': 'Held'}]}, 1)
    assert p.brief_places_retrieval_payload(tags, location) == legacy
    assert store.get(p.canonical_key('recommend', modern)) is None, 'Never copy an old response to a new query key'
    store.put(p.canonical_key('recommend', modern), {'results': [{'name': 'Filtered'}]}, 1)
    assert p.brief_places_retrieval_payload(tags, location) == modern


def test_a_legacy_empty_result_does_not_prevent_the_correct_location_search(store):
    modern = p.brief_places_payload(['urn:tag:food'], 'Berlin, Germany')
    legacy = {k: v for k, v in modern.items() if k != 'filter_location'}
    legacy['signal_location'] = 'Berlin, Germany'
    store.put(p.canonical_key('recommend', legacy), {'results': []}, 1)
    assert p.brief_places_retrieval_payload(['urn:tag:food'], 'Berlin, Germany') == modern


def test_unheld_location_with_live_off_names_the_location_and_a_real_recovery(monkeypatch, store):
    provider = QlooHarnessProvider()
    store.put(p.canonical_key('recommend', {'filter_location': 'Berlin, Germany'}), {
        'operation': 'recommend', 'results': [{'name': 'Reference'}],
        'query_intent': {'signals': {'tags': ['urn:tag:food']}, 'filters': {'location': 'Berlin, Germany'}}}, 1)
    monkeypatch.setenv('QLOO_LIVE_ENABLED', 'false')
    with pytest.raises(QlooHarnessError) as caught:
        provider.recommend_places(['urn:tag:food'], 'Another City')
    assert caught.value.code == 'LIVE_DISABLED'
    assert 'Another City' in str(caught.value)
    assert 'Berlin, Germany' in str(caught.value)
    assert 'returned no places' not in str(caught.value), 'An unheld query is not evidence of no places'


def _run_with(monkeypatch, stdout, returncode=1, raise_exc=None):
    provider = QlooHarnessProvider()
    monkeypatch.setattr(provider, '_resolve_command', lambda: ['fake-qloo'])

    def run(*args, **kwargs):
        if raise_exc:
            raise raise_exc
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr='secret context')
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(QlooHarnessError) as caught:
        provider._run_workflow('find_tags', {'query': 'x', 'limit': 3})
    return caught.value


@pytest.mark.parametrize('error, code', [
    ({'code': 'QLOO_RATE_LIMITED'}, 'RATE_LIMITED'),
    ({'status': 429}, 'RATE_LIMITED'),
    ({'code': 'QLOO_AUTH'}, 'UPSTREAM_UNAUTHENTICATED'),
    ({'status': 401}, 'UPSTREAM_UNAUTHENTICATED'),
    ({'status': 502}, 'PROVIDER_UNAVAILABLE'),
    ({'status': 400}, 'INVALID_UPSTREAM_REQUEST'),
    ({'code': 'TOOL_INPUT'}, 'INVALID_UPSTREAM_REQUEST'),
    ({'code': 'FILTER_IGNORED'}, 'UPSTREAM_REJECTED'),
    ({'code': 'QLOO_DNS_ERROR'}, 'PROVIDER_UNAVAILABLE'),
    ({'code': 'QLOO_TIMEOUT'}, 'PROVIDER_UNAVAILABLE'),
    ({'code': 'SOMETHING_NEW'}, 'UPSTREAM_REJECTED'),
])
def test_harness_failures_map_to_stated_codes_and_statuses(monkeypatch, error, code):
    exc = _run_with(monkeypatch, json.dumps({'error': error}))
    assert exc.code == code
    assert 'secret context' not in str(exc)  # stderr is never surfaced
    assert main.ERROR_STATUS.get(code, 502) in {422, 429, 502, 503, 504}


def test_unreadable_failure_output_is_still_a_stated_rejection(monkeypatch):
    assert _run_with(monkeypatch, 'not json').code == 'UPSTREAM_REJECTED'


def test_a_timeout_and_a_missing_binary_are_stated(monkeypatch):
    assert _run_with(monkeypatch, '', raise_exc=subprocess.TimeoutExpired('qloo', 90)).code == 'UPSTREAM_TIMEOUT'
    assert _run_with(monkeypatch, '', raise_exc=OSError('no such file')).code == 'PROVIDER_UNAVAILABLE'


def test_a_successful_but_malformed_answer_is_rejected(monkeypatch):
    assert _run_with(monkeypatch, 'not json', returncode=0).code == 'UPSTREAM_MALFORMED'
    assert _run_with(monkeypatch, '[1, 2]', returncode=0).code == 'UPSTREAM_MALFORMED'


def test_every_mapped_code_has_an_http_status():
    codes = {'RATE_LIMITED', 'UPSTREAM_UNAUTHENTICATED', 'PROVIDER_UNAVAILABLE', 'INVALID_UPSTREAM_REQUEST',
             'UPSTREAM_REJECTED', 'UPSTREAM_TIMEOUT', 'UPSTREAM_MALFORMED', 'QUOTA_EXHAUSTED',
             'LIVE_DISABLED', 'BUDGET_UNAVAILABLE', 'MODEL_UNAVAILABLE', 'NO_EVIDENCE', 'NEEDS_INPUT'}
    assert codes <= set(main.ERROR_STATUS)


def test_a_matching_place_returned_for_another_city_is_named_in_what_is_missing():
    """Observed live: Qloo returned a Chicago climbing gym for a Denver query."""
    from types import SimpleNamespace
    from backend.outcome import build_outcome
    from backend import relevance
    category = relevance.classify_brief('Wellness', 'bouldering gym', 'beginner climbers')
    place = SimpleNamespace(kind='entity', label='First Ascent Uptown', location='Chicago, Illinois',
                            relevance={'evidenceClass': 'unverified_geography'})
    outcome = build_outcome(category=category, evidence=[place], concepts=[])
    assert outcome['state'] == 'insufficient_evidence'
    assert any('First Ascent Uptown (Chicago, Illinois)' in line for line in outcome['missing'])
