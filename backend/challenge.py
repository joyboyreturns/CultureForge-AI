"""Challenge a direction: does the local evidence hold it up?

Every tool that reads an API answers with what the API holds. This module
asks the harder question — *can this idea be built here, and is there room for
it* — and, more importantly, it is built so that the answer can be **no**.

Two checks, each one a Qloo workflow, each one able to fail:

1. **Does the audience pull toward this place?** (`rank`) The neighbourhood's
   real venues are ranked against the audience's cultural signals. A
   direction built around the place that ranks *last* for those signals is a
   direction the audience does not pull toward.
2. **Is there room, or a fight?** (`compare_audiences`) The direction's
   anchor is compared with the rest of the neighbourhood. Qloo's tag URNs
   carry their family, and the family is what makes this readable: a
   ``genre`` or ``category`` tag says what the place **is** — a park is a
   park — while an ``activities``, ``inclusivity``, ``interests`` or
   ``lifestyle`` tag says what culture **happens** there. An anchor that
   carries only the first kind brings nothing the neighbourhood does not
   already have: it is the same crowd in a different room. An anchor that
   carries the second kind is the opening.

The verdicts are deliberately narrow. These checks establish **local cultural
fit**, not demand, competition, rent or willingness to pay — and the reason
each one is reported says exactly that:

- ``supported`` — it passes the checks that could be run, within the
  evidence that was retrieved.
- ``contested`` — the evidence contradicts a specific premise, and the
  premise is named.
- ``unproven`` — there was not enough retrieved evidence to say either way.

A direction is never called a good business. It is called supported,
contested, or unproven, by the evidence.
"""
from __future__ import annotations

from typing import Optional

from .models import Evidence, GenerateResponse, ProjectRequest
from .providers import QlooHarnessError, QlooHarnessProvider

SUPPORTED = 'supported'
CONTESTED = 'contested'
UNPROVEN = 'unproven'

#: The order a challenged set is presented in. A direction the evidence
#: supports leads; one the evidence argues with is last.
VERDICT_ORDER = {SUPPORTED: 0, UNPROVEN: 1, CONTESTED: 2}

#: What the verdict is about, in words. The verdict is narrow on purpose: it
#: says whether the *audience* pulls toward the place a direction is built
#: around, and whether that place brings a cultural signal the neighbourhood
#: does not already have. It does not say the business is good, and it is
#: labelled so that nobody can read more into it than it says.
VERDICT_SCOPE = 'Audience–anchor fit'

#: The version of the decision policy. A verdict that cannot be traced to the
#: policy that produced it is not a verdict, it is an opinion.
POLICY_VERSION = 'anchor-fit-1'

#: Below this many retrieved venues, a check is reported as inconclusive
#: rather than as a verdict. Two places are not a market.
MINIMUM_VENUES = 3

#: The tag families that say what a place **is** — or how it runs. Every
#: place has these, so they cannot tell one place from another: a place is a
#: "genre" and a "category", and it offers a "service_type".
PLAIN_FAMILIES = ('genre', 'category', 'service_type', 'amenities', 'services',
                   'facilities', 'features')

#: The families that carry the culture, in the founder's words: cuisine,
#: ambience, good_for, inclusivity, activities, interests, lifestyle, setting,
#: decor, mood, and the rest.
CULTURAL_FAMILIES = ('cuisine', 'ambience', 'good_for', 'inclusivity', 'activities',
                      'interests', 'lifestyle', 'setting', 'decor', 'mood', 'events',
                      'demographic', 'customer_segment', 'subculture', 'values',
                      'occasion', 'diet', 'travel_style', 'personality')

#: How the two kinds of tag are named on screen.
SIGNAL_WORDS = 'cuisine, ambience, good_for, inclusivity, activities and the rest'


def guess_demographic(audience: str) -> str:
    """The demographic phrase to rank against, read from the founder's words.

    Qloo's ``rank`` workflow needs a profile to rank against — a location
    and a tag list on their own return nothing — and it converts a plain
    phrase such as "young adults" into its own age and gender signals. The
    phrase that was sent is returned with the answer, so the studio can show
    it rather than leave the ranking unexplained.
    """
    text = (audience or '').lower()
    if 'senior' in text or 'elderly' in text or 'retire' in text:
        return 'seniors'
    if 'gen z' in text or 'gen-z' in text or 'teen' in text:
        return 'gen z'
    if 'millennial' in text:
        return 'millennials'
    if 'women' in text or 'female' in text or 'woman' in text:
        return 'women 35-44' if any(word in text for word in ('35', '40', '45')) else 'women 25-34'
    if 'men' in text or 'male' in text or 'man' in text:
        return 'men 35-44' if any(word in text for word in ('35', '40', '45')) else 'men 25-34'
    if 'young' in text:
        return 'young adults'
    return 'millennials'


