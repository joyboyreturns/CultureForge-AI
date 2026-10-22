"""Evidence for each business in an idea, kept separate, with every simplification stated.

``intent.py`` reads the idea. This module attaches what Qloo returned for each component and says,
per component, which of these is true:

* ``exact`` / ``near``   a returned Qloo category tag matched the requested words (exact: same words;
                          near: the tag's name contains them all). Qloo exposes no tag hierarchy, so
                          these are name matches, not taxonomy relationships.
* ``broader``             no tag matched the specific words; a broader search string was used instead.
                          That broadening is CultureForge's, and it is disclosed.
* ``tag_no_places``       a category tag exists but Qloo returned no places for it in this city.
* ``unresolved``          no returned tag matched any search string tried.
* ``not_retrieved``       the evidence is not held and this answer may not spend a request.
* ``provider_error``      Qloo could not answer (rate limit, timeout, credential). Not a statement about
                          coverage.

A place count here is a count of what Qloo returned. Overlap is the places returned for both
components, by Qloo's own entity ID, and nothing else.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .evidence_store import canonical_key, get_store
from .intent import MAX_COMPONENTS, BusinessIntent, IntentComponent

#: Workflows a hybrid may add to the baseline: one find_tags and one recommend for the second business,
#: plus one category-only recommend when the audience-shaped one is empty.
HYBRID_EXTRA_WORKFLOWS = 3

#: States in which no category filter could be built for a component.
NO_FILTER = ('unresolved', 'not_retrieved', 'provider_error')


@dataclass
class TagResolution:
    result: Optional[dict] = None
    tag: Optional[str] = None
    name: Optional[str] = None
    quality: Optional[str] = None      # exact | near | broader
    query: str = ''
    tried: list = field(default_factory=list)
    cached: bool = True
    requests: int = 0
    workflows: int = 0


def held_tag(component: IntentComponent) -> tuple[TagResolution, bool]:
    """What the evidence store already holds for a component's category. Spends nothing.

    Returns (resolution, complete): ``complete`` is False when a search string has not been asked yet.
    """
    from .providers import rank_category_tag
    store = get_store()
    resolution = TagResolution()
    for index, query in enumerate(component.queries):
        envelope = store.get(canonical_key('find_tags', {'query': query, 'limit': 10}))
        resolution.query = query
        if envelope is None:
            return resolution, False
        resolution.result = envelope
        resolution.tried.append(query)
        tag, quality, name = rank_category_tag(envelope, query)
        if tag:
            resolution.tag, resolution.name = tag, name
            resolution.quality = quality if index == 0 else 'broader'
            return resolution, True
    return resolution, True


def resolve_tag(provider, component: IntentComponent) -> TagResolution:
    """Ask find_tags for the component's search strings in order; stop at the first matching tag.

    A single-string component costs the same one request the app always spent. A failure raises: a rate
    limit or timeout is not evidence that a category is unsupported.
    """
    from .providers import rank_category_tag
    resolution = TagResolution()
    for index, query in enumerate(component.queries):
        envelope, was_cached, requests = provider.run_workflow_cached('find_tags', {'query': query, 'limit': 10})
        resolution.workflows += 1
        resolution.requests += requests
        resolution.cached = resolution.cached and was_cached
        resolution.result, resolution.query = envelope, query
        resolution.tried.append(query)
        tag, quality, name = rank_category_tag(envelope, query)
        if tag:
            resolution.tag, resolution.name = tag, name
            resolution.quality = quality if index == 0 else 'broader'
            return resolution
    return resolution


def _mentions(modifier: str, text: str) -> bool:
    return re.search(r'\b' + re.escape(modifier.replace('-', ' ')) + r'\b', text.replace('-', ' '), re.I) is not None


def _place_view(item) -> dict:
    relevance = item.relevance or {}
    return {'entityId': item.entityId, 'name': item.label, 'location': item.location,
            'evidenceClass': relevance.get('evidenceClass'), 'anchorEligible': bool(relevance.get('anchorEligible'))}


def _modifier_checks(component: IntentComponent, texts: list[str]) -> list[dict]:
    return [{'word': word, 'mentionedIn': sum(_mentions(word, text) for text in texts), 'of': len(texts)}
            for word in component.modifiers]


def _entry(component: IntentComponent, resolution: TagResolution, state: str, places: list[dict],
           texts: list[str], category_only: bool = False, message: str = '', code: str = '') -> dict:
    entry = {
        'role': component.role, 'phrase': component.phrase, 'categoryLabel': component.categoryLabel or component.phrase,
        'state': state, 'queriesTried': list(resolution.tried),
        'tag': {'id': resolution.tag, 'name': resolution.name, 'quality': resolution.quality} if resolution.tag else None,
        'placeCount': len(places), 'directCount': sum(p['evidenceClass'] == 'direct_business' for p in places),
        'places': places[:10], 'modifiers': _modifier_checks(component, texts),
        'categoryOnly': category_only, 'message': message,
    }
    if code:
        entry['code'] = code
    return entry


def _state_for(resolution: TagResolution, places: list[dict], complete: bool) -> str:
    if resolution.tag is None:
        return 'unresolved' if complete else 'not_retrieved'
    return resolution.quality if places else 'tag_no_places'


def retrieve_secondary(provider, project, component: IntentComponent, tags: list[str], *, retrieve: bool,
                       remaining: Optional[int], category_only: bool) -> tuple[dict, int, bool, int]:
    """(entry, requests spent, whether anything was fetched live, workflows used) for one more business."""
    from .providers import BRIEF_PLACE_LIMIT, QlooHarnessError, brief_places_payload  # noqa: F401
    from .relevance import assess
    resolution, complete = held_tag(component)
    spent, live, workflows = 0, False, 0
    try:
        if retrieve and not (resolution.tag or complete):
            needed = 2
            if remaining is not None and remaining < needed:
                return (_entry(component, resolution, 'not_retrieved', [], [], message=(
                    'This run had no workflow allowance left to look up the second business.')), 0, False, 0)
            resolution = resolve_tag(provider, component)
            spent, workflows, live = resolution.requests, resolution.workflows, not resolution.cached
            complete = True
        if not resolution.tag:
            return _entry(component, resolution, _state_for(resolution, [], complete), [], [],
                          message=('Qloo returned no category tag matching "%s".' % component.phrase) if complete else
                          'The category for this business is not held and this answer may not fetch it.'), spent, live, workflows
        payload = {'target_type': 'place', 'signal_location': project.location, 'limit': BRIEF_PLACE_LIMIT,
                   'include_tags': [resolution.tag], 'include_tags_operator': 'intersection'}
        if not category_only:
            payload['signal_tags'] = list(tags)
        store = get_store()
        envelope = store.get(canonical_key('recommend', payload))
        was_cached = envelope is not None
        if envelope is None and not retrieve:
            return _entry(component, resolution, 'not_retrieved', [], [],
                          message='The places for this business are not held and this answer may not fetch them.'), spent, live, workflows
        if envelope is None:
            if remaining is not None and remaining - workflows < 1:
                return _entry(component, resolution, 'not_retrieved', [], [],
                              message='This run had no workflow allowance left to retrieve the second business.'), spent, live, workflows
            envelope, was_cached, requests = provider.run_workflow_cached('recommend', payload)
            spent, workflows, live = spent + requests, workflows + 1, live or not was_cached
        rows = provider.rows(envelope)
        used_category_only = category_only
        if not rows and not category_only and (remaining is None or remaining - workflows >= 1):
            fallback = {k: v for k, v in payload.items() if k != 'signal_tags'}
            envelope, was_cached, requests = provider.run_workflow_cached('recommend', fallback)
            spent, workflows, live = spent + requests, workflows + 1, live or not was_cached
            rows, used_category_only = provider.rows(envelope), True
    except QlooHarnessError as exc:
        return _entry(component, resolution, 'provider_error', [], [], message=str(exc), code=exc.code), spent, live, workflows
    places, texts = [], []
    for row in rows[:BRIEF_PLACE_LIMIT]:
        name = row.get('name')
        if not isinstance(name, str) or not name.strip():
            continue
        properties = row.get('properties') if isinstance(row.get('properties'), dict) else {}
        geocode = properties.get('geocode') if isinstance(properties.get('geocode'), dict) else {}
        from .providers import _returned_location
        description = properties.get('description') or properties.get('short_description') or ''
        entity_id = row.get('entity_id') or row.get('id')
        relevance = assess(business_type=project.businessType, idea=component.phrase, audience=project.audience,
                           location=project.location, name=name, description=description,
                           returned_location=_returned_location(geocode), has_identifier=bool(entity_id))
        places.append({'entityId': entity_id if isinstance(entity_id, str) else None, 'name': name,
                       'location': _returned_location(geocode) or None,
                       'evidenceClass': relevance.get('evidenceClass'), 'anchorEligible': relevance['anchorEligible']})
        texts.append(f'{name} {description}')
    state = _state_for(resolution, places, True)
    message = ''
    if state == 'tag_no_places':
        message = (f'Qloo has a category tag for "{component.phrase}", but returned no places for it in '
                   f'{project.location}. That is a gap in Qloo\'s local evidence, not a finding about the business.')
    return _entry(component, resolution, state, places, texts, used_category_only, message), spent, live, workflows


def build(provider, project, intent: BusinessIntent, tags: list[str], evidence: list, recommendations: dict, *,
          retrieve: bool, remaining: Optional[int] = None) -> tuple[BusinessIntent, int, bool, int]:
    """Attach per-component evidence and the disclosures to a copy of the intent.

    Returns (intent, requests spent, whether anything was fetched live, workflows used).
    """
    report = intent.model_copy(deep=True)
    entities = [item for item in evidence if item.kind == 'entity']
    texts = [f'{item.label} {item.description or ""}' for item in entities]
    primary = report.primary
    entries: list[dict] = []
    spent, live, workflows = 0, False, 0
    signals = ((recommendations.get('query_intent') or {}).get('signals') or {}).get('tags')
    category_only = bool(provider.rows(recommendations)) and not signals and bool(
        ((recommendations.get('query_intent') or {}).get('filters') or {}).get('includeTags'))
    if primary is not None:
        if primary.status == 'unresolved':
            entries.append(_entry(primary, TagResolution(), 'unresolved', [], [],
                                  message=report.clarification or 'No business could be read from the idea.'))
        else:
            resolution, complete = held_tag(primary)
            places = [_place_view(item) for item in entities]
            entries.append(_entry(primary, resolution, _state_for(resolution, places, complete), places, texts,
                                  category_only,
                                  '' if places else 'Qloo returned no places for this category in this city.'))
    for component in report.components[1:MAX_COMPONENTS]:
        entry, requests, was_live, used = retrieve_secondary(
            provider, project, component, tags, retrieve=retrieve,
            remaining=None if remaining is None else remaining - workflows, category_only=category_only)
        entries.append(entry)
        spent, live, workflows = spent + requests, live or was_live, workflows + used
    report.evidence = entries
    _disclose(report, entries)
    report.overlap = _overlap(entries) if report.hybrid else None
    return report, spent, live, workflows


def _disclose(report: BusinessIntent, entries: list[dict]) -> None:
    for entry in entries:
        phrase = entry['phrase']
        tag = entry.get('tag') or {}
        if entry['state'] == 'broader':
            report.substitutions.append(
                f'Requested "{phrase}"; Qloo returned no category tag for those exact words, so the broader '
                f'"{(entry["queriesTried"] or [""])[-1]}" search was used. This broadening is CultureForge\'s own, '
                'not a relationship Qloo reports.')
        elif entry['state'] == 'near' and tag.get('name'):
            report.substitutions.append(
                f'Requested "{phrase}"; the nearest Qloo category tag is "{tag["name"]}", which contains the same words.')
        for check in entry['modifiers']:
            if not entry['placeCount']:
                continue
            word, n, total = check['word'], check['mentionedIn'], check['of']
            label = entry['categoryLabel'].lower()
            if entry['state'] in ('exact', 'near') and entry['tag'] and word.replace('-', ' ') in (tag.get('name') or '').casefold():
                continue
            report.substitutions.append(
                f'Showing general {label} evidence; {word}-specific relevance is not verified by Qloo\'s category. '
                + (f'{n} of {total} returned places mention "{word}" in their Qloo text.' if n else
                   f'None of the {total} returned places mention "{word}" in their Qloo text.'))
        if entry['categoryOnly'] and entry['placeCount']:
            report.substitutions.append(
                f'The {phrase} places were retrieved for the category in this city only: no place matched the category and '
                'the audience\'s tags together, so the audience did not shape which places appear.')
    skipped = [c for c in report.components[MAX_COMPONENTS:]]
    if skipped:
        report.substitutions.append(f'"{skipped[0].phrase}" was named but not researched: at most {MAX_COMPONENTS} businesses are retrieved.')


def _overlap(entries: list[dict]) -> dict:
    streams = [e for e in entries if e['placeCount']]
    if len(streams) < len(entries) or len(entries) < 2:
        missing = [e['phrase'] for e in entries if not e['placeCount']]
        return {'established': False, 'sharedPlaces': [],
                'statement': 'Overlap not established: no places were retrieved for ' + ', '.join(missing) + '.'}
    first = {p['entityId']: p['name'] for p in entries[0]['places'] if p['entityId']}
    shared = [{'entityId': p['entityId'], 'name': p['name']} for p in entries[1]['places']
              if p['entityId'] and p['entityId'] in first]
    if not shared:
        return {'established': False, 'sharedPlaces': [],
                'statement': 'Overlap not established: no place was returned for both businesses. Each list is a '
                             'bounded sample, so this is not evidence that none exists.'}
    return {'established': True, 'sharedPlaces': shared,
            'statement': f'{len(shared)} place(s) were returned for both businesses ({", ".join(s["name"] for s in shared[:3])}). '
                         'That shows the two categories co-occur in Qloo\'s data for those places; it does not show '
                         'demand for the combined business.'}


def idea_alternatives(intent: BusinessIntent, tried: tuple = ()) -> list[dict]:
    """Rewrites of the idea a founder can accept with one click, each built only from words they wrote.

    A hybrid can be researched as either of its businesses alone; a specialised idea can be searched
    without the specialisation. Nothing here invents a category, and a rewrite whose words were already
    searched (``tried``) is left out: offering it would only repeat the failure.
    """
    options: list[dict] = []
    seen: set[str] = set()

    def add(label: str, value: str) -> None:
        value = value.strip()
        if value and value.casefold() not in seen and value.casefold() != intent.original.casefold() \
                and value.casefold() not in {t.casefold() for t in tried}:
            seen.add(value.casefold())
            options.append({'kind': 'idea', 'label': label, 'value': value[:160]})

    if intent.hybrid:
        for component in intent.components[:MAX_COMPONENTS]:
            add(f'Research only: {component.phrase}', component.phrase)
    for component in intent.components[:1]:
        if component.modifiers and component.status != 'unresolved':
            plain = ' '.join(w for w in component.phrase.split()
                             if w.casefold().replace('-', ' ') not in {m.replace('-', ' ') for m in component.modifiers})
            if plain and plain.casefold() != component.phrase.casefold():
                add(f'Without "{", ".join(component.modifiers)}": {plain}', plain)
    return options[:3]
