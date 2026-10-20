from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from typing import Optional
from uuid import uuid4

from .comparison import compare_audiences as compare_audiences_native
from .comparison import rank_entities, recompose
from .evidence_store import get_store
from .models import (CompareAudiencesRequest, CompareRequest, ErrorBody, ErrorResponse,
                     GenerateResponse, ProjectRequest, RankRequest, RecomposeRequest,
                     ShareRequest)
from .providers import (COMPOSER_VERSION, QLOO_WORKFLOWS, QlooHarnessError,
                        QlooHarnessProvider, get_provider)
from .research import registry as research_registry, start_research

app = FastAPI(
    title='CultureForge API',
    version='0.2.0',
    description=(
        'CultureForge turns a business brief into evidence-backed directions, using Qloo. '
        'Every response is either a result or the same error envelope: '
        '{"detail": "<a sentence>", "error": {"code", "message", "retryable", "details"}, "requestId"}.'
    ),
    openapi_tags=[
        {'name': 'brief', 'description': 'The brief, its directions, and the evidence behind them.'},
        {'name': 'evidence', 'description': 'Qloo workflows run directly, and their answers.'},
        {'name': 'agent', 'description': 'The research agent and its runs.'},
        {'name': 'sharing', 'description': 'Frozen explorations that reopen exactly.'},
        {'name': 'platform', 'description': 'Health, keys, and metering.'},
    ],
)

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


# ---------------------------------------------------------------------------
# The error envelope
#
# Every failure answers the same way, so a caller can branch on the code
# rather than on the wording. `detail` stays because the studio renders that
# string straight to the founder.
# ---------------------------------------------------------------------------

#: How each failure maps onto a status code.
ERROR_STATUS = {
    'INVALID_REQUEST': 422,
    'INVALID_UPSTREAM_REQUEST': 422,
    'NEEDS_INPUT': 422,
    'NO_EVIDENCE': 422,
    'NO_CACHED_EVIDENCE': 409,
    'RATE_LIMITED': 429,
    'ALLOWANCE_EXHAUSTED': 429,
    'QUOTA_EXHAUSTED': 503,
    'PROVIDER_UNAVAILABLE': 503,
    'UPSTREAM_TIMEOUT': 504,
    'RUN_TIMEOUT': 504,
    'UPSTREAM_UNAUTHENTICATED': 502,
    'UPSTREAM_MALFORMED': 502,
    'UPSTREAM_REJECTED': 502,
}


def error_response(code: str, message: str, *, status: Optional[int] = None,
                   retryable: bool = False, details: Optional[dict] = None) -> JSONResponse:
    """The one shape every failure uses."""
    payload = ErrorResponse(
        detail=message,
        error=ErrorBody(code=code, message=message, retryable=retryable, details=details or {}),
        requestId=f'req-{uuid4().hex[:12]}',
    )
    return JSONResponse(status_code=status or ERROR_STATUS.get(code, 502),
                        content=payload.model_dump())


@app.exception_handler(QlooHarnessError)
async def qloo_error_handler(request: Request, exc: QlooHarnessError):
    return error_response(exc.code, str(exc), retryable=exc.retryable, details=exc.details)


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else 'The request could not be completed.'
    code = {400: 'INVALID_REQUEST', 401: 'UNAUTHORIZED', 403: 'FORBIDDEN',
            404: 'NOT_FOUND', 405: 'METHOD_NOT_ALLOWED', 409: 'CONFLICT',
            429: 'RATE_LIMITED', 503: 'UNAVAILABLE'}.get(exc.status_code, 'REQUEST_FAILED')
    return error_response(code, message, status=exc.status_code)


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
    return error_response('VALIDATION_FAILED', '; '.join(problems) or 'Invalid request.',
                          status=422, details={'fields': [p.split(':')[0] for p in problems if ':' in p]})


@app.get('/api/health', tags=['platform'], summary='Which provider is active, and what it can do')
def health():
    current_provider = get_provider()
    live = current_provider.__class__.__name__ == 'QlooHarnessProvider'
    return {
        'status': 'ok',
        'dataMode': 'live' if live else 'mock',
        'version': app.version,
        'workflows': list(QLOO_WORKFLOWS) if live else [],
        'composerVersion': COMPOSER_VERSION,
    }


@app.get('/health', include_in_schema=False)
def health_alias():
    """Alias for tools that probe a conventional /health path."""
    return health()


@app.post('/api/projects/generate', response_model=GenerateResponse, tags=['brief'],
          summary='Answer a brief with evidence-backed directions')
def generate(project: ProjectRequest) -> GenerateResponse:
    """Resolve the brief into cultural signals, retrieve the local evidence,
    and compose three directions that each name the venues they came from.

    A brief that has been answered before is served from held evidence and
    costs no upstream request. The delivery says which it was.
    """
    return get_provider().generate(project)


@app.post('/api/projects/compare', tags=['brief'],
          summary='Re-research the same brief for a different audience')
