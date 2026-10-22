from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import json
import os
import secrets
import time
from typing import Optional
from uuid import uuid4

from .comparison import compare_audiences as compare_audiences_native
from .comparison import rank_entities, recompose
from .challenge import DEMOGRAPHIC_CHOICES, challenge_directions, guess_demographic
from .challenge import POLICY_VERSION as CHALLENGE_POLICY_VERSION
from .challenge_probe import challenge_probe
from . import config, examples
from .evidence_store import get_store
from .reasoning import AnalysisUnavailable, analyze as analyze_evidence
from .reasoning import budget_state as analysis_budget_state
from .llm import status as llm_status
from .presentation import presentation_key
from .selector import select as select_evidence
from .models import (CompareAudiencesRequest, CompareRequest, ChallengeProbeRequest, ChallengeRequest,
                     EntityListRequest, EntityRequest, ErrorBody, ErrorResponse,
                     EvidenceAnalysisRequest,
                     EvidencePresentationRequest, GenerateResponse,
                     ChatRequest, InvestigationRequest, KeyRequest, ProfileRequest, ReportRequest, WorkspaceRequest, ProjectRequest, ProvenanceMetadata,
                     RankRequest, RecomposeRequest, ShareRequest, TrendsRequest,
                     WherePopularRequest)
from .platform import get_platform
from . import metering
from .investigation import FACET_QUESTIONS, FACETS, _bounds, _demographics, _geography_points, _workflow_for, investigate
from .providers import (COMPOSER_VERSION, QLOO_ENTITY_TYPES, QLOO_WORKFLOWS, QlooHarnessError,
                        capabilities,
                        audience_demographics_payload, brief_tags_payload, describe_payload, entity_tags_payload,
                        trends_payload, where_popular_payload,
                        QlooHarnessProvider, get_provider)
from .research import registry as research_registry, start_research

