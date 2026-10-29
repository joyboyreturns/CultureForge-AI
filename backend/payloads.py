"""The request for each Qloo workflow, built in one place.

Qloo rejects fields it does not know, so every workflow has its own builder and every path that asks
the same question builds the same payload, which is what lets them share one cache entry. Nothing here
makes a request: `providers.py` sends what these return.
"""
from __future__ import annotations

import re
from typing import Optional

from .evidence_store import canonical_key, get_store
from .intent import interpret

# The exact set of query parameters this app sends to Qloo. A provenance
# panel may only show a parameter that appears here. Anything else is dropped
# before it can reach the panel, so a future change to the harness cannot
# quietly start exposing a new field.
SAFE_QUERY_KEYS = {
    # find_tags
    'filter.query', 'feature.semantic_search',
    # recommend and rank
    'filter.type', 'filter.location.query', 'signal.location.query',
    'take', 'feature.explainability',
    'signal.interests.tags', 'operator.signal.interests.tags',
    'signal.interests.entities',
    'signal.demographics.gender', 'signal.demographics.age',
    'filter.tags', 'operator.filter.tags',
    'filter.exclude.tags', 'operator.filter.exclude.tags',
    'filter.exclude.entities',
    'filter.results.entities',
    # compare_audiences
    'a.signal.interests.entities', 'b.signal.interests.entities',
}


def safe_query(query: dict) -> dict:
    """Keep only the parameters that are safe to display."""
    if not isinstance(query, dict):
        return {}
    return {key: value for key, value in query.items() if key in SAFE_QUERY_KEYS}


#: How many audience seeds a brief resolves to, and how many places it
#: retrieves. Ten is the most the evidence test can use: Qloo's rank and
#: compare_audiences accept at most ten entities per list.
BRIEF_TAG_LIMIT = 3
BRIEF_PLACE_LIMIT = 10
#: How many entities the audience bridge asks for in each other domain.
BRIDGE_LIMIT = 5


def _returned_location(geocode: dict) -> str:
    """Where Qloo says a place is: its city, metro area and region, once each, and never the country.

    Suburbs are reported under their own council ("City of Yarra") with the
    metro area ("Melbourne") separate, so the metro must be kept or every
    suburb reads as another city. The country is left out on purpose: it would
    make any place in the same country look like the requested city.
    """
    parts: list[str] = []
    for value in (geocode.get('city'), geocode.get('metro'), geocode.get('admin1_region')):
        if isinstance(value, str) and value.strip() and value.strip().casefold() not in (p.casefold() for p in parts):
            parts.append(value.strip())
    return ', '.join(parts)


def brief_tags_payload(business_type: str, audience: str) -> dict:
    """The find_tags request for a brief. Every path that resolves a brief's
    audience builds it here, so they all share one cache entry."""
    return {'query': f'{business_type} {audience}'.strip(), 'limit': BRIEF_TAG_LIMIT}


def effective_category_query(queries: list[str]) -> str:
    """The search string a brief's category is resolved with, given what is already held.

    The most specific string comes first. If its answer is held and holds no matching tag, the next
    (broader) string is used, so every payload builder agrees with the resolution step without
    asking Qloo anything.
    """
    store = get_store()
    for query in queries:
        held = store.get(canonical_key('find_tags', {'query': query, 'limit': 10}))
        if held is None or select_category_tag(held, query):
            return query
    return queries[-1]


def brief_category_payload(business_idea: str) -> Optional[dict]:
    """The find_tags request that resolves the idea's own category.

    Known categories carry a query term; an unfamiliar one is looked up by its
    own words. A hybrid idea resolves its first business here (the others are
    retrieved separately). A category that cannot be named sends no filter at all.
    """
    from .intent import interpret
    primary = interpret(business_idea).primary if business_idea else None
    if primary is None or primary.status == 'unresolved' or not primary.queries:
        return None
    return {'query': effective_category_query(primary.queries), 'limit': 10}


def envelope_rows(envelope: dict) -> list[dict]:
    """The result rows of an envelope, whichever shape Qloo answered in."""
    rows = envelope.get('results', [])
    if isinstance(rows, dict):
        rows = rows.get('entities', rows.get('tags', []))
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _name_tokens(text: str) -> set[str]:
    """Words of a tag name, with shop/store and plurals treated as one word."""
    out = set()
    for word in re.findall(r'\w+', str(text).casefold()):
        word = 'store' if word in ('shop', 'shops', 'stores') else word
        out.add(word[:-1] if len(word) > 3 and word.endswith('s') else word)
    return out


