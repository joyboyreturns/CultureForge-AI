#!/usr/bin/env python3
"""Smoke-test a running CultureForge deployment without spending quota.

    python3 scripts/smoke_test.py https://<your-host>
    python3 scripts/smoke_test.py http://127.0.0.1:8000

It checks that the landing page and studio are served, that /api/health
reports a ready live provider and its profile, and that the prepared
example briefs are listed. Then it answers the first prepared brief **only
if the server already holds its evidence** (seeds, places and bridge
domains), and fails if that answer cost any upstream Qloo request. If the
model gateway is on and the brief's names are not held, that answer may make
one model naming request. A cold brief is reported and skipped, never fetched:
run scripts/prewarm.py --live for that.

Exit code 0 means every check passed; 1 means at least one failed.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

failures = 0


def check(label: str, condition: bool, detail: str = '') -> bool:
    global failures
    print(f"{'[ok]  ' if condition else '[FAIL]'} {label}{f' - {detail}' if detail else ''}")
    if not condition:
        failures += 1
    return condition


def get(base: str, path: str, timeout: int = 20) -> tuple[int, str, str]:
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as response:
            return response.status, response.headers.get('content-type', ''), response.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get('content-type', ''), exc.read().decode('utf-8', 'replace')
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, '', str(exc)


def post(base: str, path: str, body: dict, timeout: int = 120) -> tuple[int, dict]:
    request = urllib.request.Request(base + path, data=json.dumps(body).encode(), method='POST',
                                     headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode())
        except json.JSONDecodeError:
            return exc.code, {}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    base = sys.argv[1].rstrip('/')
    print(f'Smoke test: {base}\n')

    for path in ('/', '/studio/'):
        status, kind, _ = get(base, path)
        check(f'GET {path} serves HTML', status == 200 and 'text/html' in kind, f'{status} {kind}')

    status, _, text = get(base, '/health')
    check('GET /health', status == 200, str(status))
    status, _, text = get(base, '/api/health')
    health = json.loads(text) if status == 200 else {}
    check('GET /api/health', status == 200, str(status))
    check('Live Qloo provider is ready', health.get('dataMode') == 'live' and health.get('providerReady') is True,
          health.get('reason') or '')
    print(f"       profile={health.get('profile')} live={health.get('qlooLiveEnabled')} "
          f"budgets={json.dumps((health.get('budgets') or {}).get('qloo'))} cache={json.dumps(health.get('cache'))}")
    if health.get('profileWarning'):
        check('RUN_PROFILE is valid', False, health['profileWarning'])

    status, _, text = get(base, '/api/examples')
    examples = json.loads(text).get('examples', []) if status == 200 else []
    check('Prepared example briefs are listed', status == 200 and len(examples) >= 8, f'{len(examples)} listed')
    held = [row for row in examples if row.get('held')]
    check('At least one prepared brief is held', bool(held), f'{len(held)} of {len(examples)} held')

    first = examples[0] if examples else None
    if first and first.get('held'):
        status, answer = post(base, '/api/projects/generate', first['project'])
        cost = (answer.get('delivery') or {}).get('transportRequests')
        check('The landing-page brief answers from held evidence', status == 200 and bool(answer.get('concepts')),
              f'{status}, {len(answer.get("concepts") or [])} directions')
        check('...and it cost no upstream request', cost == 0, f'transportRequests={cost}')
    elif first:
        print(f"[skip] {first['id']} is not held, so it was not run. Prewarm it: "
              f"python3 scripts/prewarm.py --live --base-url {base}")

    status, _, _ = get(base, '/api/qloo/workflows')
    check('GET /api/qloo/workflows', status == 200, str(status))

    print(f"\n{'All checks passed.' if not failures else f'{failures} check(s) failed.'} "
          'No Qloo request was made. Answering a held brief may make one model naming request '
          'if its names are not held yet.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
