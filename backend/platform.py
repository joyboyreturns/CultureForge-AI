"""The platform layer: workspaces, issued keys, saved explorations, and metering.

This is what makes the product something a partner could license rather than
a prototype that forgets everything when the tab closes.

The rules it holds to:

  - A credential is stored as a hash. The plaintext key is shown once, at
    issue, and never again.
  - Every private resource belongs to a workspace, and every read checks that
    the caller owns it.
  - A shared snapshot is immutable, explicitly created, revocable, and reached
    through a long random token rather than a guessable id.
  - API requests are metered separately from the upstream Qloo calls they may
    cause, because they are different costs.

SQLite is enough for a single-instance release and needs no service to run.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

#: Where the platform database lives. The evidence cache is separate on
#: purpose: the cache is disposable, the platform state is not.
DEFAULT_DB_PATH = Path(os.getenv('CULTUREFORGE_DB', Path.home() / '.cache' / 'cultureforge' / 'platform.db'))

#: How a key is named, so a customer can tell at a glance which is which.
SCOPES = ('read', 'write', 'export')

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    created_at    REAL NOT NULL,
    plan          TEXT NOT NULL DEFAULT 'partner'
);

CREATE TABLE IF NOT EXISTS api_keys (
    id            TEXT PRIMARY KEY,
    workspace_id  TEXT NOT NULL REFERENCES workspaces(id),
    prefix        TEXT NOT NULL,
    key_hash      TEXT NOT NULL,
    scopes        TEXT NOT NULL,
    created_at    REAL NOT NULL,
    expires_at    REAL,
    revoked_at    REAL,
    last_used_at  REAL
);
CREATE INDEX IF NOT EXISTS api_keys_workspace ON api_keys(workspace_id);

CREATE TABLE IF NOT EXISTS explorations (
    id              TEXT PRIMARY KEY,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    project_id      TEXT,
    title           TEXT NOT NULL,
    brief           TEXT NOT NULL,
    composer_version TEXT,
    created_at      REAL NOT NULL,
    updated_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS explorations_workspace ON explorations(workspace_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS exploration_versions (
    id              TEXT PRIMARY KEY,
    exploration_id  TEXT NOT NULL REFERENCES explorations(id),
    version         INTEGER NOT NULL,
    payload         TEXT NOT NULL,
    delivery        TEXT,
    created_at      REAL NOT NULL,
    note            TEXT
);
CREATE INDEX IF NOT EXISTS exploration_versions_exploration
    ON exploration_versions(exploration_id, version DESC);

CREATE TABLE IF NOT EXISTS research_runs (
    id              TEXT PRIMARY KEY,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    status          TEXT NOT NULL,
    brief           TEXT NOT NULL,
    created_at      REAL NOT NULL,
    finished_at     REAL
);
CREATE INDEX IF NOT EXISTS research_runs_workspace ON research_runs(workspace_id, created_at DESC);

CREATE TABLE IF NOT EXISTS usage_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id    TEXT,
    key_prefix      TEXT,
    route           TEXT NOT NULL,
    method          TEXT NOT NULL,
    status          INTEGER NOT NULL,
    upstream_calls  INTEGER NOT NULL DEFAULT 0,
    duration_ms     INTEGER NOT NULL DEFAULT 0,
    created_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS usage_events_workspace ON usage_events(workspace_id, created_at DESC);

CREATE TABLE IF NOT EXISTS share_snapshots (
    id          TEXT PRIMARY KEY,
    exploration_id TEXT,
    payload     TEXT NOT NULL,
    created_at  REAL NOT NULL,
    revoked_at  REAL
);
"""


