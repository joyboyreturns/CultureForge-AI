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

from .evidence_store import known_location
from .models import ProjectRequest, TraceEvent
from .providers import QlooHarnessError, QlooHarnessProvider, mark_reused

# A cold research run may not spend more than this many Qloo workflows.
DEFAULT_RUN_ALLOWANCE = 3
# A run is abandoned if it takes longer than this.
DEFAULT_RUN_TIMEOUT_SECONDS = 240

STATUS_RUNNING = 'running'
STATUS_COMPLETE = 'complete'
STATUS_CLARIFY = 'clarify'
STATUS_FAILED = 'failed'


class ResearchRun:
    """One research run, and the trace it produced."""

    def __init__(self, project: ProjectRequest, audience: Optional[str] = None):
        self.id = f'run-{uuid.uuid4().hex[:12]}'
        self.created_at = time.time()
        self.project = project
        self.audience = audience or project.audience
        self.status = STATUS_RUNNING
        self.events: list[dict] = []
        self.result: Optional[dict] = None
        self.clarification: Optional[dict] = None
        self.error: Optional[str] = None
        self.transport_requests = 0
        self.workflow_calls = 0
        self.seed_tag_ids: list[str] = []
        self._lock = threading.Lock()

    def add_event(self, event: TraceEvent) -> None:
        with self._lock:
            self.events.append(event.model_dump())

    def snapshot(self) -> dict:
        with self._lock:
            return {
                'runId': self.id,
                'status': self.status,
                'createdAt': self.created_at,
                'audience': self.audience,
                'events': list(self.events),
                'result': self.result,
                'clarification': self.clarification,
                'error': self.error,
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

    def recent(self, limit: int = 10) -> list[dict]:
        with self._lock:
            ids = self._order[-limit:][::-1]
            return [self._runs[i].snapshot() for i in ids if i in self._runs]


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


def start_research(project: ProjectRequest, audience: Optional[str] = None,
                   seed_tag_ids: Optional[list[str]] = None,
                   allowance: int = DEFAULT_RUN_ALLOWANCE) -> ResearchRun:
    """Start a run in the background and return it immediately."""
    run = ResearchRun(project, audience)
    run.seed_tag_ids = list(seed_tag_ids or [])
    registry.add(run)
    thread = threading.Thread(target=_execute, args=(run, allowance), daemon=True)
    thread.start()
    return run


def _execute(run: ResearchRun, allowance: int) -> None:
    provider = QlooHarnessProvider()
    started = time.time()

    try:
        if time.time() - started > DEFAULT_RUN_TIMEOUT_SECONDS:
            raise QlooHarnessError('The research run took too long and was stopped.', code='RUN_TIMEOUT', retryable=True)

        # ---- step 1: resolve the audience into confirmed Qloo seeds ----
        if run.seed_tag_ids:
            # The founder already confirmed these, so the audience is not
            # resolved again and no call is spent.
            run.workflow_calls += 1
            tag_envelope = {
                'operation': 'find_tags', 'status': 'ok',
                'results': [{'id': tag_id} for tag_id in run.seed_tag_ids],
                'execution': {'duration_ms': 0},
                'provenance': {'endpoint': 'confirmed by the founder', 'requests': []},
            }
            run.add_event(_event(run, 'use-confirmed-seeds', tag_envelope, result_count=len(run.seed_tag_ids),
                                 detail='Used the audience seeds the founder confirmed.'))
        else:
            run.workflow_calls += 1
            tag_envelope, cached, requests = provider.run_workflow_cached('find_tags', {
                'query': f'{run.project.businessType} {run.audience}'.strip(), 'limit': 3,
            })
            run.transport_requests += requests
            tag_event = _event(run, 'resolve-audience', tag_envelope, result_count=3)
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
        if run.workflow_calls >= allowance:
            raise QlooHarnessError('The research run reached its call allowance before it could retrieve evidence.', code='ALLOWANCE_EXHAUSTED')
        run.workflow_calls += 1
        rec_envelope, cached, requests = provider.run_workflow_cached('recommend', {
            'target_type': 'place', 'signal_tags': tags,
            'signal_location': run.project.location, 'limit': 5,
        })
        run.transport_requests += requests
        rec_event = _event(run, 'retrieve-evidence', rec_envelope,
                           result_count=len(provider.rows(rec_envelope)))
        if cached:
            mark_reused(rec_event, detail='Reused cached Qloo recommend.')
        run.add_event(rec_event)

        if rec_envelope.get('status') == 'needs_input':
            run.status = STATUS_CLARIFY
            run.clarification = {
                'reason': 'Qloo needs a clearer location for this audience.',
                'question': 'Which neighbourhood or city should we look in?',
                'field': 'location',
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
            run.clarification = {
                'reason': f"Qloo returned no places for '{run.project.location}' for this audience.",
                'question': 'Try a nearby city, or describe the audience differently.',
                'field': 'location',
                'suggestion': suggestion,
            }
            return

        # ---- step 3: compose, using the evidence just cached ----
        # generate() reuses the two cached envelopes, so this costs no new call.
        response = provider.generate(run.project, seed_tag_ids=run.seed_tag_ids or None)
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

        if not response.concepts:
            run.status = STATUS_CLARIFY
            run.clarification = {
                'reason': 'The evidence did not support three distinct business directions.',
                'question': 'Try a different audience description, or a location with more local data.',
                'field': 'audience',
            }
            return

        run.result = response.model_dump()
        run.status = STATUS_COMPLETE

    except QlooHarnessError as exc:
        run.status = STATUS_FAILED
        run.error = str(exc)
    except Exception:  # noqa: BLE001 - a run must never take the process down
        run.status = STATUS_FAILED
        run.error = 'The research run could not be completed.'
