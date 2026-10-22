"""Pace requests to the model gateway so its own rate limit is not hit.

A live run found that the Vercel AI Gateway route in use allows **5 requests
per minute** for this team (`X-Ratelimit-Limit-Requests: 5`, `Retry-After`
on the 429). The agent loop makes up to ten requests, so left alone it ran
into the limit and fell back to the rule composer after doing the work.

Every model request, from either transport, waits here first. At most
`LLM_REQUESTS_PER_MINUTE` start in any rolling minute; the rest wait for a
slot. If the gateway answers 429 anyway, `note_limited` records its
`Retry-After` so that everything waits for it, not just the caller that was
refused. This paces requests; it is not a local budget, so it applies in the
judging profile too. Set the limit to 0 to switch it off, or to the real
number if the gateway's limit is raised.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Callable, Optional

from . import config

_lock = threading.Lock()
_starts: deque[float] = deque()
_blocked_until = 0.0

#: The longest a single request will be made to wait for a slot.
MAX_WAIT_SECONDS = 90.0


def wait_for_slot(now: Optional[Callable[[], float]] = None, sleep: Optional[Callable[[float], None]] = None) -> float:
    """Block until a request may start. Returns the seconds spent waiting."""
    now = now or (lambda: time.time())
    sleep = sleep or (lambda seconds: time.sleep(seconds))
    limit = config.llm_requests_per_minute()
    if limit <= 0:
        return 0.0
    waited = 0.0
    while True:
        with _lock:
            t = now()
            while _starts and t - _starts[0] >= 60.0:
                _starts.popleft()
            if t >= _blocked_until and len(_starts) < limit:
                _starts.append(t)
                return waited
            delay = max(_blocked_until - t, (60.0 - (t - _starts[0])) if len(_starts) >= limit else 0.0) + 0.05
        if waited + delay > MAX_WAIT_SECONDS:
            return waited   # give up waiting; the request is made and the gateway decides
        sleep(delay)
        waited += delay


def note_limited(retry_after: Optional[str], now: Optional[Callable[[], float]] = None) -> float:
    """The gateway refused a request. Everything waits out its Retry-After."""
    global _blocked_until
    now = now or (lambda: time.time())
    try:
        seconds = float(retry_after) if retry_after is not None else 15.0
    except (TypeError, ValueError):
        seconds = 15.0
    seconds = min(max(seconds, 1.0), 60.0)
    with _lock:
        _blocked_until = max(_blocked_until, now() + seconds)
    return seconds


def reset() -> None:
    """For tests."""
    global _blocked_until
    with _lock:
        _starts.clear()
        _blocked_until = 0.0