def _tag_family(tag_id: Optional[str]) -> str:
    """The family a Qloo tag belongs to: ``urn:tag:activities:place:x`` -> ``activities``."""
    if not isinstance(tag_id, str):
        return ''
    parts = tag_id.split(':')
    # urn : tag : family : scope [ : value ]
    return parts[2] if len(parts) > 2 else ''


def _is_cultural_signal(tag: dict) -> bool:
    """Whether a tag says something about the culture, rather than the type.

    A ``genre``, ``category`` or ``service_type`` tag is what the place is
    and how it runs — "Place", "City Park", "Dine-in" — and every place has
    one. The families that carry the culture are the ones a founder can build
    on: "Bar food", "Energetic", "Nightlife", "LGBTQ+ friendly", "Hiking".
    An unknown family counts as plain, so the rule can say no.
    """
    family = _tag_family(tag.get('tag_id'))
    if family in PLAIN_FAMILIES:
        return False
    return family in CULTURAL_FAMILIES


def _venues(evidence: list[Evidence]) -> list[Evidence]:
    return [item for item in evidence if item.kind == 'entity' and item.entityId]


def _rank_venues(provider: QlooHarnessProvider, project: ProjectRequest,
                 venues: list[Evidence], demographic: str) -> dict[str, dict]:
    """Rank the neighbourhood's venues against a profile for this audience.

    One call for the whole set, so the directions can be compared with each
    other: each one is judged by where *its* venue lands among the places
    Qloo actually returned.

    The profile is a demographic phrase rather than the audience's own tags:
    Qloo's `rank` workflow returns nothing when it is given a location and a
    tag list alone, and it converts the phrase into its own age and gender
    signals, which come back with the answer.
    """
    if not venues:
        return {}
    envelope, _cached, _requests = provider.run_workflow_cached('rank', {
        'options': [venue.entityId for venue in venues if venue.entityId],
        'option_type': 'place',
        'signal_location': project.location,
        'demographic': demographic,
    })
    ranked: dict[str, dict] = {}
    for index, row in enumerate(provider.rows(envelope)):
        entity_id = row.get('entity_id') or row.get('id')
        if not isinstance(entity_id, str):
            continue
        ranked[entity_id] = {
            'position': index + 1,
            'total': 0,
            'affinity': provider._affinity(row),
            'name': row.get('name') or '',
        }
    for entry in ranked.values():
        entry['total'] = len(ranked)
    return ranked


def _compare_with_neighbourhood(provider: QlooHarnessProvider, anchor: Evidence,
                                other_venues: list[Evidence]) -> dict:
    """Compare the direction's anchor with the rest of the neighbourhood.

    One place against the others, so what comes back is about *that* place:
    the tags it shares with the neighbourhood, and the ones only it carries.
    """
    if not anchor.entityId or not other_venues:
        return {}
    envelope, _cached, _requests = provider.run_workflow_cached('compare_audiences', {
        'group_a': [anchor.entityId],
        'group_b': [venue.entityId for venue in other_venues if venue.entityId],
        'target_type': 'place',
        'limit': 12,
    })
    results = envelope.get('results')
    results = results if isinstance(results, dict) else {}

    def rows(key: str) -> list[dict]:
        value = results.get(key)
        return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []

    shared = [row for row in rows('tags')]
    own = rows('a')
    signals = [row for row in own if _is_cultural_signal(row)]
    types = [row for row in own if not _is_cultural_signal(row)]
    return {
        'shared': [{'tag': row.get('name') or row.get('tag_id'),
                    'score': (row.get('query') or {}).get('score') if isinstance(row.get('query'), dict) else None}
                   for row in shared if row.get('name') or row.get('tag_id')],
        'ownSignals': [{'tag': row.get('name') or row.get('tag_id'),
                        'family': _tag_family(row.get('tag_id')),
                        'popularity': row.get('popularity')} for row in signals],
        'ownTypes': [row.get('name') or row.get('tag_id') for row in types],
        'compared': 1 + len(other_venues),
    }


