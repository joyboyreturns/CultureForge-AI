from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from uuid import uuid4

from .comparison import compare_audiences as compare_audiences_native
from .comparison import rank_entities, recompose
from .evidence_store import get_store
from .models import CompareRequest, GenerateResponse, ProjectRequest, RecomposeRequest
from .providers import QlooHarnessError, QlooHarnessProvider, get_provider
from .research import registry as research_registry, start_research

app = FastAPI(title='CultureForge API', version='0.1.0')

# The frontend is served from a different port than the API whenever it is
# hosted as static files, so allow the usual local development origins. The
# Qloo credential never leaves the backend, so this exposes only the read-only
# project API.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r'http://(localhost|127\.0\.0\.1)(:\d+)?',
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['Content-Type'],
)


@app.get('/api/health')
def health():
    current_provider = get_provider()
    return {
        'status': 'ok',
        'dataMode': 'live' if current_provider.__class__.__name__ == 'QlooHarnessProvider' else 'mock',
    }


@app.get('/health', include_in_schema=False)
def health_alias():
    """Alias for tools that probe a conventional /health path."""
    return health()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a readable message instead of FastAPI's default error list.

    The frontend renders `detail` directly as the user-facing message, so a
    list of validation objects would be shown as a raw Python dict dump.
    """
    problems = []
    for error in exc.errors():
        location = '.'.join(str(part) for part in error.get('loc', []) if part != 'body')
        message = error.get('msg', 'Invalid value')
        problems.append(f'{location}: {message}' if location else message)
    return JSONResponse(status_code=422, content={'detail': '; '.join(problems) or 'Invalid request.'})


@app.post('/api/projects/generate', response_model=GenerateResponse)
def generate(project: ProjectRequest) -> GenerateResponse:
    try:
        return get_provider().generate(project)
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post('/api/projects/compare')
def compare(request: CompareRequest) -> dict:
    """Re-research the same brief for a different audience.

    The scenario lab needs real evidence for the alternative audience, not a
    locally computed score shift. This runs the same two Qloo workflows against
    the new audience and returns the composed directions and their evidence.
    """
    try:
        provider = get_provider()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not isinstance(provider, QlooHarnessProvider):
        raise HTTPException(status_code=409, detail='Live comparison needs the Qloo provider. Run the backend in qloo mode.')
    try:
        project = request.project.model_copy(update={'audience': request.audience})
        response = provider.generate(project)
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        'audience': request.audience,
        'concepts': [concept.model_dump() for concept in response.concepts],
        'evidence': [item.model_dump() for item in response.evidence],
        'signals': [signal.model_dump() for signal in response.signals],
        'trace': [event.model_dump() for event in response.trace],
        'delivery': response.delivery.model_dump() if response.delivery else None,
        'resolvedTags': response.provenance.resolved_tags if response.provenance else [],
        'notice': response.notice,
    }


# ---------------------------------------------------------------------------
# The research agent
# ---------------------------------------------------------------------------
@app.post('/api/research/runs')
def start_run(request: CompareRequest) -> dict:
    """Start a bounded research run and return its id straight away."""
    run = start_research(request.project, request.audience, request.seedTagIds)
    return {'runId': run.id, 'status': run.status}


@app.get('/api/research/runs/{run_id}')
def run_status(run_id: str) -> dict:
    run = research_registry.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail='That research run is no longer available.')
    return run.snapshot()


@app.get('/api/research/runs')
def recent_runs() -> dict:
    return {'runs': research_registry.recent()}


# ---------------------------------------------------------------------------
# Confirmed taste seeds
# ---------------------------------------------------------------------------
@app.post('/api/taste/resolve')
def resolve_taste(request: CompareRequest) -> dict:
    """Resolve an audience into candidate Qloo seeds, before any research runs.

    The founder confirms these, so the research queries what they meant rather
    than a guess the app made for them.
    """
    try:
        provider = get_provider()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not isinstance(provider, QlooHarnessProvider):
        raise HTTPException(status_code=409, detail='Resolving taste seeds needs the Qloo provider.')
    try:
        # The same limit the provider uses, so this shares one cache entry and
        # costs no upstream call when the audience has been resolved before.
        envelope, cached, _requests = provider.run_workflow_cached('find_tags', {
            'query': f'{request.project.businessType} {request.audience}'.strip(), 'limit': 3,
        })
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    candidates = []
    for row in provider.rows(envelope):
        tag_id = provider.tag_id(row)
        if not tag_id:
            continue
        # Qloo's own name for the signal, so the founder confirms the same
        # wording they will later see attached to the evidence.
        name = row.get('name')
        candidates.append({
            'tagId': tag_id,
            'label': name if isinstance(name, str) and name.strip()
                     else tag_id.rsplit(':', 1)[-1].replace('_', ' ').strip().capitalize(),
            'popularity': row.get('popularity'),
            'type': row.get('type'),
        })
    return {
        'audience': request.audience,
        'candidates': candidates,
        'cached': cached,
        'unresolved': envelope.get('query_intent', {}).get('unresolved', []),
    }


# ---------------------------------------------------------------------------
# Snapshots: an exploration that can be reopened exactly as it was shown
# ---------------------------------------------------------------------------
@app.post('/api/explorations/share')
def share_exploration(payload: dict) -> dict:
    """Freeze an exploration so a judge can open exactly what was shown."""
    snapshot_id = f'snap-{uuid4().hex[:12]}'
    get_store().save_snapshot(snapshot_id, payload)
    return {'snapshotId': snapshot_id}


@app.get('/api/snapshots/{snapshot_id}')
def read_snapshot(snapshot_id: str) -> dict:
    payload = get_store().get_snapshot(snapshot_id)
    if not payload:
        raise HTTPException(status_code=404, detail='That snapshot is no longer available.')
    return payload


# ---------------------------------------------------------------------------
# Native Qloo comparisons, ranking, and recomposition
# ---------------------------------------------------------------------------
@app.post('/api/projects/compare/audiences')
def compare_audiences(request: dict) -> dict:
    """Qloo's own A/B between two groups of entities."""
    group_a = [str(x) for x in (request.get('groupA') or [])]
    group_b = [str(x) for x in (request.get('groupB') or [])]
    try:
        return compare_audiences_native(
            group_a, group_b,
            target_type=str(request.get('targetType') or 'place'),
            limit=int(request.get('limit') or 12),
        )
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post('/api/projects/rank')
def rank_anchors(request: dict) -> dict:
    """Rank real Qloo entities by affinity for a signal set."""
    options = [str(x) for x in (request.get('options') or [])]
    signals = [str(x) for x in (request.get('signals') or [])]
    include_tags = [str(x) for x in (request.get('includeTags') or [])]
    try:
        return rank_entities(
            options,
            signals=signals or None,
            include_tags=include_tags or None,
            option_type=str(request.get('optionType') or 'place'),
            signal_location=request.get('signalLocation') or None,
            demographic=request.get('demographic') or None,
            limit=int(request.get('limit') or 6),
        )
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post('/api/projects/recompose')
def recompose_route(request: RecomposeRequest) -> dict:
    """Rebuild the directions without the given evidence, using no new call."""
    try:
        return recompose(
            request.project,
            exclude_entity_ids=request.excludeEntityIds,
            exclude_tag_ids=request.excludeTagIds,
        )
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
