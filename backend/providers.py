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
from uuid import uuid4

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .concept_composer import compose
from .models import (Concept, CulturalSignal, Decision, Delivery, Evidence, ExperienceMoment,
                      GenerateResponse, ProjectRequest, ProvenanceMetadata, TraceEvent)

class CultureProvider(ABC):
    @abstractmethod
    def generate(self, project: ProjectRequest) -> GenerateResponse:
        """Return concepts and provenance-aware cultural signals."""

class MockCultureProvider(CultureProvider):
    """Clearly illustrative prototype content. No Qloo calls are made."""
    def generate(self, project: ProjectRequest) -> GenerateResponse:
        from .mock_generator import generate_mock
        return generate_mock(project)

class QlooHarnessError(RuntimeError):
    """A safe-to-display provider failure; deliberately contains no CLI output or secrets."""

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
            raise QlooHarnessError('Qloo provider is selected but neither scripts/qloo_exec.mjs nor the qloo CLI is available. Install @qloo/qloo-harness and complete qloo setup.')
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
                    'hackathon API quota. Raise QLOO_MAX_CALLS_PER_HOUR or QLOO_MAX_CALLS_PER_DAY to allow more.'
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
            raise QlooHarnessError('Qloo request timed out. Try again later.') from exc
        except OSError as exc:
            raise QlooHarnessError('Unable to start the Qloo CLI.') from exc
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
            if code == 'QLOO_RATE_LIMITED':
                raise QlooHarnessError('Qloo rate limited this key. Wait before retrying; live signals are temporarily unavailable.')
            if code == 'QLOO_AUTH':
                raise QlooHarnessError('Qloo rejected the credential. Check the API key and the base URL.')
            raise QlooHarnessError('Qloo rejected the request. Check the backend credential and CLI status.')
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise QlooHarnessError('Qloo CLI returned an unreadable response.') from exc
        if not isinstance(result, dict):
            raise QlooHarnessError('Qloo CLI returned an unexpected response shape.')
        return result

    @staticmethod
    def _rows(envelope: dict) -> list[dict]:
        rows = envelope.get('results', [])
        if isinstance(rows, dict):
            rows = rows.get('entities', rows.get('tags', []))
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    @staticmethod
    def _tag_id(row: dict) -> str | None:
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

    def generate(self, project: ProjectRequest) -> GenerateResponse:
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
                )
                return cached[1].model_copy(update={
                    'projectId': f'cf-{uuid4().hex[:10]}',
                    'project': project,
                    'delivery': delivery,
                })
            if cached:
                self._cache.pop(cache_key, None)

        query = f'{project.businessType} {project.audience}'.strip()
        tag_result = self._run_workflow('find_tags', {'query': query, 'limit': 3})
        if tag_result.get('status') == 'needs_input':
            raise QlooHarnessError('Qloo needs a clearer cultural seed. Refine the audience description and try again.')
        matched_tags = [tag for row in self._rows(tag_result) if (tag := self._tag_id(row))][:3]
        if not matched_tags:
            raise QlooHarnessError('Qloo did not resolve any cultural tags for this audience. Refine the description and try again.')

        recommendations = self._run_workflow('recommend', {
            'target_type': 'place', 'signal_tags': matched_tags,
            'signal_location': project.location, 'limit': 5,
        })
        if recommendations.get('status') == 'needs_input':
            raise QlooHarnessError('Qloo needs a clearer location or cultural seed. Refine the project details and try again.')
        rows = self._rows(recommendations)
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
            raise QlooHarnessError('Qloo returned no usable recommendation results for this project.')

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
        trace.append(tag_trace)

        for tag in matched_tags:
            evidence_id = f'ev-tag-{len(evidence)}'
            tag_evidence_ids[tag] = evidence_id
            evidence.append(Evidence(
                id=evidence_id, kind='tag', label=self._tag_label(tag), tagId=tag,
                traceId=tag_trace.id, description='Audience seed resolved by Qloo from the founder’s audience description.',
            ))

        entity_trace = self._trace_event('retrieve-local-evidence', 'recommend', recommendations, len(rows))
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
            delivery=Delivery(kind='fresh', acquiredAt=acquired_at, servedAt=datetime.now(timezone.utc).isoformat(),
                              expiresAt=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()),
        )
        with self._lock:
            if len(self._cache) >= self.CACHE_MAX_ENTRIES:
                oldest_key = min(self._cache, key=lambda key: self._cache[key][0])
                self._cache.pop(oldest_key, None)
            self._cache[cache_key] = (time.monotonic(), response)
        return response

    @staticmethod
    def _tag_label(tag_id: str) -> str:
        return tag_id.rsplit(':', 1)[-1].replace('_', ' ').strip().capitalize()

    @staticmethod
    def _trace_event(step: str, workflow: str, envelope: dict, result_count: int) -> TraceEvent:
        """Build a trace event from the harness execution block."""
        execution = envelope.get('execution') if isinstance(envelope.get('execution'), dict) else {}
        provenance = envelope.get('provenance') if isinstance(envelope.get('provenance'), dict) else {}
        endpoint = provenance.get('endpoint')
        detail = f'Qloo {workflow} → {endpoint}' if endpoint else f'Qloo {workflow}'
        return TraceEvent(
            id=f'trace-{workflow}-{step}',
            step=step, workflow=workflow,
            status='ok' if envelope.get('status', 'ok') == 'ok' else 'needs_input',
            durationMs=execution.get('duration_ms') if isinstance(execution.get('duration_ms'), int) else None,
            correlationId=execution.get('correlation_id') if isinstance(execution.get('correlation_id'), str) else None,
            resultCount=result_count, detail=detail,
            acquiredAt=datetime.now(timezone.utc).isoformat(),
        )

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
            investment='Derived from live Qloo evidence',
            signals=list(composed.signals),
            accent=composed.accent,
            image=composed.image or '',
            direction=str(index + 1).zfill(2),
            imageAlt=composed.image_alt,
            personality=composed.personality,
            audienceRationale=composed.positioning,
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
    elif selected == 'qloo' or _is_qloo_configured():
        provider_type = 'qloo'
    else:
        provider_type = 'mock'

    if provider_type not in _cached_providers:
        if provider_type == 'qloo':
            _cached_providers['qloo'] = QlooHarnessProvider(command=os.getenv('QLOO_CLI', 'qloo'))
        else:
            _cached_providers['mock'] = MockCultureProvider()
    return _cached_providers[provider_type]

def create_provider() -> CultureProvider:
    return get_provider()

provider: CultureProvider = create_provider()