def _challenge_one(provider: QlooHarnessProvider, project: ProjectRequest,
                   concept, venues: list[Evidence], tags: list[str],
                   ranking: dict[str, dict],
                   anchor_override: Optional[str] = None) -> dict:
    """One direction, and the checks run against it.

    The direction states what it is claiming before it is checked, and what
    result would contradict it. The claim, the falsifier and the verdict come
    back together, so the reader can see the reasoning and disagree with it.
    """
    # The concept's own order matters: the first venue it cites is the one it
    # is built around, and that is the one the checks are about.
    by_id = {venue.id: venue for venue in venues}
    concept_venues = [by_id[eid] for eid in concept.evidenceIds if eid in by_id]
    cited = {venue.id for venue in concept_venues}
    other_venues = [venue for venue in venues if venue.id not in cited]
    primary = concept_venues[0] if concept_venues else None

    # The judge may hold the claim to a different anchor: the same direction,
    # built around a different place. The verdict then answers for that one.
    if anchor_override:
        alternative = next((venue for venue in venues if venue.entityId == anchor_override), None)
        if alternative is not None:
            primary = alternative
            other_venues = [venue for venue in venues if venue.entityId != anchor_override]

    result = {
        'directionId': concept.id,
        'name': concept.name,
        'verdict': UNPROVEN,
        'scope': VERDICT_SCOPE,
        'reason': '',
        'claim': (
            f'The place this direction is built around — {primary.label} — is one this audience '
            'is drawn to, and it carries a cultural signal the rest of the neighbourhood does not.'
            if primary else 'This direction names no place, so it makes no claim to check.'
        ),
        'falsifier': (
            f'Qloo ranks {primary.label} last of the places it returned for this audience, or it '
            'carries only the signals every place here carries.'
            if primary else 'There is nothing to falsify.'
        ),
        'unprovenIf': (
            'Qloo returned too few places to compare, or no ranking and no comparison came back.'
        ),
        'anchor': {'entityId': primary.entityId, 'label': primary.label} if primary else None,
        'alternatives': [
            {'entityId': venue.entityId, 'label': venue.label}
            for venue in venues if primary is not None and venue.entityId != primary.entityId
        ],
        'checks': [],
        'coverage': {
            'venuesRetrieved': len(venues),
            'venuesCited': len(concept_venues),
            'venuesCompared': 0,
            'tagsUsed': len(tags),
            'note': '',
        },
    }

    if not concept_venues:
        result['reason'] = 'This direction cites no venue, so there is nothing to test.'
        return result

    # ---- is there enough evidence to say anything? ------------------------
    if len(venues) < MINIMUM_VENUES:
        result['reason'] = (
            f'Qloo returned {len(venues)} place'
            f'{"" if len(venues) == 1 else "s"} for this brief. '
            'That is not enough to test a direction against.'
        )
        result['coverage']['note'] = 'Too few places were retrieved to test this.'
        return result

    # ---- check 1: does the audience pull toward this place? ---------------
    rank_entry = ranking.get(primary.entityId) if primary else None
    if rank_entry:
        position, total = rank_entry['position'], rank_entry['total']
        affinity = rank_entry['affinity']
        if position == 1:
            result['checks'].append({
                'name': 'Does the audience pull toward this place?',
                'result': 'pass',
                'detail': (
                    f'Qloo ranks {primary.label} first of {total} places for this audience’s '
                    'cultural signals.'
                ),
                'metric': {'affinity': affinity, 'position': position, 'of': total},
            })
        elif position == total and total > 1:
            result['checks'].append({
                'name': 'Does the audience pull toward this place?',
                'result': 'fail',
                'detail': (
                    f'Qloo ranks {primary.label} last of {total} places for this audience’s '
                    'cultural signals. The audience pulls somewhere else.'
                ),
                'metric': {'affinity': affinity, 'position': position, 'of': total},
            })
        else:
            result['checks'].append({
                'name': 'Does the audience pull toward this place?',
                'result': 'mixed',
                'detail': (
                    f'Qloo ranks {primary.label} {position} of {total} for this audience’s '
                    'cultural signals.'
                ),
                'metric': {'affinity': affinity, 'position': position, 'of': total},
            })
    else:
        result['checks'].append({
            'name': 'Does the audience pull toward this place?',
            'result': 'mixed',
            'detail': 'Qloo returned no ranking for these places against this audience’s signals.',
            'metric': {},
        })

    # ---- check 2: is there room, or a fight? -----------------------------
    comparison = _compare_with_neighbourhood(provider, primary, other_venues) if primary else {}
    if comparison:
        result['coverage']['venuesCompared'] = comparison['compared']
        signals, types, shared = comparison['ownSignals'], comparison['ownTypes'], comparison['shared']
        if signals:
            labels = ', '.join(str(entry.get('tag')) for entry in signals[:3])
            result['checks'].append({
                'name': 'Is there room, or a fight?',
                'result': 'pass',
                'detail': (
                    f'{primary.label} carries {len(signals)} cultural signal'
                    f'{"" if len(signals) == 1 else "s"} the other places here do not: {labels}. '
                    'That is the opening.'
                ),
                'metric': {'signals': len(signals), 'shared': len(shared)},
            })
        elif types:
            result['checks'].append({
                'name': 'Is there room, or a fight?',
                'result': 'fail',
                'detail': (
                    f'{primary.label} carries only what the neighbourhood already has: '
                    f'{", ".join(str(label) for label in types[:3])}. It is the same kind of place, '
                    'for the same audience.'
                ),
                'metric': {'signals': 0, 'shared': len(shared)},
            })
        else:
            result['checks'].append({
                'name': 'Is there room, or a fight?',
                'result': 'mixed',
                'detail': 'Qloo returned no cultural comparison for these places.',
                'metric': {'signals': 0, 'shared': 0},
            })
    else:
        result['checks'].append({
            'name': 'Is there room, or a fight?',
            'result': 'mixed',
            'detail': 'There was no second group of places to compare these with.',
            'metric': {},
        })

    # ---- the verdict ------------------------------------------------------
    failures = [check for check in result['checks'] if check['result'] == 'fail']
    passes = [check for check in result['checks'] if check['result'] == 'pass']
    if failures:
        result['verdict'] = CONTESTED
        result['reason'] = failures[0]['detail']
    elif passes:
        result['verdict'] = SUPPORTED
        result['reason'] = passes[0]['detail']
    else:
        result['verdict'] = UNPROVEN
        result['reason'] = 'The retrieved evidence did not settle this direction either way.'
    result['coverage']['note'] = (
        f'Judged on {len(venues)} places Qloo returned for this brief, '
        f'{len(concept_venues)} of which this direction cites. '
        'These checks speak to local cultural fit only — not demand, competition, rent, or '
        'willingness to pay.'
    )
    result['coverage']['howSignalsWereCounted'] = (
        f'A tag counts as a cultural signal when it is not a {SIGNAL_WORDS.split(",")[0]} '
        f'type tag: Qloo’s “genre” and “category” tags say what a place is, and every place has one.'
    )
    return result


