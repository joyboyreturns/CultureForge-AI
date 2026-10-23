#!/usr/bin/env python3
"""Run ONE brief through the studio's research-run path and report what happened.

This is an observation tool, not a loop: it takes one brief, starts one run
against the serving instance, polls it, and prints the milestones a judge would
wait through (first event, first evidence, first partial answer, completion),
the Qloo requests spent, the places returned (with the relevance reason),
the agent's steps and the verdicts of the evidence test.

It spends real Qloo requests when the brief is not held. It never retries and
never loops over briefs, so the cost of a run is the cost printed at the end.

    python3 scripts/brief_probe.py --base-url http://127.0.0.1:8030 \
        --business "Retail" --idea "independent bookshop" \
        --audience "Readers of translated fiction" --location "Mexico City, Mexico"
    python3 scripts/brief_probe.py --example brooklyn-gen-z-cafe     # a prepared brief
    python3 scripts/brief_probe.py ... --challenge --json out.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def call(base: str, method: str, path: str, body: dict | None = None, timeout: int = 300) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode() or '{}')
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode() or '{}')
        except json.JSONDecodeError:
            return exc.code, {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--example', default='', help='id of a prepared brief in shared/demoBriefs.json')
    parser.add_argument('--business', default='')
    parser.add_argument('--idea', default='')
    parser.add_argument('--audience', default='')
    parser.add_argument('--location', default='')
    parser.add_argument('--budget', default='$25k – $50k')
    parser.add_argument('--objective', default='Build a loyal community')
    parser.add_argument('--challenge', action='store_true', help='also run the evidence test (more Qloo requests when cold)')
    parser.add_argument('--timeout', type=int, default=480)
    parser.add_argument('--json', default='', help='write the full final record here')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')

    if args.example:
        briefs = json.loads((ROOT / 'shared' / 'demoBriefs.json').read_text())['briefs']
        match = next((b for b in briefs if b['id'] == args.example), None)
        if not match:
            print(f'unknown example {args.example}')
            return 2
        project = dict(match['project'])
    else:
        project = {'businessType': args.business, 'businessIdea': args.idea, 'audience': args.audience,
                   'location': args.location, 'budget': args.budget, 'objectives': [args.objective]}
    print('INPUT  ', json.dumps(project, ensure_ascii=False))

    _, before = call(base, 'GET', '/api/health', timeout=20)
    qloo_before = (before.get('budgets') or {}).get('qloo', {}).get('callsToday')
    llm_before = (before.get('budgets') or {}).get('llm', {}).get('callsToday')

    t0 = time.monotonic()
    status, started = call(base, 'POST', '/api/research/runs',
                           {'project': project, 'audience': project['audience'], 'seedTagIds': []}, timeout=60)
    if status != 202:
        print(f'START  HTTP {status}: {json.dumps(started)[:400]}')
        return 1
    run_id = started['runId']
    marks: dict[str, float] = {}
    seen = 0
    run: dict = {}
    while time.monotonic() - t0 < args.timeout:
        time.sleep(1.0)
        status, run = call(base, 'GET', f'/api/research/runs/{run_id}', timeout=30)
        elapsed = time.monotonic() - t0
        for event in run.get('events', [])[seen:]:
            print(f"  +{elapsed:6.1f}s  {event['step']:<28} {event['status']:<8} {(event.get('detail') or '')[:110]}")
        seen = len(run.get('events', []))
        if run.get('events') and 'firstEvent' not in marks:
            marks['firstEvent'] = elapsed
        if run.get('partialResult') and 'partial' not in marks:
            marks['partial'] = elapsed
        if run['status'] != 'running':
            marks['done'] = elapsed
            break
    else:
        print('TIMEOUT: the run did not finish; it is still running on the server.')

    print()
    print(f"STATUS {run.get('status')}  error={run.get('errorCode')}  total={marks.get('done', -1):.1f}s  "
          f"firstEvent={marks.get('firstEvent', -1):.1f}s  partialAnswer={marks.get('partial', -1):.1f}s  "
          f"timings={run.get('timings')}")
    print(f"COST   transportRequests={run.get('transportRequests')} workflowCalls={run.get('workflowCalls')}")
    if run.get('clarification'):
        print('CLARIFY', json.dumps(run['clarification'], ensure_ascii=False)[:700])
    if run.get('error'):
        print('ERROR  ', run['error'])

    result = run.get('result') or run.get('partialResult') or {}
    label = 'FINAL' if run.get('result') else 'PARTIAL'
    evidence = result.get('evidence', [])
    places = [e for e in evidence if e.get('kind') == 'entity']
    print(f'{label}: {len(result.get("concepts", []))} direction(s), {len(places)} place(s)')
    for place in places:
        print(f"   place  {place.get('label')[:48]:<48} {place.get('entityType') or ''} | "
              f"{(place.get('relevance') or {}).get('verdict', '') if isinstance(place.get('relevance'), dict) else ''}")
    for concept in result.get('concepts', []):
        print(f"   idea   {concept['name']} — {concept['tagline'][:100]}")
        print(f"          cites {len(concept.get('evidenceIds', []))} item(s)")
    agent = result.get('agent') or {}
    if agent:
        print(f"AGENT  mode={agent.get('mode')} status={agent.get('status')} modelCalls={agent.get('modelCalls')} "
              f"stop={agent.get('stoppingReason')}")
        for step in agent.get('steps', []):
            print(f"   step {step['index']} {step['tool']} [{step['status']}] cached={step['cached']} "
                  f"upstream={step['upstreamRequests']} — {step['reason'][:90]} => {step['detail'][:100]}")
        for rejected in agent.get('rejectedClaims', []):
            print('   rejected claim:', json.dumps(rejected, ensure_ascii=False)[:200])
    intent = result.get('intent')
    if intent:
        print('INTENT ', json.dumps(intent, ensure_ascii=False)[:600])

    record = {'input': project, 'run': run, 'marks': marks}
    if args.challenge and result.get('concepts'):
        t1 = time.monotonic()
        status, tested = call(base, 'POST', '/api/projects/challenge', {'project': project}, timeout=300)
        print(f'CHALLENGE HTTP {status} in {time.monotonic() - t1:.1f}s')
        for item in tested.get('directions', []):
            print(f"   {item.get('verdict'):<10} {item.get('directionId')} — {(item.get('reason') or '')[:130]}")
        record['challenge'] = tested

    _, after = call(base, 'GET', '/api/health', timeout=20)
    qloo_after = (after.get('budgets') or {}).get('qloo', {}).get('callsToday')
    llm_after = (after.get('budgets') or {}).get('llm', {}).get('callsToday')
    print(f'COUNTERS qloo calls today {qloo_before} -> {qloo_after}; model calls today {llm_before} -> {llm_after}')
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(record, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
