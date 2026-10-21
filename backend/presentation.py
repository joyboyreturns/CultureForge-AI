"""Presenting the raw Qloo data without rewriting it.

The evidence a judge reads is untidy, and the untidiness is not cosmetic. A
park-managing nonprofit comes back with the same weight as a bar. A type tag
("Office") sits next to a cultural one ("LGBTQ+ friendly"). Every place comes
back with the same city string, which does not tell you which borough it is
in. A description is a marketing paragraph. A popularity of exactly zero
looks like broken data when it is a real value.

Cleaning that with a language model is the obvious move and the wrong one: a
model asked to tidy a description will happily turn "Nonprofit organization
managing a waterfront park" into "Brooklyn Bridge Park", and the app would
then be showing a fact the API never returned.

So the cleaning here is **rules**, and it never touches the evidence itself:

* The organisation stays an organisation, under its own name, with Qloo's own
  words attached to it.
* A type tag stays a type tag, and is filed as one.
* The location is shown as Qloo returned it, next to the location that was
  asked for, with the difference stated rather than smoothed over.
* A long description is excerpted at a sentence boundary — never rewritten —
  and the original is one click away.
* A missing value is unknown, not zero. A returned zero is shown as returned.

The result is a **presentation object** that sits beside the evidence. It
changes no id, no metric, no policy input and no verdict. It is the same
evidence, arranged so a reader is not misled by the shape of it.

There is an optional second layer: Frontier AI may *choose* which of Qloo's
own sentences to lead with, by id. It cannot write a word — see
`selector.py` — so it cannot invent a fact either.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Optional

#: The version of these rules. It is part of the selector's cache key, so a
#: change to the rules invalidates anything the model chose under the old
#: ones.
PRESENTATION_VERSION = 'presentation-1'

#: The families that say what a place **is** — or how it runs. Every place
#: has these, so they cannot tell one place from another.
PLAIN_FAMILIES = ('genre', 'category', 'service_type', 'amenities', 'services',
                   'facilities', 'features')

#: The words Qloo uses in its own descriptions when the entity is an
#: organisation rather than a place someone goes to.
_ORGANISATION_WORDS = (
    'nonprofit', 'non-profit', 'organization', 'organisation', 'corporation',
    'company', 'foundation', 'agency', 'authority', 'department', 'llc',
    'inc.', 'inc ', 'trust', 'association', 'society', 'consortium',
)

#: A sentence ends with a full stop, a question mark, an exclamation mark, or
#: a semicolon. Marketing copy breaks at commas, so those do not end one.
_SENTENCE_END = re.compile(r'(?<=[.!?;])\s+')

#: How many characters the lead-in excerpt may hold.
EXCERPT_LIMIT = 320


def tag_family(tag_id: Optional[str]) -> str:
    """The family a Qloo tag belongs to: ``urn:tag:activities:place:x`` -> ``activities``."""
    if not isinstance(tag_id, str):
        return ''
    parts = tag_id.split(':')
    return parts[2] if len(parts) > 2 else ''


def tag_bucket(tag_id: Optional[str]) -> str:
    """Which bucket a tag belongs in: the culture, the type, or neither.

    A family the rules do not know is filed as *other*, never as culture. The
    rule can then say no.
    """
    family = tag_family(tag_id)
    if family in PLAIN_FAMILIES:
        return 'type_operations'
    if family:
        return 'cultural'
    return 'other'


def is_organisation(description: Optional[str]) -> bool:
    """Whether Qloo's own description calls this entity an organisation."""
    text = (description or '').lower()
    if not text:
        return False
    head = text[:160]
    return any(word in head for word in _ORGANISATION_WORDS)


def split_sentences(text: Optional[str]) -> list[dict]:
    """The returned description, split into complete sentences with ids.

    The text is never rewritten. A sentence that is cut off by the limit is
    not included at all, so what is shown is always what Qloo wrote.
    """
    if not text:
        return []
    trimmed = ' '.join(text.split())
    if not trimmed:
        return []
    parts = [part.strip() for part in _SENTENCE_END.split(trimmed) if part.strip()]
    return [{'id': f'description:{index}', 'text': part}
            for index, part in enumerate(parts)]


def excerpt(text: Optional[str], limit: int = EXCERPT_LIMIT) -> tuple[str, bool]:
    """A lead-in from the returned description, at a sentence boundary.

    Returns the excerpt and whether the full text continues past it.
    """
    sentences = split_sentences(text)
    if not sentences:
        return '', False
    chosen: list[str] = []
    length = 0
    for sentence in sentences:
        addition = len(sentence['text']) + (1 if chosen else 0)
        if chosen and length + addition > limit:
            break
        chosen.append(sentence['text'])
        length += addition
    if not chosen:
        chosen = [sentences[0]['text']]
    return ' '.join(chosen), len(chosen) < len(sentences)


