"""The call ledgers: limits hold, and concurrent workers lose no calls."""
from __future__ import annotations

import json
import multiprocessing
import sqlite3
import time
from pathlib import Path

import pytest

from backend import ledger


def _rows(ledger_name: str) -> int:
    with sqlite3.connect(ledger.DB_PATH) as connection:
        return connection.execute('SELECT COUNT(*) FROM calls WHERE ledger = ?', (ledger_name,)).fetchone()[0]


def test_a_reservation_past_the_hour_limit_is_refused_and_not_recorded():
    for _ in range(3):
        ledger.reserve(ledger.QLOO, hour_limit=3, day_limit=10)
    with pytest.raises(ledger.BudgetExceeded) as caught:
        ledger.reserve(ledger.QLOO, hour_limit=3, day_limit=10)
    assert 0 < caught.value.resets_in_seconds <= 3600
    assert ledger.counts(ledger.QLOO) == (3, 3)


def test_the_day_limit_counts_calls_older_than_an_hour(monkeypatch):
    now = time.time()
    monkeypatch.setattr(ledger.time, 'time', lambda: now - 2 * 3600)
    ledger.reserve(ledger.QLOO)
    ledger.reserve(ledger.QLOO)
    monkeypatch.setattr(ledger.time, 'time', lambda: now)
    assert ledger.counts(ledger.QLOO) == (0, 2)
    with pytest.raises(ledger.BudgetExceeded):
        ledger.reserve(ledger.QLOO, hour_limit=5, day_limit=2)


def test_calls_older_than_a_day_stop_counting_and_are_pruned(monkeypatch):
    now = time.time()
    monkeypatch.setattr(ledger.time, 'time', lambda: now - 25 * 3600)
    ledger.reserve(ledger.QLOO)
    monkeypatch.setattr(ledger.time, 'time', lambda: now)
    assert ledger.counts(ledger.QLOO) == (0, 0)
    ledger.reserve(ledger.QLOO, day_limit=1)
    assert _rows(ledger.QLOO) == 1


def test_the_ledgers_are_counted_separately():
    ledger.reserve(ledger.QLOO)
    ledger.record(ledger.LLM_NAMING)
    ledger.record(ledger.LLM_NAMING)
    assert ledger.counts(ledger.QLOO)[1] == 1
    assert ledger.counts(ledger.LLM_NAMING)[1] == 2
    assert ledger.counts(ledger.ANALYSIS)[1] == 0


def test_check_records_nothing():
    ledger.check(ledger.LLM_NAMING, hour_limit=1, day_limit=1)
    assert ledger.counts(ledger.LLM_NAMING) == (0, 0)
    ledger.record(ledger.LLM_NAMING)
    with pytest.raises(ledger.BudgetExceeded):
        ledger.check(ledger.LLM_NAMING, hour_limit=1, day_limit=1)


def test_a_legacy_json_ledger_is_imported_once_and_renamed():
    now = time.time()
    legacy = Path(ledger.DB_PATH).parent / 'qloo_calls.json'
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps({'calls': [now - 60, now - 7200, now - 2 * 86400, 'junk']}), encoding='utf-8')
    assert ledger.counts(ledger.QLOO) == (1, 2)
    assert not legacy.exists()
    assert legacy.with_name('qloo_calls.json.migrated').exists()
    # A second open does not import it again.
    assert ledger.counts(ledger.QLOO) == (1, 2)


def _worker(db_path: str, attempts: int, day_limit, results) -> None:
    ledger.DB_PATH = Path(db_path)
    granted = 0
    for _ in range(attempts):
        try:
            ledger.reserve(ledger.QLOO, None, day_limit)
            granted += 1
        except ledger.BudgetExceeded:
            pass
    results.put(granted)


def _race(db_path: Path, processes: int, attempts: int, day_limit) -> int:
    context = multiprocessing.get_context('spawn')
    results = context.Queue()
    workers = [context.Process(target=_worker, args=(str(db_path), attempts, day_limit, results))
               for _ in range(processes)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(60)
        assert worker.exitcode == 0
    return sum(results.get(timeout=5) for _ in workers)


def test_concurrent_processes_lose_no_calls():
    """The JSON ledger lost calls when two workers rewrote it at once."""
    assert _race(ledger.DB_PATH, processes=6, attempts=25, day_limit=None) == 150
    assert _rows(ledger.QLOO) == 150


def test_concurrent_processes_cannot_pass_a_limit_together():
    assert _race(ledger.DB_PATH, processes=6, attempts=10, day_limit=25) == 25
    assert _rows(ledger.QLOO) == 25
