"""Conservative, inspectable relevance rules over returned Qloo text.

Retrieval affinity is an association, not proof of category or local demand.
All sources remain inspectable; only suitable references can anchor a concept.
No extra network calls, invented confidence percentages, or inferred geography.
"""
from __future__ import annotations

import re

VERSION = 'relevance-1'
FAMILIES = {
    'bakery': ('bakery', 'bakeries', 'bread', 'sourdough', 'croissant', 'patisserie', 'pâtisserie', 'boulangerie'),
    'coffee': ('café', 'cafe', 'coffee', 'espresso'),
    'records': ('vinyl', 'record shop', 'record store', 'records'),
    'ceramics': ('ceramic', 'ceramics', 'pottery', 'potter', 'potters'),
    'fashion': ('fashion', 'clothing', 'apparel', 'boutique'),
    'wellness': ('wellness', 'spa', 'yoga', 'meditation', 'fitness', 'pilates'),
    'hospitality': ('hotel', 'resort', 'hostel', 'guesthouse', 'lodging'),
    'music': ('concert', 'concerts', 'music', 'performance', 'comedy', 'theatre', 'theater'),
    'food': ('restaurant', 'restaurants', 'dining', 'bar', 'pizza', 'bakery', 'bakeries', 'bread', 'café', 'cafe', 'coffee'),
}
CATEGORY = {'Food & beverage': 'food', 'Hospitality': 'hospitality', 'Wellness': 'wellness', 'Entertainment': 'music'}


def matches(text: str, terms) -> list[str]:
    return [term for term in terms if re.search(r'\b' + re.escape(term) + r'\b', text, re.I)]


def brief_family(business_type: str, idea: str, audience: str) -> str:
    # An explicit business takes precedence over an audience's incidental interests.
    for text in (idea, audience):
        for family, terms in FAMILIES.items():
            if matches(text, terms):
                return family
    return CATEGORY.get(business_type, '')


def assess(*, business_type: str, idea: str, audience: str, location: str,
           name: str, description: str, returned_location: str = '',
           kind: str = 'entity', has_identifier: bool = True) -> dict:
    family = brief_family(business_type, idea, audience)
    text = f'{name} {description}'
    hits = matches(text, FAMILIES.get(family, ()))
    reasons = []
    if not has_identifier:
        relation = 'excluded'
        reasons.append('No returned Qloo identifier; this source cannot anchor or support a cited direction.')
    elif kind == 'crossdomain':
        relation = 'indirect'
        reasons.append('Same audience seeds, another domain, no location constraint. No business-specific relationship was established.')
    elif hits:
        relation = 'direct'
        reasons.append(f'Returned text matches the {family} brief: {", ".join(hits)}. This is a text match, not verified operating suitability.')
    elif family:
        relation = 'indirect'
        reasons.append(f'Returned text does not establish a {family} reference. Retained as a cultural association; excluded from concept anchors.')
    else:
        relation = 'unknown'
        reasons.append('The brief has no recognized category. Specify the business idea to assess reference suitability.')
    if not returned_location:
        geography = 'unknown'
        reasons.append('No location metadata returned. The query location is not the place location.')
    elif location.split(',')[0].strip().casefold() in returned_location.casefold():
        geography = 'text_match'
        reasons.append('Returned location text matches the requested city; neighbourhood and travel time are unverified.')
    else:
        geography = 'unverified'
        reasons.append(f'Returned location is {returned_location}; it does not confirm the requested city {location}.')
    return {'version': VERSION, 'relationship': relation, 'category': family or 'unknown',
            'anchorEligible': relation == 'direct', 'geography': geography,
            'audience': 'returned_for_seeds', 'confidence': 'rule_assessment_only',
            'reasons': reasons}
