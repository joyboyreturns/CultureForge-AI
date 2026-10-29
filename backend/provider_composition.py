"""How a run's evidence becomes the trace, the model-written names and the concepts on screen.

Split from the provider so that the part that talks to Qloo and the part that dresses its answer are
read separately. These are methods of `QlooHarnessProvider` by inheritance, so `provider._trace_event`
and `QlooHarnessProvider._composed_concept` keep working.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from . import metering
from .evidence_store import cached_call, canonical_key, get_store
from .models import Concept, Decision, ExperienceMoment, TraceEvent
from .payloads import safe_query


class CompositionMixin:
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
            model = naming.get('model') or 'the configured model'
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
        """Let the configured model name the directions, and keep the rules in charge.

        The model is given the audience signals and the venues each direction
        is built from — and no numbers at all, so it cannot state one. Its
        answer is held in the evidence store like everything else, so a
        repeated brief spends no model request.
        """
        from . import llm

        report = {'used': False, 'attempted': False, 'model': None, 'reason': None, 'dropped': []}
        if not llm.is_configured():
            report['reason'] = 'The model gateway is not enabled or configured, so the rule engine named these directions.'
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
            'businessIdea': project.businessIdea,
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
            # The prompt is part of the answer: names held under an older
            # prompt are not the names this prompt would produce.
            'promptVersion': llm.PROMPT_VERSION,
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
                'endpoint': 'vercel-ai-gateway',
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
