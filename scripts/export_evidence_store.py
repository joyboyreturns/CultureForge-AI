#!/usr/bin/env python3
"""Ship this machine's held evidence to a deployment, through shared/demoPack.json.

Everything the local evidence store holds — every Qloo answer, held agent
report, model naming and analysis, each under its original acquisition time —
and every definitive venue geocode is merged into the demo pack. A deployment
loads the pack at start-up (backend/demo_pack.py) as pinned entries, so a brief
researched here opens there from held evidence, with no Qloo or model request.

Nothing is fetched and nothing is invented: only what the store already holds
is copied, and it never replaces a fresher answer the deployment holds. The
store keeps no failures, so none are shipped. The pack never shrinks: entries
already in it are kept.

    python3 scripts/export_evidence_store.py          # merge the local store into the pack
    python3 scripts/export_evidence_store.py --check  # report what would be added, write nothing
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PACK = ROOT / 'shared' / 'demoPack.json'
DEFINITIVE = ('plotted', 'not_found', 'outside_city', 'area_only', 'ambiguous')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='report only; do not write the pack')
    args = parser.parse_args()
    from backend import geocode
    from backend.evidence_store import ADAPTER_VERSION, get_store

    pack = json.loads(PACK.read_text(encoding='utf-8')) if PACK.is_file() else {}
    if pack and pack.get('adapterVersion') != ADAPTER_VERSION:
        print(f'The pack is for adapter {pack.get("adapterVersion")}; this store is {ADAPTER_VERSION}. '
              'Rebuild the pack with scripts/export_demo_pack.py first.')
        return 1
    evidence = dict(pack.get('evidence') or {})
    geocodes = dict(pack.get('geocodes') or {})
    store = get_store()
    added = 0
    for key, entry in sorted(store._cache.items()):
        if key in evidence or 'envelope' not in entry:
            continue
        evidence[key] = {'envelope': entry['envelope'], 'storedAt': entry['storedAt'],
                         'transportRequests': entry.get('transportRequests', 1)}
        added += 1
    new_geo = {k: v for k, v in geocode._load().items()
               if k not in geocodes and isinstance(v, dict) and v.get('status') in DEFINITIVE}
    geocodes.update(new_geo)
    print(f'Local store: {len(store._cache)} entries. Adding {added} to the pack '
          f'({len(evidence)} in all), and {len(new_geo)} geocodes ({len(geocodes)} in all).')
    if args.check:
        return 0
    pack.update({
        'note': 'Real Qloo responses with their original acquisition times, verified venue geocodes, and held '
                'model naming, agent reports and analyses. The prepared demos are built by '
                'scripts/export_demo_pack.py; everything else a working copy held is added by '
                'scripts/export_evidence_store.py. Loaded by backend/demo_pack.py.',
        'adapterVersion': ADAPTER_VERSION, 'evidence': evidence, 'geocodes': geocodes,
    })
    pack.setdefault('demos', [])
    pack.setdefault('gaps', [])
    PACK.write_text(json.dumps(pack, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Wrote {PACK.relative_to(ROOT)}: {PACK.stat().st_size // 1024} KB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