class Platform:
    """The persistence layer. One database, one connection, one lock."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or DEFAULT_DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute('PRAGMA journal_mode=WAL')
        self._connection.execute('PRAGMA foreign_keys=ON')
        with self._lock:
            self._connection.executescript(SCHEMA)
            self._connection.commit()

    # ------------------------------------------------------------- internals
    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self._connection.execute(sql, params)
            self._connection.commit()
            return cursor

    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._connection.execute(sql, params).fetchall())

    def _one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        rows = self._query(sql, params)
        return rows[0] if rows else None

    # ------------------------------------------------------------ workspaces
    def create_workspace(self, name: str, plan: str = 'partner') -> dict:
        workspace_id = f'ws-{secrets.token_hex(8)}'
        now = time.time()
        self._execute(
            'INSERT INTO workspaces (id, name, created_at, plan) VALUES (?, ?, ?, ?)',
            (workspace_id, name, now, plan))
        return {'id': workspace_id, 'name': name, 'plan': plan, 'createdAt': now}

    def workspace(self, workspace_id: str) -> Optional[dict]:
        row = self._one('SELECT * FROM workspaces WHERE id = ?', (workspace_id,))
        if not row:
            return None
        return {'id': row['id'], 'name': row['name'], 'plan': row['plan'], 'createdAt': row['created_at']}

    def workspaces(self) -> list[dict]:
        return [self.workspace(row['id']) for row in self._query('SELECT id FROM workspaces ORDER BY created_at')]

    # ------------------------------------------------------------- api keys
    def issue_key(self, workspace_id: str, scopes: list[str], expires_at: Optional[float] = None) -> dict:
        """Issue a key. The plaintext is returned once and never stored."""
        if not workspace_id or not self.workspace(workspace_id):
            raise ValueError('That workspace does not exist.')
        chosen = [scope for scope in scopes if scope in SCOPES] or ['read']
        secret = secrets.token_urlsafe(32)
        prefix = f'cfk_{secret[:8]}'
        key_id = f'key-{secrets.token_hex(8)}'
        now = time.time()
        self._execute(
            'INSERT INTO api_keys (id, workspace_id, prefix, key_hash, scopes, created_at, expires_at)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?)',
            (key_id, workspace_id, prefix, hash_key(secret), ','.join(chosen), now, expires_at))
        return {
            'id': key_id,
            'prefix': prefix,
            'workspaceId': workspace_id,
            'scopes': chosen,
            'createdAt': now,
            'expiresAt': expires_at,
            # Shown once. It is not recoverable from the stored hash.
            'key': f'{prefix}.{secret}',
        }

    def keys(self, workspace_id: str) -> list[dict]:
        rows = self._query('SELECT * FROM api_keys WHERE workspace_id = ? ORDER BY created_at DESC', (workspace_id,))
        return [{
            'id': row['id'], 'prefix': row['prefix'], 'scopes': row['scopes'].split(','),
            'createdAt': row['created_at'], 'expiresAt': row['expires_at'],
            'revokedAt': row['revoked_at'], 'lastUsedAt': row['last_used_at'],
        } for row in rows]

    def revoke_key(self, key_id: str, workspace_id: Optional[str] = None) -> bool:
        """Revoke a key.

        When a workspace is given, the key must belong to it. A caller that
        names one workspace must not be able to revoke another's key.
        """
        if workspace_id:
            row = self._one('SELECT id FROM api_keys WHERE id = ? AND workspace_id = ?',
                            (key_id, workspace_id))
        else:
            row = self._one('SELECT id FROM api_keys WHERE id = ?', (key_id,))
        if not row:
            return False
        self._execute('UPDATE api_keys SET revoked_at = ? WHERE id = ?', (time.time(), key_id))
        return True

    def authenticate(self, presented: str) -> Optional[dict]:
        """Check a presented key. The plaintext is compared in constant time."""
        if not presented or '.' not in presented:
            return None
        prefix, _, secret = presented.partition('.')
        rows = self._query('SELECT * FROM api_keys WHERE prefix = ?', (prefix,))
        for row in rows:
            if row['revoked_at']:
                continue
            if row['expires_at'] and row['expires_at'] < time.time():
                continue
            if hmac.compare_digest(row['key_hash'], hash_key(secret)):
                self._execute('UPDATE api_keys SET last_used_at = ? WHERE id = ?', (time.time(), row['id']))
                return {
                    'keyId': row['id'], 'prefix': row['prefix'], 'workspaceId': row['workspace_id'],
                    'scopes': row['scopes'].split(','),
                }
        return None

    # ---------------------------------------------------------- explorations
    def save_exploration(self, workspace_id: str, payload: dict, title: str,
                         brief: dict, project_id: Optional[str] = None,
                         delivery: Optional[dict] = None, note: Optional[str] = None,
                         exploration_id: Optional[str] = None) -> dict:
        """Save an exploration, and a new version of it if it already exists."""
        now = time.time()
        existing = self._one('SELECT id, version_count FROM (SELECT id, 0 AS version_count FROM explorations)'
                             ' WHERE id = ?', (exploration_id,)) if exploration_id else None
        if exploration_id and existing:
            version = self._next_version(exploration_id)
            self._execute(
                'INSERT INTO exploration_versions (id, exploration_id, version, payload, delivery, created_at, note)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (f'ver-{secrets.token_hex(8)}', exploration_id, version,
                 json.dumps(payload), json.dumps(delivery) if delivery else None, now, note))
            self._execute('UPDATE explorations SET updated_at = ?, title = ? WHERE id = ?',
                           (now, title, exploration_id))
            return self.exploration(exploration_id) or {}
        if not exploration_id:
            # Asking the same brief again is the same exploration, not a new
            # list entry: a shared demo workspace would otherwise fill with
            # copies. A new version is kept only when the answer changed.
            repeat = self._same_brief(workspace_id, brief)
            if repeat:
                latest = self._one('SELECT payload FROM exploration_versions WHERE exploration_id = ?'
                                   ' ORDER BY version DESC LIMIT 1', (repeat['id'],))
                if latest and _answer_fingerprint(json.loads(latest['payload'])) == _answer_fingerprint(payload):
                    self._execute('UPDATE explorations SET updated_at = ? WHERE id = ?', (now, repeat['id']))
                    return self.exploration(repeat['id']) or {}
                return self.save_exploration(workspace_id, payload, title, brief, project_id=project_id,
                                             delivery=delivery, note=note, exploration_id=repeat['id'])
        new_id = exploration_id or f'exp-{secrets.token_hex(8)}'
        self._execute(
            'INSERT INTO explorations (id, workspace_id, project_id, title, brief, composer_version, created_at, updated_at)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (new_id, workspace_id, project_id, title, json.dumps(brief),
             (payload or {}).get('composerVersion'), now, now))
        self._execute(
            'INSERT INTO exploration_versions (id, exploration_id, version, payload, delivery, created_at, note)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?)',
            (f'ver-{secrets.token_hex(8)}', new_id, 1, json.dumps(payload),
             json.dumps(delivery) if delivery else None, now, note))
        return self.exploration(new_id) or {}

    def _same_brief(self, workspace_id: str, brief: dict) -> Optional[sqlite3.Row]:
        for row in self._query('SELECT id, brief FROM explorations WHERE workspace_id = ?'
                               ' ORDER BY updated_at DESC', (workspace_id,)):
            try:
                if json.loads(row['brief']) == brief:
                    return row
            except (TypeError, ValueError):
                continue
        return None

    def _next_version(self, exploration_id: str) -> int:
        row = self._one('SELECT MAX(version) AS v FROM exploration_versions WHERE exploration_id = ?',
                         (exploration_id,))
        return int((row['v'] or 0)) + 1

    def exploration(self, exploration_id: str) -> Optional[dict]:
        row = self._one('SELECT * FROM explorations WHERE id = ?', (exploration_id,))
        if not row:
            return None
        versions = self._query(
            'SELECT id, version, created_at, note, delivery FROM exploration_versions'
            ' WHERE exploration_id = ? ORDER BY version DESC', (exploration_id,))
        return {
            'id': row['id'],
            'workspaceId': row['workspace_id'],
            'projectId': row['project_id'],
            'title': row['title'],
            'brief': json.loads(row['brief']),
            'composerVersion': row['composer_version'],
            'createdAt': row['created_at'],
            'updatedAt': row['updated_at'],
            'versions': [{
                'id': v['id'], 'version': v['version'], 'createdAt': v['created_at'],
                'note': v['note'], 'delivery': json.loads(v['delivery']) if v['delivery'] else None,
            } for v in versions],
        }

    def exploration_payload(self, exploration_id: str, version: Optional[int] = None) -> Optional[dict]:
        if version is None:
            row = self._one('SELECT payload FROM exploration_versions WHERE exploration_id = ?'
                            ' ORDER BY version DESC LIMIT 1', (exploration_id,))
        else:
            row = self._one('SELECT payload FROM exploration_versions WHERE exploration_id = ? AND version = ?',
                            (exploration_id, version))
        return json.loads(row['payload']) if row else None

    def explorations(self, workspace_id: str, limit: int = 50) -> list[dict]:
        rows = self._query(
            'SELECT id FROM explorations WHERE workspace_id = ? ORDER BY updated_at DESC LIMIT ?',
            (workspace_id, limit))
        return [self.exploration(row['id']) for row in rows]

    def delete_exploration(self, exploration_id: str, workspace_id: str) -> bool:
        row = self._one('SELECT id FROM explorations WHERE id = ? AND workspace_id = ?',
                        (exploration_id, workspace_id))
        if not row:
            return False
        self._execute('DELETE FROM exploration_versions WHERE exploration_id = ?', (exploration_id,))
        self._execute('DELETE FROM explorations WHERE id = ?', (exploration_id,))
        return True

    # ------------------------------------------------------- share snapshots
    def save_share(self, payload: dict, exploration_id: Optional[str] = None) -> str:
        snapshot_id = f'snap-{secrets.token_urlsafe(18)}'
        self._execute(
            'INSERT INTO share_snapshots (id, exploration_id, payload, created_at) VALUES (?, ?, ?, ?)',
            (snapshot_id, exploration_id, json.dumps(payload), time.time()))
        return snapshot_id

    def share(self, snapshot_id: str) -> Optional[dict]:
        row = self._one('SELECT * FROM share_snapshots WHERE id = ?', (snapshot_id,))
        if not row or row['revoked_at']:
            return None
        record = json.loads(row['payload'])
        record['snapshotId'] = snapshot_id
        return record

    def revoke_share(self, snapshot_id: str) -> bool:
        row = self._one('SELECT id FROM share_snapshots WHERE id = ?', (snapshot_id,))
        if not row:
            return False
        self._execute('UPDATE share_snapshots SET revoked_at = ? WHERE id = ?', (time.time(), snapshot_id))
        return True

    # ---------------------------------------------------------------- usage
    def record_usage(self, route: str, method: str, status: int, workspace_id: Optional[str] = None,
                     key_prefix: Optional[str] = None, upstream_calls: int = 0,
                     duration_ms: int = 0) -> None:
        self._execute(
            'INSERT INTO usage_events (workspace_id, key_prefix, route, method, status, upstream_calls, duration_ms, created_at)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (workspace_id, key_prefix, route, method, status, upstream_calls, duration_ms, time.time()))

    def usage(self, workspace_id: Optional[str] = None, days: int = 30) -> dict:
        since = time.time() - days * 86400
        if workspace_id:
            rows = self._query('SELECT * FROM usage_events WHERE workspace_id = ? AND created_at >= ?',
                               (workspace_id, since))
        else:
            rows = self._query('SELECT * FROM usage_events WHERE created_at >= ?', (since,))
        by_route: dict[str, int] = {}
        upstream = 0
        for row in rows:
            by_route[row['route']] = by_route.get(row['route'], 0) + 1
            upstream += int(row['upstream_calls'] or 0)
        return {
            'requests': len(rows),
            'upstreamCalls': upstream,
            'byRoute': by_route,
            'windowDays': days,
            'since': since,
        }


def hash_key(secret: str) -> str:
    """Hash a key with a per-deployment salt, so a stolen database is not a
    stolen key book."""
    salt = os.getenv('CULTUREFORGE_KEY_SALT', 'cultureforge-development-salt')
    return hashlib.sha256(f'{salt}:{secret}'.encode('utf-8')).hexdigest()


def _answer_fingerprint(payload: dict) -> str:
    """What makes two answers to the same brief the same answer: the evidence
    and the directions, not the id, the timings or the trace."""
    payload = payload or {}
    evidence = [(item.get('entityId') or item.get('tagId'), item.get('kind')) for item in payload.get('evidence') or []]
    concepts = [(item.get('name'), item.get('description'), tuple(item.get('evidenceIds') or []))
                for item in payload.get('concepts') or []]
    return json.dumps([evidence, concepts, payload.get('composerVersion')], sort_keys=True, default=str)


_platform: Optional[Platform] = None
_platform_lock = threading.Lock()


def get_platform() -> Platform:
    global _platform
    with _platform_lock:
        if _platform is None:
            _platform = Platform()
        return _platform
