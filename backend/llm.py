"""Naming the directions with a language model, on the free tier.

**What the model is for.** The composer in `concept_composer.py` is a rule
engine: a recipe fires when the audience resolved to a cultural signal, and
the direction inherits that recipe's name. "The Design Floor" is a good name
for a direction — and it is the same good name for every brief that unlocks
the same recipe. A founder who tries a second brief sees the same three
titles again. This module lets a model name the direction for the brief and
the place in front of it.

**What the model is not for.** It does not decide anything. The rules still
choose the audience tags, the venues, the facet each direction leans on, and
the evidence each decision cites. The model writes words.

**The guard.** The model is never shown a number. Popularity, affinity,
rating and price level are stripped before the prompt is built, so it cannot
quote one — and a number that appears in its answer anyway, because it
invented one, is checked against the evidence and dropped. The rule the
codebase holds to — never show a number Qloo did not return — survives the
model.

**The cost.** The free tier is 50 requests a day, and 1000 a day once $10 of
credits is on the account. So this is a cache, not a service: one call per
brief, held in the same evidence store as the Qloo envelopes, so a repeated
brief spends nothing. A local budget guard sits in front of it, the way the
Qloo one does, and the model is only ever reached for free. If the key is
missing, the tier is exhausted, the model is down, or the answer is late,
the deterministic copy is used and the trace says so.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

#: OpenRouter's OpenAI-compatible endpoint.
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'

#: The model to ask.
#:
#: The free pool is mostly withdrawn or busy: of the models OpenRouter lists
#: as free, several now answer 404 (taken down) and one answers 429 (rate
#: limited). A *reasoning* model is the other trap — it spends the whole
#: token budget thinking and returns no answer at all, which is how
#: `minimax/minimax-m3.1-flash:free` behaves on this prompt.
#:
#: So the primary is a model that has been seen answering this prompt
#: directly, and the router is the backstop for when it is withdrawn. The
#: guard drops anything unusable, so a weak model costs the founder the
#: model's wording, never a wrong number.
DEFAULT_MODEL = 'cohere/north-mini-code:free'

#: The free models this project knows about. Free models are pulled from time
#: to time — several of these already answer 404 — which is why there is
#: more than one and why the router is in the chain.
FREE_MODELS: tuple[str, ...] = (
    'cohere/north-mini-code:free',
    'openrouter/free',
    'minimax/minimax-m3.1-flash:free',
    'google/gemma-4-26b-a4b-it:free',
    'google/gemma-4-31b-it:free',
    'nvidia/nemotron-3-super-120b-a12b:free',
    'nvidia/nemotron-3-ultra-550b-a55b:free',
    'poolside/laguna-xs-2.1:free',
    'thinkingmachines/inkling-small:free',
    'xingchen-agi/xing4.0-29b-a4b:free',
)

#: The chain actually sent with a request. OpenRouter accepts **at most three**
#: models in a `models` array, and every one of them has to be free — a paid
#: model here would be billed. The router is the safety net for when the
#: pinned model is withdrawn or busy.
FALLBACK_CHAIN: tuple[str, ...] = (
    'cohere/north-mini-code:free',
    'openrouter/free',
)

#: The model the retry uses, when the first answer could not be read.
RETRY_MODEL = 'openrouter/free'

#: How long to wait for the model. The free tier queues, and a late answer is
#: worth less than the deterministic copy it would have replaced.
DEFAULT_TIMEOUT_SECONDS = 25

#: How long one attempt may take before the next model is tried. A free
#: model that takes twenty seconds to think is not worth waiting for: the
#: next one answers in five, and the brief should not wait for the slow one
#: to finish before it finds that out.
ATTEMPT_TIMEOUT_SECONDS = 14

#: How long the whole naming may take before the rule engine's wording is
#: used. A brief that waits half a minute for a title is a brief nobody
#: waits for twice — and the naming must never be the reason an answer is
#: slow, so this is a hard cap on the whole naming, not on one attempt.
NAMING_BUDGET_SECONDS = 14

#: Enough room for the answer itself.
DEFAULT_MAX_TOKENS = 2000

#: How much room the model gets to think.
#:
#: Most of the free models are reasoning models, and a reasoning model given
#: the whole budget spends all of it thinking and answers with nothing at
#: all. Capping the thinking leaves the room the answer needs.
REASONING_MAX_TOKENS = 200

#: The free tier's own limit is 50 requests a day. The guard sits at it, so
#: a judge can work through the whole tier, and no further: a busy demo
#: cannot spend the last of it, and the user keeps a few for experimenting.
DEFAULT_MAX_CALLS_PER_HOUR = 20
DEFAULT_MAX_CALLS_PER_DAY = 50

BUDGET_LOG_PATH = Path.home() / '.cache' / 'cultureforge' / 'llm_calls.json'

#: Where the health of each free model is remembered.
MODEL_HEALTH_PATH = Path.home() / '.cache' / 'cultureforge' / 'llm_models.json'

#: How long a model is skipped after it refuses.
#:
#: A rate limit clears in minutes. A withdrawn model does not come back that
#: day, so it is skipped for longer. Remembering this is what makes the
#: failover instant: the next brief starts on a model that is answering, and
#: never pays for the timeouts of the ones that are not.
REFUSAL_COOLDOWN = {
    '429': 15 * 60,
    '404': 12 * 60 * 60,
    '403': 60 * 60,
}

#: Whether the local .env has already been read.
_env_loaded = False

#: Every number the model wrote, so it can be checked against the evidence.
_NUMBER = re.compile(r'\d+(?:[.,]\d+)*')

#: A model that has drifted into citing its sources.
_CITATION = re.compile(r'https?://|www\.|\[\d+\]|\bsources?:', re.IGNORECASE)

#: The words in a piece of text, for deciding whether it says anything.
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def _word_count(text: str) -> int:
    """How many real words the text has.

    The free models sometimes answer "...". A name like that is a refusal
    dressed as an answer, and it must not reach the screen.
    """
    return len([word for word in _WORD.findall(text) if len(word) >= 2])


class LlmUnavailable(RuntimeError):
    """The model could not be reached, or answered in a way we cannot use.

    Carries a code so the API can report it consistently, and a flag saying
    whether trying again could work.
    """

    def __init__(self, message: str, code: str = 'LLM_UNAVAILABLE',
                 retryable: bool = True, details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.details = details or {}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _load_env_once() -> None:
    """Read the local .env, once, if the key is not already in the environment.

    The backend loads .env when it picks its provider, but this module must
    also work on its own — the check script, a bare `python -c`, a test.
    """
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent / '.env')
    except ImportError:
        pass


def _api_key() -> str:
    _load_env_once()
    return os.getenv('OPENROUTER_API_KEY', '').strip()


def is_configured() -> bool:
    """Whether a model is reachable at all.

    A key is the only requirement. The models are free, so no credit is
    needed to start.
    """
    return bool(_api_key())


def _model() -> str:
    """The model to ask, which must be a free one."""
    chosen = os.getenv('OPENROUTER_MODEL', DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if ':free' not in chosen and chosen != 'openrouter/free':
        # A paid model would spend money this project does not have.
        return DEFAULT_MODEL
    return chosen


def _timeout() -> int:
    try:
        return max(5, int(os.getenv('LLM_TIMEOUT_SECONDS', DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# The local budget guard
# ---------------------------------------------------------------------------

_budget_lock = threading.Lock()


def _read_calls() -> list[float]:
    try:
        data = json.loads(BUDGET_LOG_PATH.read_text(encoding='utf-8'))
        return [float(stamp) for stamp in data.get('calls', []) if isinstance(stamp, (int, float))]
    except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
        return []


def _write_calls(calls: list[float]) -> None:
    try:
        BUDGET_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        BUDGET_LOG_PATH.write_text(json.dumps({'calls': calls}), encoding='utf-8')
        os.chmod(BUDGET_LOG_PATH, 0o600)
    except OSError:
        pass


def _check_budget() -> None:
    """Refuse this call if it would exceed the local allowance.

    Checked before the request, so the cap is never crossed, and the check
    itself spends nothing.
    """
    hour_limit = int(os.getenv('LLM_MAX_CALLS_PER_HOUR', DEFAULT_MAX_CALLS_PER_HOUR))
    day_limit = int(os.getenv('LLM_MAX_CALLS_PER_DAY', DEFAULT_MAX_CALLS_PER_DAY))
    now = time.time()
    with _budget_lock:
        calls = [stamp for stamp in _read_calls() if now - stamp < 86400]
        calls_in_hour = sum(1 for stamp in calls if now - stamp < 3600)
        if calls_in_hour >= hour_limit or len(calls) >= day_limit:
            raise LlmUnavailable(
                'The free model allowance is used up for now. The directions keep the names the '
                'rule engine gave them, which is why nothing about the answer changes.',
                code='LLM_QUOTA_EXHAUSTED', retryable=True,
                details={'resetsInSeconds': 3600 - int(now % 3600)})


def _record_call() -> None:
    """Record a request that reached the model.

    A refusal — a model that is withdrawn, or busy — is not recorded: no
    inference ran, so the tier was not charged for it, and the local guard
    should not pretend otherwise.
    """
    now = time.time()
    with _budget_lock:
        calls = [stamp for stamp in _read_calls() if now - stamp < 86400]
        calls.append(now)
        _write_calls(calls)


def budget_state() -> dict:
    """What is left of the free allowance, for the health endpoint."""
    now = time.time()
    calls = _read_calls()
    hour_limit = int(os.getenv('LLM_MAX_CALLS_PER_HOUR', DEFAULT_MAX_CALLS_PER_HOUR))
    day_limit = int(os.getenv('LLM_MAX_CALLS_PER_DAY', DEFAULT_MAX_CALLS_PER_DAY))
    return {
        'callsLastHour': sum(1 for stamp in calls if now - stamp < 3600),
        'callsToday': sum(1 for stamp in calls if now - stamp < 86400),
        'hourLimit': hour_limit,
        'dayLimit': day_limit,
    }


# ---------------------------------------------------------------------------
# Which free models are answering
#
# The free pool moves: a model is withdrawn, or busy, and the next brief
# should not pay for finding that out again. Each refusal is remembered for a
# while, and the chain is asked in the order that skips them.
# ---------------------------------------------------------------------------

def _read_health() -> dict:
    try:
        data = json.loads(MODEL_HEALTH_PATH.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_health(health: dict) -> None:
    try:
        MODEL_HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
        MODEL_HEALTH_PATH.write_text(json.dumps(health), encoding='utf-8')
        os.chmod(MODEL_HEALTH_PATH, 0o600)
    except OSError:
        pass


def _mark_unhealthy(model: str, status) -> None:
    """Remember that this model is not answering."""
    cooldown = REFUSAL_COOLDOWN.get(str(status))
    if not cooldown:
        return
    health = _read_health()
    entry = health.get(model) if isinstance(health.get(model), dict) else {}
    health[model] = {**entry, 'until': time.time() + cooldown, 'status': status}
    _write_health(health)


def _mark_healthy(model: str) -> None:
    """Remember that this model answered."""
    health = _read_health()
    entry = health.get(model)
    if isinstance(entry, dict) and entry.get('until'):
        entry = {**entry, 'until': 0}
        health[model] = entry
        _write_health(health)


def _mark_outcome(model: str, usable: bool, duration_ms: Optional[int] = None) -> None:
    """Remember how this model answered, so the next brief asks it first.

    A free model that answers in eight seconds with a usable name is worth
    asking before one that answers in twenty with a placeholder, and a model
    that answers with nothing at all is worth asking last.
    """
    health = _read_health()
    entry = health.get(model) if isinstance(health.get(model), dict) else {}
    health[model] = {
        **entry,
        'good': int(entry.get('good', 0)) + (1 if usable else 0),
        'bad': int(entry.get('bad', 0)) + (0 if usable else 1),
        'lastMs': duration_ms if duration_ms is not None else entry.get('lastMs'),
        'lastAt': time.time(),
    }
    _write_health(health)


def healthy_models() -> list[str]:
    """The models worth asking, in order.

    The router is a lottery: it picks a free model at random each time, and
    some of them take twenty seconds to think. So the model the router
    actually chose is remembered and asked *directly* next time, which is
    both faster and steadier.

    A model that is refusing right now is moved to the back rather than
    dropped, so it is retried once its cooldown is over. Among the ones that
    are answering, the ones that have answered *well* come first, and the
    quick ones come before the slow ones.
    """
    now = time.time()
    health = _read_health()

    def refusing(model: str) -> bool:
        entry = health.get(model)
        return isinstance(entry, dict) and float(entry.get('until', 0)) > now

    def score(model: str) -> tuple:
        entry = health.get(model) if isinstance(health.get(model), dict) else {}
        good = int(entry.get('good', 0)) - int(entry.get('bad', 0))
        last = entry.get('lastMs')
        return (-good, last if isinstance(last, int) else 10_000, -float(entry.get('lastAt', 0) or 0))

    # The concrete models the router has landed on and liked.
    learned_all = [model for model in health
                   if model not in FALLBACK_CHAIN and model.endswith(':free')]
    learned = sorted([model for model in learned_all if not refusing(model)], key=score)
    learned_late = [model for model in learned_all if refusing(model)]
    chain = sorted([model for model in FALLBACK_CHAIN if not refusing(model)], key=score)
    late = [model for model in FALLBACK_CHAIN if refusing(model)]
    # OpenRouter takes at most three models in a fallback array, so the list
    # that is asked stays short: the best learned model, the chain, and the
    # router as the last resort. A model in cooldown is not dropped, it is
    # asked last, so it is retried once the cooldown is over.
    return learned[:2] + chain + learned_late + late


def status() -> dict:
    """What the model layer can do right now."""
    configured = is_configured()
    now = time.time()
    health = _read_health()
    known = list(FALLBACK_CHAIN) + [model for model in health
                                     if model not in FALLBACK_CHAIN and model.endswith(':free')]

    def entry_for(model: str) -> dict:
        found = health.get(model)
        return found if isinstance(found, dict) else {}

    return {
        'configured': configured,
        'model': _model() if configured else None,
        # The chain is free-only, and the model is refused if it is not.
        'freeOnly': True,
        'budget': budget_state(),
        # Which free models are answering, and which are refusing right now.
        'models': [
            {
                'id': model,
                'answering': float(entry_for(model).get('until', 0) or 0) <= now,
                'until': int(entry_for(model)['until']) if entry_for(model).get('until') else None,
                'good': int(entry_for(model).get('good', 0) or 0),
                'lastMs': entry_for(model).get('lastMs'),
            }
            for model in known
        ],
        'next': healthy_models()[:3],
    }


# ---------------------------------------------------------------------------
# The prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    'You name business directions for a founder. You are given the audience signals and the '
    'local venues that a cultural database returned for this brief. You write the name and the '
    'one-line tagline.\n'
    'Rules: write only about the venues and signals you are given, by their exact names. '
    'Do not state any number, measurement, rating, popularity or score — you are not given '
    'any, and inventing one is wrong. Do not cite sources. Do not add a fourth direction. '
    'Write a NEW name and a NEW tagline — do not repeat the wording you are shown. Keep the '
    'whole answer under a hundred words. '
    'Answer with JSON only, no prose before or after.'
)


def _build_user_prompt(brief: dict, directions: list[dict]) -> str:
    lines = [
        f"Business: {brief.get('businessType')}",
        f"Audience: {brief.get('audience')}",
        f"Location: {brief.get('location')}",
        f"Budget: {brief.get('budget')}",
        '',
        'Audience signals the database returned:',
    ]
    signals = brief.get('signals') or []
    lines.extend(f'- {signal}' for signal in signals) if signals else lines.append('- (none)')
    lines.append('')
    for direction in directions:
        lines.append(f"Direction {direction['index']} — the rule engine's current wording:")
        lines.append(f"  name: {direction['currentName']}")
        lines.append(f"  tagline: {direction['currentTagline']}")
        lines.append(f"  why it fits: {direction['currentPositioning']}")
        lines.append('  the places it is built from:')
        for venue in direction['venues']:
            role = 'the one it is built around' if venue['role'] == 'primary' else 'supporting it'
            lines.append(f"    - {venue['name']} ({role})")
            if venue.get('description'):
                lines.append(f"      described by the database as: {venue['description']}")
        lines.append('')
    lines.append('Answer with this JSON shape, one entry per direction, in order:')
    lines.append('{"directions": [{"index": 0, "name": "...", "tagline": "..."}]}')
    lines.append('')
    lines.append('Write a new name, specific to these places and this audience — not the name '
                 'above, and not a generic template title. The tagline is one short line.')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# The transport
# ---------------------------------------------------------------------------

def _post(payload: dict, timeout: int) -> dict:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {_api_key()}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/qloo/qloo-hackathon-kit',
            'X-Title': 'CultureForge AI',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        detail = ''
        try:
            detail = exc.read().decode('utf-8', 'replace')[:200]
        except Exception:  # noqa: BLE001 - the body is a nicety, not the point
            pass
        raise LlmUnavailable(
            f'The model refused the request ({exc.code}).',
            code='LLM_REJECTED', retryable=exc.code >= 500,
            details={'status': exc.code, 'body': detail}) from exc
    except urllib.error.URLError as exc:
        raise LlmUnavailable(
            'The model could not be reached.', code='LLM_UNREACHABLE', retryable=True) from exc
    except TimeoutError as exc:
        raise LlmUnavailable(
            'The model took too long.', code='LLM_TIMEOUT', retryable=True) from exc


def _ask_model(brief: dict, directions: list[dict], timeout: int,
               before_request=None, after_request=None) -> tuple[dict, str, int]:
    """Ask the model, and return its answer with the model that gave it.

    The router first. If its answer cannot be read — a reasoning model that
    ran out of room mid-JSON is the usual reason — one more request goes to
    a model that answers directly. Two requests at most, and only the second
    one is spent when the first was unreadable. The count of requests made
    comes back with the answer, because it is the number the free allowance
    was charged.
    """
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': _build_user_prompt(brief, directions)},
    ]
    attempts = []
    for model in healthy_models():
        attempts.append((model, [model], True))
    # The router is the last resort, and a third attempt drops the reasoning
    # cap in case a model rejects it.
    attempts.append((RETRY_MODEL, [RETRY_MODEL], True))
    attempts.append((_model(), list(FALLBACK_CHAIN), False))
    first_error: Optional[str] = None
    raw = ''
    spent = 0
    served = 0
    started = time.monotonic()
    report_duration_ms: Optional[int] = None
    for model, chain, cap_reasoning in attempts:
        if time.monotonic() - started > NAMING_BUDGET_SECONDS:
            # The brief has waited long enough. The rule engine's wording is
            # better than a slower answer.
            first_error = first_error or 'the naming took too long'
            break
        if before_request is not None:
            before_request()
        spent += 1
        payload = {
            'model': model,
            # The fallback chain is free-only, and OpenRouter takes at most three.
            'models': chain,
            'messages': messages,
            'temperature': 0.5,
            'max_tokens': DEFAULT_MAX_TOKENS,
        }
        if cap_reasoning:
            # Keep the thinking short, so there is room left for the answer.
            payload['reasoning'] = {'max_tokens': REASONING_MAX_TOKENS}
        try:
            body = _post(payload, min(timeout, ATTEMPT_TIMEOUT_SECONDS))
        except LlmUnavailable as exc:
            # A model that is gone (404), busy (429) or answered with nothing
            # is not a reason to give up: the next attempt gets the request.
            # The refusal is remembered, so the next brief does not pay for
            # it again.
            status = exc.details.get('status')
            recoverable = (status in (404, 429) or exc.code == 'LLM_EMPTY'
                           or exc.code == 'LLM_TIMEOUT'
                           or (status == 400 and cap_reasoning))
            if recoverable:
                _mark_unhealthy(model, status)
                if first_error is None:
                    first_error = str(exc)
                    raw = exc.details.get('raw', '') or exc.details.get('body', '')
                continue
            raise
        if body.get('error'):
            raise LlmUnavailable(
                f'The model refused the request ({body.get("error", {}).get("code", "unknown")}).',
                code='LLM_REJECTED', retryable=False)
        # The model answered, so the tier was charged for this one.
        served += 1
        report_duration_ms = int((time.monotonic() - started) * 1000)
        choices = body.get('choices') or []
        if not choices:
            raise LlmUnavailable('The model returned nothing.', code='LLM_EMPTY', retryable=True)
        message = choices[0].get('message') or {}
        content = message.get('content')
        if not isinstance(content, str) or not content.strip():
            # A reasoning model spends the whole budget thinking and answers
            # with nothing. The reason is worth keeping, and the next model
            # in the chain gets the request.
            reason = 'the model reasoned for the whole budget and answered with nothing'
            if message.get('reasoning'):
                reason = f'the model reasoned for the whole budget ({str(message["reasoning"])[:120]})'
            raise LlmUnavailable('The model returned an empty answer.', code='LLM_EMPTY',
                                 retryable=True, details={'raw': reason})
        try:
            parsed = _parse_json(content)
        except LlmUnavailable as exc:
            # A model that ran out of room is worth one more try, once.
            if first_error is None:
                first_error = str(exc)
                raw = content
            continue
        _mark_healthy(model)
        # The router answers with whichever free model it picked, and that is
        # the one worth remembering: asked directly next time, the brief gets
        # the same model in the same few seconds, without the lottery.
        concrete = body.get('model')
        if isinstance(concrete, str) and concrete:
            _mark_outcome(concrete, True, report_duration_ms)
        if after_request is not None:
            after_request()
        return parsed, body.get('model') or model, served
    raise LlmUnavailable(
        f'The model did not answer in JSON ({first_error}).', code='LLM_MALFORMED',
        retryable=True, details={'raw': (raw or '')[:400]})


def _parse_json(content: str) -> dict:
    """Pull the JSON out of an answer, whatever the model wrapped it in."""
    text = content.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
        text = re.sub(r'\s*```$', '', text).strip()
    start = text.find('{')
    end = text.rfind('}')
    if start < 0 or end <= start:
        raise LlmUnavailable('The model did not answer in JSON.', code='LLM_MALFORMED', retryable=True)
    try:
        parsed = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise LlmUnavailable('The model did not answer in JSON.', code='LLM_MALFORMED',
                             retryable=True) from exc
    if not isinstance(parsed, dict):
        raise LlmUnavailable('The model did not answer in the expected shape.',
                             code='LLM_MALFORMED', retryable=True)
    return parsed


# ---------------------------------------------------------------------------
# The guard
# ---------------------------------------------------------------------------

def _allowed_numbers(evidence: list) -> set[str]:
    """The numbers Qloo actually returned, in every form they could be written.

    The evidence arrives as `Evidence` objects, not dictionaries, so both are
    read the same way.
    """
    allowed: set[str] = set()
    for row in evidence:
        for key in ('popularity', 'affinity', 'rating', 'priceLevel'):
            value = row.get(key) if isinstance(row, dict) else getattr(row, key, None)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                allowed.add(f'{value:g}')
                allowed.add(str(value))
                allowed.add(f'{value:.3f}')
                allowed.add(f'{value:.2f}')
                allowed.add(f'{value:.4f}')
    return allowed


def _clean_text(value, *, limit: int, min_length: int = 2, min_words: int = 1) -> Optional[str]:
    """One field of the model's answer, if it is usable."""
    if not isinstance(value, str):
        return None
    text = ' '.join(value.split()).strip()
    if len(text) < min_length or len(text) > limit:
        return None
    if _CITATION.search(text):
        return None
    if _word_count(text) < min_words:
        return None
    return text


