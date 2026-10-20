"""Counting the upstream calls a request caused.

An API request and an upstream Qloo request are two different costs. A
partner is billed for the first; the hackathon quota is spent on the second.
Metering them apart is the only way to report both honestly.

The provider adds to the counter as it spends, and the API layer reads it
when the response goes back out.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

#: The upstream calls made by the request currently being served.
_upstream_calls: ContextVar[Optional[list[int]]] = ContextVar('upstream_calls', default=None)


def begin() -> list[int]:
    """Start counting the upstream calls for the request now being served."""
    counter: list[int] = [0]
    _upstream_calls.set(counter)
    return counter


def count(request: int = 1) -> None:
    """Record that this request spent `request` upstream calls."""
    counter = _upstream_calls.get()
    if counter is not None:
        counter[0] += request


def total() -> int:
    """How many upstream calls the request now being served has spent."""
    counter = _upstream_calls.get()
    return counter[0] if counter else 0
