"""Shared fixtures. No live Qloo calls are made anywhere in this suite."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / 'fixtures'


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
