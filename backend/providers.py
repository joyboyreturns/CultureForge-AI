"""Culture data providers: transparent sample data or the official Qloo harness."""
from __future__ import annotations
from abc import ABC, abstractmethod
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

from .models import Concept, CulturalSignal, GenerateResponse, ProjectRequest, ProvenanceMetadata

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
    """
    CACHE_TTL_SECONDS = 24 * 60 * 60
    CACHE_MAX_ENTRIES = 128

    def __init__(self, command: str = 'qloo', timeout_seconds: int = 45):
        self.command = command
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, tuple[float, GenerateResponse]] = {}
        self._lock = threading.Lock()

    def _run_workflow(self, operation: str, payload: dict) -> dict:
        executable = shutil.which(self.command)
        if not executable:
            raise QlooHarnessError('Qloo provider is selected but the qloo CLI is not installed. Install @qloo/qloo-harness and complete qloo setup.')
        # The CLI accepts a request file; using a mode-0600 temporary file avoids putting
        # audience text in shell arguments and avoids leaking it to process listings.
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json', delete=False) as request_file:
                json.dump(payload, request_file)
                request_path = request_file.name
            os.chmod(request_path, 0o600)
            completed = subprocess.run(
                [executable, 'exec', operation, '--input-file', request_path],
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
                # Return a fresh project ID and the current request alongside cached Qloo data.
                return cached[1].model_copy(update={'projectId': f'cf-{uuid4().hex[:10]}', 'project': project, 'concepts': MockCultureProvider().generate(project).concepts})
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

        # Concept cards and fit scores remain sample templates; Qloo affinities are shown
        # separately and are never converted into fabricated audience-fit percentages.
        sample = MockCultureProvider().generate(project)
        response = GenerateResponse(
            projectId=f'cf-{uuid4().hex[:10]}', project=project,
            concepts=sample.concepts, signals=signals, dataMode='live', conceptMode='sample',
            notice='Qloo aggregate signals are live. Concept narratives and fit scores remain illustrative sample templates.',
            provenance=ProvenanceMetadata(source='Qloo API', endpoint='qloo exec find_tags → recommend', documentation='https://github.com/qloo/qloo-hackathon-kit', resolved_tags=matched_tags),
        )
        with self._lock:
            if len(self._cache) >= self.CACHE_MAX_ENTRIES:
                oldest_key = min(self._cache, key=lambda key: self._cache[key][0])
                self._cache.pop(oldest_key, None)
            self._cache[cache_key] = (time.monotonic(), response)
        return response

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
