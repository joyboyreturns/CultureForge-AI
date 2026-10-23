#!/usr/bin/env python3
"""Exercise every prepared category without spending upstream quota.

Run only against a server with Qloo, models and geocoding disabled.
python3 scripts/judge_replay.py --base-url http://127.0.0.1:8011
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def call(base, route, body=None):
    request = urllib.request.Request(base + route,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read()
            return response.status, json.loads(raw) if 'json' in response.headers.get('content-type', '') else raw
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8011')
    parser.add_argument('--json', default='artifacts/validation/judge-replay.json')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    _, health = call(base, '/api/health')
    assert health['qlooLiveEnabled'] is False, 'Replay requires the Qloo kill switch'
    assert not health['llm']['configured'], 'Replay requires the model disabled'
    assert health['profile'] == 'judging', 'Use the judging profile'
    _, listing = call(base, '/api/examples')
    rows = []
    for example in listing['examples']:
        assert example['held'], f"Unheld example: {example['id']}"
        start = time.monotonic()
        status, result = call(base, '/api/projects/generate', example['project'])
        assert status == 200, (example['id'], status, result)
        assert result['concepts'], f"Prepared example returned no directions: {example['id']}"
        assert result['delivery']['transportRequests'] == 0
        ids = {item['id'] for item in result['evidence']}
        trace_ids = {event['id'] for event in result['trace']}
        for concept in result['concepts']:
            assert set(concept['evidenceIds']) <= ids
            assert all(set(d['evidenceIds']) <= ids for d in concept['decisions'])
            assert all(concept.get(field) is None for field in ['audienceFit', 'culturalRelevance', 'feasibility'])
        assert all(not item.get('traceId') or item['traceId'] in trace_ids for item in result['evidence'])
        first = next((item for item in result['evidence'] if item['kind'] == 'entity'
            and item['id'] in result['concepts'][0]['evidenceIds']), None)
        if first:
            status, rebuilt = call(base, '/api/projects/recompose', {
                'project': example['project'], 'excludeEntityIds': [first['entityId']]})
            assert status == 200
            assert all(item.get('entityId') != first['entityId'] for item in rebuilt['evidence'])
            remaining = {item['id'] for item in rebuilt['evidence']}
            assert all(set(c['evidenceIds']) <= remaining for c in rebuilt['concepts'])
        status, verdicts = call(base, '/api/projects/challenge', {'project': example['project']})
        assert status == 200 and len(verdicts['directions']) == len(result['concepts'])
        assert all(v['verdict'] in ('supported', 'contested', 'unproven')
            and v.get('scope') and v.get('falsifier') for v in verdicts['directions'])
        status, pdf = call(base, '/api/report/pdf', {'result': result, 'challenge': verdicts})
        assert status == 200 and pdf.startswith(b'%PDF-'), f"PDF failed: {example['id']}"
        row = {'id': example['id'], 'category': example['project']['businessType'],
            'location': example['project']['location'], 'directions': len(result['concepts']),
            'places': sum(e['kind'] == 'entity' for e in result['evidence']),
            'verdicts': [v['verdict'] for v in verdicts['directions']], 'pdf': 'valid response',
            'seconds': round(time.monotonic() - start, 2), 'upstreamRequests': 0}
        rows.append(row)
        print(json.dumps(row), flush=True)
    # Malformed judge inputs must fail before retrieval.
    base_project = listing['examples'][0]['project']
    for label, change in [('empty audience', {'audience': ''}),
                          ('empty city', {'location': ''}),
                          ('objectives as string', {'objectives': 'Make money'}),
                          ('oversized idea', {'businessIdea': 'x' * 161})]:
        status, error = call(base, '/api/projects/generate', {**base_project, **change})
        assert status == 422 and isinstance(error.get('detail'), str), (label, status)
    Path(args.json).write_text(json.dumps({'examples': rows, 'malformedInputs': 4}, indent=2))
    print(f'PASS: {len(rows)} prepared examples across all five business types; four malformed inputs rejected.')


if __name__ == '__main__':
    main()
