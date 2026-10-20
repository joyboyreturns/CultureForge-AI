"""Native Qloo comparisons, and recomposition from evidence already held.

Three jobs the scenario lab and the evidence panel need:

* **compare_audiences** - the real A/B. Qloo resolves two groups of entities
  and returns the cultural tags they share, each with a comparison score and
  the number of entities in each group that carry it, plus the tags that make
  each group distinct. This is measured, not modelled.
* **rank** - a tournament between real Qloo entities, ranked by affinity for
  a given signal set. It can only rank entities Qloo returned; it cannot rank
  invented business concepts.
* **recompose** - drop one piece of evidence and rebuild the directions from
  what is left, without spending another call. This is what proves the answer
  actually depends on the evidence.

Everything here is normalised into plain dictionaries so the frontend never
has to know the wire shape.
"""
from __future__ import annotations

from typing import Optional

from .evidence_store import canonical_key, get_store
from .providers import QlooHarnessError, QlooHarnessProvider

# A parameter is safe to show in a provenance panel only if it cannot carry
# anything sensitive. Everything else is dropped rather than redacted later.
SAFE_QUERY_KEYS = {
    'filter.type', 'filter.location.query', 'signal.location.query', 'take',
    'operator.signal.interests.tags', 'signal.interests.tags',
    'signal.interests.entities', 'a.signal.interests.entities',
    'b.signal.interests.entities', 'feature.explainability', 'limit',
}


def safe_query(query: dict) -> dict:
    """Keep only the parameters that are safe to display."""
    if not isinstance(query, dict):
        return {}
    return {key: value for key, value in query.items() if key in SAFE_QUERY_KEYS}


def compare_audiences(group_a: list[str], group_b: list[str], target_type: str = 'place',
                      limit: int = 12) -> dict:
    """Compare two groups of Qloo entities, natively.

    Returns the shared tags with their comparison score, and the tags that
    distinguish each group.
    """
    if not group_a or not group_b:
        raise QlooHarnessError('Both sides of a comparison need at least one entity.')
    provider = QlooHarnessProvider()
    envelope, _cached, _requests = provider.run_workflow_cached('compare_audiences', {
        'group_a': group_a, 'group_b': group_b, 'target_type': target_type, 'limit': limit,
    })
    results = envelope.get('results') or {}
    if not isinstance(results, dict):
        results = {}

    def rows(key: str) -> list[dict]:
        value = results.get(key)
        return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []

    shared = []
    for row in rows('tags'):
        query = row.get('query') if isinstance(row.get('query'), dict) else {}
        a_hits = query.get('a.signal.interests.entities')
        b_hits = query.get('b.signal.interests.entities')
        shared.append({
            'tagId': row.get('tag_id'),
            'label': row.get('name'),
            'subtype': row.get('subtype'),
            'popularity': row.get('popularity'),
            'score': query.get('score'),
            'groupAHits': len(a_hits) if isinstance(a_hits, list) else None,
            'groupBHits': len(b_hits) if isinstance(b_hits, list) else None,
        })

    def own(key: str) -> list[dict]:
        out = []
        for row in rows(key):
            out.append({
                'tagId': row.get('tag_id'),
                'label': row.get('name'),
                'subtype': row.get('subtype'),
                'popularity': row.get('popularity'),
            })
        return out

    return {
        'shared': shared,
        'groupA': own('a'),
        'groupB': own('b'),
        'matchedEntities': len(rows('matchEntities')),
        'interpretation': envelope.get('interpretation'),
        'trace': provider._trace_event('compare-audiences', 'compare_audiences', envelope, len(shared)).model_dump(),
    }


