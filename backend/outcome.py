"""Why an answer has no supported direction, and what to do next.

States: supported, promising_unverified, contested, insufficient_evidence,
provider_failure. Nothing here invents evidence: a state is read from the
classified evidence, and ``missing`` names exactly what was not found.
"""
from __future__ import annotations

SUPPORTED = 'supported'
PROMISING = 'promising_unverified'
CONTESTED = 'contested'
INSUFFICIENT = 'insufficient_evidence'
PROVIDER_FAILURE = 'provider_failure'


def _counts(evidence) -> dict:
    counts: dict = {}
    for item in evidence:
        if getattr(item, 'kind', '') not in ('entity', 'crossdomain'):
            continue
        cls = (getattr(item, 'relevance', None) or {}).get('evidenceClass', 'unrelated')
        counts[cls] = counts.get(cls, 0) + 1
    return counts


def build_outcome(*, category, evidence, concepts, provider_failed: bool = False) -> dict:
    counts = _counts(evidence)
    base = {'counts': counts, 'category': category.family or None, 'categoryLabel': category.matched or None}
    if provider_failed:
        return {**base, 'state': PROVIDER_FAILURE, 'missing': ['A completed Qloo response'],
                'recovery': [{'action': 'retry', 'label': 'Try again'}]}
    if concepts:
        return {**base, 'state': SUPPORTED if counts.get('direct_business') else PROMISING, 'missing': [], 'recovery': []}
    missing: list[str] = []
    recovery: list[dict] = []
    if category.specificity == 'unknown' or not category.family:
        missing.append('A business category CultureForge could resolve from the idea')
        recovery.append({'action': 'name_business', 'label': 'Name the main kind of business'})
    else:
        if not counts.get('direct_business'):
            missing.append(f'Returned places that are themselves a {category.matched or category.family} business')
            recovery.append({'action': 'change_audience', 'label': 'Broaden or change the audience'})
            recovery.append({'action': 'change_location', 'label': 'Try a nearby or larger city'})
        if counts.get('cultural_attraction'):
            missing.append('Attractions were returned, but they are context, not competitors or references')
        if counts.get('unverified_geography'):
            missing.append('Matching places were returned for a different location than the one requested')
    if not missing:
        missing.append('Enough distinct, cited evidence to compose a direction')
    state = INSUFFICIENT
    return {**base, 'state': state, 'missing': missing, 'recovery': recovery}
