"""The business idea, read into typed components without losing any of it.

``category.resolve`` answers "which one category is this phrase". This module
answers the question above it: what did the founder actually ask for. It keeps

* every business the idea names (a hybrid is two components, never one),
* every specialisation word ("vegan", "vintage"), and
* every simplification the system made, as a sentence the screen can show.

Rules read the idea first. A model is consulted only when the rules cannot
resolve it, once per idea, and what it returns is a *proposal*: component
phrases and ``find_tags`` search strings. It cannot name a Qloo tag, and the
proposal is validated before any of it can reach a request. Nothing here makes
a network call; the optional model result is read from the evidence store.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from . import category as taxonomy

MAX_COMPONENTS = 2          # components researched; a third is named and left out
SEARCH_PATTERN = re.compile(r"^[a-z0-9][a-z0-9 '&\-]{1,38}[a-z0-9]$")
_LOCATION_CUT = re.compile(r'\b(?:in|near|at|around)\b', re.I)
_ARTICLE = re.compile(r'^\s*(?:a|an|the|some|my|our)\s+', re.I)
_CONNECTOR = re.compile(
    r'\s*(?:\b(?:combined with|combined|combo with|plus|and also|(?:that|which) also '
    r'(?:serves|sells|has|offers|doubles as)|also (?:serves|sells)|doubles as|with|and)\b|[&+/])\s*', re.I)


class IntentComponent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['primary', 'secondary']
    phrase: str = Field(max_length=80)
    categoryId: str = ''
    categoryLabel: str = ''
    status: Literal['canonical', 'open_vocabulary', 'unresolved']
    #: find_tags search strings in the order they are tried. The first is the most
    #: specific; the second is broader and, if used, is disclosed as a substitution.
    queries: list[str] = Field(default_factory=list, max_length=2)
    modifiers: list[str] = Field(default_factory=list, max_length=6)
    source: Literal['rules', 'model'] = 'rules'


class BusinessIntent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    original: str = Field(max_length=160)
    components: list[IntentComponent] = Field(default_factory=list, max_length=3)
    hybrid: bool = False
    ambiguous: bool = False
    clarification: str = ''
    #: Parts of the idea that were not used to choose a category ("with outdoor seating").
    unused: list[str] = Field(default_factory=list, max_length=4)
    #: Every simplification, as a sentence the founder can read.
    substitutions: list[str] = Field(default_factory=list, max_length=8)
    source: Literal['rules', 'model'] = 'rules'
    #: One entry per component, filled after retrieval (see providers.intent_report).
    evidence: list[dict] = Field(default_factory=list)
    overlap: Optional[dict] = None

    @property
    def primary(self) -> Optional[IntentComponent]:
        return self.components[0] if self.components else None

    @property
    def secondary(self) -> list[IntentComponent]:
        return self.components[1:]


def _business_like(part: str) -> bool:
    words = re.findall(r"[\w'’-]+", part.casefold())
    if not words:
        return False
    if words[-1] in taxonomy.BUSINESS_NOUNS:
        return True
    return taxonomy.resolve(part).status == 'canonical'


def _strip_specialisations(text: str) -> str:
    return ' '.join(w for w in re.findall(r"[\w'’-]+", text) if w.casefold() not in taxonomy.SPECIALISATIONS)


def _component(role: str, phrase: str, source: str = 'rules') -> IntentComponent:
    resolution = taxonomy.resolve(phrase)
    modifiers = list(taxonomy.modifiers_in(phrase))
    if resolution.status == 'canonical':
        spec = taxonomy.CATEGORIES[resolution.id]
        narrow = resolution.matched in spec.get('narrow', ())
        queries = [resolution.matched, resolution.query] if narrow and resolution.matched != resolution.query \
            else [resolution.query]
        return IntentComponent(role=role, phrase=phrase, categoryId=resolution.id, categoryLabel=resolution.label,
                               status='canonical', queries=queries, modifiers=modifiers, source=source)
    if resolution.status == 'open_vocabulary':
        queries = [resolution.query]
        broader = _strip_specialisations(resolution.query).casefold()
        if broader and broader != resolution.query and \
                not all(w in taxonomy.GENERIC_ONLY | taxonomy.NEUTRAL for w in broader.split()):
            queries.append(broader)
        return IntentComponent(role=role, phrase=phrase, categoryLabel=resolution.label, status='open_vocabulary',
                               queries=queries, modifiers=modifiers, source=source)
    return IntentComponent(role=role, phrase=phrase, status='unresolved', modifiers=modifiers, source=source)


def _frame_and_location_stripped(idea: str) -> str:
    """The idea without a question frame or a trailing place."""
    text = re.sub(r'[?.!]+$', '', (idea or '').strip())
    text = taxonomy._FRAME.sub('', text, count=1)
    cut = _LOCATION_CUT.search(text)
    if cut and cut.start() > 0:
        text = text[:cut.start()]
    return text.strip(' ,-')


def split_components(idea: str) -> tuple[list[str], list[str]]:
    """(component phrases, unused trailing parts). A split needs every kept part to be a business."""
    pieces = [p for p in _CONNECTOR.split(_frame_and_location_stripped(idea))]
    pieces = [_ARTICLE.sub('', p).strip(' ,-') for p in pieces if p and p.strip(' ,-')]
    if len(pieces) < 2 or not _business_like(pieces[0]):
        # "fish and chips shop" is one business, not two.
        return [], []
    parts = [pieces[0]]
    unused: list[str] = []
    for piece in pieces[1:]:
        if len(parts) < 3 and _business_like(piece) and not unused:
            parts.append(piece)
        else:
            unused.append(piece)
    if len(parts) < 2:
        return [], []
    # Two parts that resolve to the same category are one business described twice.
    ids = [taxonomy.resolve(p).id or p.casefold() for p in parts]
    if len(set(ids)) < len(ids):
        return [], []
    return parts, unused


def llm_key(idea: str) -> str:
    return 'intent_llm:' + re.sub(r'\s+', ' ', (idea or '').strip().casefold())


def validate_proposal(raw: object) -> Optional[dict]:
    """A model's interpretation, accepted only if every field is in range. None otherwise."""
    if not isinstance(raw, dict) or set(raw) - {'components', 'ambiguous', 'clarification'}:
        return None
    components = raw.get('components')
    if not isinstance(components, list) or not 1 <= len(components) <= 3:
        return None
    clean = []
    for item in components:
        if not isinstance(item, dict) or set(item) - {'phrase', 'search'}:
            return None
        phrase, search = item.get('phrase'), item.get('search')
        if not isinstance(phrase, str) or not 2 <= len(phrase.strip()) <= 60:
            return None
        if not isinstance(search, str) or not SEARCH_PATTERN.match(search.strip().casefold()):
            return None
        if 'urn:' in phrase.casefold() or 'urn:' in search.casefold():
            return None
        clean.append({'phrase': phrase.strip(), 'search': search.strip().casefold()})
    clarification = raw.get('clarification', '')
    if not isinstance(clarification, str) or len(clarification) > 160:
        return None
    return {'components': clean, 'ambiguous': bool(raw.get('ambiguous')), 'clarification': clarification.strip()}