def rank_entities(options: list[str], signals: Optional[list[str]] = None,
                  include_tags: Optional[list[str]] = None, option_type: str = 'place',
                  signal_location: Optional[str] = None, limit: int = 6) -> dict:
    """Rank real Qloo entities by affinity for a signal set.

    The Qloo `rank` workflow takes entity inputs for `options` and `signals`,
    and tag inputs for `include_tags`. The audience enters as tags, which is
    how a tournament between real venues becomes an answer about an audience.
    """
    if not options:
        raise QlooHarnessError('Ranking needs at least one entity to rank.')
    provider = QlooHarnessProvider()
    # The rank workflow takes no `limit`: it returns one row per option.
    payload: dict = {'options': options, 'option_type': option_type}
    if signals:
        payload['signals'] = signals
    if include_tags:
        payload['include_tags'] = include_tags
    if signal_location:
        payload['signal_location'] = signal_location
    envelope, _cached, _requests = provider.run_workflow_cached('rank', payload)
    if envelope.get('status') == 'needs_input':
        raise QlooHarnessError('Qloo needs a clearer signal set for this ranking.')
    rows = provider.rows(envelope)
    ranked = []
    for index, row in enumerate(rows):
        ranked.append({
            'entityId': row.get('entity_id') or row.get('id'),
            'label': row.get('name'),
            'affinity': provider._affinity(row),
            'popularity': row.get('popularity'),
            'position': index + 1,
        })
    return {
        'ranked': ranked,
        'trace': provider._trace_event('rank-anchors', 'rank', envelope, len(ranked)).model_dump(),
    }


def recompose(project, evidence_store=None, exclude_entity_ids: Optional[list[str]] = None,
               exclude_tag_ids: Optional[list[str]] = None) -> dict:
    """Rebuild the directions without the given evidence, using no new call.

    This is the check that the answer really depends on the data: remove one
    venue and see which decisions lose their support.
    """
    exclude_entity_ids = set(exclude_entity_ids or [])
    exclude_tag_ids = set(exclude_tag_ids or [])
    provider = QlooHarnessProvider()

    # The cached envelopes are addressed by the same canonical key the
    # provider used, so this costs no upstream request.
    query = f'{project.businessType} {project.audience}'.strip()
    tag_key = canonical_key('find_tags', {'query': query, 'limit': 3})
    store = evidence_store or get_store()
    tag_envelope = store.get(tag_key)
    if tag_envelope is None:
        raise QlooHarnessError('There is no cached evidence for this brief yet. Run the research first.')
    tags = [tag for row in provider.rows(tag_envelope) if (tag := provider.tag_id(row))][:3]
    tags = [tag for tag in tags if tag not in exclude_tag_ids]
    if not tags:
        raise QlooHarnessError('Every audience seed was removed, so there is nothing left to reason from.')
    rec_key = canonical_key('recommend', {
        'target_type': 'place', 'signal_tags': tags,
        'signal_location': project.location, 'limit': 5,
    })
    rec_envelope = store.get(rec_key)
    if rec_envelope is None:
        raise QlooHarnessError('There is no cached evidence for this brief yet. Run the research first.')

    response = provider.generate(project, tag_envelope, rec_envelope)

    # Drop the excluded entities from the evidence and from every decision.
    kept_evidence = [
        item for item in response.evidence
        if not (item.kind == 'entity' and item.entityId in exclude_entity_ids)
        and not (item.kind == 'tag' and item.tagId in exclude_tag_ids)
    ]
    kept_ids = {item.id for item in kept_evidence}
    concepts = []
    for concept in response.concepts:
        decisions = [
            decision for decision in concept.decisions
            if any(eid in kept_ids for eid in decision.evidenceIds)
        ]
        if not decisions:
            continue  # this direction lost all of its support
        concepts.append(concept.model_copy(update={
            'evidenceIds': [eid for eid in concept.evidenceIds if eid in kept_ids],
            'decisions': decisions,
        }))

    return {
        'concepts': [concept.model_dump() for concept in concepts],
        'evidence': [item.model_dump() for item in kept_evidence],
        'dropped': len(response.evidence) - len(kept_evidence),
        'notice': (
            'Recomposed from the evidence already retrieved for this brief. Qloo was not called again.'
        ),
    }
