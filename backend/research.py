"""A bounded, observable research agent.

Not a narration of progress: a real state machine whose next step depends on
the last result, with a stopping rule and a call budget.

    resolve  -> the founder's audience becomes confirmed Qloo seeds
    retrieve -> local evidence for the brief
    evaluate -> is the evidence strong enough to support distinct directions?
    compose  -> build the directions, or ask the founder to clarify

Every step appends a real trace event carrying the duration and correlation id
the Qloo harness reported. A run that cannot proceed stops and says why rather
than guessing. A run that exceeds its allowance stops and says that.

No LLM is required, and none is assumed: the decisions here are deterministic
rules over the API's own responses.
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Optional

from . import config
from .evidence_store import known_location
from .agent import run_agent
from .models import AgentReport, ProjectRequest, TraceEvent
from .intent_report import build as build_intent_report, idea_alternatives, resolve_tag
from .providers import (QlooHarnessError, QlooHarnessProvider, brief_places_retrieval_payload,
                        brief_tags_payload, brief_category_payload, select_category_tag, mark_reused)

# How many Qloo workflows a cold research run may spend is set by the run
# profile (RESEARCH_RUN_MAX_WORKFLOWS): a count in dev, and none in judging,
# where the timeout below is what bounds a run.
_FROM_PROFILE = object()
# A run is abandoned if it takes longer than this.
DEFAULT_RUN_TIMEOUT_SECONDS = 420

STATUS_RUNNING = 'running'
STATUS_COMPLETE = 'complete'
STATUS_CLARIFY = 'clarify'
STATUS_FAILED = 'failed'


class ResearchRun:
    """One research run, and the trace it produced."""

    def __init__(self, project: ProjectRequest, audience: Optional[str] = None,
                 workspace_id: Optional[str] = None):
        self.id = f'run-{uuid.uuid4().hex[:12]}'
        self.created_at = time.time()
        self.project = project
        self.audience = audience or project.audience
        self.workspace_id = workspace_id
        self.status = STATUS_RUNNING
        self.events: list[dict] = []
        self.result: Optional[dict] = None
        self.partial_result: Optional[dict] = None
        self.timings: dict[str, int] = {}
        self.clarification: Optional[dict] = None
        self.error: Optional[str] = None
        self.error_code: Optional[str] = None
        self.transport_requests = 0
        self.workflow_calls = 0
        self.seed_tag_ids: list[str] = []
        self.key = ''
        self._lock = threading.Lock()

    def add_event(self, event: TraceEvent) -> None:
        with self._lock:
            self.events.append(event.model_dump())

    def close_event(self, event_id: str, status: str, detail: Optional[str] = None,
                    duration_ms: Optional[int] = None) -> None:
        """Finish a step that was announced while it was still running."""
        with self._lock:
            for event in self.events:
                if event.get('id') == event_id:
                    event['status'] = status
                    if detail:
                        event['detail'] = detail
                    if duration_ms is not None:
                        event['durationMs'] = duration_ms
                    return

    def snapshot(self) -> dict:
        with self._lock:
            return {
                'runId': self.id,
                'status': self.status,
                'createdAt': self.created_at,
                'audience': self.audience,
                'events': list(self.events),
                'result': self.result,
                'partialResult': self.partial_result,
                'timings': dict(self.timings),
                'clarification': self.clarification,
                'error': self.error,
                'errorCode': self.error_code,
                'transportRequests': self.transport_requests,
                'workflowCalls': self.workflow_calls,
            }


class ResearchRegistry:
    """Keeps the runs for this process."""

    def __init__(self, limit: int = 64):
        self._runs: dict[str, ResearchRun] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self._limit = limit

    def add(self, run: ResearchRun) -> None:
        with self._lock:
            self._runs[run.id] = run
            self._order.append(run.id)
            while len(self._order) > self._limit:
                oldest = self._order.pop(0)
                self._runs.pop(oldest, None)

    def get(self, run_id: str) -> Optional[ResearchRun]:
        with self._lock:
            return self._runs.get(run_id)

    def running_for(self, key: str) -> Optional[ResearchRun]:
        """The run of this exact brief that is still going, so a second visitor joins it."""
        with self._lock:
            for run_id in reversed(self._order):
                run = self._runs.get(run_id)
                if run and run.key == key and run.status == STATUS_RUNNING:
                    return run
        return None

    def recent(self, limit: int = 10, workspace_id: Optional[str] = None) -> list[dict]:
        """The latest runs, newest first. Given a workspace, only that workspace's own."""
        with self._lock:
            runs = [self._runs[i] for i in reversed(self._order) if i in self._runs]
        if workspace_id is not None:
            runs = [run for run in runs if run.workspace_id == workspace_id]
        return [run.snapshot() for run in runs[:limit]]