def rank_category_tag(envelope: dict, query: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """(tag id, 'exact' or 'near', tag name) for a returned category tag, or (None, None, None).

    A natural language label resolves to many tag families, and many of them
    (cuisine, product service, amenity) return no places at all. The place
    categories (``urn:tag:category:place:…``, ``genre:place:…``,
    ``specialty_dish:place:…``) are the ones places carry. An exact label wins
    over a near one; a near one must contain every word of the query. Both are
    name matches: Qloo documents no tag hierarchy, so nothing here is a
    parent or child relationship. No URN is ever written here: only a
    returned identifier is chosen.
    """
    families = ('category', 'genre', 'specialty_dish', 'cuisine', 'product_category', 'service_type',
                'product_service', 'setting')
    wanted = _name_tokens(query)
    rows = [row for row in envelope_rows(envelope or {})
            if isinstance(row.get('id'), str) and row['id'].startswith('urn:tag:')
            and len(row['id'].split(':')) >= 4 and row['id'].split(':')[2] in families]

    def rank(row: dict) -> tuple[int, int]:
        parts = row['id'].split(':')
        return (0 if len(parts) > 3 and parts[3] == 'place' else 1, families.index(parts[2]))

    exact = [r for r in rows if _name_tokens(r.get('name', '')) == wanted]
    near = [r for r in rows if wanted and wanted <= _name_tokens(r.get('name', ''))]
    for quality, group in (('exact', exact), ('near', near)):
        if group:
            best = min(group, key=rank)
            return best['id'], quality, best.get('name') if isinstance(best.get('name'), str) else None
    return None, None, None


def select_category_tag(envelope: dict, query: str) -> Optional[str]:
    """The tag id :func:`rank_category_tag` chose, or None."""
    return rank_category_tag(envelope, query)[0]


def brief_places_payload(tags: list[str], location: str, business_idea: str = '') -> dict:
    """The recommend request for a brief's local places."""
    payload = {'target_type': 'place', 'signal_tags': list(tags),
               'filter_location': location, 'limit': BRIEF_PLACE_LIMIT}
    category_payload = brief_category_payload(business_idea)
    if category_payload:
        held = get_store().get(canonical_key('find_tags', category_payload)) or {}
        category_tag = select_category_tag(held, category_payload['query'])
        # Unresolved labels fail closed in the official harness. Production
        # callers resolve the category first; cache-only readers spend nothing.
        payload['include_tags'] = [category_tag or category_payload['query']]
        payload['include_tags_operator'] = 'intersection'
    return payload


def brief_places_retrieval_payload(tags: list[str], location: str, business_idea: str = '', evidence_store=None) -> dict:
    """Reuse a smaller authentic held sample without broadening its constraints.

    Earlier releases asked for five places. Keep that exact request/provenance
    rather than copying its answer under a ten-place cache key or spending
    another request merely to enlarge the sample.
    """
    payload = brief_places_payload(tags, location, business_idea)
    return held_place_payload(payload, evidence_store)


def held_place_payload(payload: dict, evidence_store=None) -> dict:
    """Prefer a held real request, retaining its original key and provenance.

    Fresh requests constrain result geography with filter_location. Old
    signal-location responses remain replayable, never relabelled as a
    filtered response. A modern held response always takes precedence.
    """
    store = evidence_store if evidence_store is not None else get_store()
    candidates = [payload, {**payload, 'limit': 5}]
    if payload.get('filter_location') and not payload.get('signal_location'):
        legacy = {k: v for k, v in payload.items() if k != 'filter_location'}
        legacy['signal_location'] = payload['filter_location']
        candidates += [legacy, {**legacy, 'limit': 5}]
    for candidate in candidates:
        envelope = store.get(canonical_key('recommend', candidate))
        if envelope is not None and (candidate.get('filter_location') or envelope.get('results')):
            return candidate
    return payload


def bridge_payload(tags: list[str], domain: str) -> dict:
    """The recommend request for one other domain, from the audience tags
    alone. The location is deliberately left out: this asks what the audience
    gravitates to, not what is near the brief."""
    return {'target_type': domain, 'signal_tags': list(tags), 'limit': BRIDGE_LIMIT}


def describe_payload(entity: str, entity_type: Optional[str] = None) -> dict:
    payload: dict = {'entity': entity}
    if entity_type:
        payload['type'] = entity_type
    return payload


def entity_tags_payload(entities: list[str], entity_type: Optional[str] = None,
                        limit: int = 10) -> dict:
    payload: dict = {'entities': list(entities)[:5]}
    if entity_type:
        payload['entity_type'] = entity_type
    payload['limit'] = limit
    return payload


def where_popular_payload(entity: str, within: str, entity_type: Optional[str] = None,
                          limit: int = 20) -> dict:
    payload: dict = {'entity': entity, 'within': within, 'limit': limit}
    if entity_type:
        payload['entity_type'] = entity_type
    return payload


def audience_demographics_payload(entity: str, entity_type: Optional[str] = None,
                                  limit: int = 5) -> dict:
    payload: dict = {'entity': entity, 'limit': limit}
    if entity_type:
        payload['entity_type'] = entity_type
    return payload


def trends_payload(entities: list[str], entity_type: str, start_date: str,
                   end_date: str, limit: int = 10) -> dict:
    return {
        'entities': list(entities)[:5],
        'entity_type': entity_type,
        'start_date': start_date,
        'end_date': end_date,
        'limit': limit,
    }
