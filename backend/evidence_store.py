"""Durable evidence store.

Three jobs:

1. **A cache that survives a restart.** The live Qloo path takes about 25
   seconds. A demo must never be at the mercy of that, and a restarted
   backend must not lose everything it already paid for. Entries live on disk
   under ``~/.cache/cultureforge`` and are keyed by the canonical workflow
   input, so the same brief never spends a call twice.
2. **Single-flight de-duplication.** Two requests for the same evidence
   arriving at once must produce one upstream call, not two.
3. **Snapshots.** An exploration can be frozen and addressed by an opaque id,
   so a judge can open exactly what was shown without re-running anything.

The store also counts *transport* requests, not just workflow invocations: one
workflow can make more than one upstream HTTP request, and the quota guard has
to reflect what was actually spent.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

ADAPTER_VERSION = '2'  # bump when the shape of a stored envelope changes

STORE_DIR = Path(os.getenv('CULTUREFORGE_CACHE_DIR', Path.home() / '.cache' / 'cultureforge'))
CACHE_FILE = STORE_DIR / 'evidence_cache.json'
SNAPSHOT_FILE = STORE_DIR / 'snapshots.json'

DEFAULT_TTL_SECONDS = 24 * 60 * 60


def canonical_key(workflow: str, payload: dict) -> str:
    """A stable key for a workflow call."""
    material = json.dumps({'workflow': workflow, 'payload': payload, 'v': ADAPTER_VERSION},
                          sort_keys=True, default=str)
    return hashlib.sha256(material.encode()).hexdigest()


class EvidenceStore:
    """A small, thread-safe, on-disk cache and snapshot store."""

    def __init__(self, directory: Optional[Path] = None):
        self.directory = Path(directory) if directory else STORE_DIR
        self.cache_file = self.directory / CACHE_FILE.name
        self.snapshot_file = self.directory / SNAPSHOT_FILE.name
        self._lock = threading.Lock()
        self._inflight: dict[str, threading.Event] = {}
        self._cache: dict[str, dict] = {}
        self._snapshots: dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------ io
    def _load(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        for path, target in ((self.cache_file, self._cache), (self.snapshot_file, self._snapshots)):
            try:
                if path.is_file():
                    loaded = json.loads(path.read_text(encoding='utf-8'))
                    if isinstance(loaded, dict):
                        target.update(loaded)
            except (OSError, json.JSONDecodeError):
                pass

    def _persist_cache(self) -> None:
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_file.with_suffix('.tmp')
            tmp.write_text(json.dumps(self._cache, default=str), encoding='utf-8')
            os.replace(tmp, self.cache_file)
        except OSError:
            pass

    def _persist_snapshots(self) -> None:
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            tmp = self.snapshot_file.with_suffix('.tmp')
            tmp.write_text(json.dumps(self._snapshots, default=str), encoding='utf-8')
            os.replace(tmp, self.snapshot_file)
        except OSError:
            pass

    # --------------------------------------------------------------- cache
    def get(self, key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Optional[dict]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            if time.time() - float(entry.get('storedAt', 0)) > ttl_seconds:
                self._cache.pop(key, None)
                self._persist_cache()
                return None
            return entry.get('envelope')

    def put(self, key: str, envelope: dict, transport_requests: int = 1) -> None:
        with self._lock:
            self._cache[key] = {
                'envelope': envelope,
                'storedAt': time.time(),
                'transportRequests': transport_requests,
            }
            self._persist_cache()

    def transport_requests(self, key: str) -> int:
        with self._lock:
            entry = self._cache.get(key) or {}
            return int(entry.get('transportRequests', 0))

    # ------------------------------------------------------- single flight
    def acquire(self, key: str) -> bool:
        """Claim the right to make the upstream call. False if someone else has it."""
        with self._lock:
            if key in self._inflight:
                return False
            self._inflight[key] = threading.Event()
            return True

    def release(self, key: str) -> None:
        with self._lock:
            event = self._inflight.pop(key, None)
        if event:
            event.set()

    def wait_for(self, key: str, timeout: float = 120.0) -> Optional[dict]:
        with self._lock:
            event = self._inflight.get(key)
        if event is None:
            return self.get(key)
        event.wait(timeout)
        return self.get(key)

    # ------------------------------------------------------------ snapshots
    def save_snapshot(self, snapshot_id: str, payload: dict) -> dict:
        record = {'id': snapshot_id, 'createdAt': time.time(), 'payload': payload}
        with self._lock:
            self._snapshots[snapshot_id] = record
            self._persist_snapshots()
        return record

    def get_snapshot(self, snapshot_id: str) -> Optional[dict]:
        with self._lock:
            record = self._snapshots.get(snapshot_id)
        return record.get('payload') if record else None

    def snapshot_count(self) -> int:
        with self._lock:
            return len(self._snapshots)

    # ---------------------------------------------------------------- stats
    def stats(self) -> dict:
        with self._lock:
            entries = list(self._cache.values())
        return {
            'entries': len(entries),
            'transportRequestsCached': sum(int(e.get('transportRequests', 0)) for e in entries),
            'snapshots': len(self._snapshots),
        }


_store: Optional[EvidenceStore] = None
_store_lock = threading.Lock()


def get_store() -> EvidenceStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = EvidenceStore()
        return _store


def transport_request_count(envelope: dict) -> int:
    """How many upstream HTTP requests a workflow envelope actually made."""
    provenance = envelope.get('provenance') if isinstance(envelope.get('provenance'), dict) else {}
    requests = provenance.get('requests')
    if isinstance(requests, list) and requests:
        return len(requests)
    return 1


def cached_call(key: str, run: Callable[[], dict], ttl_seconds: int = DEFAULT_TTL_SECONDS) -> tuple[dict, bool, int]:
    """Run a workflow through the cache, collapsing concurrent duplicates.

    Returns (envelope, was_cached, transport_requests). The count is what
    *this* call spent upstream, not what the key has cost in total: evidence
    that was already held cost nothing, and saying so is the point of the
    store. The cumulative total stays on the entry.
    """
    store = get_store()
    cached = store.get(key, ttl_seconds)
    if cached is not None:
        return cached, True, 0

    if not store.acquire(key):
        # Another request is already making this exact call; wait for it.
        envelope = store.wait_for(key)
        if envelope is not None:
            # This caller did not make the upstream request, so it spent nothing.
            return envelope, True, 0
        # The other call failed; fall through and try it ourselves.
        store.acquire(key)

    try:
        envelope = run()
    finally:
        store.release(key)

    requests = transport_request_count(envelope)
    store.put(key, envelope, requests)
    return envelope, False, requests
