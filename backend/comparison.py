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
from .providers import (QlooHarnessError, QlooHarnessProvider, brief_places_retrieval_payload,
                        brief_tags_payload, safe_query)

__all__ = ['compare_audiences', 'rank_entities', 'recompose', 'safe_query']


def compare_audiences(group_a: list[str], group_b: list[str], target_type: str = 'place',
                      limit: int = 12) -> dict:
    """Compare two groups of Qloo entities, natively.

    Returns the shared tags with their comparison score, and the tags that
    distinguish each group.
    """
    if not group_a or not group_b:
        raise QlooHarnessError('Both sides of a comparison need at least one entity.', code='INVALID_REQUEST')
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
                  signal_location: Optional[str] = None, demographic: Optional[str] = None,
                  limit: int = 6) -> dict:
    """Rank real Qloo entities by affinity for a signal set.

    The Qloo `rank` workflow takes entity inputs for `options` and `signals`,
    and tag inputs for `include_tags`. A `demographic` is the natural way to
    bring an audience in: Qloo converts the phrase into its own documented
    age and gender signals, and the converted signal is returned so it can be
    shown rather than assumed.
    """
    if not options:
        raise QlooHarnessError('Ranking needs at least one entity to rank.', code='INVALID_REQUEST')
    provider = QlooHarnessProvider()
    # The rank workflow takes no `limit`: it returns one row per option.
    payload: dict = {'options': options, 'option_type': option_type}
    if signals:
        payload['signals'] = signals
    if include_tags:
        payload['include_tags'] = include_tags
    if signal_location:
        payload['signal_location'] = signal_location
    if demographic:
        payload['demographic'] = demographic
    envelope, _cached, _requests = provider.run_workflow_cached('rank', payload)
    if envelope.get('status') == 'needs_input':
        raise QlooHarnessError('Qloo needs a clearer signal set for this ranking.', code='INVALID_UPSTREAM_REQUEST')
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
    trace = provider._trace_event('rank-anchors', 'rank', envelope, len(ranked)).model_dump()
    return {
        'ranked': ranked,
        # The converted signal, taken from the request Qloo actually sent.
        'signalsUsed': (trace.get('request') or {}).get('query') or {},
        'trace': trace,
    }


def _without(envelope: dict, drop: set[str], provider: QlooHarnessProvider) -> dict:
    """A copy of an envelope with the excluded rows taken out.

    The rows are removed **before** the composer sees them. Filtering the
    composer's output afterwards would leave the removed venue's description,
    photograph and decisions in place, and the answer would claim to have
    been rebuilt when it had only been trimmed.
    """
    if not drop:
        return envelope
    rows = provider.rows(envelope)
    kept = []
    for row in rows:
        entity_id = row.get('entity_id') or row.get('id')
        tag = provider.tag_id(row)
        if isinstance(entity_id, str) and entity_id in drop:
            continue
        if tag and tag in drop:
            continue
        kept.append(row)
    if isinstance(envelope.get('results'), dict):
        copy = dict(envelope)
        results = dict(envelope['results'])
        for key in ('entities', 'tags'):
            if isinstance(results.get(key), list):
                results[key] = kept
        copy['results'] = results
        return copy
    copy = dict(envelope)
    copy['results'] = kept
    return copy


def recompose(project, evidence_store=None, exclude_entity_ids: Optional[list[str]] = None,
               exclude_tag_ids: Optional[list[str]] = None,
               tag_envelope: Optional[dict] = None,
               recommend_envelope: Optional[dict] = None,
               seed_tag_ids: Optional[list[str]] = None,
               retain_entity_ids: Optional[list[str]] = None) -> dict:
    """Rebuild the directions without the given evidence, using no new call.

    This is the check that the answer really depends on the data: remove one
    venue and see the directions rebuilt without it. The removal happens
    before the composition, so the venue is gone from the description, the
    photograph and the decisions — not just from the evidence list.
    """
    exclude_entity_ids = set(exclude_entity_ids or [])
    exclude_tag_ids = set(exclude_tag_ids or [])
    provider = QlooHarnessProvider()

    # The cached envelopes are addressed by the same canonical key the
    # provider used, so this costs no upstream request.
    tag_key = canonical_key('find_tags', brief_tags_payload(project.businessType, project.audience))
    store = evidence_store or get_store()
    tag_envelope = tag_envelope or store.get(tag_key)
    if tag_envelope is None:
        raise QlooHarnessError('There is no cached evidence for this brief yet. Run the research first.', code='NO_CACHED_EVIDENCE')
    tags = [tag for row in provider.rows(tag_envelope) if (tag := provider.tag_id(row))][:3]
    if seed_tag_ids:
        selected = set(seed_tag_ids)
        tags = [tag for tag in tags if tag in selected]
        tag_envelope = _without(tag_envelope,
                                {provider.tag_id(row) for row in provider.rows(tag_envelope)} - selected,
                                provider)
    if not [tag for tag in tags if tag not in exclude_tag_ids]:
        raise QlooHarnessError('Every audience seed was removed, so there is nothing left to reason from.', code='INVALID_REQUEST')
    rec_key = canonical_key('recommend', brief_places_retrieval_payload(tags, project.location, project.businessIdea, evidence_store=store))
    rec_envelope = recommend_envelope or store.get(rec_key)
    if rec_envelope is None:
        raise QlooHarnessError('There is no cached evidence for this brief yet. Run the research first.', code='NO_CACHED_EVIDENCE')
    if retain_entity_ids is not None:
        retained = set(retain_entity_ids)
        exclude_entity_ids |= {entity_id for row in provider.rows(rec_envelope)
                               if isinstance((entity_id := row.get('entity_id') or row.get('id')), str)} - retained

    # The exclusions are applied to the held evidence *before* the composer
    # runs, so the directions are rebuilt from what is left.
    tag_envelope = _without(tag_envelope, exclude_tag_ids, provider)
    rec_envelope = _without(rec_envelope, exclude_entity_ids, provider)

    # No model call: this is a zero-upstream operation, and the deterministic
    # wording is what the rules produce on their own.
    # The bridge is read from held evidence only: a rebuild never calls Qloo.
    response = provider.generate(project, tag_envelope, rec_envelope, allow_naming=False,
                                 bridge_held_only=True)

    # And the evidence and decisions are checked against what is actually
    # left, so nothing cites a venue that is gone.
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
        'trace': [event.model_dump() for event in response.trace],
        'delivery': response.delivery.model_dump() if response.delivery else None,
        'composerVersion': response.composerVersion,
        # What was actually taken out, counted from the exclusions rather
        # than from the difference: the answer was composed from what was
        # left, so the two are the same length.
        'dropped': len(exclude_entity_ids) + len(exclude_tag_ids),
        'notice': (
            'Rebuilt from the evidence already retrieved for this brief, with the removed '
            'places taken out before the directions were composed. Qloo was not called again, '
            'and no model was asked to name anything.'
        ),
    }