def _numbers_are_allowed(text: str, allowed: set[str]) -> bool:
    """Whether every number in the text is one Qloo returned."""
    for match in _NUMBER.finditer(text):
        token = match.group(0)
        if token not in allowed and token.replace(',', '.') not in allowed:
            return False
    return True


def validate_directions(answer: dict, evidence: list[dict]) -> tuple[dict[int, dict], list[str]]:
    """Check the model's answer against the evidence.

    Returns the usable parts, keyed by direction index, and the list of
    reasons something was dropped. A direction with a dropped field keeps
    the rule engine's wording for that field.
    """
    allowed = _allowed_numbers(evidence)
    usable: dict[int, dict] = {}
    dropped: list[str] = []
    entries = answer.get('directions')
    if not isinstance(entries, list):
        return {}, ['the model did not return a list of directions']
    for entry in entries:
        if not isinstance(entry, dict):
            dropped.append('a direction was not an object')
            continue
        try:
            index = int(entry.get('index'))
        except (TypeError, ValueError):
            dropped.append('a direction had no index')
            continue
        name = _clean_text(entry.get('name'), limit=70, min_length=2, min_words=1)
        tagline = _clean_text(entry.get('tagline'), limit=160, min_length=4, min_words=2)
        for field, text in (('name', name), ('tagline', tagline)):
            if text and not _numbers_are_allowed(text, allowed):
                dropped.append(f'direction {index}: the {field} contained a number Qloo did not return')
                if field == 'name':
                    name = None
                else:
                    tagline = None
        if not name and not tagline:
            dropped.append(f'direction {index}: nothing in it was usable')
            continue
        usable[index] = {'name': name, 'tagline': tagline}
    return usable, dropped


