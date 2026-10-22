"""The run profile, and every limit it sets.

One environment variable decides how careful the server is with quota:

    RUN_PROFILE=dev       the local call budgets below are enforced
    RUN_PROFILE=judging   every call-count budget is off

Judging removes only the *counts*. It keeps everything that protects a judge
from a bad answer: the per-request timeouts, the stated handling of a 429,
401 or 5xx, the cool-down after Qloo rate-limits the key, single-flight
de-duplication and the durable evidence cache. Qloo's own server-side quota
still applies in either profile, which is what `scripts/prewarm.py` is for.

`QLOO_LIVE_ENABLED=false` is the emergency switch: held evidence is still
served, and nothing new is fetched from Qloo.

Everything here is read from the environment at call time, so a test can
change a profile with `monkeypatch.setenv` and a host can change one with a
restart, never with a code edit.
"""
from __future__ import annotations

import os
from typing import Optional

PROFILE_DEV = 'dev'
PROFILE_JUDGING = 'judging'
PROFILES = (PROFILE_DEV, PROFILE_JUDGING)

#: The dev-profile call budgets. `.env.example` and the README state the same
#: numbers, and `backend/tests/test_config.py` fails when they drift.
DEV_LIMITS: dict[str, int] = {
    'QLOO_MAX_CALLS_PER_HOUR': 20,
    'QLOO_MAX_CALLS_PER_DAY': 100,
    'LLM_MAX_CALLS_PER_HOUR': 20,
    'LLM_MAX_CALLS_PER_DAY': 50,
    'AI_GATEWAY_ANALYSIS_DAILY_LIMIT': 10,
    # Seeds, places, one recommend per bridge domain (three by default), and
    # three live Qloo calls for the agent loop.
    'RESEARCH_RUN_MAX_WORKFLOWS': 8,
}

#: Limits the environment may lower but never raise in the dev profile. The
#: analysis allowance was designed around this cost ceiling.
DEV_CEILINGS: dict[str, int] = {
    'AI_GATEWAY_ANALYSIS_DAILY_LIMIT': 10,
}

#: How long held evidence answers before it is fetched again. Judging holds it
#: longer, so evidence prewarmed before judging opens is still there when a
#: judge clicks a week later. `CULTUREFORGE_EVIDENCE_TTL_HOURS` overrides both.
EVIDENCE_TTL_HOURS = {PROFILE_DEV: 24, PROFILE_JUDGING: 14 * 24}

#: How long live Qloo calls pause after Qloo rate-limits the key. Held
#: evidence is still served while it lasts.
DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS = 60

_FALSE = {'0', 'false', 'no', 'off'}


def run_profile() -> str:
    """The active profile. Anything unrecognised is treated as dev, the safe one."""
    value = os.getenv('RUN_PROFILE', '').strip().lower()
    return value if value in PROFILES else PROFILE_DEV


def profile_warning() -> Optional[str]:
    """Why the profile in the environment was not used, if it was not."""
    value = os.getenv('RUN_PROFILE', '').strip()
    if value and value.lower() not in PROFILES:
        return f'RUN_PROFILE={value!r} is not a profile; using dev, with budgets enforced.'
    return None


def budgets_enforced() -> bool:
    return run_profile() != PROFILE_JUDGING


def limit(name: str) -> Optional[int]:
    """A call-count limit, or None when it is not enforced.

    In judging every limit is None. In dev the environment sets it; an unset
    or unreadable value falls back to the default, and a value below one
    becomes one, so a typo can never switch a budget off by accident.
    """
    if name not in DEV_LIMITS:
        raise KeyError(name)
    if not budgets_enforced():
        return None
    default = DEV_LIMITS[name]
    raw = os.getenv(name, '').strip()
    try:
        value = int(raw) if raw else default
    except ValueError:
        value = default
    value = max(1, value)
    ceiling = DEV_CEILINGS.get(name)
    return min(value, ceiling) if ceiling else value


#: The entity types the audience bridge may ask Qloo for. Places are the
#: brief's own evidence, so they are not a bridge domain.
BRIDGE_DOMAIN_CHOICES = ('artist', 'movie', 'brand', 'book', 'podcast', 'tv_show', 'videogame', 'album')
DEFAULT_BRIDGE_DOMAINS = ('artist', 'movie', 'brand')


def bridge_domains() -> list[str]:
    """The non-place domains the audience's tags are also sent to.

    `CULTUREFORGE_BRIDGE_DOMAINS` is a comma-separated list; `off` (or an
    empty value) switches the bridge off. Unknown names are ignored rather
    than sent to Qloo, which would reject them.
    """
    raw = os.getenv('CULTUREFORGE_BRIDGE_DOMAINS')
    if raw is None:
        return list(DEFAULT_BRIDGE_DOMAINS)
    if raw.strip().lower() in ('', 'off', 'none', 'false', '0'):
        return []
    chosen: list[str] = []
    for item in raw.split(','):
        name = item.strip().lower()
        if name in BRIDGE_DOMAIN_CHOICES and name not in chosen:
            chosen.append(name)
    return chosen


def qloo_live_enabled() -> bool:
    """False only when the kill switch is thrown: serve held evidence, fetch nothing."""
    return os.getenv('QLOO_LIVE_ENABLED', 'true').strip().lower() not in _FALSE


def evidence_ttl_seconds() -> int:
    raw = os.getenv('CULTUREFORGE_EVIDENCE_TTL_HOURS', '').strip()
    try:
        hours = float(raw) if raw else EVIDENCE_TTL_HOURS[run_profile()]
    except ValueError:
        hours = EVIDENCE_TTL_HOURS[run_profile()]
    return max(1, int(hours * 3600))


def rate_limit_cooldown_seconds() -> int:
    raw = os.getenv('QLOO_RATE_LIMIT_COOLDOWN_SECONDS', '').strip()
    try:
        return max(0, int(raw)) if raw else DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS
    except ValueError:
        return DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS


def describe_limit(value: Optional[int]) -> int | str:
    """A limit as /api/health reports it."""
    return 'unlimited' if value is None else value


def summary() -> dict:
    """The profile as /api/health reports it. It never raises."""
    return {
        'profile': run_profile(),
        'profileWarning': profile_warning(),
        'budgetsEnforced': budgets_enforced(),
        'qlooLiveEnabled': qloo_live_enabled(),
        'evidenceTtlHours': round(evidence_ttl_seconds() / 3600, 2),
        'rateLimitCooldownSeconds': rate_limit_cooldown_seconds(),
        'bridgeDomains': bridge_domains(),
    }
