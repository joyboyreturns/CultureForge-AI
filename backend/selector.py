"""Letting a model *choose* from the evidence, without letting it write any.

The founder's instinct was to have the model clean up the raw Qloo data and
present it. The risk is that a model asked to tidy a description will turn
"Nonprofit organization managing a waterfront park" into "Brooklyn Bridge
Park" — and the app would then be showing a fact the API never returned.

So the model does not write here. It **selects**: it is given the returned
sentences and tags, each with an id, and it answers with ids. The server
renders its own strings, and an id that does not belong to the record is
rejected. The model can therefore choose which of Qloo's own words to lead
with, and it cannot put a word of its own on the screen.

The rules it cannot break:

* Every id must belong to this exact input.
* Every selected sentence or tag must belong to that entity.
* No duplicates, no unknown ids, no cross-entity references.
* At most two sentences and four tags per place.
* Nothing selected is ever fed into the composition, the verdicts or the
  filtering. It is a display choice and nothing else.

If the model is unavailable, is slow, or answers with something that does not
pass the validation, the deterministic excerpt stays and nothing is lost.
"""
from __future__ import annotations

from typing import Optional

from . import presentation
from .llm import select_source_items

#: How many sentences the model may choose for one place.
MAX_SENTENCES = 2

#: How many tags the model may choose for one place.
MAX_TAGS = 4


def _records(evidence: list) -> list[dict]:
    """The input the model is given: ids, and the server's own text.

    The text travels with the id so the model can judge which sentence
    matters, but it is the id that comes back.
    """
    records = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        if item.get('kind') != 'entity' or not item.get('entityId'):
            continue
        sentences = presentation.split_sentences(item.get('description'))
        if not sentences:
            continue
        records.append({
            'entityId': item['entityId'],
            'label': item.get('label'),
            'sentences': [{'id': sentence['id'], 'text': sentence['text']}
                          for sentence in sentences],
            'tags': [],
        })
    return records


def validate(answer: Optional[dict], records: list[dict]) -> dict[str, dict]:
    """Keep only the selections that are genuinely in the input.

    Everything else is dropped silently: a selection that cannot be trusted
    is not worth showing a warning about, because the deterministic excerpt
    is still on screen.
    """
    if not isinstance(answer, dict):
        return {}
    by_entity = {record['entityId']: record for record in records}
    sentences_by_id = {
        record['entityId']: {s['id']: s['text'] for s in record['sentences']}
        for record in records
    }
    chosen: dict[str, dict] = {}
    entries = answer.get('records')
    if not isinstance(entries, list):
        return {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entity_id = entry.get('entityId')
        if not isinstance(entity_id, str) or entity_id not in by_entity:
            continue
        picked_sentences: list[str] = []
        for value in entry.get('sentenceIds') or []:
            if not isinstance(value, str):
                continue
            if value not in sentences_by_id[entity_id]:
                continue
            if value in picked_sentences:
                continue
            picked_sentences.append(value)
            if len(picked_sentences) >= MAX_SENTENCES:
                break
        picked_tags: list[str] = []
        for value in entry.get('tagIds') or []:
            if not isinstance(value, str):
                continue
            if value in picked_tags:
                continue
            picked_tags.append(value)
            if len(picked_tags) >= MAX_TAGS:
                break
        if picked_sentences or picked_tags:
            chosen[entity_id] = {
                'sentenceIds': picked_sentences,
                'tagIds': picked_tags,
                # The server's own words, so nothing has to be reconstructed
                # on the way to the screen.
                'sentences': [sentences_by_id[entity_id][sid] for sid in picked_sentences],
            }
    return chosen


def select(evidence: list) -> dict:
    """Choose, from the returned evidence, what to lead with.

    Never raises. The result always says what happened, so the screen can
    be honest about whether the model helped or the rules did.
    """
    records = _records(evidence)
    report: dict = {
        'used': False,
        'attempted': False,
        'model': None,
        'reason': None,
        'selections': {},
        'source': 'rules',
    }
    if not records:
        report['reason'] = 'There was nothing to choose from.'
        return report
    answer, model_report = select_source_items(records)
    report.update({
        'used': bool(model_report.get('used')),
        'attempted': bool(model_report.get('attempted')),
        'model': model_report.get('model'),
        'reason': model_report.get('reason'),
    })
    chosen = validate(answer, records)
    if not chosen:
        report['reason'] = report['reason'] or 'The model chose nothing that could be used.'
        return report
    report['selections'] = chosen
    report['source'] = 'model'
    return report
