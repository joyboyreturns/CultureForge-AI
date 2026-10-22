"""Conservative, inspectable relevance rules over returned Qloo text.

Retrieval affinity is an association, not proof of category or local demand.
All sources remain inspectable; only suitable references can anchor a concept.
No extra network calls, invented confidence percentages, or inferred geography.

A brief is classified by its own words, never by a broader category it sits
inside. "Ice cream parlour" is not food, "gaming cafe" is not coffee and
"medical store" is not wellness. A category the rules do not recognise is
reported as unknown, and it is not widened to the business type or to an
audience's incidental words.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

VERSION = 'relevance-2'

#: Terms that identify a returned place. Used to judge whether a place's own
#: text is a reference for a family.
FAMILIES = {
    'bakery': ('bakery', 'bakeries', 'bread', 'sourdough', 'croissant', 'patisserie', 'pâtisserie', 'boulangerie'),
    'coffee': ('café', 'cafe', 'coffee', 'espresso'),
    'records': ('vinyl', 'record shop', 'record store', 'records'),
    'ceramics': ('ceramic', 'ceramics', 'pottery', 'potter', 'potters'),
    'fashion': ('fashion', 'clothing', 'apparel', 'boutique'),
    'wellness': ('wellness', 'spa', 'yoga', 'meditation', 'fitness', 'pilates'),
    'hospitality': ('hotel', 'resort', 'hostel', 'guesthouse', 'lodging'),
    'music': ('concert', 'concerts', 'music', 'performance', 'comedy', 'theatre', 'theater'),
    'frozen_dessert': ('ice cream', 'gelato', 'gelateria', 'frozen yogurt', 'frozen yoghurt', 'sorbet', 'creamery'),
    'gaming': ('gaming', 'esports', 'arcade', 'video game', 'video games', 'board game', 'board games'),
    'pharmacy': ('pharmacy', 'pharmacies', 'chemist', 'drugstore', 'apothecary'),
    'clinic': ('hospital', 'clinic', 'dentist'),
    'food': ('restaurant', 'restaurants', 'dining', 'bar', 'pizza', 'bakery', 'bakeries', 'bread', 'café', 'cafe', 'coffee'),
}

#: The broad family a business type falls back to, and only when the idea is blank.
CATEGORY = {'Food & beverage': 'food', 'Hospitality': 'hospitality', 'Wellness': 'wellness', 'Entertainment': 'music'}

#: Whole phrases that name a specific category. The longest match wins, so
#: "gaming cafe" is gaming before the generic word "cafe" is considered.
SPECIFIC_PHRASES = {
    'ice cream parlour': 'frozen_dessert', 'ice cream parlor': 'frozen_dessert', 'ice cream shop': 'frozen_dessert',
    'ice cream': 'frozen_dessert', 'gelato': 'frozen_dessert', 'gelateria': 'frozen_dessert',
    'frozen yogurt': 'frozen_dessert', 'frozen yoghurt': 'frozen_dessert', 'sorbet': 'frozen_dessert',
    'creamery': 'frozen_dessert',
    'gaming cafe': 'gaming', 'gaming bar': 'gaming', 'board game cafe': 'gaming', 'board game bar': 'gaming',
    'internet cafe': 'gaming', 'esports bar': 'gaming', 'arcade': 'gaming', 'video game shop': 'gaming',
    'medical store': 'pharmacy', 'pharmacy': 'pharmacy', 'chemist': 'pharmacy', 'drugstore': 'pharmacy',
    'apothecary': 'pharmacy',
    'hospital': 'clinic', 'clinic': 'clinic', 'dentist': 'clinic',
    'record shop': 'records', 'record store': 'records',
    'coffee shop': 'coffee',
}

#: Generic head nouns. On their own they name a family only when no more
#: specific term is present, and their modifiers must be neutral.
HEAD_FAMILY = {
    'cafe': 'coffee', 'café': 'coffee', 'coffee': 'coffee', 'bakery': 'bakery',
    'bar': 'food', 'restaurant': 'food',
    'shop': None, 'store': None, 'studio': None, 'parlour': None, 'parlor': None,
}

#: Modifiers that describe how a place operates rather than what it is.
NEUTRAL_MODIFIERS = frozenset({
    'a', 'an', 'the', 'our', 'best', 'good', 'great', 'top', 'new', 'little', 'small', 'local', 'independent',
    'artisan', 'specialty', 'craft', 'modern', 'classic', 'third', 'wave', 'neighbourhood', 'neighborhood',
    'family', 'community', 'design', 'cozy', 'cosy', 'quiet', 'daily', 'everyday', 'organic', 'vegan',
    'vegetarian', 'sustainable',
})

#: Which business types may take a distinctive family from the audience words
#: when the idea is blank. A records audience under Retail is a records brief;
#: an ice cream audience under Retail is not.
TYPE_COMPAT = {
    'Retail': {'records', 'ceramics', 'fashion', 'pharmacy', 'gaming'},
    'Food & beverage': {'bakery', 'coffee', 'frozen_dessert', 'food'},
    'Hospitality': {'hospitality', 'food'},
    'Wellness': {'wellness', 'pharmacy', 'clinic'},
    'Entertainment': {'music', 'gaming'},
}
#: Families an audience's words may choose on their own. Broad families such as
#: food or music are only ever the business-type fallback.
DISTINCTIVE_AUDIENCE_FAMILIES = {'records', 'ceramics', 'fashion', 'bakery'}

_CUT_WORDS = {'for', 'in', 'near', 'with', 'of', 'by', 'at'}


@dataclass(frozen=True)
class BriefCategory:
    family: str
    source: str        # idea | audience | business_type | none
    specificity: str   # specific | broad | unknown
    matched: str
    reason: str


def matches(text: str, terms) -> list[str]:
    return [term for term in terms if re.search(r'\b' + re.escape(term) + r'\b', text, re.I)]


def _normalise(idea: str) -> list[str]:
    """Lowercase words of the idea, up to the first preposition."""
    words = re.sub(r'[-&]', ' ', (idea or '').casefold())
    words = re.findall(r"[\w'’]+", words)
    kept = []
    for word in words:
        if word in _CUT_WORDS:
            break
        kept.append(word)
    return kept


def _phrase_in(phrase: str, text: str) -> bool:
    return re.search(r'\b' + re.escape(phrase) + r'\b', text) is not None


def _brief_terms(family: str) -> tuple[str, ...]:
    """Family terms that are specific enough to name a brief on their own."""
    return tuple(term for term in FAMILIES.get(family, ()) if term not in HEAD_FAMILY)


def classify_brief(business_type: str, idea: str, audience: str) -> BriefCategory:
    words = _normalise(idea)
    text = ' '.join(words)
    if not text:
        return _from_audience_or_type(business_type, audience)

    phrases = sorted((p for p in SPECIFIC_PHRASES if _phrase_in(p, text)), key=len, reverse=True)
    if phrases:
        families = {SPECIFIC_PHRASES[p] for p in phrases if len(p) == len(phrases[0])}
        if len(families) == 1:
            family = families.pop()
            return BriefCategory(family, 'idea', 'specific', phrases[0],
                                 f'The idea "{idea.strip()}" names a {family.replace("_", " ")} category.')

    term_hits = {}
    for family in FAMILIES:
        if family == 'food':
            # Food is the broad family: it is read from the head noun or the
            # business type, never from a word such as "bread" that names
            # something more specific.
            continue
        found = [term for term in _brief_terms(family) if _phrase_in(term, text)]
        if found:
            term_hits[family] = found
    if len(term_hits) > 1:
        return _unknown(idea, business_type, 'The idea names more than one category: '
                        + ', '.join(sorted(term_hits)) + '.')
    if term_hits:
        family, found = next(iter(term_hits.items()))
        head = HEAD_FAMILY.get(words[-1]) if words else None
        if head and head != family:
            return _unknown(idea, business_type, f'The head "{words[-1]}" and "{found[0]}" name different categories.')
        return BriefCategory(family, 'idea', 'specific', found[0],
                             f'The idea "{idea.strip()}" names a {family} category through "{found[0]}".')

    head = words[-1]
    if head not in HEAD_FAMILY:
        return _unknown(idea, business_type, f'The head noun "{head}" is not a category CultureForge recognises.')
    family = HEAD_FAMILY[head]
    if family is None:
        return _unknown(idea, business_type, f'"{head}" alone does not name a category CultureForge recognises.')
    for modifier in words[:-1]:
        if modifier in NEUTRAL_MODIFIERS or modifier in FAMILIES.get(family, ()) or HEAD_FAMILY.get(modifier) == family:
            continue
        return _unknown(idea, business_type, f'The modifier "{modifier}" is not one CultureForge recognises, '
                        f'so "{head}" was not read as {family}.')
    return BriefCategory(family, 'idea', 'specific', head,
                         f'The idea "{idea.strip()}" names a {family} category through "{head}".')


def _from_audience_or_type(business_type: str, audience: str) -> BriefCategory:
    """With no idea, only a distinctive audience word can choose a family.

    Otherwise the broad business type applies, and only where it maps to one.
    """
    compatible = TYPE_COMPAT.get(business_type, set())
    for family in sorted(DISTINCTIVE_AUDIENCE_FAMILIES & compatible):
        found = matches(audience or '', _brief_terms(family))
        if found:
            return BriefCategory(family, 'audience', 'specific', found[0],
                                 f'With no idea, the audience words "{found[0]}" name a {family} category '
                                 f'for a {business_type} brief.')
    broad = CATEGORY.get(business_type, '')
    if broad:
        return BriefCategory(broad, 'business_type', 'broad', business_type,
                             f'With no idea, the broad {business_type} type gives the {broad} category.')
    return BriefCategory('', 'none', 'unknown', '', 'The brief has no recognised category.')


def _unknown(idea: str, business_type: str, detail: str) -> BriefCategory:
    scope = f'the {business_type} type' if business_type else 'the business type'
    return BriefCategory('', 'idea', 'unknown', '',
                         f'The idea "{idea.strip()}" is not a category CultureForge can match. {detail} '
                         f'It was not widened to {scope}.')


def brief_family(business_type: str, idea: str, audience: str) -> str:
    return classify_brief(business_type, idea, audience).family


def assess(*, business_type: str, idea: str, audience: str, location: str,
           name: str, description: str, returned_location: str = '',
           kind: str = 'entity', has_identifier: bool = True) -> dict:
    category = classify_brief(business_type, idea, audience)
    family = category.family
    text = f'{name} {description}'
    hits = matches(text, FAMILIES.get(family, ()))
    reasons = [category.reason]
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
            'categorySource': category.source, 'categorySpecificity': category.specificity,
            'categoryMatched': category.matched,
            'anchorEligible': relation == 'direct', 'geography': geography,
            'audience': 'returned_for_seeds', 'confidence': 'rule_assessment_only',
            'reasons': reasons}
