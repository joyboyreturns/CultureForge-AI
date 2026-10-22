#!/usr/bin/env python3
"""Build shared/demoPack.json from real Qloo answers for the three prepared demos.

It runs the demos' own flows in-process (the landing-page generate route, the
audience step, the evidence challenge, the first direction's interest cells and
the venue geocodes) and records exactly which held evidence they read. By
default it spends nothing: with QLOO_LIVE_ENABLED=false a missing answer is
reported, not invented. Add --live to fetch what is missing, once, through the
normal quota guard (judging profile).

    python3 scripts/export_demo_pack.py            # report what is held, write the pack if complete
    python3 scripts/export_demo_pack.py --live     # fetch the gaps first
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEMOS = ('tokyo-morning-bakery', 'paris-ice-cream', 'melbourne-specialty-coffee')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--only', action='append')
    parser.add_argument('--allow-gaps', action='store_true', help='write the pack even if some flows were not held')
    args = parser.parse_args()
    os.environ.setdefault('RUN_PROFILE', 'judging')
    os.environ['AI_GATEWAY_ENABLED'] = 'false'
    if not args.live:
        os.environ['QLOO_LIVE_ENABLED'] = 'false'
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
    if not args.live:
        os.environ['QLOO_LIVE_ENABLED'] = 'false'
    os.environ['AI_GATEWAY_ENABLED'] = 'false'
    from fastapi.testclient import TestClient
    from backend import geocode
    from backend.evidence_store import ADAPTER_VERSION, get_store
    from backend.main import app

    store = get_store()
    read: set[str] = set()
    original_get = type(store).get

    def recording_get(self, key, ttl_seconds=None):
        value = original_get(self, key, ttl_seconds)
        if value is not None:
            read.add(key)
        return value

    type(store).get = recording_get
    client = TestClient(app)
    briefs = {b['id']: b for b in json.loads((ROOT / 'shared' / 'demoBriefs.json').read_text())['briefs']}
    problems, venues = [], []
    for demo in args.only or DEMOS:
        project = briefs[demo]['project']
        print(f'== {demo}')
        steps = [('audience seeds', '/api/taste/resolve',
                  {'project': project, 'audience': project['audience']}),
                 ('answer', '/api/projects/generate', project)]
        answer = None
        for label, path, body in steps:
            response = client.post(path, json=body, timeout=300)
            ok = response.status_code == 200
            print(f'  {label}: HTTP {response.status_code}')
            if not ok:
                problems.append(f'{demo}: {label}: {response.text[:200]}')
            elif path.endswith('generate'):
                answer = response.json()
        if not answer:
            continue
        places = [e for e in answer['evidence'] if e['kind'] == 'entity']
        anchor = next((e for e in places if answer['concepts'] and e['id'] in answer['concepts'][0]['evidenceIds']), None) \
            or (places[0] if places else None)
        if anchor and anchor.get('entityId'):
            r = client.post('/api/qloo/where-popular',
                            json={'entity': anchor['entityId'], 'within': project['location'], 'limit': 20}, timeout=300)
            print(f'  cells for {anchor["label"]}: HTTP {r.status_code}')
            if r.status_code != 200:
                problems.append(f'{demo}: cells: {r.text[:200]}')
        r = client.post('/api/projects/challenge', json={'project': project}, timeout=300)
        print(f'  challenge: HTTP {r.status_code}')
        if r.status_code != 200:
            problems.append(f'{demo}: challenge: {r.text[:200]}')
        eligible = [e for e in places if (e.get('relevance') or {}).get('evidenceClass') in
                    ('direct_business', 'indirect_business', 'cultural_attraction')]
        venues += [{'id': e['id'], 'address': e.get('address') or '', 'city': project['location'], 'name': e['label']}
                   for e in eligible]
    # geocode (network, throttled, cached); only after the evidence is complete
    if venues:
        for i in range(0, len(venues), 3):
            geocode.geocode_venues(venues[i:i + 3])
    type(store).get = original_get
    if problems and not args.allow_gaps:
        print('\nINCOMPLETE — not writing the pack:')
        for p in problems:
            print('  -', p)
        return 1
    entries = {k: {'envelope': store._cache[k]['envelope'], 'storedAt': store._cache[k]['storedAt'],
                   'transportRequests': store._cache[k].get('transportRequests', 1)} for k in sorted(read) if k in store._cache}
    wanted = {f'v3|{v["address"].strip().casefold()}|{v["city"].strip().casefold()}' for v in venues if v['address']}
    geo = {k: v for k, v in geocode._load().items() if k in wanted and v.get('status') in
           ('plotted', 'not_found', 'outside_city', 'area_only', 'ambiguous')}
    previous = {}
    if (ROOT / 'shared' / 'demoPack.json').is_file():
        try:
            previous = json.loads((ROOT / 'shared' / 'demoPack.json').read_text())
        except ValueError:
            previous = {}
    if previous.get('adapterVersion') == ADAPTER_VERSION:
        entries = {**previous.get('evidence', {}), **entries}   # a partial run adds to the pack, never shrinks it
        geo = {**previous.get('geocodes', {}), **geo}
    pack = {'note': 'Real Qloo responses for the prepared demos, with their original acquisition times, and the verified '
                    'venue geocodes. Built by scripts/export_demo_pack.py; loaded by backend/demo_pack.py.',
            'gaps': problems, 'adapterVersion': ADAPTER_VERSION, 'demos': list(DEMOS), 'evidence': entries, 'geocodes': geo}
    out = ROOT / 'shared' / 'demoPack.json'
    out.write_text(json.dumps(pack, ensure_ascii=False, separators=(',', ':')))
    for gap in problems:
        print('  gap:', gap[:140])
    print(f'\nWrote {out.name}: {len(entries)} Qloo answers, {len(geo)} geocodes, {out.stat().st_size // 1024} KB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
