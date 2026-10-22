"""Challenge a direction: does the local evidence hold it up?

Every tool that reads an API answers with what the API holds. This module
asks the harder question — *can this idea be built here, and is there room for
it* — and, more importantly, it is built so that the answer can be **no**.

Two checks, each one a Qloo workflow, each one able to fail:

1. **Where does this place sit for that profile?** (`rank`) The retrieved
   places are ranked against a demographic profile — proposed by
   CultureForge from the founder's own words, shown before the test runs,
   and changeable — because Qloo's ``rank`` workflow returns nothing when it
   is given a location and a tag list alone. The request carries a profile
   and a location, **not** the audience's own cultural tags, and the wording
   says so. The anchor passes in the top third of the ranked places, fails
   in the bottom third, and is mixed in between (``rank_band``).
2. **What cultural tags were returned for this anchor?**
   (``compare_audiences``) The anchor is compared with **every other place
   that was returned**, cited or not, so that changing the anchor changes
   one assumption and not two. Qloo's tag URNs carry their family, and the
   family is what makes this readable: a ``genre`` or ``category`` tag says
   what the place **is** — a park is a park — while an ``activities``,
   ``inclusivity``, ``interests`` or ``lifestyle`` tag says what culture
   **happens** there. A qualifying cultural tag returned for the anchor is
   a potential input to a concept. It is never called exclusive: the
   comparison response is a bounded list, and a tag's absence from it is
   not proof that the other places lack it.

The verdicts are deliberately narrow. These checks assess a **scoped anchor
hypothesis within the retrieved sample**, not demand, competition, rent or
willingness to pay — and the reason each one is reported says exactly that:

- ``supported`` — it passes the checks that could be run, within the
  evidence that was retrieved.
- ``contested`` — the evidence contradicts a specific premise, and the
  premise is named.
- ``unproven`` — there was not enough retrieved evidence to say either way.

A direction is never called a good business. It is called supported,
contested, or unproven, by the evidence.

Policy anchor-fit-4 is written out in docs/EVIDENCE_POLICY.md: the rule,
its inputs, the minimum sample, the confidence label and the sensitivity
checks. It produces no score. Every number it reports is a position, a count
or a value Qloo returned.
"""
from __future__ import annotations

import re
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
#: says whether the place a direction is built around ranks well for a
#: demographic profile, and whether Qloo returned a qualifying cultural tag
#: for it in a comparison with the other retrieved places. It does not say the
#: business is good, and it is labelled so that nobody can read more into it
#: than it says.
VERDICT_SCOPE = 'Anchor fit within the retrieved sample'

#: The version of the decision policy. A verdict that cannot be traced to the
#: policy that produced it is not a verdict, it is an opinion.
POLICY_VERSION = 'anchor-fit-4'

#: Below this many retrieved venues, a check is reported as inconclusive
#: rather than as a verdict. Two places are not a market.
MINIMUM_VENUES = 3

#: From this many ranked places, the confidence label is "moderate"; below
#: it, "low". It is never "high": the sample is at most ten places, ranked
#: against one demographic profile.
MODERATE_SAMPLE = 6

#: The demographic phrases this policy will send to Qloo's rank workflow.
#: These are the phrases Qloo's documented mapping converts into age and
#: gender signals; anything else is refused before a request is made.
DEMOGRAPHIC_CHOICES = ('gen z', 'millennials', 'young adults', 'women 25-34', 'women 35-44',
                       'men 25-34', 'men 35-44', 'seniors')
DEFAULT_DEMOGRAPHIC = 'millennials'


