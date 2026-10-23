"""A bounded, cached attempt to find replacements for a direction's anchor.

This is a separate observation, not a new direction verdict. One exclusion
query can show that Qloo returned alternatives for the same audience seeds
and location, but an empty bounded response cannot establish that none exist.
"""
from __future__ import annotations

import re

from .models import ChallengeProbeRequest, Evidence
from .providers import QlooHarnessError, QlooHarnessProvider

POLICY_VERSION = 'replacement-probe-2'
BOUNDARY = (
    'This probe tests Qloo retrieval with one returned place excluded. It does not test '
    'demand, competition, rent, willingness to pay, or commercial viability.'
)


def _primary_anchor(request: ChallengeProbeRequest) -> tuple[Evidence, list[Evidence]]:
    revision = request.revision
    direction = next((item for item in revision.concepts if item.id == request.directionId), None)
    if direction is None:
        raise QlooHarnessError('That direction is not part of the exploration on screen.', code='INVALID_REQUEST')
    evidence = {item.id: item for item in revision.evidence}
    cited_places = [evidence[item_id] for item_id in direction.evidenceIds
                    if item_id in evidence and evidence[item_id].kind == 'entity'
                    and evidence[item_id].entityId and evidence[item_id].entityType in ('place', 'urn:entity:place')]
    if not cited_places:
        raise QlooHarnessError('This direction has no cited Qloo place to exclude.', code='NO_EVIDENCE')
    if not re.fullmatch(r'[A-Za-z0-9:_-]{1,200}', cited_places[0].entityId or ''):
        raise QlooHarnessError('The cited place has an invalid Qloo entity ID.', code='INVALID_REQUEST')
    return cited_places[0], cited_places


def challenge_probe(request: ChallengeProbeRequest, provider: QlooHarnessProvider) -> dict:
    """Exclude the direction's first cited place and report Qloo's response."""
    anchor, cited_places = _primary_anchor(request)
    tags = list(dict.fromkeys(request.revision.resolvedTags))
    if not tags or any(not isinstance(tag, str) or len(tag) > 240 or not tag.startswith('urn:tag:') for tag in tags):
        raise QlooHarnessError('The exploration has no valid Qloo audience tags for this probe.', code='NO_EVIDENCE')
    if not request.project.location.strip():
        raise QlooHarnessError('A location is required to hold this probe to the original context.', code='INVALID_REQUEST')

    # Fixed, typed payload: callers cannot provide Qloo query keys or alter
    # the audience/location while the anchor is excluded.
    payload = {
        'filter.type': 'urn:entity:place',
        'signal.interests.tags': ','.join(sorted(tags[:3])),
        'operator.signal.interests.tags': 'intersection',
        'filter.location.query': request.project.location.strip(),
        'filter.exclude.entities': anchor.entityId,
        'take': 5,
        'feature.explainability': True,
    }
    envelope, cached, requests = provider.run_insights_probe_cached(payload)
    rows = provider.rows(envelope)
    returned: list[Evidence] = []
    for index, row in enumerate(rows):
        entity_id = row.get('entity_id') or row.get('id')
        name = row.get('name')
        if not isinstance(entity_id, str) or not isinstance(name, str) or entity_id == anchor.entityId:
            continue
        properties = row.get('properties') if isinstance(row.get('properties'), dict) else {}
        geocode = properties.get('geocode') if isinstance(properties.get('geocode'), dict) else {}
        returned_location = geocode.get('name')
        returned.append(Evidence(
            id=f'probe-{index + 1}', kind='entity', label=name,
            entityId=entity_id, entityType='place',
            affinity=provider._affinity(row),
            description=properties.get('description') if isinstance(properties.get('description'), str) else None,
            image=properties.get('image') if isinstance(properties.get('image'), str) else None,
            location=returned_location if isinstance(returned_location, str) else None,
        ))

    return {
        'policyVersion': POLICY_VERSION,
        'directionId': request.directionId,
        'outcome': 'unresolved',
        'hypothesis': (
            f'Qloo may return other places for the same audience seeds near '
            f'{request.project.location} when {anchor.label} is excluded.'
        ),
        'falsifier': (
            'No replacement appeared in this bounded response. That leaves the question '
            'unresolved; absence from a limited result set is not proof of absence.'
        ),
        'anchor': {'entityId': anchor.entityId, 'label': anchor.label},
        'sources': [{'entityId': item.entityId, 'label': item.label} for item in cited_places],
        'replacements': returned,
        'observation': (
            f'Qloo returned {len(returned)} replacement place'
            f'{"s" if len(returned) != 1 else ""} after excluding {anchor.label}.'
        ),
        'scope': f'Audience seeds: {len(tags[:3])}; location: {request.project.location}; places returned: up to 5.',
        'query': payload,
        'cached': cached,
        'transportRequests': requests,
        'limitations': BOUNDARY,
    }