app = FastAPI(
    title='CultureForge API',
    version='0.3.0',
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

# The deployed studio is served from the same origin as the API and needs no
# CORS. Local development serves it from another port, so local origins are
# allowed; a deployment that hosts the studio elsewhere names its origins in
# CULTUREFORGE_ALLOWED_ORIGINS (comma-separated, exact). The Qloo credential
# never leaves the backend.
ALLOWED_ORIGINS = [origin.strip().rstrip('/') for origin in
                   os.getenv('CULTUREFORGE_ALLOWED_ORIGINS', '').split(',') if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
    'LIVE_DISABLED': 503,
    'BUDGET_UNAVAILABLE': 503,
    'MODEL_UNAVAILABLE': 503,
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


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    """Whatever nothing else caught still answers in the one envelope, with an id
    a person can quote, and the traceback goes to the server log."""
    import logging
    logging.getLogger('cultureforge').exception('Unhandled error on %s %s', request.method, request.url.path)
    return error_response('INTERNAL_ERROR', 'Something went wrong on the server, and nothing was changed. '
                          'Try again; if it keeps happening, quote the request id.', status=500, retryable=True)


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
    """What this server can answer with right now.

    It never raises. A missing Qloo key is a state the studio has to be able
    to read and show, so it is reported as `providerReady: false` with the
    reason, rather than as a failed request. It also says which run profile
    is active, what each budget allows (or `unlimited`), and how much
    evidence is held. It makes no upstream request.
    """
    try:
        current_provider = get_provider()
    except QlooHarnessError as exc:
        return {
            'status': 'degraded',
            'dataMode': 'live',
            'providerReady': False,
            'reason': str(exc),
            'version': app.version,
            'workflows': [],
            'composerVersion': COMPOSER_VERSION,
            'llm': llm_status(),
            **_operating_state(),
        }
    live = current_provider.__class__.__name__ == 'QlooHarnessProvider'
    return {
        'status': 'ok',
        'dataMode': 'live' if live else 'mock',
        'providerReady': live,
        'reason': None,
        'version': app.version,
        'workflows': list(QLOO_WORKFLOWS) if live else [],
        'composerVersion': COMPOSER_VERSION,
        'llm': llm_status(),
        **_operating_state(),
    }


def _operating_state() -> dict:
    """The run profile, the budgets it sets, and the evidence already held."""
    state: dict = {**config.summary()}
    state['budgets'] = {
        'qloo': QlooHarnessProvider.budget_state(),
        'llm': llm_status()['budget'],
        'analysis': analysis_budget_state(),
        'researchRunWorkflows': config.describe_limit(config.limit('RESEARCH_RUN_MAX_WORKFLOWS')),
    }
    try:
        state['cache'] = get_store().stats()
    except Exception:  # pragma: no cover - health must never raise
        state['cache'] = None
    return state


@app.get('/api/examples', tags=['brief'],
         summary='The prepared example briefs, and whether their evidence is held')
def list_examples() -> dict:
    """The briefs the studio offers as examples.

    `held` means the evidence store already has this brief's audience seeds
    and places, so running it costs no upstream request. Asking costs none.
    """
    return {'examples': examples.listing()}


@app.get('/health', include_in_schema=False)
def health_alias():
    """Alias for tools that probe a conventional /health path."""
    return health()


@app.post('/api/projects/generate', response_model=GenerateResponse, tags=['brief'],
          summary='Answer a brief with evidence-backed directions')
def generate(project: ProjectRequest, request: Request) -> GenerateResponse:
    """Resolve the brief into cultural signals, retrieve the local evidence,
    and compose three directions that each name the venues they came from.

    A brief that has been answered before is served from held evidence and
    costs no upstream request. The delivery says which it was.

    Every answer is saved to the caller's workspace, so it is still there
    after the tab closes and can be exported or handed to somebody else.
    """
    response = get_provider().generate(project)
    try:
        if request is not None:
            workspace, _prefix = resolve_workspace(request)
            get_platform().save_exploration(
                workspace['id'], response.model_dump(),
                title=f"{project.businessType} for {project.audience}",
                brief=project.model_dump(),
                project_id=response.projectId,
                delivery=response.delivery.model_dump() if response.delivery else None)
    except Exception:  # pragma: no cover - saving must never break an answer
        pass
    return response


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
# The platform: workspaces, issued keys, metering, saved explorations
#
# The studio runs in a local workspace so a founder never has to sign up for
# anything to try it. A partner calls the same API with an issued key, and
# lands in their own workspace, where everything they save is theirs.
# ---------------------------------------------------------------------------

#: The workspace the studio uses when no key is presented.
LOCAL_WORKSPACE_NAME = 'Local studio'


def resolve_workspace(request: Request) -> tuple[dict, Optional[str]]:
    """Which workspace this request belongs to, and the key prefix that opened it.

    A presented bearer key decides. Without one, the request lands in the
    local studio workspace, which is created once and reused.
    """
    header = request.headers.get('authorization', '')
    presented = header[7:].strip() if header.lower().startswith('bearer ') else ''
    if presented:
        identity = get_platform().authenticate(presented)
        if identity is None:
            raise HTTPException(status_code=401, detail='That API key is not valid, has expired, or has been revoked.')
        workspace = get_platform().workspace(identity['workspaceId'])
        if not workspace:
            raise HTTPException(status_code=403, detail='That key belongs to a workspace that no longer exists.')
        return workspace, identity['prefix']
    platform = get_platform()
    existing = next((w for w in platform.workspaces() if w['name'] == LOCAL_WORKSPACE_NAME), None)
    return existing or platform.create_workspace(LOCAL_WORKSPACE_NAME, plan='studio'), None


@app.middleware('http')
async def meter_requests(request: Request, call_next):
    """Count every API request, and every upstream call it caused.

    The two are different costs: an API request is what a partner pays for,
    and an upstream call is what the hackathon quota pays for.
    """
    started = time.monotonic()
    counter = metering.begin()
    response = await call_next(request)
    duration_ms = int((time.monotonic() - started) * 1000)
    try:
        workspace, prefix = resolve_workspace(request)
        get_platform().record_usage(
            route=request.url.path, method=request.method, status=response.status_code,
            workspace_id=workspace['id'], key_prefix=prefix,
            upstream_calls=counter[0], duration_ms=duration_ms)
    except HTTPException:
        pass
    except Exception:  # pragma: no cover - metering must never break a request
        pass
    return response


def _require_operator(request: Request) -> None:
    """Whether the caller may provision and revoke.

    These routes are for the operator, not for a founder. There is no account
    system behind them, so they are closed by default: an operator token is
    required when one is configured, and otherwise only a request from this
    machine is allowed. A key presented by a partner is not an operator
    credential — authentication is not authorisation.
    """
    token = os.getenv('CULTUREFORGE_OPERATOR_TOKEN', '').strip()
    if token:
        presented = request.headers.get('x-operator-token', '').strip()
        if not secrets.compare_digest(presented, token):
            raise HTTPException(status_code=401, detail='This route needs the operator token.')
        return
    host = request.client.host if request.client else ''
    if host not in ('127.0.0.1', '::1', 'localhost'):
        raise HTTPException(
            status_code=403,
            detail='This route is for the operator and is only open on this machine. '
                   'Set CULTUREFORGE_OPERATOR_TOKEN to open it elsewhere.')


@app.post('/api/workspaces', status_code=201, tags=['platform'],
          summary='Provision a workspace for a partner')
def create_workspace(request: Request, payload: WorkspaceRequest) -> dict:
    """Provision a workspace. The operator does this; there is no self-service
    signup, because there is no billing behind it yet."""
    _require_operator(request)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail='A workspace needs a name.')
    return get_platform().create_workspace(name, plan=payload.plan or 'partner')


@app.post('/api/workspaces/{workspace_id}/keys', status_code=201, tags=['platform'],
          summary='Issue an API key for a workspace')
def issue_key(request: Request, workspace_id: str, payload: KeyRequest) -> dict:
    """Issue an API key. The key is shown once, here, and never again."""
    _require_operator(request)
    try:
        return get_platform().issue_key(workspace_id, list(payload.scopes), expires_at=payload.expiresAt)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get('/api/workspaces/{workspace_id}/keys', tags=['platform'],
         summary='The keys issued for a workspace')
def list_keys(request: Request, workspace_id: str) -> dict:
    _require_operator(request)
    return {'keys': get_platform().keys(workspace_id)}


@app.delete('/api/workspaces/{workspace_id}/keys/{key_id}', status_code=204, tags=['platform'],
            summary='Revoke an API key')
def revoke_key(request: Request, workspace_id: str, key_id: str) -> Response:
    _require_operator(request)
    # The key has to belong to the workspace the caller named.
    if not get_platform().revoke_key(key_id, workspace_id):
        raise HTTPException(status_code=404, detail='That key does not exist.')
    return Response(status_code=204)


@app.get('/api/usage', tags=['platform'],
         summary='How much this API has been used')
def usage(days: int = 30) -> dict:
    """Metered usage: requests, and the upstream calls they caused."""
    return get_platform().usage(days=max(1, min(days, 365)))


@app.get('/api/explorations', tags=['brief'],
         summary='The explorations this workspace has saved')
def list_explorations(request: Request, limit: int = 50) -> dict:
    workspace, _prefix = resolve_workspace(request)
    return {'explorations': get_platform().explorations(workspace['id'], limit=max(1, min(limit, 200)))}


@app.get('/api/explorations/{exploration_id}', tags=['brief'],
         summary='One saved exploration, with its versions')
def read_exploration(request: Request, exploration_id: str) -> dict:
    workspace, _prefix = resolve_workspace(request)
    record = get_platform().exploration(exploration_id)
    if not record or record['workspaceId'] != workspace['id']:
        raise HTTPException(status_code=404, detail='That exploration does not exist.')
    record['result'] = get_platform().exploration_payload(exploration_id)
    return record


@app.get('/api/explorations/{exploration_id}/export', tags=['brief'],
         summary='Download an exploration as JSON or Markdown')
def export_exploration(request: Request, exploration_id: str, format: str = 'json') -> Response:
    workspace, _prefix = resolve_workspace(request)
    record = get_platform().exploration(exploration_id)
    if not record or record['workspaceId'] != workspace['id']:
        raise HTTPException(status_code=404, detail='That exploration does not exist.')
    payload = get_platform().exploration_payload(exploration_id)
    if payload is None:
        raise HTTPException(status_code=404, detail='That exploration has no saved result.')
    if format == 'markdown':
        body = render_markdown(payload)
        return Response(body, media_type='text/markdown; charset=utf-8',
                        headers={'Content-Disposition': f'attachment; filename="{exploration_id}.md"'})
    if format != 'json':
        raise HTTPException(status_code=422, detail="The export format must be 'json' or 'markdown'.")
    return Response(json.dumps(payload, indent=2, ensure_ascii=False),
                    media_type='application/json',
                    headers={'Content-Disposition': f'attachment; filename="{exploration_id}.json"'})


def render_markdown(payload: dict) -> str:
    """The export a founder would actually send to a partner."""
    brief = payload.get('project') or {}
    lines = [
        f"# {brief.get('businessType', 'CultureForge')} — {brief.get('location', 'exploration')}",
        '',
        f"- **Audience**: {brief.get('audience', 'not stated')}",
        f"- **Location**: {brief.get('location', 'not stated')}",
        f"- **Budget**: {brief.get('budget', 'not stated')}",
        f"- **Objectives**: {', '.join(brief.get('objectives') or []) or 'none stated'}",
        '',
    ]
    for concept in payload.get('concepts') or []:
        lines += [f"## {concept.get('name')}", f"*{concept.get('tagline')}*", '',
                  concept.get('description') or '', '']
        if concept.get('decisions'):
            lines.append('### Why this direction')
            for decision in concept['decisions']:
                lines.append(f"- **{decision.get('field')}**: {decision.get('proposal')}")
            lines.append('')
        if concept.get('limitations'):
            lines.append('### What this does not establish')
            lines += [f"- {line}" for line in concept['limitations']]
            lines.append('')
    if payload.get('notice'):
        lines += ['---', '', payload['notice']]
    lines += ['', '---', '', '_Produced by CultureForge AI. Cultural evidence from the Qloo API; '
              'business directions are CultureForge\'s interpretation of it._']
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Investigating a direction, and Qloo's full workflow surface
# ---------------------------------------------------------------------------

@app.post('/api/projects/investigate', tags=['evidence'],
          summary='Investigate one direction: what does it still not know?')
def investigate_route(request: InvestigationRequest) -> dict:
    """Open the questions a direction has not answered yet, and answer them.

    The founder picks the direction and the questions. Each question is one
    named Qloo workflow, the answer records which workflow produced it, and
    every call is cached so a second look costs nothing.
    """
    return investigate(
        request.project,
        direction_id=request.directionId or None,
        entity_ids=[entity for entity in request.entityIds if entity],
        within=request.within or request.project.location or 'United States',
        facets=list(request.facets),
        seed_tag_ids=list(request.seedTagIds) or None,
        reference=request.reference or None,
    )


@app.get('/api/facets', tags=['evidence'], summary='The questions an investigation can open')
def list_facets() -> dict:
    """What the founder can choose to have investigated, in plain language."""
    return {
        'facets': [
            {'id': facet, 'workflow': _workflow_for(facet), 'question': FACET_QUESTIONS[facet]}
            for facet in FACETS
        ],
    }


# ---------------------------------------------------------------------------
# Qloo's workflows, one route each, so a partner can reach the full surface
# ---------------------------------------------------------------------------

@app.get('/api/qloo/workflows', tags=['evidence'],
         summary='The Qloo workflows this app can reach, and how to call them')
def qloo_workflows() -> dict:
    """A machine-readable capability matrix.

    Every Qloo workflow has its own contract, and each rejects fields it does
    not know — the field carrying the entity type is not the same field in
    every workflow, and `rank` takes no limit at all. This is the contract,
    so a partner can read it rather than discover it by getting it wrong.
    """
    return {
        'workflows': capabilities(),
        'entityTypes': list(QLOO_ENTITY_TYPES),
        'note': ('Every workflow is read-only, cached, and metered. The delivery on any '
                 'result says whether the evidence was freshly fetched or already held.'),
    }


@app.post('/api/qloo/describe', tags=['evidence'], summary='Resolve one entity and describe it')
def qloo_describe(request: EntityRequest) -> dict:
    """Qloo's `describe` workflow: one named entity, and the metadata Qloo holds."""
    provider = QlooHarnessProvider()
    envelope, cached, requests = provider.run_workflow_cached(
        'describe', describe_payload(request.entity, request.entityType))
    return _workflow_response('describe', envelope, cached, requests)


@app.post('/api/qloo/entity-tags', tags=['evidence'], summary='The concepts that characterise entities')
def qloo_entity_tags(request: EntityListRequest) -> dict:
    """Qloo's `entity_tags` workflow."""
    entities = [entity for entity in request.entities if entity]
    if not entities:
        raise HTTPException(status_code=422, detail='Name at least one entity.')
    provider = QlooHarnessProvider()
    envelope, cached, requests = provider.run_workflow_cached(
        'entity_tags', entity_tags_payload(entities, request.entityType, request.limit))
    return _workflow_response('entity_tags', envelope, cached, requests)


@app.post('/api/qloo/where-popular', tags=['evidence'],
          summary='Where an entity has strong affinity, as geographic cells')
def qloo_where_popular(request: WherePopularRequest) -> dict:
    """Qloo's `where_popular` workflow.

    The answer is a set of geographic cells for interest mapping. They are not
    the coordinates of venues.
    """
    provider = QlooHarnessProvider()
    envelope, cached, requests = provider.run_workflow_cached(
        'where_popular', where_popular_payload(request.entity, request.within, request.entityType, request.limit))
    response = _workflow_response('where_popular', envelope, cached, requests)
    points = _geography_points(envelope)
    response['points'] = points
    response['bounds'] = _bounds(points)
    response['note'] = ('Qloo supplies geographic popularity cells for interest mapping. '
                        'These are distinct from precise venue coordinates.')
    return response


@app.post('/api/qloo/audience-demographics', tags=['evidence'],
          summary='The demographic index for one entity')
def qloo_audience_demographics(request: EntityRequest) -> dict:
    """Qloo's `audience_demographics` workflow."""
    provider = QlooHarnessProvider()
    envelope, cached, requests = provider.run_workflow_cached(
        'audience_demographics', audience_demographics_payload(request.entity, request.entityType, request.limit))
    response = _workflow_response('audience_demographics', envelope, cached, requests)
    response['demographics'] = _demographics(envelope)
    return response


@app.post('/api/qloo/trends', tags=['evidence'],
          summary='Popularity over time for one to five entities')
def qloo_trends(request: TrendsRequest) -> dict:
    """Qloo's `trends` workflow."""
    entities = [entity for entity in request.entities if entity]
    if not entities:
        raise HTTPException(status_code=422, detail='Name at least one entity.')
    provider = QlooHarnessProvider()
    envelope, cached, requests = provider.run_workflow_cached('trends', trends_payload(
        entities, request.entityType or 'place',
        request.startDate, request.endDate, request.limit))
    return _workflow_response('trends', envelope, cached, requests)


def _workflow_response(operation: str, envelope: dict, cached: bool, requests: int) -> dict:
    """One shape for every Qloo workflow answer, so a caller can read them all
    the same way."""
    execution = envelope.get('execution') if isinstance(envelope.get('execution'), dict) else {}
    provenance = envelope.get('provenance') if isinstance(envelope.get('provenance'), dict) else {}
    return {
        'workflow': operation,
        'status': envelope.get('status', 'ok'),
        'results': envelope.get('results') or [],
        'resultCount': len(envelope.get('results') or []) if isinstance(envelope.get('results'), list) else 0,
        'cached': cached,
        'transportRequests': requests,
        'durationMs': execution.get('duration_ms') if isinstance(execution.get('duration_ms'), int) else None,
        'endpoint': provenance.get('endpoint'),
        'documentation': provenance.get('documentation'),
        'queryIntent': envelope.get('query_intent'),
    }


# ---------------------------------------------------------------------------
# The research agent
# ---------------------------------------------------------------------------
@app.post('/api/research/runs', status_code=202, tags=['agent'],
          summary='Start a research run and get its id straight away')
def start_run(request: CompareRequest, response: Response, http_request: Request) -> dict:
    """Start a bounded research run and return its id straight away.

    202 Accepted: the work continues in the background. Poll
    `GET /api/research/runs/{runId}` for the steps it takes.

    The run is answered into the caller's workspace, so the exploration it
    produces is saved the same way the direct route saves one.
    """
    workspace, _prefix = resolve_workspace(http_request)
    run = start_research(request.project, request.audience, request.seedTagIds,
                         workspace_id=workspace['id'])
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
    envelope, cached, _requests = provider.run_workflow_cached(
        'find_tags', brief_tags_payload(request.project.businessType, request.audience))
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
    snapshot_id = get_platform().save_share(payload.model_dump())
    response.headers['Location'] = f'/api/snapshots/{snapshot_id}'
    return {'snapshotId': snapshot_id, 'url': f'/api/snapshots/{snapshot_id}'}


@app.get('/api/snapshots/{snapshot_id}', tags=['sharing'], summary='Reopen a frozen exploration')
def read_snapshot(snapshot_id: str) -> dict:
    # The platform store is the durable one; the evidence store still holds
    # snapshots taken before the platform existed.
    payload = get_platform().share(snapshot_id) or get_store().get_snapshot(snapshot_id)
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


def _revision_response(request: ChallengeRequest):
    """The exploration as it stands, when the app sent it.

    The test has to answer about the evidence on screen. A brief that was
    recomposed, or an audience whose seeds were confirmed by hand, has an
    answer that a fresh generation from the brief would not reproduce — and
    a verdict about a different exploration would be a verdict about nothing.
    """
    revision = request.revision
    if revision is None or not revision.evidence or not revision.concepts:
        return None
    return GenerateResponse(
        projectId='cf-revision',
        project=request.project,
        concepts=revision.concepts,
        signals=[],
        dataMode='live',
        conceptMode='evidence_composed',
        notice='Tested against the exploration on screen.',
        provenance=ProvenanceMetadata(source='Qloo API', resolved_tags=revision.resolvedTags),
        evidence=revision.evidence,
        trace=[],
    )


@app.post('/api/projects/challenge', tags=['evidence'],
          summary='Test the directions against the local evidence')
def challenge_directions_route(request: ChallengeRequest) -> dict:
    """Test a direction against the local evidence — and let the answer be no.

    The brief is re-composed from evidence that is already held, so this
    costs no Qloo call of its own until the two checks run. The verdict is
    about local cultural fit and nothing else, and says so.
    """
    provider = get_provider()
    if not isinstance(provider, QlooHarnessProvider):
        raise HTTPException(status_code=409, detail='Testing a direction needs the Qloo provider.')
    response = _revision_response(request)
    if response is None:
        # No revision was sent, so there is nothing on screen to test. The
        # brief is composed from the evidence already held.
        response = provider.generate(request.project)
    return challenge_directions(request.project, response, request.directionId or None,
                                request.anchorEntityId or None, request.demographic or None)


@app.post('/api/chat', tags=['agent'],
          summary='Ask the evidence a follow-up question; every claim cites Qloo IDs')
def ask_the_evidence(request: ChatRequest) -> dict:
    """Answer from the exploration's own evidence, plus at most three Qloo
    workflows the model can justify. Claims that cite anything not observed,
    or state numbers of their own, are rejected; with none left the answer is
    a refusal. Needs the model gateway; without it this is a 503."""
    from .chat import ChatUnavailable, ask
    try:
        return ask(request)
    except ChatUnavailable as exc:
        return error_response(exc.code, str(exc), retryable=True)


@app.post('/api/report/pdf', tags=['brief'],
          summary='The exploration as a client-ready PDF',
          responses={200: {'content': {'application/pdf': {}}}})
def report_pdf(request: ReportRequest) -> Response:
    """Cover, audience seeds, directions with their cited evidence, verdicts,
    the evidence table with Qloo IDs, held interest cells and the limits.
    Makes no Qloo or model request."""
    from .report_pdf import build_pdf
    content = build_pdf(request.result, request.challenge)
    name = ''.join(ch for ch in request.result.projectId if ch.isalnum() or ch == '-')[:40] or 'exploration'
    return Response(content=content, media_type='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename="cultureforge-{name}.pdf"'})