registry = ResearchRegistry()


def _event(run: ResearchRun, step: str, envelope: dict, *, status: str = 'ok',
           result_count: Optional[int] = None, detail: Optional[str] = None) -> TraceEvent:
    execution = envelope.get('execution') if isinstance(envelope.get('execution'), dict) else {}
    provenance = envelope.get('provenance') if isinstance(envelope.get('provenance'), dict) else {}
    return TraceEvent(
        id=f'trace-{uuid.uuid4().hex[:8]}',
        step=step,
        workflow=envelope.get('operation'),
        status=status,
        durationMs=execution.get('duration_ms') if isinstance(execution.get('duration_ms'), int) else None,
        correlationId=execution.get('correlation_id') if isinstance(execution.get('correlation_id'), str) else None,
        resultCount=result_count,
        detail=detail or (f"Qloo {envelope.get('operation')} → {provenance.get('endpoint')}" if provenance.get('endpoint') else None),
        evidenceIds=[],
        acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    )


def run_key(project: ProjectRequest, audience: Optional[str], seed_tag_ids: Optional[list[str]]) -> str:
    """What makes two requests the same brief: the whole project, the audience and the confirmed seeds."""
    import json
    return json.dumps([project.model_dump(), audience or project.audience, sorted(seed_tag_ids or [])],
                      sort_keys=True, ensure_ascii=False)


def start_research(project: ProjectRequest, audience: Optional[str] = None,
                   seed_tag_ids: Optional[list[str]] = None,
                   allowance=_FROM_PROFILE,
                   workspace_id: Optional[str] = None,
                   on_finish=None) -> ResearchRun:
    """Start a run in the background and return it immediately.

    `on_finish` is called once when the run ends, however it ends.
    """
    if allowance is _FROM_PROFILE:
        allowance = config.limit('RESEARCH_RUN_MAX_WORKFLOWS')
    run = ResearchRun(project, audience, workspace_id)
    run.seed_tag_ids = list(seed_tag_ids or [])
    run.key = run_key(project, audience, seed_tag_ids)
    registry.add(run)

    thread = threading.Thread(target=_execute_and_release, args=(run, allowance, on_finish), daemon=True)
    thread.start()
    return run


def _execute_and_release(run: ResearchRun, allowance: Optional[int], on_finish=None) -> None:
    try:
        _execute(run, allowance)
    finally:
        if on_finish:
            on_finish()


def _save_exploration(run: ResearchRun, response) -> None:
    """Keep the run's answer in the workspace, the way the direct route does.

    A run that is answered is an exploration, and it belongs to whoever asked
    for it. Saving must never break the run, so every failure here is
    swallowed: the answer still reaches the founder.
    """
    if not run.workspace_id:
        return
    try:
        from .platform import get_platform
        get_platform().save_exploration(
            run.workspace_id, response.model_dump(),
            title=f"{run.project.businessType} for {run.project.audience}",
            brief=run.project.model_dump(),
            project_id=response.projectId,
            delivery=response.delivery.model_dump() if response.delivery else None)
    except Exception:  # noqa: BLE001 - saving must never break an answer
        pass