def compare(request: CompareRequest) -> dict:
    """Re-research the same brief for a different audience.

    The scenario lab needs real evidence for the alternative audience, not a
    locally computed score shift. This runs the same two Qloo workflows against
    the new audience and returns the composed directions and their evidence.
    """
    provider = get_provider()
    if not isinstance(provider, QlooHarnessProvider):
        raise HTTPException(status_code=409, detail='Live comparison needs the Qloo provider. Run the backend in qloo mode.')
    project = request.project.model_copy(update={'audience': request.audience})
    response = provider.generate(project)
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
@app.post('/api/research/runs', status_code=202, tags=['agent'],
          summary='Start a research run and get its id straight away')
def start_run(request: CompareRequest, response: Response) -> dict:
    """Start a bounded research run and return its id straight away.

    202 Accepted: the work continues in the background. Poll
    `GET /api/research/runs/{runId}` for the steps it takes.
    """
    run = start_research(request.project, request.audience, request.seedTagIds)
    response.headers['Location'] = f'/api/research/runs/{run.id}'
    return {'runId': run.id, 'status': run.status, 'statusUrl': f'/api/research/runs/{run.id}'}


@app.get('/api/research/runs/{run_id}', tags=['agent'], summary='The state of one research run')
def run_status(run_id: str) -> dict:
    run = research_registry.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail='That research run is no longer available.')
    return run.snapshot()


@app.get('/api/research/runs', tags=['agent'], summary='The recent research runs')
def recent_runs() -> dict:
    return {'runs': research_registry.recent()}


# ---------------------------------------------------------------------------
# Confirmed taste seeds
# ---------------------------------------------------------------------------
@app.post('/api/taste/resolve', tags=['brief'],
          summary='Resolve an audience into the Qloo signals it maps to')
def resolve_taste(request: CompareRequest) -> dict:
    """Resolve an audience into candidate Qloo seeds, before any research runs.

    The founder confirms these, so the research queries what they meant rather
    than a guess the app made for them.
    """
    provider = get_provider()
    if not isinstance(provider, QlooHarnessProvider):
        raise HTTPException(status_code=409, detail='Resolving taste seeds needs the Qloo provider.')
    # The same limit the provider uses, so this shares one cache entry and
    # costs no upstream call when the audience has been resolved before.
    envelope, cached, _requests = provider.run_workflow_cached('find_tags', {
        'query': f'{request.project.businessType} {request.audience}'.strip(), 'limit': 3,
    })
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
@app.post('/api/explorations/share', status_code=201, tags=['sharing'],
          summary='Freeze an exploration so a shared link reopens exactly it')
def share_exploration(payload: ShareRequest, response: Response) -> dict:
    """Freeze an exploration so a judge can open exactly what was shown."""
    snapshot_id = f'snap-{uuid4().hex[:12]}'
    get_store().save_snapshot(snapshot_id, payload.model_dump())
    response.headers['Location'] = f'/api/snapshots/{snapshot_id}'
    return {'snapshotId': snapshot_id, 'url': f'/api/snapshots/{snapshot_id}'}


@app.get('/api/snapshots/{snapshot_id}', tags=['sharing'], summary='Reopen a frozen exploration')
def read_snapshot(snapshot_id: str) -> dict:
    payload = get_store().get_snapshot(snapshot_id)
    if not payload:
        raise HTTPException(status_code=404, detail='That snapshot is no longer available.')
    return payload


# ---------------------------------------------------------------------------
# Native Qloo comparisons, ranking, and recomposition
# ---------------------------------------------------------------------------
@app.post('/api/projects/compare/audiences', tags=['evidence'],
          summary="Qloo's own A/B between two groups of entities")
def compare_audiences(request: CompareAudiencesRequest) -> dict:
    """Qloo's own A/B between two groups of entities.

    Both groups must hold at least one entity, and no other field is accepted:
    the request is built from these fields alone, so Qloo never sees an
    argument the app did not intend to send.
    """
    return compare_audiences_native(
        request.groupA, request.groupB,
        target_type=request.targetType,
        limit=request.limit,
    )


@app.post('/api/projects/rank', tags=['evidence'],
          summary='Rank real Qloo entities by affinity for a signal set')
def rank_anchors(request: RankRequest) -> dict:
    """Rank real Qloo entities by affinity for a signal set.

    Qloo's `rank` workflow rejects unknown fields, so the request is built
    from these fields alone. The answer includes the signal Qloo actually
    sent, because a demographic phrase is converted on their side.
    """
    return rank_entities(
        request.options,
        signals=request.signals or None,
        include_tags=request.includeTags or None,
        option_type=request.optionType,
        signal_location=request.signalLocation,
        demographic=request.demographic,
        limit=request.limit,
    )


@app.post('/api/projects/recompose', tags=['brief'],
          summary='Rebuild the directions without a piece of the evidence')
def recompose_route(request: RecomposeRequest) -> dict:
    """Rebuild the directions without the given evidence, using no new call."""
    return recompose(
        request.project,
        exclude_entity_ids=request.excludeEntityIds,
        exclude_tag_ids=request.excludeTagIds,
    )