@app.post('/api/profile/propose', tags=['evidence'],
          summary='The demographic profile the evidence test would rank against')
def propose_profile(request: ProfileRequest) -> dict:
    """Shown before the test runs, so a default is never applied silently.

    `named` says whether the brief named this demographic; when it did not,
    the profile is a default and the screen says so. Costs no Qloo request.
    """
    demographic, named = guess_demographic(request.audience)
    return {'demographic': demographic, 'named': named, 'choices': list(DEMOGRAPHIC_CHOICES),
            'policyVersion': CHALLENGE_POLICY_VERSION}


@app.post('/api/projects/challenge-probe', tags=['evidence'],
          summary='Exclude one cited place and retrieve bounded replacements')
def challenge_probe_route(request: ChallengeProbeRequest) -> dict:
    """Run one cached Insights exclusion probe against the on-screen direction.

    This is reported separately from the anchor-fit verdict. The probe does
    not revise the direction automatically, and an empty bounded result is
    unresolved rather than negative evidence.
    """
    provider = get_provider()
    if not isinstance(provider, QlooHarnessProvider):
        raise HTTPException(status_code=409, detail='A replacement probe needs the Qloo provider.')
    return challenge_probe(request, provider)


@app.post('/api/projects/analyze', tags=['evidence'],
          summary='Compare directions using the Qloo evidence already on screen')
