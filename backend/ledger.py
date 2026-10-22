"""The call ledgers behind every local budget, in one SQLite file.

Three ledgers count what this server has asked of upstream services:

    qloo        every Qloo workflow, reserved before the request is sent
    llm_naming  every model naming/selection request that got an answer
    analysis    every evidence-analysis request, reserved before it is sent

They used to be JSON files rewritten on each call, guarded by an in-process
lock. Two workers could each read the file, append a call, and write it back,
and one of the two calls would disappear. Here a reservation is one
`BEGIN IMMEDIATE` transaction: SQLite holds the write lock across the count
and the insert, so concurrent workers and processes queue instead of losing
calls, and a limit cannot be passed by two callers at once.

The ledger counts in both run profiles. Only the limits change with the
profile (see config.py), so /api/health can say what was spent either way.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Optional

QLOO = 'qloo'
LLM_NAMING = 'llm_naming'
ANALYSIS = 'analysis'

DB_PATH = Path(os.getenv('CULTUREFORGE_CACHE_DIR', Path.home() / '.cache' / 'cultureforge')) / 'budget.db'

#: The JSON files these ledgers replaced, imported once and then renamed.
LEGACY_FILES = {
    QLOO: 'qloo_calls.json',
    LLM_NAMING: 'gateway_naming_calls.json',
    ANALYSIS: 'gateway_analysis_calls.json',
}

DAY_SECONDS = 86400
HOUR_SECONDS = 3600


class LedgerError(RuntimeError):
    """The ledger could not be read or written."""


class BudgetExceeded(RuntimeError):
    """A reservation would pass a limit. Nothing was recorded."""

    def __init__(self, resets_in_seconds: int):
        super().__init__('budget exceeded')
        self.resets_in_seconds = resets_in_seconds


#: Ledger files this process has already prepared (WAL mode and schema).
_prepared: set[str] = set()


def _prepare(connection: sqlite3.Connection, path: Path) -> None:
    """Switch a ledger file to WAL and create its table, once per process.

    SQLite can refuse the switch to WAL with "database is locked" without
    waiting, when several processes open a fresh file together, so the
    one-time setup retries briefly instead of failing a request.
    """
    for attempt in range(50):
        try:
            if connection.execute('PRAGMA journal_mode').fetchone()[0] != 'wal':
                connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('CREATE TABLE IF NOT EXISTS calls (ledger TEXT NOT NULL, stamp REAL NOT NULL)')
            connection.execute('CREATE INDEX IF NOT EXISTS calls_by_ledger ON calls (ledger, stamp)')
            _prepared.add(str(path))
            return
        except sqlite3.OperationalError as exc:
            if 'locked' not in str(exc) or attempt == 49:
                raise
            time.sleep(0.02)


def _connect() -> sqlite3.Connection:
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists()
    # Autocommit mode: every transaction below is opened explicitly. The
    # timeout makes a writer wait for another instead of failing.
    connection = sqlite3.connect(path, timeout=15, isolation_level=None)
    try:
        if fresh:
            os.chmod(path, 0o600)
        if str(path) not in _prepared:
            _prepare(connection, path)
        _migrate(connection, path.parent)
    except BaseException:
        connection.close()
        raise
    return connection


def _migrate(connection: sqlite3.Connection, directory: Path) -> None:
    """Import a legacy JSON ledger once, under the write lock, then rename it."""
    for ledger, name in LEGACY_FILES.items():
        legacy = directory / name
        if not legacy.is_file():
            continue
        connection.execute('BEGIN IMMEDIATE')
        try:
            # Another process may have imported it while this one waited.
            if legacy.is_file():
                try:
                    data = json.loads(legacy.read_text(encoding='utf-8'))
                    stamps = [float(stamp) for stamp in data.get('calls', [])
                              if isinstance(stamp, (int, float))]
                except (OSError, ValueError, AttributeError, TypeError):
                    stamps = []
                cutoff = time.time() - DAY_SECONDS
                connection.executemany('INSERT INTO calls (ledger, stamp) VALUES (?, ?)',
                                       [(ledger, stamp) for stamp in stamps if stamp > cutoff])
                legacy.replace(legacy.with_name(legacy.name + '.migrated'))
            connection.execute('COMMIT')
        except BaseException:
            connection.execute('ROLLBACK')
            raise


def _counts(connection: sqlite3.Connection, ledger: str, now: float) -> tuple[int, int]:
    row = connection.execute(
        'SELECT COALESCE(SUM(stamp > ?), 0), COUNT(*) FROM calls WHERE ledger = ? AND stamp > ?',
        (now - HOUR_SECONDS, ledger, now - DAY_SECONDS)).fetchone()
    return int(row[0]), int(row[1])


def _over(counts: tuple[int, int], hour_limit: Optional[int], day_limit: Optional[int]) -> bool:
    in_hour, in_day = counts
    return ((hour_limit is not None and in_hour >= hour_limit)
            or (day_limit is not None and in_day >= day_limit))


def reserve(ledger: str, hour_limit: Optional[int] = None, day_limit: Optional[int] = None) -> None:
    """Record one call, unless it would pass a limit (None means no limit).

    The count and the insert are one transaction, so this is safe across
    threads, workers and processes. Raises BudgetExceeded without recording
    anything, or LedgerError when the ledger cannot be used.
    """
    now = time.time()
    try:
        with closing(_connect()) as connection:
            connection.execute('BEGIN IMMEDIATE')
            try:
                connection.execute('DELETE FROM calls WHERE ledger = ? AND stamp <= ?',
                                   (ledger, now - DAY_SECONDS))
                if _over(_counts(connection, ledger, now), hour_limit, day_limit):
                    connection.execute('ROLLBACK')
                    raise BudgetExceeded(HOUR_SECONDS - int(now % HOUR_SECONDS))
                connection.execute('INSERT INTO calls (ledger, stamp) VALUES (?, ?)', (ledger, now))
                connection.execute('COMMIT')
            except sqlite3.Error:
                connection.execute('ROLLBACK')
                raise
    except sqlite3.Error as exc:
        raise LedgerError(str(exc)) from exc


def check(ledger: str, hour_limit: Optional[int] = None, day_limit: Optional[int] = None) -> None:
    """Raise BudgetExceeded if the ledger is already at a limit. Records nothing."""
    if hour_limit is None and day_limit is None:
        return
    now = time.time()
    if _over(counts(ledger, now), hour_limit, day_limit):
        raise BudgetExceeded(HOUR_SECONDS - int(now % HOUR_SECONDS))


def record(ledger: str) -> None:
    """Record one call with no limit check (it has already been made)."""
    reserve(ledger)


def counts(ledger: str, now: Optional[float] = None) -> tuple[int, int]:
    """(calls in the last hour, calls in the last day)."""
    try:
        with closing(_connect()) as connection:
            return _counts(connection, ledger, now or time.time())
    except sqlite3.Error as exc:
        raise LedgerError(str(exc)) from exc