def rank_band(position: int, total: int) -> str:
    """The rank check, as a rule: top third passes, bottom third fails.

    The band is ``k = max(1, total // 3)`` places at each end. With three to
    five places that is first and last only; with ten it is positions 1-3
    and 8-10. A single ranked place has no one to be compared with.
    """
    if total < 2:
        return 'mixed'
    k = max(1, total // 3)
    if position <= k:
        return 'pass'
    if position > total - k:
        return 'fail'
    return 'mixed'


def band_words(total: int) -> str:
    k = max(1, total // 3)
    top = 'first' if k == 1 else f'positions 1-{k}'
    bottom = 'last' if k == 1 else f'positions {total - k + 1}-{total}'
    return f'the top band is {top} and the bottom band is {bottom} of {total}'


def confidence_label(sample: int, stable: bool) -> tuple[str, str]:
    """How much weight the verdict can bear, from the sample and its stability."""
    if sample < MINIMUM_VENUES:
        return 'none', f'Fewer than {MINIMUM_VENUES} places were ranked, so there is no verdict to weigh.'
    if not stable:
        return 'low', ('Removing a single other place changes the rank check, so the verdict '
                       'depends on which places happened to be returned.')
    if sample < MODERATE_SAMPLE:
        return 'low', f'Only {sample} places were ranked.'
    return 'moderate', (f'{sample} places were ranked and no single removal changes the rank check. '
                        'It is not "high": the sample is at most ten places and one demographic profile.')


def _sensitivity(ranking: dict[str, dict], anchor_id: Optional[str],
                 labels: dict[str, str]) -> dict:
    """Leave-one-out and alternative anchors, from the same ranking: no new call.

    Leave-one-out removes each other ranked place in turn and re-applies the
    band rule to the anchor's new position. Alternative anchors apply the
    rule to every other ranked place. Only the rank check is recomputed; the
    tag check needs its own Qloo comparison, which the re-test runs.
    """
    order = sorted(ranking.items(), key=lambda item: item[1]['position'])
    ids = [entity_id for entity_id, _ in order]
    total = len(ids)
    if not anchor_id or anchor_id not in ids or total < MINIMUM_VENUES:
        return {'stable': False, 'checked': False, 'changesWhenRemoved': [], 'alternativeAnchors': []}
    original = rank_band(ids.index(anchor_id) + 1, total)
    changes = []
    for removed in ids:
        if removed == anchor_id:
            continue
        remaining = [entity_id for entity_id in ids if entity_id != removed]
        result = rank_band(remaining.index(anchor_id) + 1, total - 1)
        if result != original:
            changes.append({'removed': labels.get(removed, removed), 'rankCheck': result})
    alternatives = [{
        'entityId': entity_id,
        'label': labels.get(entity_id, entity_id),
        'position': index + 1,
        'rankCheck': rank_band(index + 1, total),
    } for index, entity_id in enumerate(ids) if entity_id != anchor_id]
    return {'stable': not changes, 'checked': True, 'rankCheck': original,
            'changesWhenRemoved': changes, 'alternativeAnchors': alternatives}

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


#: The demographic phrases Qloo's documented mapping understands, matched on
#: whole words. A substring match is how "restaurant" ends up looking like
#: "rest", so the pattern is anchored to word boundaries.
_DEMOGRAPHIC_RULES: tuple[tuple[str, str], ...] = (
    (r'\bseniors?\b|\belderly\b|\bretire\w*\b', 'seniors'),
    (r'\bgen[\s-]?z\b|\bteens?\b|\bteenagers?\b', 'gen z'),
    (r'\bmillennials?\b', 'millennials'),
    (r'\bwomen\b|\bfemale\b|\bwoman\b', 'women'),
    (r'\bmen\b|\bmale\b|\bman\b', 'men'),
    (r'\byoung(?:er)?\b', 'young adults'),
)

#: The ages that move a profile up a band. Both the digits and the words
#: count: "in their thirties" is as plain as "35".
_OLDER_AGE = re.compile(r'\b(3\d|4\d|5\d)\b|\b(thirties|forties|fifties)\b')


def guess_demographic(audience: str) -> tuple[str, bool]:
    """The demographic phrase to rank against, read from the founder's words.

    Qloo's ``rank`` workflow needs a profile to rank against — a location
    and a tag list on their own return nothing — and it converts a plain
    phrase such as "young adults" into its own age and gender signals.

    Two things this must not do. It must not match a word inside another
    word: "restaurant" is not "rest". And it must not pretend the phrase was
    inferred by Qloo — CultureForge proposes it from the brief, Qloo
    converts it into request signals. The second value says whether the
    phrase was actually named in the brief; when it was not, the screen says
    that the profile was a default and that it can be changed.
    """
    text = (audience or '').lower()
    older = _OLDER_AGE.search(text)
    for pattern, phrase in _DEMOGRAPHIC_RULES:
        if not re.search(pattern, text):
            continue
        if phrase in ('women', 'men'):
            band = '35-44' if older else '25-34'
            return f'{phrase} {band}', True
        return phrase, True
    return DEFAULT_DEMOGRAPHIC, False


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


def _compare_with_other_places(provider: QlooHarnessProvider, anchor: Evidence,
                               other_venues: list[Evidence]) -> dict:
    """Compare the direction's anchor with the other retrieved places.

    One place against the others, so what comes back is about *that* place:
    the tags Qloo returned for it, and the tags both sides carry.

    The comparison set is always **every other place Qloo returned**, whether
    or not the direction cites it. A comparison against only the uncited
    places would change the universe when the anchor changes, and the two
    answers would not be comparable.
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

    shared = rows('tags')
    own = rows('a')
    # A tag that appears in the shared list is explicitly carried by both
    # sides. A tag that is absent from it is not proof that the other side
    # lacks it — the comparison response is a bounded list — so nothing here
    # claims that a tag is exclusive to the anchor.
    shared_ids = {row.get('tag_id') for row in shared if row.get('tag_id')}
    signals = [row for row in own if _is_cultural_signal(row)]
    types = [row for row in own if not _is_cultural_signal(row)]
    shared_labels = [
        row.get('name') or row.get('tag_id')
        for row in shared if row.get('name') or row.get('tag_id')
    ]
    return {
        'shared': [{'tag': row.get('name') or row.get('tag_id'),
                    'score': (row.get('query') or {}).get('score') if isinstance(row.get('query'), dict) else None}
                   for row in shared if row.get('name') or row.get('tag_id')],
        'ownSignals': [{'tag': row.get('name') or row.get('tag_id'),
                        'family': _tag_family(row.get('tag_id')),
                        'popularity': row.get('popularity'),
                        'alsoShared': row.get('tag_id') in shared_ids}
                       for row in signals],
        'ownTypes': [row.get('name') or row.get('tag_id') for row in types],
        'sharedSignals': [
            row.get('name') or row.get('tag_id')
            for row in shared
            if _is_cultural_signal(row) and (row.get('name') or row.get('tag_id'))
        ] or shared_labels[:3],
        'compared': 1 + len(other_venues),
        'comparedWith': [venue.label for venue in other_venues if venue.entityId],
    }


def _challenge_one(provider: QlooHarnessProvider, project: ProjectRequest,
                   concept, venues: list[Evidence], tags: list[str],
                   ranking: dict[str, dict], demographic: str, inferred: bool,
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
    primary = concept_venues[0] if concept_venues else None
    original_anchor = primary.entityId if primary else None

    # The comparison set is every other place Qloo returned, cited or not.
    # Changing the anchor must change one assumption, not two.
    other_venues = [venue for venue in venues if venue.entityId != (primary.entityId if primary else None)]

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
            f'Within the places Qloo returned, {primary.label} ranks in the top third for the '
            'demographic profile, and Qloo returned a qualifying cultural tag '
            'for it in the comparison against the other retrieved places.'
            if primary else 'This direction names no place, so it makes no claim to check.'
        ),
        'falsifier': (
            f'Qloo ranks {primary.label} in the bottom third of the places it returned for that '
            'demographic. (No qualifying cultural tag leaves it unproven, not contradicted.)'
            if primary else 'There is nothing to falsify.'
        ),
        'unprovenIf': (
            'Qloo returned too few places to compare, or either the ranking or the tag '
            'comparison could not be run.'
        ),
        'anchor': {'entityId': primary.entityId, 'label': primary.label} if primary else None,
        # When the anchor was changed, the direction itself was not rebuilt.
        # The screen has to say so, or a badge sits beside a description and
        # a photograph that belong to a different place.
        'originalAnchor': ({
            'entityId': original_anchor,
            'label': next((venue.label for venue in venues
                           if venue.entityId == original_anchor), ''),
        } if original_anchor and primary and original_anchor != primary.entityId else None),
        'isCounterfactual': bool(anchor_override and primary
                                 and original_anchor != primary.entityId),
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

    # ---- check 1: where does this place sit for the inferred profile? ------
    # The ranking request carries a demographic profile and a location, not
    # the audience's own cultural tags. The wording says so.
    rank_entry = ranking.get(primary.entityId) if primary else None
    # CultureForge proposes the profile; Qloo converts it into the request
    # signals it actually ranks against. The screen says which is which.
    if inferred == 'chosen':
        profile = f'the “{demographic}” demographic you chose, near {project.location}'
    elif inferred:
        profile = f'the “{demographic}” demographic CultureForge proposed from the brief, near {project.location}'
    else:
        profile = (f'the default “{demographic}” demographic — no demographic was named in the '
                   f'brief, so this is a default and can be changed — near {project.location}')
    if rank_entry:
        position, total = rank_entry['position'], rank_entry['total']
        affinity = rank_entry['affinity']
        outcome = rank_band(position, total)
        where = {'pass': 'in the top band', 'fail': 'in the bottom band', 'mixed': 'between the bands'}[outcome]
        detail = (f'Qloo ranks {primary.label} {position} of the {total} places it returned for '
                  f'{profile}: {where} ({band_words(total)}).')
        detail += (' It ranks low within this retrieved set.' if outcome == 'fail'
                   else ' This ranking does not use the audience signals you selected.')
        result['checks'].append({
            'name': 'Where does this place sit for that profile?',
            'result': outcome,
            'detail': detail,
            'metric': {'affinity': affinity, 'position': position, 'of': total,
                       'demographic': demographic},
        })
    else:
        result['checks'].append({
            'name': 'Where does this place sit for that profile?',
            'result': 'mixed',
            'detail': f'Qloo returned no ranking for these places for {profile}.',
            'metric': {'demographic': demographic},
        })

    # ---- check 2: is there room, or a fight? -----------------------------
    comparison = _compare_with_other_places(provider, primary, other_venues) if primary else {}
    if comparison:
        result['coverage']['venuesCompared'] = comparison['compared']
        result['coverage']['comparedWith'] = comparison['comparedWith']
        signals, types = comparison['ownSignals'], comparison['ownTypes']
        shared = comparison['shared']
        others = 'the other retrieved places'
        if signals:
            labels = ', '.join(str(entry.get('tag')) for entry in signals[:3])
            shared_note = ''
            if comparison['sharedSignals']:
                shared_note = (f' Qloo also returned '
                               f'{", ".join(str(label) for label in comparison["sharedSignals"][:3])} '
                               'for both sides.')
            result['checks'].append({
                'name': 'What cultural tags were returned for this anchor?',
                'result': 'pass',
                'detail': (
                    f'Qloo returned {len(signals)} qualifying cultural tag'
                    f'{"" if len(signals) == 1 else "s"} for {primary.label} in the comparison '
                    f'against {others}: {labels}.{shared_note} This is what the tag data shows '
                    'about the anchor — it does not establish that the other places lack them, '
                    'and it is not evidence of an unmet need.'
                ),
                'metric': {'signals': len(signals), 'shared': len(shared)},
            })
        elif types:
            # The tags returned for the anchor are type and operational tags.
            # That is neither a cultural signal nor evidence against it.
            result['checks'].append({
                'name': 'What cultural tags were returned for this anchor?',
                'result': 'mixed',
                'detail': (
                    f'The tags returned for {primary.label} in this comparison are type and '
                    f'operational tags ({", ".join(str(label) for label in types[:3])}). No '
                    'qualifying cultural tag was returned for it under this policy, so '
                    'distinctiveness is unproven.'
                ),
                'metric': {'signals': 0, 'shared': len(shared)},
            })
        else:
            result['checks'].append({
                'name': 'What cultural tags were returned for this anchor?',
                'result': 'mixed',
                'detail': (
                    f'Qloo returned no qualifying cultural tag for {primary.label} in this '
                    'comparison, so distinctiveness is unproven.'
                ),
                'metric': {'signals': 0, 'shared': len(shared)},
            })
    else:
        result['checks'].append({
            'name': 'What cultural tags were returned for this anchor?',
            'result': 'mixed',
            'detail': 'There was no second group of places to compare these with.',
            'metric': {},
        })

    # ---- the verdict ------------------------------------------------------
    failures = [check for check in result['checks'] if check['result'] == 'fail']
    passes = [check for check in result['checks'] if check['result'] == 'pass']
    mixed = [check for check in result['checks'] if check['result'] == 'mixed']
    if failures:
        result['verdict'] = CONTESTED
        result['reason'] = failures[0]['detail']
    elif len(passes) == len(result['checks']) and result['checks']:
        # Both checks have to hold. One passing check and one missing is not
        # a verdict, it is half an answer.
        result['verdict'] = SUPPORTED
        result['reason'] = passes[0]['detail']
    elif mixed:
        result['verdict'] = UNPROVEN
        result['reason'] = mixed[0]['detail']
    else:
        result['verdict'] = UNPROVEN
        result['reason'] = 'The retrieved evidence did not settle this direction either way.'
    rank_check = next((check for check in result['checks']
                       if check['name'] == 'Where does this place sit for that profile?'), None)
    tag_check = next((check for check in result['checks']
                      if check['name'] == 'What cultural tags were returned for this anchor?'), None)
    sample = max((entry['total'] for entry in ranking.values()), default=0)
    sensitivity = _sensitivity(ranking, primary.entityId if primary else None,
                               {venue.entityId: venue.label for venue in venues if venue.entityId})
    confidence, confidence_reason = confidence_label(sample, sensitivity['stable'])
    result['index'] = {
        'policy': POLICY_VERSION,
        'rule': ('Contested if the rank check fails; supported only if the rank check and the '
                 'tag check both pass; otherwise unproven.'),
        'rankCheck': rank_check['result'] if rank_check else None,
        'tagCheck': tag_check['result'] if tag_check else None,
        'qualifyingTags': (tag_check or {}).get('metric', {}).get('signals'),
        'sampleSize': sample,
        'minimumSample': MINIMUM_VENUES,
        'confidence': confidence,
        'confidenceReason': confidence_reason,
        'sensitivity': sensitivity,
    }
    result['coverage']['note'] = (
        f'Judged on {len(venues)} places Qloo returned for this brief, '
        f'{len(concept_venues)} of which this direction cites. '
        'These checks assess a scoped anchor hypothesis within the retrieved sample — they do '
        'not measure demand, competition, rent, or willingness to pay.'
    )
    result['coverage']['howSignalsWereCounted'] = (
        'This policy counts a Qloo tag as a cultural signal when its family is not one of '
        + ', '.join(PLAIN_FAMILIES)
        + ' — the families that say what a place is and how it runs. A family the policy does '
        'not know does not count.'
    )
    return result


def challenge_directions(project: ProjectRequest, response: GenerateResponse,
                          direction_id: Optional[str] = None,
                          anchor_entity_id: Optional[str] = None,
                          demographic_override: Optional[str] = None) -> dict:
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

    proposed, named = guess_demographic(project.audience)
    if demographic_override:
        if demographic_override not in DEMOGRAPHIC_CHOICES:
            raise QlooHarnessError('That demographic profile is not one this policy can send to Qloo.',
                                   code='INVALID_REQUEST')
        demographic, inferred = demographic_override, 'chosen'
    else:
        demographic, inferred = proposed, named
    ranking = _rank_venues(provider, project, venues, demographic)
    results = []
    for concept in response.concepts:
        if direction_id and concept.id != direction_id:
            continue
        results.append(_challenge_one(provider, project, concept, venues, tags, ranking,
                                       demographic, inferred, anchor_entity_id))
    if not results:
        raise QlooHarnessError('That direction is not part of this exploration.', code='INVALID_REQUEST')

    ordered = sorted(results, key=lambda entry: (VERDICT_ORDER.get(entry['verdict'], 1), entry['name']))
    return {
        # The directions are returned in the order the evidence leaves them in,
        # so every surface that renders them shows the same order. `order` is
        # kept as the explicit list for callers that need the ids.
        'directions': ordered,
        'order': [entry['directionId'] for entry in ordered],
        'arrivalOrder': [entry['directionId'] for entry in results],
        'summary': (
            f'Checked {len(results)} anchor hypoth'
            f'{"esis" if len(results) == 1 else "eses"} using a demographic ranking and '
            f'anchor-tag comparisons across {len(venues)} retrieved places. The '
            f'{len(tags)} audience seed{"" if len(tags) == 1 else "s"} were used for '
            'retrieval, not for this ranking.'
        ),
        'scope': VERDICT_SCOPE,
        'policyVersion': POLICY_VERSION,
        'profile': {
            'demographic': demographic,
            # Whether the brief actually named this demographic. When it did
            # not, the screen says the profile is a default that can be
            # changed, rather than passing a guess off as an inference.
            'inferred': inferred is True,
            'source': ('chosen' if inferred == 'chosen' else 'named' if inferred else 'default'),
            'proposed': proposed,
            'choices': list(DEMOGRAPHIC_CHOICES),
            'proposedBy': ('you, before the test ran' if inferred == 'chosen'
                           else 'CultureForge, from the brief’s own words'),
            'location': project.location,
            'signals': tags,
        },
        'whatThisIs': (
            'A CultureForge policy check using Qloo ranking and the anchor tags Qloo returned. '
            'It asks where the place an idea is built on sits for a demographic profile, and '
            'whether a qualifying cultural tag was returned for it in a comparison with the '
            'other retrieved places. It is a consistency check against the same retrieved '
            'evidence, not an independent validation of it. It does not measure demand, '
            'profitability, footfall, commercial viability, competition, rent, or willingness to '
            'pay, and it says nothing about the business as a business.'
        ),
    }
