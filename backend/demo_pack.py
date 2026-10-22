"""The prepared demos' real Qloo evidence, shipped with the repository.

``shared/demoPack.json`` is an export of what Qloo actually returned for the
three prepared briefs (seeds, places, bridges, interest cells), with the time
each answer was acquired, plus the venue geocodes that were verified for them.
At start-up it is placed in the evidence store as pinned entries, so a fresh
clone opens the demos instantly, from held evidence, with no Qloo request and
with the original acquisition time still stated on the screen. Nothing here is
invented: ``scripts/export_demo_pack.py`` builds it from real responses, and a
pack made for another adapter version is refused rather than guessed at.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from . import geocode
from .evidence_store import ADAPTER_VERSION, get_store

PACK_FILE = Path(__file__).resolve().parent.parent / 'shared' / 'demoPack.json'


def seed() -> dict:
    """Load the pack; returns what was added. Never raises: a bad pack leaves the app as it was."""
    result = {'evidence': 0, 'geocodes': 0, 'skipped': ''}
    try:
        if not PACK_FILE.is_file():
            result['skipped'] = 'no pack file'
            return result
        pack = json.loads(PACK_FILE.read_text(encoding='utf-8'))
        if pack.get('adapterVersion') != ADAPTER_VERSION:
            result['skipped'] = f'pack is for adapter {pack.get("adapterVersion")}, this is {ADAPTER_VERSION}'
            logging.getLogger(__name__).warning('Demo pack skipped: %s', result['skipped'])
            return result
        store = get_store()
        for key, entry in (pack.get('evidence') or {}).items():
            if store.seed(key, entry['envelope'], float(entry['storedAt']), int(entry.get('transportRequests', 1))):
                result['evidence'] += 1
        result['geocodes'] = geocode.seed(pack.get('geocodes') or {})
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result['skipped'] = f'pack unreadable ({type(exc).__name__})'
        logging.getLogger(__name__).warning('Demo pack skipped: %s', result['skipped'])
    return result
