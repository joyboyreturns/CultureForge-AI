#!/usr/bin/env python3
"""Fetch the prepared example briefs' evidence before anyone clicks.

Removing the local budgets (RUN_PROFILE=judging) does not remove Qloo's own
quota. This script runs every brief in shared/demoBriefs.json through the
same routes a visitor's click uses, against the server that will answer
them, so the evidence lands in that server's durable store:

    1. POST /api/research/runs       the studio's path (seeds, places, naming, agent)
    2. POST /api/projects/generate   the landing page's path
    3. POST /api/projects/challenge  the evidence test both of them offer

Read-only by default: it reports the profile and which briefs are already
held, and spends nothing. Add --live to fetch. It never retries, and it
stops at the first rate limit, exhausted budget or kill switch rather than
pressing on into the same wall.

    python3 scripts/prewarm.py                                  # what is held
    python3 scripts/prewarm.py --live                           # fetch, local server
    python3 scripts/prewarm.py --live --base-url https://<host> # fetch, deployed server
    python3 scripts/prewarm.py --live --only brooklyn-gen-z-cafe
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

#: Errors that mean every later brief would fail the same way.
STOP_CODES = {'RATE_LIMITED', 'QUOTA_EXHAUSTED', 'LIVE_DISABLED', 'UPSTREAM_UNAUTHENTICATED',
              'PROVIDER_UNAVAILABLE'}
RUN_TIMEOUT_SECONDS = 300
POLL_SECONDS = 3


class RouteError(RuntimeError):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code


def call(base: str, method: str, path: str, body: dict | None = None, timeout: int = 240) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode() or '{}')
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode() or '{}')
        except json.JSONDecodeError:
            payload = {}
        error = payload.get('error') or {}
        raise RouteError(exc.code, error.get('code', 'HTTP_ERROR'),
                         payload.get('detail') or f'HTTP {exc.code}') from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RouteError(0, 'UNREACHABLE', f'{base} did not answer ({exc}).') from exc


def research(base: str, project: dict) -> str:
    started = call(base, 'POST', '/api/research/runs',
                   {'project': project, 'audience': project['audience'], 'seedTagIds': []})
    deadline = time.time() + RUN_TIMEOUT_SECONDS
    while time.time() < deadline:
        time.sleep(POLL_SECONDS)
        run = call(base, 'GET', f"/api/research/runs/{started['runId']}")
        if run['status'] == 'running':
            continue
        if run['status'] == 'failed':
            raise RouteError(0, run.get('errorCode') or 'RUN_FAILED',
                             run.get('error') or 'The research run failed.')
        directions = len((run.get('result') or {}).get('concepts') or [])
        return f"{run['status']}, {directions} direction(s), {run.get('transportRequests', 0)} upstream request(s)"
    raise RouteError(0, 'RUN_TIMEOUT', 'The research run did not finish in time.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--live', action='store_true', help='fetch evidence (spends Qloo quota for briefs not held)')
    parser.add_argument('--only', default='', help='comma-separated brief ids')
    parser.add_argument('--skip-research', action='store_true', help='skip the studio research-run path')
    parser.add_argument('--skip-challenge', action='store_true', help='skip the evidence test')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')

    try:
        health = call(base, 'GET', '/api/health', timeout=15)
        listing = call(base, 'GET', '/api/examples', timeout=15)['examples']
    except RouteError as exc:
        print(f'[fail] {exc}')
        return 1
    print(f"server   : {base}")
    print(f"profile  : {health.get('profile')}   live Qloo: {health.get('qlooLiveEnabled')}   "
          f"provider ready: {health.get('providerReady')}")
    print(f"qloo     : {json.dumps((health.get('budgets') or {}).get('qloo'))}")
    print(f"cache    : {json.dumps(health.get('cache'))}")
    if health.get('reason'):
        print(f"reason   : {health['reason']}")

    wanted = {item.strip() for item in args.only.split(',') if item.strip()}
    chosen = [row for row in listing if not wanted or row['id'] in wanted]
    unknown = wanted - {row['id'] for row in listing}
    if unknown:
        print(f"[fail] unknown brief id(s): {', '.join(sorted(unknown))}")
        return 1
    print()
    for row in chosen:
        print(f"  {'held ' if row['held'] else 'cold '} {row['id']:<28} {row['project']['location']}")
    if not args.live:
        print('\nRead-only: nothing was fetched. Add --live to fetch the cold briefs.')
        return 0
    if health.get('dataMode') != 'live' or not health.get('providerReady'):
        print('\n[fail] this server cannot answer with live Qloo evidence, so there is nothing to prewarm.')
        return 1
    if health.get('profile') != 'judging':
        print('\n[note] the server is in the dev profile, so its local budget still applies.')

    failures: list[str] = []
    for row in chosen:
        project = row['project']
        print(f"\n== {row['id']} ({project['businessType']} · {project['location']})")
        try:
            if not args.skip_research:
                print(f"   research : {research(base, project)}")
            answer = call(base, 'POST', '/api/projects/generate', project)
            places = sum(1 for item in answer.get('evidence', []) if item.get('kind') == 'entity')
            delivery = answer.get('delivery') or {}
            print(f"   generate : {len(answer.get('concepts', []))} direction(s), {places} place(s), "
                  f"{delivery.get('transportRequests', '?')} upstream request(s)")
            if not answer.get('concepts'):
                failures.append(f"{row['id']}: no direction was supported; consider replacing this brief")
                continue
            if not args.skip_challenge:
                tested = call(base, 'POST', '/api/projects/challenge', {'project': project})
                verdicts = ', '.join(item.get('verdict', '?') for item in tested.get('directions', []))
                print(f"   challenge: {verdicts or 'no verdicts'}")
        except RouteError as exc:
            print(f"   [fail] {exc.code}: {exc}")
            failures.append(f"{row['id']}: {exc.code}")
            if exc.code in STOP_CODES:
                print('   Stopping: the next brief would meet the same limit. Nothing was retried.')
                break

    print()
    if failures:
        print('Not prewarmed:')
        for line in failures:
            print(f'  - {line}')
        return 1
    print(f'All {len(chosen)} brief(s) are held.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
