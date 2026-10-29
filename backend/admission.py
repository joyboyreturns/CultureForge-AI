"""Fair use for a public demo: who may start research that needs new Qloo evidence.

Judging lifts the call-count budgets on purpose, so nothing else stops one visitor, a crawler or
a stuck script from starting many cold briefs and spending the upstream allowance the other judges
need. Three rules, none of which touch held evidence:

  * an identical brief that is already running is joined, not started a second time;
  * only a few cold briefs run at once (more would queue behind Qloo's spacing and the model
    route's rate, and look hung);
  * one visitor may start a limited number of cold briefs an hour.

A refusal says what happened, when to come back, and that the prepared examples still open
instantly. Nothing here reads or stores anything but an address and a time.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from . import config

WINDOW_SECONDS = 3600


@dataclass
class Refusal(Exception):
    code: str
    message: str
    retry_after_seconds: int

    def __str__(self) -> str:  # pragma: no cover - exercised through the message
        return self.message


class Admission:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: set[str] = set()
        self._starts: dict[str, list[float]] = {}
        self._counter = 0

    def reset(self) -> None:
        with self._lock:
            self._active.clear()
            self._starts.clear()

    def enter(self, client: str, *, held: bool, now: Optional[float] = None) -> Optional[str]:
        """Admit one piece of work. Returns a ticket to `leave` with, or None for held work.

        Held evidence costs no upstream request and is never limited. Raises `Refusal` otherwise.
        """
        if held:
            return None
        now = time.time() if now is None else now
        limit_active, limit_client = config.max_cold_runs(), config.cold_runs_per_client_hour()
        with self._lock:
            if limit_active and len(self._active) >= limit_active:
                raise Refusal(
                    'DEMO_BUSY',
                    f'{len(self._active)} new ideas are being researched right now, which is as many as this '
                    'demo runs at once. Wait about a minute and try again, or open a prepared example: '
                    'those are held and open instantly.', 60)
            recent = [t for t in self._starts.get(client, []) if now - t < WINDOW_SECONDS]
            if limit_client and len(recent) >= limit_client:
                wait = max(1, int(WINDOW_SECONDS - (now - min(recent))))
                raise Refusal(
                    'CLIENT_RATE_LIMITED',
                    f'This connection has started {len(recent)} new ideas in the last hour, which is the most this demo '
                    f'allows each visitor, so Qloo\'s allowance stays available to other people. Try again in about '
                    f'{max(1, wait // 60)} minute(s). Prepared examples and ideas already researched open instantly.', wait)
            recent.append(now)
            self._starts[client] = recent
            self._counter += 1
            ticket = f'cold-{self._counter}'
            self._active.add(ticket)
            return ticket

    def leave(self, ticket: Optional[str]) -> None:
        if ticket is None:
            return
        with self._lock:
            self._active.discard(ticket)

    def snapshot(self) -> dict:
        with self._lock:
            return {'coldRunsActive': len(self._active),
                    'maxColdRuns': config.max_cold_runs(),
                    'coldRunsPerClientHour': config.cold_runs_per_client_hour()}


admission = Admission()


class SlidingWindowLimiter:
    """At most `limit` events per key in a rolling window; for routes that take no key."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._lock = threading.Lock()
        self._events: dict[str, list[float]] = {}

    def allow(self, key: str, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else now
        with self._lock:
            recent = [t for t in self._events.get(key, []) if now - t < self._window]
            if len(recent) >= self._limit:
                self._events[key] = recent
                return False
            recent.append(now)
            self._events[key] = recent
            if len(self._events) > 10_000:  # forget addresses with nothing recent, so the map stays bounded
                self._events = {k: v for k, v in self._events.items() if v and now - v[-1] < self._window}
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


def _is_local_peer(host: str) -> bool:
    """A loopback or private-network peer: a proxy on this machine or network, which no internet visitor can be."""
    import ipaddress
    try:
        address = ipaddress.ip_address(host.split('%')[0])
    except ValueError:
        return host in ('localhost', 'testclient')
    return address.is_loopback or address.is_private


def client_id(request) -> str:
    """The visitor's address.

    Behind a reverse proxy or tunnel on the same machine every request arrives from 127.0.0.1 (or a
    Docker bridge address), which would make all visitors one. When the connecting peer is local, or
    CULTUREFORGE_TRUST_PROXY=true, the last X-Forwarded-For value (the one the nearest proxy added) is
    the visitor. CULTUREFORGE_TRUST_PROXY=false never believes the header.
    """
    peer = request.client.host if request.client else 'unknown'
    trust = config.trust_proxy()
    if trust is None:
        trust = _is_local_peer(peer)
    if trust:
        # Cloudflare's own header names the visitor exactly; otherwise the last forwarded address.
        connecting = request.headers.get('cf-connecting-ip', '').strip()
        if connecting:
            return connecting
        forwarded = request.headers.get('x-forwarded-for', '')
        last = forwarded.split(',')[-1].strip() if forwarded else ''
        if last:
            return last
    return peer


#: Headers that a reverse proxy or tunnel adds. A request carrying one did not come from this machine.
PROXY_HEADERS = ('x-forwarded-for', 'x-real-ip', 'cf-connecting-ip', 'forwarded', 'x-forwarded-host')


def is_proxied(request) -> bool:
    return any(request.headers.get(name) for name in PROXY_HEADERS)
