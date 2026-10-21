"""Culture data providers: transparent sample data or the official Qloo harness."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Optional
from uuid import uuid4

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from . import metering
from .concept_composer import compose
from .evidence_store import cached_call, canonical_key, get_store, known_location

# Bumped whenever the composer changes what a concept means, so a stored
# snapshot is never mistaken for a current result.
#: Every read-only Qloo workflow this app can reach. The harness exposes nine;
#: these are the ones the product actually uses, and the ones a judge can see
#: being used in the provenance of any result.
QLOO_WORKFLOWS = (
    'find_tags',
    'recommend',
    'rank',
    'compare_audiences',
    'describe',
    'where_popular',
    'entity_tags',
    'audience_demographics',
    'trends',
)

COMPOSER_VERSION = '1'

# The exact set of query parameters this app sends to Qloo. A provenance
# panel may only show a parameter that appears here. Anything else is dropped
# before it can reach the panel, so a future change to the harness cannot
# quietly start exposing a new field.
SAFE_QUERY_KEYS = {
    # find_tags
    'filter.query', 'feature.semantic_search',
    # recommend and rank
    'filter.type', 'filter.location.query', 'signal.location.query',
    'take', 'feature.explainability',
    'signal.interests.tags', 'operator.signal.interests.tags',
    'signal.interests.entities',
    'signal.demographics.gender', 'signal.demographics.age',
    'filter.tags', 'operator.filter.tags',
    'filter.exclude.tags', 'operator.filter.exclude.tags',
    'filter.results.entities',
    # compare_audiences
    'a.signal.interests.entities', 'b.signal.interests.entities',
}


def safe_query(query: dict) -> dict:
    """Keep only the parameters that are safe to display."""
    if not isinstance(query, dict):
        return {}
    return {key: value for key, value in query.items() if key in SAFE_QUERY_KEYS}
from .models import (Concept, CulturalSignal, Decision, Delivery, Evidence, ExperienceMoment,
                      GenerateResponse, ProjectRequest, ProvenanceMetadata, TraceEvent)

class CultureProvider(ABC):
    @abstractmethod
    def generate(self, project: ProjectRequest) -> GenerateResponse:
        """Return concepts and provenance-aware cultural signals."""

class MockCultureProvider(CultureProvider):
    """The offline fixture. No Qloo calls are made.

    It exists so the test suite can check the HTTP contract without spending
    quota. The product never reaches it: `get_provider()` returns it only when
    `CULTUREFORGE_PROVIDER=mock` is set by name.
    """
    def generate(self, project: ProjectRequest) -> GenerateResponse:
        from .mock_generator import generate_mock
        return generate_mock(project)

# ---------------------------------------------------------------------------
# The request shape of each Qloo workflow
#
# Every Qloo workflow has its own contract, and each contract rejects fields
# it does not know. `describe` takes `type`; `where_popular` takes
# `entity_type`; `rank` has no `limit` at all. Building the payloads from one
# shared shape would be wrong in a way that only shows up as an upstream
# error, so each workflow gets its own builder here.
# ---------------------------------------------------------------------------

#: The entity types Qloo accepts, for the workflows that take one.
QLOO_ENTITY_TYPES = (
    'artist', 'book', 'brand', 'movie', 'person', 'place', 'podcast', 'tv_show',
    'videogame', 'locality', 'actor', 'album', 'author', 'director',
)

#: The capability matrix, and the single source of truth for how each workflow
#: is called. Each entry says which field carries the entity type, because
#: they are not the same field: `describe` takes `type`, the others take
#: `entity_type`. It says whether the workflow accepts a limit, because `rank`
#: does not. A partner can read this instead of discovering it by getting it
#: wrong, and the payload builders below are written from it.
QLOO_CAPABILITIES = {
    'find_tags': {
        "summary": "Search Qloo's tag ontology by natural-language concept.",
        'entityTypeField': None, 'acceptsLimit': True, 'latency': 'fast',
        'required': ['query'], 'optional': ['limit'],
    },
    'recommend': {
        'summary': 'Return places for a set of taste signals and a location.',
        'entityTypeField': 'target_type', 'acceptsLimit': True, 'latency': 'slow',
        'required': ['target_type'], 'optional': ['signal_tags', 'signal_location', 'limit'],
    },
    'rank': {
        'summary': 'Rank a caller-supplied shortlist against one signal profile.',
        'entityTypeField': 'option_type', 'acceptsLimit': False, 'latency': 'slow',
        'required': ['options', 'option_type'],
        'optional': ['signals', 'signal_location', 'demographic', 'include_tags', 'exclude_tags'],
    },
    'compare_audiences': {
        'summary': 'Compare two complete groups of entity signals.',
        'entityTypeField': 'target_type', 'acceptsLimit': True, 'latency': 'slow',
        'required': ['group_a', 'group_b'], 'optional': ['target_type', 'limit'],
    },
    'describe': {
        'summary': 'Resolve one named entity and return the metadata Qloo holds.',
        'entityTypeField': 'type', 'acceptsLimit': False, 'latency': 'fast',
        'required': ['entity'], 'optional': ['type'],
    },
    'where_popular': {
        'summary': 'Geographic cells where one entity has strong query-relative affinity.',
        'entityTypeField': 'entity_type', 'acceptsLimit': True, 'latency': 'medium',
        'required': ['entity', 'within'], 'optional': ['entity_type', 'limit'],
    },
    'entity_tags': {
        'summary': 'The concepts that jointly characterise one or more entities.',
        'entityTypeField': 'entity_type', 'acceptsLimit': True, 'latency': 'fast',
        'required': ['entities'], 'optional': ['entity_type', 'limit'],
    },
    'audience_demographics': {
        'summary': 'Aggregate demographic indexing associated with one entity.',
        'entityTypeField': 'entity_type', 'acceptsLimit': True, 'latency': 'fast',
        'required': ['entity'], 'optional': ['entity_type', 'limit'],
    },
    'trends': {
        'summary': 'Time-series popularity for one to five resolved entities.',
        'entityTypeField': 'entity_type', 'acceptsLimit': True, 'latency': 'medium',
        'required': ['entities', 'entity_type', 'start_date', 'end_date'], 'optional': ['limit'],
    },
}


def capabilities() -> list[dict]:
    """The capability matrix, as the API publishes it."""
    published = []
    for operation, spec in QLOO_CAPABILITIES.items():
        published.append({
            'id': operation,
            'summary': spec['summary'],
            'entityTypeField': spec['entityTypeField'],
            'entityTypes': list(QLOO_ENTITY_TYPES) if spec['entityTypeField'] else [],
            'acceptsLimit': spec['acceptsLimit'],
            'latency': spec['latency'],
            'required': list(spec['required']),
            'optional': list(spec['optional']),
        })
    return published


def describe_payload(entity: str, entity_type: Optional[str] = None) -> dict:
    payload: dict = {'entity': entity}
    if entity_type:
        payload['type'] = entity_type
    return payload


def entity_tags_payload(entities: list[str], entity_type: Optional[str] = None,
                        limit: int = 10) -> dict:
    payload: dict = {'entities': list(entities)[:5]}
    if entity_type:
        payload['entity_type'] = entity_type
    payload['limit'] = limit
    return payload


def where_popular_payload(entity: str, within: str, entity_type: Optional[str] = None,
                          limit: int = 20) -> dict:
    payload: dict = {'entity': entity, 'within': within, 'limit': limit}
    if entity_type:
        payload['entity_type'] = entity_type
    return payload


def audience_demographics_payload(entity: str, entity_type: Optional[str] = None,
                                  limit: int = 5) -> dict:
    payload: dict = {'entity': entity, 'limit': limit}
    if entity_type:
        payload['entity_type'] = entity_type
    return payload


def trends_payload(entities: list[str], entity_type: str, start_date: str,
                   end_date: str, limit: int = 10) -> dict:
    return {
        'entities': list(entities)[:5],
        'entity_type': entity_type,
        'start_date': start_date,
        'end_date': end_date,
        'limit': limit,
    }


class QlooHarnessError(RuntimeError):
    """A safe-to-display provider failure; deliberately contains no CLI output or secrets.

    It carries a machine-readable code so the API can answer with a consistent
    error envelope, and a flag saying whether trying again could work.
    """

    def __init__(self, message: str, code: str = 'UPSTREAM_REJECTED',
                 retryable: bool = False, details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.details = details or {}

def mark_reused(event: TraceEvent, detail: Optional[str] = None) -> TraceEvent:
    """Record that a step reused held evidence instead of waiting on the API.

    The duration inside a held envelope belongs to the call that fetched it,
    not to this run. Reporting it as-is would make a free, instant answer look
    like it sat waiting on the network for twenty seconds, so the step's own
    duration is zeroed and the original time is stated in the detail instead.
    """
    original = event.durationMs
    event.durationMs = 0
    when = f'{original / 1000:.1f}s' if original is not None else 'an unrecorded time'
    text = detail or event.detail or ''
    event.detail = f'{text} (reused from cache — the original call took {when}, this run spent no time waiting)'
    return event

class QlooHarnessProvider(CultureProvider):
    """Use the official qloo CLI to resolve tags and fetch bounded recommendations.

    The CLI owns credential storage (`qloo setup --qloo`) or reads QLOO_API_KEY from
    the server environment. Credentials never enter the frontend or command arguments.

    Hackathon keys only work against https://hackathon.api.qloo.com, which is set in
    the CLI's own config (`qloo config set base-url ...`) rather than here.

    Two guards protect the key:
    - `scripts/qloo_exec.mjs` raises the per-request timeout. The stock `qloo exec`
      client caps each attempt at 20s while /v2/insights needs ~25s, so every live
      request would otherwise time out, retry, and burn three calls for nothing.
    - A local call budget caps how many workflows this provider may issue per hour
      and per day, so a runaway demo cannot exhaust the hackathon quota.
    """
    CACHE_TTL_SECONDS = 24 * 60 * 60
    CACHE_MAX_ENTRIES = 128
    DEFAULT_MAX_CALLS_PER_HOUR = 20
    DEFAULT_MAX_CALLS_PER_DAY = 100
    BUDGET_LOG_PATH = Path.home() / '.cache' / 'cultureforge' / 'qloo_calls.json'

    def __init__(self, command: str = 'qloo', timeout_seconds: int = 90):
        self.command = command
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, tuple[float, GenerateResponse]] = {}
        self._lock = threading.Lock()

    def _resolve_command(self) -> list[str]:
        """Resolve the argv prefix used to run a Qloo workflow.

        Prefers the bundled wrapper because it can set a request timeout the CLI
        cannot. Falls back to the `qloo` binary. QLOO_CLI overrides both.
        """
        override = os.getenv('QLOO_CLI', '').strip()
        if override:
            return [shutil.which(override) or override]
        wrapper = Path(__file__).resolve().parent.parent / 'scripts' / 'qloo_exec.mjs'
        if wrapper.is_file():
            node = shutil.which('node')
            if node:
                return [node, str(wrapper)]
        executable = shutil.which(self.command)
        if not executable:
            raise QlooHarnessError('Qloo provider is selected but neither scripts/qloo_exec.mjs nor the qloo CLI is available. Install @qloo/qloo-harness and complete qloo setup.', code='PROVIDER_UNAVAILABLE', retryable=True)
        return [executable]

    def _consume_call_budget(self) -> None:
        """Count this call against the local quota guard before it is made."""
        hour_limit = int(os.getenv('QLOO_MAX_CALLS_PER_HOUR', self.DEFAULT_MAX_CALLS_PER_HOUR))
        day_limit = int(os.getenv('QLOO_MAX_CALLS_PER_DAY', self.DEFAULT_MAX_CALLS_PER_DAY))
        now = time.time()
        with self._lock:
            calls = self._read_call_log()
            calls = [stamp for stamp in calls if now - stamp < 86400]
            calls_in_hour = sum(1 for stamp in calls if now - stamp < 3600)
            if calls_in_hour >= hour_limit or len(calls) >= day_limit:
                raise QlooHarnessError(
                    'Qloo call budget reached for this period. Live signals are paused to protect the '
                    'hackathon API quota. Wait for the budget to reset, or open a saved exploration.',
                    code='QUOTA_EXHAUSTED', retryable=True,
                    details={'resetsInSeconds': 3600 - int(now % 3600)},
                )
            calls.append(now)
            self._write_call_log(calls)

    def _read_call_log(self) -> list[float]:
        try:
            data = json.loads(self.BUDGET_LOG_PATH.read_text(encoding='utf-8'))
            return [float(stamp) for stamp in data.get('calls', []) if isinstance(stamp, (int, float))]
        except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
            return []

    def _write_call_log(self, calls: list[float]) -> None:
        try:
            self.BUDGET_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.BUDGET_LOG_PATH.write_text(json.dumps({'calls': calls}), encoding='utf-8')
            os.chmod(self.BUDGET_LOG_PATH, 0o600)
        except OSError:
            pass

    def _run_workflow(self, operation: str, payload: dict) -> dict:
        command = self._resolve_command()
        self._consume_call_budget()
        # The CLI accepts a request file; using a mode-0600 temporary file avoids putting
        # audience text in shell arguments and avoids leaking it to process listings.
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json', delete=False) as request_file:
                json.dump(payload, request_file)
                request_path = request_file.name
            os.chmod(request_path, 0o600)
            completed = subprocess.run(
                [*command, 'exec', operation, '--input-file', request_path],
                capture_output=True, text=True, timeout=self.timeout_seconds,
                check=False, env=os.environ.copy(),
            )
        except subprocess.TimeoutExpired as exc:
            raise QlooHarnessError('Qloo request timed out. Try again later.', code='UPSTREAM_TIMEOUT', retryable=True) from exc
        except OSError as exc:
            raise QlooHarnessError('Unable to start the Qloo CLI.', code='PROVIDER_UNAVAILABLE', retryable=True) from exc
        finally:
            if 'request_path' in locals():
                Path(request_path).unlink(missing_ok=True)
        if completed.returncode != 0:
            # Do not return stderr to clients; it may include sensitive runtime context.
            # The structured error code on stdout is safe and tells us whether this was
            # a quota/rate-limit problem, an auth problem, or a malformed request.
            code = ''
            try:
                failure = json.loads(completed.stdout)
                code = str(failure.get('error', {}).get('code', '')) if isinstance(failure, dict) else ''
            except (json.JSONDecodeError, AttributeError):
                code = ''
            if code in ('QLOO_RATE_LIMIT', 'QLOO_RATE_LIMITED'):
                raise QlooHarnessError('Qloo rate limited this key. Wait before retrying; live signals are temporarily unavailable.', code='RATE_LIMITED', retryable=True)
            if code == 'QLOO_AUTH':
                raise QlooHarnessError('Qloo rejected the credential. Check the API key and the base URL.', code='UPSTREAM_UNAUTHENTICATED')
            if code == 'TOOL_INPUT':
                raise QlooHarnessError('Qloo rejected the shape of the request. The arguments did not match the workflow contract.', code='INVALID_UPSTREAM_REQUEST')
            if code:
                raise QlooHarnessError(f'Qloo rejected the request ({code}).', code='UPSTREAM_REJECTED', details={'upstreamCode': code})
            raise QlooHarnessError('Qloo rejected the request. Check the backend credential and CLI status.', code='UPSTREAM_REJECTED')
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise QlooHarnessError('Qloo CLI returned an unreadable response.', code='UPSTREAM_MALFORMED') from exc
        if not isinstance(result, dict):
            raise QlooHarnessError('Qloo CLI returned an unexpected response shape.', code='UPSTREAM_MALFORMED')
        return result

    def run_workflow_cached(self, operation: str, payload: dict) -> tuple[dict, bool, int]:
        """Run a workflow through the durable store.

        Returns (envelope, was_cached, transport_requests). Concurrent callers
        asking for the same evidence collapse into one upstream call, and the
        result survives a restart, so a demo never waits on the API twice.

        The request count is what this call spent. Evidence that was already
        held cost nothing, and reporting it as anything else would overstate
        what the quota was asked for.
        """
        key = canonical_key(operation, payload)
        store = get_store()
        cached = store.get(key)
        if cached is not None:
            return cached, True, 0
        envelope, was_cached, requests = cached_call(key, lambda: self._run_workflow(operation, payload))
        # Count it against the request being served, so the usage record can
        # tell an API request from the upstream calls it caused.
        metering.count(requests)
        return envelope, was_cached, requests

    @staticmethod
    def rows(envelope: dict) -> list[dict]:
        rows = envelope.get('results', [])
        if isinstance(rows, dict):
            rows = rows.get('entities', rows.get('tags', []))
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    @staticmethod
    def tag_id(row: dict) -> str | None:
        value = row.get('id') or row.get('tag_id') or row.get('tag_value')
        return value if isinstance(value, str) and value.startswith('urn:tag:') else None

    @staticmethod
    def _affinity(row: dict) -> float | None:
        value = row.get('affinity')
        if value is None and isinstance(row.get('query'), dict):
            value = row['query'].get('affinity')
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def generate(self, project: ProjectRequest, tag_result: Optional[dict] = None,
                 recommendations: Optional[dict] = None,
                 seed_tag_ids: Optional[list[str]] = None) -> GenerateResponse:
        """Compose the answer for a brief.

        `tag_result` and `recommendations` may be supplied to reuse envelopes
        that are already held, which is how recomposition rebuilds the answer
        without spending another upstream call.
        """
        cache_payload = {'businessType': project.businessType, 'audience': project.audience, 'location': project.location, 'target_type': 'place'}
        cache_key = sha256(json.dumps(cache_payload, sort_keys=True).encode()).hexdigest()
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and now - cached[0] < self.CACHE_TTL_SECONDS:
                # Reuse the evidence-backed result, but relabel the delivery so
                # the UI can say plainly that this is cached, not fresh.
                delivery = Delivery(
                    kind='cache',
                    acquiredAt=cached[1].delivery.acquiredAt if cached[1].delivery else None,
                    servedAt=datetime.now(timezone.utc).isoformat(),
                    expiresAt=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                    # Replaying a held answer spends no upstream request, so the
                    # number says zero rather than leaving the cost unknown.
                    transportRequests=0,
                    # The answer was held here, in the server's evidence store.
                    cachedIn='server',
                )
                return cached[1].model_copy(update={
                    'projectId': f'cf-{uuid4().hex[:10]}',
                    'project': project,
                    'delivery': delivery,
                })
            if cached:
                self._cache.pop(cache_key, None)

        query = f'{project.businessType} {project.audience}'.strip()
        reused = tag_result is not None and recommendations is not None
        if tag_result is None and seed_tag_ids:
            # The founder confirmed these seeds, so the audience is not
            # resolved again and no find_tags call is spent. The cached
            # resolution still holds the name and the popularity Qloo
            # returned for each seed, so the evidence keeps them.
            query = f'{project.businessType} {project.audience}'.strip()
            confirmed = set(seed_tag_ids)
            cached_rows = [
                row for row in self._cached_tag_rows(query)
                if row.get('id') in confirmed
            ]
            if cached_rows:
                tag_result = {
                    'operation': 'find_tags',
                    'status': 'ok',
                    'results': cached_rows,
                    'execution': {'duration_ms': 0},
                    'provenance': {'endpoint': 'confirmed by the founder', 'requests': []},
                }
            else:
                tag_result = {
                    'operation': 'find_tags',
                    'status': 'ok',
                    'results': [{'id': tag_id} for tag_id in seed_tag_ids],
                    'execution': {'duration_ms': 0},
                    'provenance': {'endpoint': 'confirmed by the founder', 'requests': []},
                }
            reused = True
        spent = 0
        # Whether any part of this answer had to be fetched live. The delivery
        # label follows this, not whether one part happened to be cached.
        live = False
        if tag_result is None:
            tag_result, was_cached, requests = self.run_workflow_cached('find_tags', {'query': query, 'limit': 3})
            spent += requests
            live = live or not was_cached
            reused = was_cached
        if tag_result.get('status') == 'needs_input':
            raise QlooHarnessError('Qloo needs a clearer cultural seed. Refine the audience description and try again.', code='NEEDS_INPUT')
        matched_tags = [tag for row in self.rows(tag_result) if (tag := self.tag_id(row))][:3]
        if not matched_tags:
            raise QlooHarnessError('Qloo did not resolve any cultural tags for this audience. Refine the description and try again.', code='NO_EVIDENCE')

        if recommendations is None:
            recommendations, was_cached, requests = self.run_workflow_cached('recommend', {
                'target_type': 'place', 'signal_tags': matched_tags,
                'signal_location': project.location, 'limit': 5,
            })
            spent += requests
            live = live or not was_cached
            reused = reused or was_cached
        if recommendations.get('status') == 'needs_input':
            raise QlooHarnessError('Qloo needs a clearer location or cultural seed. Refine the project details and try again.', code='NEEDS_INPUT')
        rows = self.rows(recommendations)
        signals: list[CulturalSignal] = []
        for row in rows[:5]:
            label = row.get('name')
            if not isinstance(label, str) or not label.strip():
                continue
            affinity = self._affinity(row)
            entity_id = row.get('entity_id') or row.get('id')
            detail = 'Qloo aggregate affinity result for the selected cultural tags and location.'
            if affinity is not None:
                detail += f' Raw affinity returned by Qloo: {affinity:g}.'
            signals.append(CulturalSignal(label=label, detail=detail, affinity=affinity, category='Qloo recommendation', provenance_id=entity_id if isinstance(entity_id, str) else None))
        if not signals:
            suggestion = self._known_location(matched_tags, project.location)
            if suggestion:
                raise QlooHarnessError(
                    f"Qloo returned no places for '{project.location}' for this audience. "
                    f"'{suggestion}' returned places for these same signals earlier.",
                    code='NO_EVIDENCE',
                    details={'location': project.location, 'suggestion': suggestion},
                )
            raise QlooHarnessError(
                f"Qloo returned no places for '{project.location}' for this audience.",
                code='NO_EVIDENCE',
                details={'location': project.location},
            )

        # ---- Evidence, trace and composition -----------------------------
        # Qloo supplies the audience lens (the tags) and the local evidence
        # (the entities). CultureForge supplies the business reading, and
        # names the evidence each proposal came from.
        acquired_at = datetime.now(timezone.utc).isoformat()
        trace: list[TraceEvent] = []
        evidence: list[Evidence] = []
        tag_evidence_ids: dict[str, str] = {}
        entity_evidence_ids: dict[str, str] = {}

        tag_trace = self._trace_event('resolve-audience-tags', 'find_tags', tag_result, len(matched_tags))
        if reused:
            mark_reused(tag_trace)
        trace.append(tag_trace)

        # The resolved tag rows, so each seed carries the name and the
        # popularity Qloo actually returned for it.
        tag_rows = {
            row.get('id'): row for row in self.rows(tag_result)
            if isinstance(row, dict) and isinstance(row.get('id'), str)
        }
        for tag in matched_tags:
            evidence_id = f'ev-tag-{len(evidence)}'
            tag_evidence_ids[tag] = evidence_id
            row = tag_rows.get(tag) or {}
            popularity = row.get('popularity')
            name = row.get('name')
            evidence.append(Evidence(
                id=evidence_id, kind='tag',
                label=name if isinstance(name, str) and name.strip() else self._tag_label(tag),
                tagId=tag,
                popularity=popularity if isinstance(popularity, (int, float)) else None,
                traceId=tag_trace.id, description='Audience seed resolved by Qloo from the founder’s audience description.',
            ))

        entity_trace = self._trace_event('retrieve-local-evidence', 'recommend', recommendations, len(rows))
        if reused:
            mark_reused(entity_trace)
        trace.append(entity_trace)

        entity_rows: list[dict] = []
        for row in rows[:5]:
            name = row.get('name')
            if not isinstance(name, str) or not name.strip():
                continue
            entity_id = row.get('entity_id') or row.get('id')
            properties = row.get('properties') if isinstance(row.get('properties'), dict) else {}
            image = properties.get('image')
            image_url = image.get('url') if isinstance(image, dict) else image
            geocode = properties.get('geocode') if isinstance(properties.get('geocode'), dict) else {}
            evidence_id = f'ev-entity-{len(evidence)}'
            if isinstance(entity_id, str):
                entity_evidence_ids[entity_id] = evidence_id
            evidence.append(Evidence(
                id=evidence_id, kind='entity', label=name,
                entityId=entity_id if isinstance(entity_id, str) else None,
                entityType=row.get('subtype') or row.get('type'),
                affinity=self._affinity(row),
                popularity=row.get('popularity') if isinstance(row.get('popularity'), (int, float)) else None,
                rating=properties.get('business_rating') if isinstance(properties.get('business_rating'), (int, float)) else None,
                priceLevel=properties.get('price_level') if isinstance(properties.get('price_level'), int) else None,
                description=properties.get('short_description') or properties.get('description'),
                image=image_url if isinstance(image_url, str) else None,
                location=', '.join(part for part in (geocode.get('city'), geocode.get('admin1_region')) if part) or project.location,
                traceId=entity_trace.id,
            ))
            entity_rows.append({
                'entity_id': entity_id if isinstance(entity_id, str) else '',
                'name': name,
                'description': properties.get('description') or properties.get('short_description') or '',
                'short_description': properties.get('short_description') or '',
                'image': image_url if isinstance(image_url, str) else '',
                'popularity': row.get('popularity') if isinstance(row.get('popularity'), (int, float)) else 0.0,
                'affinity': self._affinity(row) or 0.0,
                'business_rating': properties.get('business_rating'),
                'price_level': properties.get('price_level'),
            })

        composed = compose(
            business_type=project.businessType,
            audience=project.audience,
            location=project.location,
            budget=project.budget,
            tags=[{'id': tag} for tag in matched_tags],
            entities=entity_rows,
            evidence_index={},
            tag_evidence_ids=tag_evidence_ids,
            entity_evidence_ids=entity_evidence_ids,
            trace_id=entity_trace.id,
        )
        trace.append(TraceEvent(
            id='ev-compose', step='compose-directions', status='ok' if composed else 'skipped',
            resultCount=len(composed),
            detail=('Composed %d direction(s) from the returned evidence.' % len(composed)) if composed
                    else 'The returned evidence did not support a distinct business direction.',
            evidenceIds=[eid for c in composed for eid in c.evidence_ids],
        ))

        # Name the directions.
        #
        # The rules above chose the tags, the venues and the evidence; this
        # only writes the words. A brief that was named before is served
        # from the evidence store and spends no model request at all.
        named, naming = self._name_directions(project, composed, evidence, matched_tags)
        if composed:
            for index, concept in enumerate(composed):
                wording = named.get(index) or named.get(str(index)) or {}
                if wording.get('name'):
                    concept.name = wording['name']
                if wording.get('tagline'):
                    concept.tagline = wording['tagline']
                if wording.get('rationale'):
                    concept.naming = wording['rationale']
        trace.append(self._naming_trace(composed, named, naming))

        if composed:
            concepts = [self._composed_concept(project, c, index, trace) for index, c in enumerate(composed)]
            concept_mode = 'evidence_composed'
            notice = (
                'Qloo supplied the audience tags and the local venues below. The three business '
                'directions are CultureForge’s interpretation of that evidence, and each one names '
                'the returned venue it was built from. Fit scores are omitted because affinity '
                'does not measure business fit.'
            )
        else:
            # Abstain rather than pad the answer with catalog concepts.
            concepts = []
            concept_mode = 'evidence_composed'
            notice = (
                'Qloo returned live evidence for this audience and location, but it did not support '
                'three distinct business directions. Refine the audience description and try again.'
            )

        response = GenerateResponse(
            projectId=f'cf-{uuid4().hex[:10]}', project=project,
            concepts=concepts, signals=signals, dataMode='live', conceptMode=concept_mode,
            notice=notice,
            provenance=ProvenanceMetadata(source='Qloo API', endpoint='qloo exec find_tags → recommend', documentation='https://github.com/qloo/qloo-hackathon-kit', resolved_tags=matched_tags),
            evidence=evidence, trace=trace,
            composerVersion=COMPOSER_VERSION,
            delivery=Delivery(kind='fresh' if live else 'cache', acquiredAt=acquired_at, servedAt=datetime.now(timezone.utc).isoformat(), transportRequests=spent,
                              expiresAt=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                              cachedIn=None if live else 'server'),
        )
        with self._lock:
            # A failed naming is not held. The Qloo evidence is still in the
            # evidence store, so the next run costs no Qloo request and can
            # try the model again — rather than being told for a day that
            # this brief has no name.
            held = not (naming.get('attempted') and not naming.get('used'))
            if held:
                if len(self._cache) >= self.CACHE_MAX_ENTRIES:
                    oldest_key = min(self._cache, key=lambda key: self._cache[key][0])
                    self._cache.pop(oldest_key, None)
                self._cache[cache_key] = (time.monotonic(), response)
            else:
                self._cache.pop(cache_key, None)
        return response

    # ------------------------------------------------------------------
    # The remaining Qloo workflows
    #
    # Each one is read-only, cached the same way the others are, and reports
    # what it spent. They are the app's direct line to Qloo's full surface.
    # ------------------------------------------------------------------
    def describe_entity(self, entity: str, entity_type: Optional[str] = None) -> dict:
        """Resolve one named entity and return the metadata Qloo holds for it."""
        return self.run_workflow_cached('describe', describe_payload(entity, entity_type))[0]

    def entity_tags(self, entities: list[str], entity_type: Optional[str] = None,
                    limit: int = 10) -> dict:
        """The concepts that jointly characterise these entities."""
        return self.run_workflow_cached('entity_tags', entity_tags_payload(entities, entity_type, limit))[0]

    def where_popular(self, entity: str, within: str, entity_type: Optional[str] = None,
                      limit: int = 20) -> dict:
        """Where an entity has strong affinity, as geographic cells.

        These are popularity cells for interest mapping. They are not the
        coordinates of the venues themselves.
        """
        return self.run_workflow_cached('where_popular', where_popular_payload(entity, within, entity_type, limit))[0]

    def audience_demographics(self, entity: str, entity_type: Optional[str] = None,
                              limit: int = 5) -> dict:
        """Aggregate demographic indexing for one entity."""
        return self.run_workflow_cached('audience_demographics', audience_demographics_payload(entity, entity_type, limit))[0]

    def trends(self, entities: list[str], entity_type: str, start_date: str,
               end_date: str, limit: int = 10) -> dict:
        """Time-series popularity for one to five entities."""
        return self.run_workflow_cached('trends', trends_payload(entities, entity_type, start_date, end_date, limit))[0]

    @staticmethod
    def _known_location(tags: list[str], failed: str) -> Optional[str]:
        """A location this store already holds places for, for these signals.

        Offered only when Qloo itself returned places for it before, so the
        suggestion is evidence rather than a guess.
        """
        return known_location(tags, failed)

    @staticmethod
    def _cached_tag_rows(query: str) -> list[dict]:
        """The rows of an already-resolved audience, if it is still held."""
        key = canonical_key('find_tags', {'query': query, 'limit': 3})
        envelope = get_store().get(key)
        if not isinstance(envelope, dict):
            return []
        rows = envelope.get('results')
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    @staticmethod
    def _tag_label(tag_id: str) -> str:
        return tag_id.rsplit(':', 1)[-1].replace('_', ' ').strip().capitalize()

    @staticmethod
    def _trace_event(step: str, workflow: str, envelope: dict, result_count: int) -> TraceEvent:
        """Build a trace event from the harness execution block.

        The request preview is allowlisted field by field: the Qloo endpoint and
        the query parameters the harness itself recorded, never raw subprocess
        output, which can carry credentials or context.
        """
        execution = envelope.get('execution') if isinstance(envelope.get('execution'), dict) else {}
        provenance = envelope.get('provenance') if isinstance(envelope.get('provenance'), dict) else {}
        endpoint = provenance.get('endpoint')
        detail = f'Qloo {workflow} → {endpoint}' if endpoint else f'Qloo {workflow}'

        request: Optional[dict] = None
        requests = provenance.get('requests')
        if isinstance(requests, list) and requests and isinstance(requests[0], dict):
            first = requests[0]
            raw_query = first.get('query')
            request = {
                'method': first.get('method'),
                'path': first.get('path'),
                # Allowlisted field by field. The raw query is never shown.
                'query': safe_query(raw_query if isinstance(raw_query, dict) else {}),
                'endpoint': endpoint,
                'documentation': provenance.get('documentation'),
            }

        excerpt: list[str] = []
        results = envelope.get('results')
        if isinstance(results, dict):
            # compare_audiences returns a dict of lists rather than one list.
            for value in results.values():
                if isinstance(value, list):
                    results = value
                    break
        for row in (results if isinstance(results, list) else [])[:5]:
            if not isinstance(row, dict):
                continue
            label = row.get('name') or row.get('tag_id') or row.get('id')
            if isinstance(label, str) and label.strip():
                bits = [label]
                if isinstance(row.get('affinity'), (int, float)):
                    bits.append(f'affinity {row["affinity"]:.3f}')
                if isinstance(row.get('popularity'), (int, float)):
                    bits.append(f'popularity {row["popularity"]:.4f}')
                excerpt.append(' · '.join(bits))

        return TraceEvent(
            id=f'trace-{workflow}-{step}',
            step=step, workflow=workflow,
            status='ok' if envelope.get('status', 'ok') == 'ok' else 'needs_input',
            durationMs=execution.get('duration_ms') if isinstance(execution.get('duration_ms'), int) else None,
            correlationId=execution.get('correlation_id') if isinstance(execution.get('correlation_id'), str) else None,
            resultCount=result_count, detail=detail,
            request=request, resultExcerpt=excerpt or None,
            acquiredAt=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _naming_trace(composed, named: dict, naming: dict) -> TraceEvent:
        """The step that says how the directions were named, and by what."""
        duration = naming.get('durationMs')
        if naming.get('used'):
            model = naming.get('model') or 'a free model'
            detail = f'Named by {model}.'
            if naming.get('cached'):
                detail = (f'Names held from an earlier run (named by {model}). '
                          f'Original naming took {duration / 1000:.1f}s; this run spent no time waiting.')
                # A held name did not wait, so it must not be shown as though
                # it did.
                duration = 0
            if naming.get('dropped'):
                detail += ' ' + '; '.join(naming['dropped'][:2]) + '.'
        elif naming.get('attempted'):
            detail = f'The model could not be used ({naming.get("reason")}), so the rule engine named these directions.'
            if naming.get('raw'):
                detail += f' It answered: {naming["raw"][:160]}'
        else:
            detail = naming.get('reason') or 'The rule engine named these directions.'
        return TraceEvent(
            id='ev-name-directions', step='name-the-directions',
            status='ok' if naming.get('used') else 'skipped',
            resultCount=len(named),
            durationMs=duration,
            detail=detail,
            evidenceIds=[],
            acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        )

    def _name_directions(self, project, composed, evidence, matched_tags) -> tuple[dict, dict]:
        """Let a free model name the directions, and keep the rules in charge.

        The model is given the audience signals and the venues each direction
        is built from — and no numbers at all, so it cannot state one. Its
        answer is held in the evidence store like everything else, so a
        repeated brief spends no model request.
        """
        from . import llm

        report = {'used': False, 'attempted': False, 'model': None, 'reason': None, 'dropped': []}
        if not llm.is_configured():
            report['reason'] = 'No OpenRouter key is configured, so the rule engine named these directions.'
            return {}, report
        if not composed:
            return {}, report

        directions = []
        for index, concept in enumerate(composed):
            venues = []
            for position, evidence_id in enumerate(concept.evidence_ids):
                row = next((item for item in evidence if item.id == evidence_id), None)
                if row is None or row.kind != 'entity':
                    continue
                venues.append({
                    'name': row.label,
                    'role': 'primary' if position == 0 else 'support',
                    # Short: a long prompt is what pushes a reasoning model
                    # past its budget.
                    'description': (row.description or '')[:220],
                })
            if not venues:
                continue
            directions.append({
                'index': index,
                'currentName': concept.name,
                'currentTagline': concept.tagline,
                'currentPositioning': concept.positioning,
                'venues': venues,
            })
        if not directions:
            report['reason'] = 'No direction had a venue to name it after.'
            return {}, report

        brief = {
            'businessType': project.businessType,
            'audience': project.audience,
            'location': project.location,
            'budget': project.budget,
            # Qloo can return two tags with the same name; the model does not
            # need to be told twice.
            'signals': list(dict.fromkeys(self._tag_label(tag) for tag in matched_tags)),
        }
        # The key is the content the model is shown, so the same brief finds
        # the same held names.
        key = canonical_key('llm_name', {
            'brief': brief,
            'directions': [{'index': d['index'], 'name': d['currentName'],
                            'venues': [v['name'] for v in d['venues']]} for d in directions],
        })
        held = get_store().get(key)
        if held is not None:
            names = held.get('names') or {}
            if names:
                return names, {**(held.get('report') or {}), 'cached': True}
            # A held failure must not be served as an answer. Drop it and ask
            # again, rather than telling the founder for a day that this brief
            # has no name.
            get_store().discard(key)

        envelope, _cached, requests = cached_call(
            key, lambda: self._ask_model(brief, directions, evidence))
        metering.count(requests)
        names = envelope.get('names') or {}
        if not names:
            # A failure must not be held. The next run should try again
            # rather than be told for a day that the answer is the empty one.
            get_store().discard(key)
        return names, envelope.get('report') or {}

    def _ask_model(self, brief: dict, directions: list[dict], evidence: list[dict]) -> dict:
        """One call to the model, and the envelope that is held afterwards."""
        from . import llm

        started = time.monotonic()
        names, report = llm.name_directions(brief, directions, evidence)
        report.setdefault('durationMs', int((time.monotonic() - started) * 1000))
        report.setdefault('attempted', llm.is_configured())
        return {
            'names': {str(index): wording for index, wording in names.items()},
            'report': report,
            # A request was made whenever the model was reached, whether or
            # not its answer could be used. The count says so.
            'provenance': {
                'endpoint': 'openrouter/free',
                'requests': [{}] * int(report.get('requests') or (1 if report.get('attempted') else 0)),
            },
        }

    @staticmethod
    def _composed_concept(project, composed, index: int, trace: list[TraceEvent]) -> Concept:
        """Turn a composed direction into a Concept card."""
        return Concept(
            id=f'live-{index + 1}-{composed.name.lower().replace(" ", "-")}',
            name=composed.name,
            tagline=composed.tagline,
            description=composed.description,
            audienceFit=None, culturalRelevance=None, feasibility=None,
            budget=project.budget,
            investment='CultureForge planning assumption — not estimated by Qloo',
            signals=list(composed.signals),
            accent=composed.accent,
            image=composed.image or '',
            direction=str(index + 1).zfill(2),
            imageAlt=composed.image_alt,
            personality=composed.personality,
            audienceRationale=f'{composed.rationale} {composed.positioning}'.strip(),
            implementationNote=composed.ritual,
            moments=[
                ExperienceMoment(title='Why this direction', description=composed.offering),
                ExperienceMoment(title='Signature moment', description=composed.ritual),
            ],
            evidenceIds=list(composed.evidence_ids),
            decisions=[Decision(**d) for d in composed.decisions],
            limitations=list(composed.limitations),
        )

def _is_qloo_configured() -> bool:
    if os.getenv('QLOO_API_KEY'):
        return True
    config_path = Path.home() / '.qloo' / 'config'
    if config_path.is_file():
        try:
            content = config_path.read_text(encoding='utf-8')
            return 'api-key' in content or 'api_key' in content
        except OSError:
            pass
    return False

_cached_providers: dict[str, CultureProvider] = {}

def get_provider() -> CultureProvider:
    """The provider this server answers with.

    `auto` means Qloo, and only Qloo. When no key is configured there is
    nothing real to answer with, so the request fails with a stated reason
    rather than answering with a rule-based fiction that looks like data.
    Mock data is available only when it is asked for by name
    (`CULTUREFORGE_PROVIDER=mock`), which the test suite does.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    selected = os.getenv('CULTUREFORGE_PROVIDER', 'auto').strip().lower()
    if selected not in {'auto', 'mock', 'qloo'}:
        raise RuntimeError('CULTUREFORGE_PROVIDER must be auto, mock, or qloo.')
    if selected == 'mock':
        provider_type = 'mock'
    elif selected == 'qloo':
        if not _is_qloo_configured():
            raise QlooHarnessError(
                'CULTUREFORGE_PROVIDER=qloo, but no Qloo API key is configured. Set QLOO_API_KEY, '
                'or run `qloo config set api-key YOUR_KEY`.',
                code='PROVIDER_UNAVAILABLE', retryable=True)
        provider_type = 'qloo'
    else:
        if not _is_qloo_configured():
            raise QlooHarnessError(
                'No Qloo API key is configured, so there is no live evidence to answer with. '
                'Set QLOO_API_KEY in .env, or run `qloo config set api-key YOUR_KEY`.',
                code='PROVIDER_UNAVAILABLE', retryable=True)
        provider_type = 'qloo'

    if provider_type not in _cached_providers:
        if provider_type == 'qloo':
            _cached_providers['qloo'] = QlooHarnessProvider(command=os.getenv('QLOO_CLI', 'qloo'))
        else:
            _cached_providers['mock'] = MockCultureProvider()
    return _cached_providers[provider_type]

def create_provider() -> CultureProvider:
    return get_provider()


def current_provider() -> CultureProvider:
    """The provider, resolved on demand.

    Resolved lazily rather than at import, so the server can still start and
    answer /api/health when no Qloo key is configured. The routes ask for it
    per request, and a missing key becomes a stated 503 rather than a server
    that will not start.
    """
    return get_provider()