def analyze_evidence_route(request: EvidenceAnalysisRequest) -> dict:
    """Run one bounded, explicit model analysis without issuing a Qloo call."""
    try:
        return analyze_evidence(request).model_dump()
    except AnalysisUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post('/api/evidence/presentation', tags=['evidence'],
          summary='Let the configured model select which of Qloo\'s own words to lead with')
def evidence_presentation_route(request: EvidencePresentationRequest) -> dict:
    """Choose from the returned evidence what to show first.

    The model may only return ids. The server renders its own strings, so a
    selection can never put a word the API did not return on the screen. A
    selection that does not pass the validation is dropped, and the rules
    stay in place.
    """
    evidence = [item.model_dump() for item in request.evidence]
    key = presentation_key(evidence)
    store = get_store()
    held = store.get(f'presentation:{key}')
    if held is not None:
        return {**held, 'cached': True}
    report = select_evidence(evidence)
    if report.get('source') == 'model':
        # A selection is held. A failure is not, so the next look tries again.
        store.put(f'presentation:{key}', report, transport_requests=0)
    return {**report, 'cached': False}


@app.post('/api/projects/recompose', tags=['brief'],
          summary='Rebuild the directions without a piece of the evidence')
def recompose_route(request: RecomposeRequest) -> dict:
    """Rebuild the directions without the given evidence, using no new call."""
    return recompose(
        request.project,
        exclude_entity_ids=request.excludeEntityIds,
        exclude_tag_ids=request.excludeTagIds,
    )


# Register last so frontend files never shadow the typed API routes.
if os.getenv('CULTUREFORGE_STATIC_DIR'):
    from .web import mount_frontend
    mount_frontend(app, os.environ['CULTUREFORGE_STATIC_DIR'])
