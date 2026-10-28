"""The prepared example briefs, and whether their evidence is already held.

`shared/demoBriefs.json` is the one list: the studio's example picker offers
it, the landing page runs the featured `tokyo-morning-bakery` brief, and
`scripts/prewarm.py` fetches its evidence ahead of judging. Asking whether a
brief is held reads the evidence store and never calls Qloo.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .evidence_store import canonical_key, get_store
from .models import ProjectRequest
from . import config
from .providers import QlooHarnessProvider, bridge_payload, brief_places_retrieval_payload, brief_tags_payload

BRIEFS_FILE = Path(__file__).resolve().parent.parent / 'shared' / 'demoBriefs.json'


@lru_cache(maxsize=1)
def briefs() -> tuple[dict, ...]:
    """Every prepared brief, each validated against the same model a request is."""
    data = json.loads(BRIEFS_FILE.read_text(encoding='utf-8'))
    rows = []
    for row in data['briefs']:
        ProjectRequest(**row['project'])
        rows.append(row)
    return tuple(rows)


def held(project: dict) -> bool:
    """Whether the store holds the seeds, the places and every bridge domain,
    so answering this brief costs no upstream Qloo request."""
    store = get_store()
    tag_envelope = store.get(canonical_key(
        'find_tags', brief_tags_payload(project['businessType'], project['audience'])))
    if tag_envelope is None:
        return False
    tags = [tag for row in QlooHarnessProvider.rows(tag_envelope)
            if (tag := QlooHarnessProvider.tag_id(row))][:3]
    if not tags:
        return False
    if store.get(canonical_key('recommend', brief_places_retrieval_payload(tags, project['location'], project.get('businessIdea', '')))) is None:
        return False
    return all(store.get(canonical_key('recommend', bridge_payload(tags, domain))) is not None
               for domain in config.bridge_domains())


def listing() -> list[dict]:
    return [{**row, 'held': held(row['project'])} for row in briefs()]