def present_place(item, requested_location: Optional[str] = None) -> dict:
    """The presentation of one returned place.

    Nothing here changes the evidence. It is the same place, arranged so that
    a reader is not misled by the shape of it.
    """
    kind = getattr(item, 'kind', 'entity') if not isinstance(item, dict) else item.get('kind', 'entity')
    description = getattr(item, 'description', None) if not isinstance(item, dict) else item.get('description')
    label = getattr(item, 'label', '') if not isinstance(item, dict) else item.get('label', '')
    tag_id = getattr(item, 'tagId', None) if not isinstance(item, dict) else item.get('tagId')
    location = getattr(item, 'location', None) if not isinstance(item, dict) else item.get('location')
    popularity = getattr(item, 'popularity', None) if not isinstance(item, dict) else item.get('popularity')
    organisation = is_organisation(description)
    lead, more = excerpt(description)
    presentation: dict = {
        'version': PRESENTATION_VERSION,
        'id': getattr(item, 'id', None) if not isinstance(item, dict) else item.get('id'),
        'entityId': getattr(item, 'entityId', None) if not isinstance(item, dict) else item.get('entityId'),
        'label': label,
        # Whether this is a place to go to, an organisation that runs one, or
        # an audience seed. It is never guessed from the name.
        'identity': ('seed' if kind == 'tag'
                     else 'organisation' if organisation else 'place'),
        'identityNote': (
            'Qloo describes this entity as an organisation, not a place to go to. It is shown '
            'under its own name, with Qloo’s own description.'
            if organisation else ''
        ),
        # The family the seed's urn carries, so a type seed is not mistaken
        # for a cultural one.
        'tagFamily': tag_family(tag_id),
        'tagBucket': tag_bucket(tag_id),
        'excerpt': lead,
        'hasMore': more,
        'description': description,
        'requestedLocation': requested_location,
        'returnedLocation': location,
        'locationNote': '',
        'metrics': {},
        'notes': [],
    }
    if kind == 'tag':
        # A seed is not a place, so the location caveat does not apply to it.
        presentation['locationNote'] = ''
        return presentation
    if requested_location and location and requested_location.strip().lower() != location.strip().lower():
        presentation['locationNote'] = (
            f'Returned for a {requested_location} query. Qloo returned the location '
            f'“{location}”, so borough membership is not established by this field.'
        )
    if popularity == 0:
        presentation['notes'].append(
            'Qloo returned a popularity of 0.0000 for this place. That is the value it '
            'returned; it is not a measure of demand, and it is not a missing value.'
        )
    return presentation


def present_evidence(evidence: list, requested_location: Optional[str] = None) -> list[dict]:
    """The presentation of every piece of evidence, in the same order."""
    return [present_place(item, requested_location) for item in evidence]


def group_tags(tags: list[dict]) -> dict:
    """File the returned tags into the buckets the reader needs.

    The original tags are kept in every bucket. Nothing is dropped and
    nothing is renamed.
    """
    buckets: dict[str, list[dict]] = {'cultural': [], 'type_operations': [], 'other': []}
    for tag in tags or []:
        if not isinstance(tag, dict):
            continue
        tag_id = tag.get('tagId') or tag.get('tag_id')
        label = tag.get('label') or tag.get('name')
        if not label and not tag_id:
            continue
        entry = {'id': tag_id, 'label': label, 'family': tag_family(tag_id)}
        buckets[tag_bucket(tag_id)].append(entry)
    return buckets


def presentation_key(evidence: list) -> str:
    """A stable key for one bundle of evidence.

    The same places in the same order with the same words produce the same
    key, so the model's choice is held rather than asked for again.
    """
    material = json.dumps({
        'version': PRESENTATION_VERSION,
        'evidence': [
            {
                'id': getattr(item, 'id', None) if not isinstance(item, dict) else item.get('id'),
                'label': getattr(item, 'label', None) if not isinstance(item, dict) else item.get('label'),
                'description': getattr(item, 'description', None) if not isinstance(item, dict) else item.get('description'),
                'location': getattr(item, 'location', None) if not isinstance(item, dict) else item.get('location'),
            }
            for item in evidence
        ],
    }, sort_keys=True, default=str)
    return hashlib.sha256(material.encode()).hexdigest()
