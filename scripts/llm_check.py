#!/usr/bin/env python3
"""Check the free model, without spending more than one request.

The naming layer is optional: without a key, the rule engine names the
directions and everything still works. This script tells you which state you
are in, and — with --live — makes exactly one call so you can see that the
free tier answers.

    python3 scripts/llm_check.py            # read-only: what is configured
    python3 scripts/llm_check.py --live     # one request, one answer

Read-only by default, because the free tier is 50 requests a day.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ENV_FILE = Path(__file__).resolve().parent.parent / '.env'


def _load_env() -> None:
    """Read the local .env, with or without python-dotenv installed."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)
        return
    except ImportError:
        pass
    try:
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            name, _, value = line.partition('=')
            name = name.strip()
            value = value.strip().strip('"').strip("'")
            if name and name not in os.environ:
                os.environ[name] = value
    except OSError:
        pass


_load_env()

from backend import llm  # noqa: E402


def main() -> int:
    live = '--live' in sys.argv
    state = llm.status()
    print('=' * 64)
    print(' CultureForge — the free naming layer')
    print('=' * 64)
    print(f"configured : {state['configured']}")
    print(f"model      : {state['model'] or '(none — the rule engine names the directions)'}")
    print(f"free only  : {state['freeOnly']}")
    budget = state['budget']
    print(f"allowance  : {budget['callsToday']}/{budget['dayLimit']} today, "
          f"{budget['callsLastHour']}/{budget['hourLimit']} this hour")

    if not state['configured']:
        print()
        print('No OPENROUTER_API_KEY. That is not an error: the directions keep the names')
        print('the rule engine gives them, and everything else works the same.')
        print('To use the free tier: create a key at https://openrouter.ai/keys, put it in')
        print('.env as OPENROUTER_API_KEY, and run this script again.')
        return 0

    if not live:
        print()
        print('This was a read-only check. Add --live to spend one request and see the answer.')
        return 0

    print()
    print('Asking the free model for one naming…')
    evidence = [
        {'label': 'Whitney Museum of American Art', 'kind': 'entity',
         'description': 'A museum of American art in New York City.',
         'popularity': 0.7311, 'affinity': 0.51, 'rating': 4.5, 'priceLevel': 2},
    ]
    brief = {
        'businessType': 'Food & beverage',
        'audience': 'Design-conscious Gen Z',
        'location': 'Brooklyn, New York',
        'budget': '$25k – $50k',
        'signals': ['design focused', 'gen z foodies'],
    }
    directions = [{
        'index': 0,
        'currentName': 'The Design Floor',
        'currentTagline': 'A space that behaves like the thing it sells.',
        'currentPositioning': 'For an audience that treats taste as the primary signal of quality.',
        'venues': [{'name': 'Whitney Museum of American Art', 'role': 'primary',
                    'description': 'A museum of American art in New York City.'}],
    }]
    names, report = llm.name_directions(brief, directions, evidence)
    print(f"model      : {report.get('model')}")
    print(f"used       : {report.get('used')}")
    if report.get('reason'):
        print(f"reason     : {report['reason']}")
    for dropped in report.get('dropped') or []:
        print(f"dropped    : {dropped}")
    for index, wording in sorted(names.items(), key=lambda item: int(item[0])):
        print(f"direction {index}:")
        print(f"  name     : {wording.get('name')}")
        print(f"  tagline  : {wording.get('tagline')}")
        print(f"  rationale: {wording.get('rationale')}")
    print('-' * 64)
    print(json.dumps(llm.budget_state(), indent=2))
    return 0 if names else 1


if __name__ == '__main__':
    raise SystemExit(main())