def challenge_directions(project: ProjectRequest, response: GenerateResponse,
                          direction_id: Optional[str] = None,
                          anchor_entity_id: Optional[str] = None) -> dict:
    """Run the checks, and put the directions back in the order the evidence leaves them."""
    provider = QlooHarnessProvider()
    venues = _venues(response.evidence)
    tags = list(response.provenance.resolved_tags) if response.provenance else []
    if not venues:
        raise QlooHarnessError(
            'There are no places to test this brief against. Run the research first.',
            code='NO_EVIDENCE')
    if not tags:
        raise QlooHarnessError(
            'The audience did not resolve into cultural signals, so there is nothing to test against.',
            code='NO_EVIDENCE')

    ranking = _rank_venues(provider, project, venues, guess_demographic(project.audience))
    results = []
    for concept in response.concepts:
        if direction_id and concept.id != direction_id:
            continue
        results.append(_challenge_one(provider, project, concept, venues, tags, ranking,
                                       anchor_entity_id))
    if not results:
        raise QlooHarnessError('That direction is not part of this exploration.', code='INVALID_REQUEST')

    ordered = sorted(results, key=lambda entry: (VERDICT_ORDER.get(entry['verdict'], 1), entry['name']))
    return {
        'directions': results,
        'order': [entry['directionId'] for entry in ordered],
        'summary': (
            f'Tested {len(results)} direction{"" if len(results) == 1 else "s"} against '
            f'{len(venues)} places and {len(tags)} cultural signals Qloo returned.'
        ),
        'scope': VERDICT_SCOPE,
        'policyVersion': POLICY_VERSION,
        'profile': {
            'demographic': guess_demographic(project.audience),
            'location': project.location,
            'signals': tags,
        },
        'whatThisIs': (
            'Local cultural fit, measured. These checks ask whether the audience pulls toward the '
            'place an idea is built on, and whether that place brings a cultural signal the '
            'neighbourhood does not already have. They do not measure demand, competition, rent, '
            'or willingness to pay, and they say nothing about the business as a business.'
        ),
    }