def _execute(run: ResearchRun, allowance: Optional[int]) -> None:
    provider = QlooHarnessProvider()
    started = time.time()
    clock_started = time.monotonic()

    try:
        if time.time() - started > DEFAULT_RUN_TIMEOUT_SECONDS:
            raise QlooHarnessError('The research run took too long and was stopped.', code='RUN_TIMEOUT', retryable=True)

        # ---- step 1: resolve the audience into confirmed Qloo seeds ----
        if run.seed_tag_ids:
            # The founder already confirmed these, so the audience is not
            # resolved again and no call is spent.
            run.workflow_calls += 1
            tag_envelope = provider.confirmed_tag_envelope(
                run.project.businessType, run.audience, run.seed_tag_ids)
            run.add_event(_event(run, 'use-confirmed-seeds', tag_envelope, result_count=len(run.seed_tag_ids),
                                 detail='Used the audience seeds you confirmed.'))
        else:
            run.workflow_calls += 1
            tag_envelope, cached, requests = provider.run_workflow_cached(
                'find_tags', brief_tags_payload(run.project.businessType, run.audience))
            run.transport_requests += requests
            tag_event = _event(run, 'resolve-audience', tag_envelope,
                               result_count=min(3, len(provider.rows(tag_envelope))))
            if cached:
                mark_reused(tag_event, detail='Reused cached Qloo find_tags.')
            run.add_event(tag_event)

        if tag_envelope.get('status') == 'needs_input':
            run.status = STATUS_CLARIFY
            run.clarification = {
                'reason': 'Qloo could not resolve this audience into cultural seeds.',
                'question': 'Which cultural communities does this audience spend time in?',
                'field': 'audience',
            }
            return

        tags = [tag for row in provider.rows(tag_envelope) if (tag := provider.tag_id(row))][:3]
        if not tags:
            run.status = STATUS_CLARIFY
            run.clarification = {
                'reason': 'Qloo did not resolve any cultural tags for this audience.',
                'question': 'Can you describe the audience by what they do or care about, rather than a job title?',
                'field': 'audience',
            }
            return

        # ---- step 2: retrieve the local evidence ----
        interpretation, interpret_event = provider.interpret_idea(run.project.businessIdea)
        if interpret_event:
            run.add_event(interpret_event)
        primary = interpretation.primary
        resolution = None
        if run.project.businessIdea.strip() and primary is not None and primary.status == 'unresolved':
            # Nothing is spent on a request whose business cannot be named: ask instead.
            run.status = STATUS_CLARIFY
            run.clarification = {'reason': interpretation.clarification or 'The idea does not name one business.',
                                 'question': 'Which kind of business is it? Name the main one.',
                                 'field': 'businessIdea', 'code': 'AMBIGUOUS_IDEA',
                                 'actions': idea_alternatives(interpretation)}
            return
        if primary is not None and primary.status != 'unresolved':
            if allowance is not None and run.workflow_calls >= allowance:
                raise QlooHarnessError('The run reached its allowance before category resolution.', code='ALLOWANCE_EXHAUSTED')
            resolution = resolve_tag(provider, primary)
            run.workflow_calls += resolution.workflows
            run.transport_requests += resolution.requests
            category_event = _event(run, 'resolve-business-category', resolution.result,
                                    result_count=len(provider.rows(resolution.result)))
            category_event.detail = (
                f'Selected a returned Qloo tag ({resolution.quality}); this is a category filter, not an audience seed.'
                if resolution.tag else
                f'No returned tag matched {", ".join(chr(34) + q + chr(34) for q in resolution.tried)}.')
            if resolution.cached:
                mark_reused(category_event)
            run.add_event(category_event)
            if not resolution.tag:
                run.status = STATUS_CLARIFY
                run.clarification = {
                    'reason': f'Qloo returned no category tag matching "{primary.phrase}". CultureForge did not substitute another category.',
                    'question': 'Use a different or broader kind of business.',
                    'field': 'businessIdea', 'code': 'UNSUPPORTED_CATEGORY',
                    'actions': idea_alternatives(interpretation, tuple(resolution.tried))}
                return
        if allowance is not None and run.workflow_calls >= allowance:
            raise QlooHarnessError('The research run reached its call allowance before it could retrieve evidence.', code='ALLOWANCE_EXHAUSTED')
        run.workflow_calls += 1
        rec_envelope, cached, requests = provider.recommend_places(tags, run.project.location, run.project.businessIdea)
        run.transport_requests += requests
        rec_event = _event(run, 'retrieve-evidence', rec_envelope,
                           result_count=len(provider.rows(rec_envelope)))
        if cached:
            mark_reused(rec_event, detail='Reused cached Qloo recommend.')
        run.add_event(rec_event)
        run.timings['firstEvidenceMs'] = round((time.monotonic() - clock_started) * 1000)

        if rec_envelope.get('status') == 'needs_input':
            run.status = STATUS_CLARIFY
            run.clarification = {
                'reason': 'Qloo could not resolve a category, location or audience constraint.',
                'question': 'Review the business idea and confirmed audience seeds, or try a clearer city.',
                'field': 'businessIdea' if run.project.businessIdea else 'location',
                'suggestion': None,
            }
            return

        if not provider.rows(rec_envelope):
            run.status = STATUS_CLARIFY
            # A location Qloo cannot resolve is a dead end unless the founder
            # is told what to change. If this store already holds places for
            # these same signals somewhere else, that location is offered —
            # it is evidence, not a guess, and it costs nothing to take.
            suggestion = known_location(tags, run.project.location)
            if primary is not None and primary.status != 'unresolved' and resolution is not None and resolution.tag:
                # The category exists in Qloo; its places in this city do not. That is a gap in local
                # evidence, and it is said as that, with the founder's own words as ways out.
                run.clarification = {
                    'reason': f'Qloo has a category for "{primary.phrase}" but returned no places for it in '
                              f"'{run.project.location}'. That is a gap in Qloo's local evidence, not a finding about the business.",
                    'question': 'Try a nearby or larger city, or a broader kind of business.',
                    'field': 'location', 'suggestion': suggestion, 'code': 'CATEGORY_NO_PLACES',
                    'actions': idea_alternatives(interpretation)}
                return
            run.clarification = {
                'reason': f"Qloo returned no places for '{run.project.location}' for this audience.",
                'question': 'Try a nearby city, or describe the audience differently.',
                'field': 'location',
                'suggestion': suggestion,
            }
            return

        # Publish a real deterministic answer before bridges, naming or the
        # bounded controller. Explicit envelopes avoid even cache lookups and
        # cannot spend an upstream request. A partial answer is labelled as such.
        initial = provider.generate(
            run.project, tag_result=tag_envelope, recommendations=rec_envelope,
            allow_naming=False, domains=[])
        if initial.delivery:
            initial.delivery.transportRequests = run.transport_requests
            if run.transport_requests:
                initial.delivery.kind = 'fresh'
                initial.delivery.cachedIn = None
        run.partial_result = initial.model_dump()
        # A hybrid's second business is retrieved here, inside the run's allowance, so every later
        # composition finds it held and spends nothing.
        if interpretation.hybrid:
            room = None if allowance is None else max(0, allowance - run.workflow_calls)
            hybrid, spent_extra, _live, used = build_intent_report(
                provider, run.project, interpretation, tags, initial.evidence, rec_envelope, retrieve=True, remaining=room)
            initial.intent = hybrid
            run.partial_result = initial.model_dump()
            run.workflow_calls += used
            run.transport_requests += spent_extra
            for entry in hybrid.evidence[1:]:
                run.add_event(TraceEvent(
                    id=f'trace-{uuid.uuid4().hex[:8]}', step='retrieve-second-business',
                    status='error' if entry['state'] == 'provider_error' else 'ok', resultCount=entry['placeCount'],
                    detail=f"{entry['phrase']}: {entry['state']}. {entry.get('message') or ''}".strip()[:600],
                    acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))

        if initial.concepts:
            run.timings['firstConceptMs'] = round((time.monotonic() - clock_started) * 1000)
        run.add_event(TraceEvent(
            id='trace-initial-answer', step='initial-answer-ready', status='ok',
            resultCount=len(initial.concepts),
            detail='Initial rule composition is available. Bridge retrieval and model analysis are still pending.',
            acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))

        # ---- step 3: compose, using the evidence just cached ----
        # generate() reuses the two cached envelopes, so this costs no new call.
        announced: list[str] = []

        def announce(step: str, detail: str) -> None:
            event_id = f'trace-{uuid.uuid4().hex[:8]}'
            announced.append(event_id)
            run.add_event(TraceEvent(
                id=event_id,
                step=step,
                status='running',
                detail=detail,
                acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            ))

        # ---- the audience bridge: what else this audience gravitates to ----
        # Each domain is one more workflow, so in dev the run's allowance
        # decides how many are asked; any left out are stated, not hidden.
        domains = config.bridge_domains()
        if allowance is not None:
            room = max(0, allowance - run.workflow_calls)
            if room < len(domains):
                run.add_event(TraceEvent(
                    id=f'trace-{uuid.uuid4().hex[:8]}', step='bridge-domains', status='skipped',
                    detail=(f"The run allowance left room for {room} of {len(domains)} bridge domains; "
                            f"skipped: {', '.join(domains[room:])}."),
                    acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
            domains = domains[:room]
        run.workflow_calls += len(domains)

        response = provider.generate(run.project, seed_tag_ids=run.seed_tag_ids or None,
                                     on_step=announce, domains=domains, retrieve_secondary=False)
        # The seeds and places were held by now, so what generate() spent
        # is what the bridge fetched.
        run.transport_requests += (response.delivery.transportRequests or 0) if response.delivery else 0
        for event in response.trace:
            if event.step.startswith('bridge-'):
                run.add_event(event)
        # The announced step is now finished, and it is closed with what
        # actually happened rather than left running for ever.
        naming_event = next((event for event in response.trace
                              if event.step == 'name-the-directions'), None)
        for event_id in announced:
            run.close_event(
                event_id,
                status=(naming_event.status if naming_event else 'skipped'),
                detail=(naming_event.detail if naming_event
                        else 'The directions kept the rule engine\u2019s names.'),
                duration_ms=(naming_event.durationMs if naming_event else None),
            )
        run.add_event(TraceEvent(
            id=f'trace-{uuid.uuid4().hex[:8]}',
            step='compose-directions',
            status='ok' if response.concepts else 'skipped',
            resultCount=len(response.concepts),
            detail=(f'Composed {len(response.concepts)} direction(s) from the returned evidence.'
                    if response.concepts else
                    'The returned evidence did not support a distinct business direction.'),
            evidenceIds=[eid for concept in response.concepts for eid in concept.evidenceIds],
            acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        ))

        # The bounded agent loop becomes part of the research run itself:
        # up to eight plan-act-observe steps over allowlisted Qloo workflows,
        # then a cited analysis. In dev it spends only what is left of this
        # run's allowance. A disabled or unavailable model keeps the
        # deterministic composition intact.
        def record_agent_event(event: TraceEvent) -> None:
            run.add_event(event)
            response.trace.append(event)

        if response.concepts:
            response.agent = run_agent(
                response, tag_envelope, rec_envelope,
                remaining_allowance=None if allowance is None else max(0, allowance - run.workflow_calls),
                deadline=started + DEFAULT_RUN_TIMEOUT_SECONDS,
                on_event=record_agent_event,
            )
        else:
            # Nothing was composed, so there is no direction for the agent to test. Spending Qloo
            # requests and two minutes on claims about nothing would only delay the honest answer.
            record_agent_event(TraceEvent(
                id=f'trace-{uuid.uuid4().hex[:8]}', step='agent-plan', status='skipped',
                detail='No direction was supported by the returned evidence, so the agent had nothing to test and spent no further request.',
                acquiredAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
            response.agent = AgentReport(
                mode='rules', status='skipped',
                stoppingReason='No direction was supported by the returned evidence, so the agent did not run.')

        # The answer's stated cost is the whole run's: the seeds and places this
        # run fetched, the bridge domains, and the agent's live workflows. Left
        # to generate(), it would count only what generate() fetched itself.
        # A held report replays steps that an earlier run paid for; this run spent nothing on them.
        if response.agent and not response.agent.cached:
            run.transport_requests += sum(step.upstreamRequests for step in response.agent.steps)
        if response.delivery:
            response.delivery.transportRequests = run.transport_requests
            if run.transport_requests:
                response.delivery.kind = 'fresh'
                response.delivery.cachedIn = None

        run.result = response.model_dump()
        run.timings['completeMs'] = round((time.monotonic() - clock_started) * 1000)
        run.status = STATUS_COMPLETE
        _save_exploration(run, response)

    except QlooHarnessError as exc:
        run.status = STATUS_FAILED
        run.error = str(exc)
        run.error_code = exc.code
    except Exception:  # noqa: BLE001 - a run must never take the process down
        run.status = STATUS_FAILED
        run.error = 'The research run could not be completed.'