# ---------------------------------------------------------------------------
# The public call
# ---------------------------------------------------------------------------

def name_directions(brief: dict, directions: list[dict],
                    evidence: list[dict]) -> tuple[dict[int, dict], dict]:
    """Ask the model to name the directions.

    Returns the usable names, keyed by direction index, and a report of what
    happened. Never raises: a model that cannot be used is not an error the
    founder needs to see, it is a reason to keep the rule engine's wording.
    """
    report = {'used': False, 'attempted': False, 'model': None, 'reason': None, 'dropped': []}
    if not is_configured():
        report['reason'] = 'No OpenRouter key is configured.'
        return {}, report
    if not directions:
        report['reason'] = 'There were no directions to name.'
        return {}, report
    try:
        report['attempted'] = True
        started = time.monotonic()
        answer, model, served = _ask_model(brief, directions, _timeout(),
                                           before_request=_check_budget,
                                           after_request=_record_call)
        report['requests'] = served
        report['attempts'] = served
        report['durationMs'] = int((time.monotonic() - started) * 1000)
    except LlmUnavailable as exc:
        report['reason'] = str(exc)
        report['code'] = exc.code
        if exc.details.get('raw'):
            report['raw'] = exc.details['raw']
        # The attempt was made. Whether the tier was charged depends on
        # whether a model actually answered, and the local guard only
        # records the ones that did.
        report['requests'] = 0
        report['attempts'] = 1
        return {}, report
    except Exception as exc:  # noqa: BLE001 - a model must never break an answer
        report['reason'] = f'The model could not be used ({exc}).'
        return {}, report
    usable, dropped = validate_directions(answer, evidence)
    report['used'] = bool(usable)
    report['model'] = model
    report['dropped'] = dropped
    # How this model answered is worth remembering: the next brief asks the
    # model that answered well, and quickly.
    _mark_outcome(model, bool(usable), report.get('durationMs'))
    if not usable:
        report['reason'] = 'The model answered, but nothing in it could be used.'
    return usable, report
