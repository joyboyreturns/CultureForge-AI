"""Shared fixtures. No live Qloo calls are made anywhere in this suite."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / 'fixtures'


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    """Tests must not depend on credentials or modify the owner's saved work."""
    from backend import evidence_store, ledger, platform, providers

    monkeypatch.setenv('CULTUREFORGE_PROVIDER', 'mock')
    # A developer's .env may hold RUN_PROFILE=judging or the kill switch; the
    # suite runs in the dev profile unless a test says otherwise.
    monkeypatch.setitem(providers._RATE_LIMIT, 'until', 0.0)
    monkeypatch.setenv('RUN_PROFILE', 'dev')
    monkeypatch.setenv('QLOO_LIVE_ENABLED', 'true')
    for name in ('CULTUREFORGE_EVIDENCE_TTL_HOURS', 'QLOO_RATE_LIMIT_COOLDOWN_SECONDS'):
        monkeypatch.setenv(name, '')
    monkeypatch.setattr(platform, 'DEFAULT_DB_PATH', tmp_path / 'platform.db')
    monkeypatch.setattr(platform, '_platform', None)
    monkeypatch.setattr(evidence_store, 'STORE_DIR', tmp_path / 'cache')
    monkeypatch.setattr(evidence_store, '_store', None)
    monkeypatch.setattr(providers, '_cached_providers', {})
    monkeypatch.setattr(ledger, 'DB_PATH', tmp_path / 'budget.db')
    # No test may reach the real Qloo CLI. A workflow that misses the test's
    # own evidence store fails loudly here instead of spending live quota.
    # Tests of the transport replace subprocess.run with their own fake.
    import subprocess

    def no_live_qloo(*args, **kwargs):
        raise AssertionError(f'a test tried to run the Qloo CLI: {args[0] if args else kwargs}')
    monkeypatch.setattr(subprocess, 'run', no_live_qloo)
    # The audience bridge is off unless a test switches it on with its own
    # held envelopes.
    monkeypatch.setenv('CULTUREFORGE_BRIDGE_DOMAINS', 'off')
    yield
    if platform._platform is not None:
        platform._platform._connection.close()


@pytest.fixture(scope='session')
def recommend_places() -> dict:
    """A real captured /v2/insights response, sanitised of nothing but itself."""
    return json.loads((FIXTURES / 'recommend_places.json').read_text(encoding='utf-8'))


@pytest.fixture(scope='session')
def entities(recommend_places: dict) -> list[dict]:
    """The entity rows, normalised the way the provider does."""
    rows = []
    for row in recommend_places.get('results', []):
        properties = row.get('properties') or {}
        image = properties.get('image')
        rows.append({
            'entity_id': row.get('entity_id', ''),
            'name': row.get('name', ''),
            'description': properties.get('description') or '',
            'short_description': properties.get('short_description') or '',
            'image': (image or {}).get('url', '') if isinstance(image, dict) else (image or ''),
            'popularity': row.get('popularity') or 0.0,
            'affinity': row.get('affinity') or 0.0,
            'business_rating': properties.get('business_rating'),
            'price_level': properties.get('price_level'),
        })
    return rows


@pytest.fixture
def store(tmp_path, monkeypatch):
    """An isolated evidence store."""
    from backend import evidence_store

    monkeypatch.setattr(evidence_store, 'STORE_DIR', tmp_path)
    monkeypatch.setattr(evidence_store, 'CACHE_FILE', tmp_path / 'evidence_cache.json')
    monkeypatch.setattr(evidence_store, 'SNAPSHOT_FILE', tmp_path / 'snapshots.json')
    monkeypatch.setattr(evidence_store, '_store', None)
    return evidence_store.get_store()


@pytest.fixture(autouse=True)
def no_model_calls(monkeypatch):
    """The suite never calls a model.

    The local model allowance is bounded, and a test that reached the network
    would spend part of it every time the suite ran. The naming layer is off
    for every test; the ones that care about it switch it back on themselves.
    """
    from backend import llm

    from backend import reasoning

    monkeypatch.setattr(llm, 'is_configured', lambda: False)
    monkeypatch.setattr(reasoning, 'configured', lambda: False)
    # And no request may leave for the Gateway, whatever a test switches on.
    # Tests of the transport replace urlopen with their own fake.
    import urllib.request

    def no_live_model(*args, **kwargs):
        raise AssertionError('a test tried to open a network connection')
    monkeypatch.setattr(urllib.request, 'urlopen', no_live_model)
    # Blank, so a display name in a developer's .env cannot leak into a test.
    monkeypatch.setenv('AI_GATEWAY_DISPLAY_MODEL', '')