def _from_proposal(idea: str, proposal: dict) -> BusinessIntent:
    comps = []
    for index, item in enumerate(proposal['components']):
        base = _component('primary' if index == 0 else 'secondary', item['phrase'], 'model')
        queries = list(base.queries) if base.status == 'canonical' else [item['search']]
        if base.status != 'canonical':
            broader = _strip_specialisations(item['search']).casefold()
            if broader and broader != item['search']:
                queries.append(broader)
        comps.append(base.model_copy(update={
            'status': 'canonical' if base.status == 'canonical' else 'open_vocabulary',
            'queries': queries[:2], 'categoryLabel': base.categoryLabel or item['phrase']}))
    return BusinessIntent(original=idea, components=comps, hybrid=len(comps) > 1,
                          ambiguous=proposal['ambiguous'], clarification=proposal['clarification'], source='model')


def _held_proposal(idea: str, store) -> Optional[dict]:
    if store is None:
        from .evidence_store import get_store
        store = get_store()
    held = store.get(llm_key(idea))
    return validate_proposal(held.get('proposal')) if isinstance(held, dict) else None


def _finish(intent: BusinessIntent) -> BusinessIntent:
    """Add a sentence for each part of the idea the rules did not use."""
    if len(intent.components) > MAX_COMPONENTS:
        intent.substitutions.append(
            f'"{intent.components[MAX_COMPONENTS].phrase}" was named but not researched: '
            f'at most {MAX_COMPONENTS} businesses are retrieved per idea.')
    for tail in intent.unused:
        intent.substitutions.append(
            f'"{tail}" was not used to choose a category; it does not change which Qloo places were requested.')
    return intent


