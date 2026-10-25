"""Investigating a direction: the agent asks what it does not know, and finds out.

A brief produces three directions, each resting on the venues Qloo returned.
But a direction also rests on things nobody has checked: is this audience
really concentrated here, do these venues share a cultural signature, what
does the demographic profile of the reference place look like.

This module is the agent closing those gaps. It is deliberately bounded and
explicit about what it is doing:

  - the founder chooses the direction, and may choose the facets
  - each facet is one named Qloo workflow, and the answer says which one
  - every call is cached, so a second look costs nothing
  - the findings are Qloo's, and the reading of them is labelled as ours
  - what the investigation could not establish is stated, not glossed over
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import ProjectRequest
from .providers import QlooHarnessError, QlooHarnessProvider, mark_reused
from .evidence_store import canonical_key, get_store

#: The facets an investigation can open. Each is one Qloo workflow.
FACETS = ('geography', 'tags', 'demographics', 'describe', 'trends')

#: What each facet means, in the founder's language rather than the API's.
FACET_QUESTIONS = {
    'geography': 'Where does interest in this reference place actually concentrate?',
    'tags': 'Do these venues share a cultural signature, or only a location?',
    'demographics': 'Who is indexed against this reference place?',
    'describe': 'What does Qloo know about this reference place in full?',
    'trends': 'Is this reference place gaining or losing momentum?',
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bounds(points: list[dict]) -> dict:
    if not points:
        return {'west': 0, 'south': 0, 'east': 0, 'north': 0}
    lats = [p['lat'] for p in points]
    lons = [p['lon'] for p in points]
    return {
        'west': min(lons), 'south': min(lats), 'east': max(lons), 'north': max(lats),
    }


def _geography_points(envelope: dict) -> list[dict]:
    """The heatmap cells, in the shape the map draws."""
    points: list[dict] = []
    for row in envelope.get('results') or []:
        if not isinstance(row, dict):
            continue
        location = row.get('location') if isinstance(row.get('location'), dict) else {}
        query = row.get('query') if isinstance(row.get('query'), dict) else {}
        lat = location.get('latitude')
        lon = location.get('longitude')
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        affinity = query.get('affinity')
        popularity = query.get('popularity')
        points.append({
            'lat': float(lat),
            'lon': float(lon),
            'geohash': location.get('geohash'),
            'affinity': float(affinity) if isinstance(affinity, (int, float)) else None,
            'popularity': float(popularity) if isinstance(popularity, (int, float)) else None,
        })
    return points


def _demographics(envelope: dict) -> Optional[dict]:
    rows = envelope.get('results') or []
    if not rows or not isinstance(rows[0], dict):
        return None
    row = rows[0]
    query = row.get('query') if isinstance(row.get('query'), dict) else {}
    age = {k: v for k, v in (query.get('age') or {}).items() if isinstance(v, (int, float))}
    gender = {k: v for k, v in (query.get('gender') or {}).items() if isinstance(v, (int, float))}
    return {
        'entityId': row.get('entity_id'),
        'age': age,
        'gender': gender,
        # A negative value means the group is under-indexed here, not that
        # there are fewer people. The sign has to survive to the screen.
        'note': 'A demographic index for this entity. Negative values mean the group is under-indexed here.',
    }


def investigate(project: ProjectRequest, direction_id: Optional[str], entity_ids: list[str],
                within: str, facets: list[str], seed_tag_ids: Optional[list[str]] = None,
                reference: Optional[str] = None) -> dict:
    """Run the chosen facets against the evidence this exploration rests on.

    `within` is the geographic area the map is drawn inside. `reference` is the
    entity the investigation is about — normally the venue the chosen
    direction was built from.
    """
    provider = QlooHarnessProvider()
    chosen = [facet for facet in FACETS if facet in facets]
    if not chosen:
        raise QlooHarnessError('Choose at least one thing to investigate.', code='INVALID_REQUEST')

    target = reference or (entity_ids[0] if entity_ids else None)
    if not target:
        raise QlooHarnessError('There is no venue to investigate yet.', code='INVALID_REQUEST')

    tools: list[dict] = []
    geography: Optional[dict] = None
    tags: list[dict] = []
    demographics: Optional[dict] = None
    description: Optional[dict] = None
    trend: Optional[dict] = None
    findings: list[str] = []
    limitations: list[str] = []
    spent = 0

    for facet in chosen:
        operation, payload = _call_for(facet, provider, target, entity_ids, within)
        try:
            envelope, cached, requests = provider.run_workflow_cached(operation, payload)
        except QlooHarnessError as exc:
            tools.append({'facet': facet, 'workflow': _workflow_for(facet), 'status': 'error',
                          'detail': str(exc), 'cached': False, 'resultCount': 0})
            limitations.append(f'{FACET_QUESTIONS[facet]} — Qloo could not answer this: {exc}')
            continue
        spent += requests
        trace = provider._trace_event(f'investigate-{facet}', operation, envelope,
                                      len(provider.rows(envelope)))
        original_duration = trace.durationMs
        if cached:
            mark_reused(trace, FACET_QUESTIONS[facet])
        acquired = get_store().stored_at(canonical_key(operation, payload))
        tool = {
            'facet': facet,
            'workflow': _workflow_for(facet),
            'question': FACET_QUESTIONS[facet],
            'status': envelope.get('status', 'ok'),
            'cached': cached,
            'transportRequests': requests,
            'durationMs': trace.durationMs,
            'originalDurationMs': original_duration if cached else None,
            'resultCount': len(envelope.get('results') or []) if isinstance(envelope.get('results'), list) else 0,
            'acquiredAt': (datetime.fromtimestamp(acquired, timezone.utc).isoformat()
                           if acquired is not None else (None if cached else _now())),
        }
        if cached:
            tool['detail'] = trace.detail
        tools.append(tool)

        if facet == 'geography':
            points = _geography_points(envelope)
            geography = {
                'entityId': target,
                'within': within,
                'points': points,
                'bounds': _bounds(points),
                'metric': 'Qloo affinity for this entity inside the area',
                'note': ('Qloo supplies geographic popularity cells for interest mapping. '
                         'These are distinct from precise venue coordinates.'),
            }
            if points:
                findings.append(
                    f'Qloo returned {len(points)} geographic cells where this entity has affinity, '
                    f'inside {within}.')
            else:
                limitations.append(f'Qloo returned no geographic cells for this entity inside {within}.')
        elif facet == 'tags':
            for row in envelope.get('results') or []:
                if not isinstance(row, dict) or not row.get('id'):
                    continue
                tags.append({
                    'id': row.get('id'), 'name': row.get('name'), 'type': row.get('type'),
                    'popularity': row.get('popularity'), 'affinity': row.get('affinity'),
                })
            if tags:
                findings.append(
                    f'{len(tags)} concepts characterise the venues, led by '
                    + ', '.join(str(t.get('name')) for t in tags[:3]) + '.')
            else:
                limitations.append('Qloo returned no concepts for these venues.')
        elif facet == 'demographics':
            demographics = _demographics(envelope)
            if demographics and demographics.get('age'):
                findings.append('Qloo returned a demographic index for the reference place.')
            else:
                limitations.append('Qloo returned no demographic index for the reference place.')
        elif facet == 'describe':
            rows = envelope.get('results') or []
            if rows and isinstance(rows[0], dict):
                row = rows[0]
                properties = row.get('properties') if isinstance(row.get('properties'), dict) else {}
                geocode = properties.get('geocode') if isinstance(properties.get('geocode'), dict) else {}
                description = {
                    'entityId': row.get('entity_id'),
                    'name': row.get('name'),
                    'popularity': row.get('popularity'),
                    'description': properties.get('description'),
                    'address': properties.get('address'),
                    'rating': properties.get('business_rating'),
                    'image': (properties.get('image') or {}).get('url')
                    if isinstance(properties.get('image'), dict) else properties.get('image'),
                    'geocode': geocode,
                }
                findings.append(f'Qloo describes {row.get("name")} in detail.')
            else:
                limitations.append('Qloo returned no detail for the reference place.')
        elif facet == 'trends':
            rows = envelope.get('results') or []
            series = rows[0] if rows and isinstance(rows[0], list) else (rows if isinstance(rows, list) else [])
            trend = {'series': series[:120], 'note': 'Qloo popularity over time for the reference place.'}
            if series:
                findings.append(f'Qloo returned {len(series)} points of popularity history.')
            else:
                limitations.append('Qloo returned no popularity history for the reference place.')

    return {
        'directionId': direction_id,
        'project': project.model_dump(),
        'facets': chosen,
        'questions': [FACET_QUESTIONS[facet] for facet in chosen],
        'reference': target,
        'within': within,
        'tools': tools,
        'geography': geography,
        'tags': tags,
        'demographics': demographics,
        'describe': description,
        'trends': trend,
        'findings': findings,
        'limitations': limitations,
        'transportRequests': spent,
        'investigatedAt': _now(),
    }


def _workflow_for(facet: str) -> str:
    return {
        'geography': 'where_popular',
        'tags': 'entity_tags',
        'demographics': 'audience_demographics',
        'describe': 'describe',
        'trends': 'trends',
    }[facet]


def _call_for(facet: str, provider: QlooHarnessProvider, target: str,
              entity_ids: list[str], within: str):
    """The exact upstream call for a facet, as (operation, payload)."""
    if facet == 'geography':
        return 'where_popular', {'entity': target, 'within': within, 'limit': 20}
    if facet == 'tags':
        return 'entity_tags', {'entities': list(entity_ids)[:5] or [target], 'entity_type': 'place', 'limit': 10}
    if facet == 'demographics':
        return 'audience_demographics', {'entity': target, 'entity_type': 'place', 'limit': 5}
    if facet == 'describe':
        return 'describe', {'entity': target, 'type': 'place'}
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=90)
    return 'trends', {
        'entities': [target], 'entity_type': 'place',
        'start_date': start.isoformat(), 'end_date': end.isoformat(), 'limit': 10,
    }