def interpret(idea: str, *, store=None) -> BusinessIntent:
    """The idea as typed components. Rules first; a held model proposal only for what rules cannot read."""
    idea = (idea or '').strip()[:160]
    if not idea:
        return BusinessIntent(original='', ambiguous=True, clarification='No business idea was given.')
    parts, unused = split_components(idea)
    if parts:
        comps = [_component('primary' if i == 0 else 'secondary', p) for i, p in enumerate(parts)]
        intent = BusinessIntent(original=idea, components=comps, hybrid=True, unused=unused[:4])
        if any(c.status == 'unresolved' for c in comps):
            intent.ambiguous = True
            intent.clarification = 'Name each business in the combination, for example "bakery and bookstore".'
        return _finish(intent)
    phrase = taxonomy.head_phrase(idea)
    primary = _component('primary', phrase or idea)
    stripped = _frame_and_location_stripped(idea)
    tail = stripped[len(phrase):].strip(' ,-') if phrase and stripped.casefold().startswith(phrase.casefold()) else ''
    intent = BusinessIntent(original=idea, components=[primary], unused=[tail] if tail else [])
    if primary.status == 'unresolved':
        proposal = _held_proposal(idea, store)
        if proposal:
            return _finish(_from_proposal(idea, proposal))
        intent.ambiguous = True
        intent.unused = []
        intent.clarification = 'Name the main kind of business, for example "ice cream parlour".'
    return _finish(intent)


def needs_model(intent: BusinessIntent) -> bool:
    """True only when rules left the main business unread, and no model proposal is held."""
    primary = intent.primary
    return intent.source == 'rules' and primary is not None and primary.status == 'unresolved'


def primary_phrase(idea: str) -> str:
    """The idea reduced to its first business. Unchanged for anything that is not a hybrid."""
    parts, _ = split_components(idea)
    return parts[0] if parts else idea


def primary_resolution(idea: str) -> taxonomy.CategoryResolution:
    """The category resolution for the idea's first business, or for a held, validated model reading."""
    primary = interpret(idea).primary
    if primary is not None and primary.source == 'model' and primary.queries:
        words = tuple(w for w in primary.phrase.casefold().split() if len(w) > 2)
        # A model reading that lands on a known category judges places by that category's own
        # words (bookstore, librería ...), not only by the one word the founder typed: a bookshop
        # called a "bookstore" in Qloo's text is still a bookshop.
        known = taxonomy.CATEGORIES.get(primary.categoryId)
        terms = tuple(dict.fromkeys(words + tuple(t.casefold() for t in known['terms']))) if known else words
        return taxonomy.CategoryResolution(
            primary.categoryId, primary.categoryLabel, primary.queries[0], primary.status, primary.phrase.casefold(),
            terms, tuple(known['adjacent']) if known else (),
            'Read from a validated model proposal; the tag is still resolved by Qloo.')
    return taxonomy.resolve(primary_phrase(idea))
