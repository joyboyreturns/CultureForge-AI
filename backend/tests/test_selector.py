"""The model selects from the evidence; it never writes any of it.

No network is touched. The model's answer is scripted, and the point is that whatever it says, only
ids that belong to this exact input can reach the screen.
"""
from __future__ import annotations

from backend import selector

EVIDENCE = [
    {'kind': 'entity', 'entityId': 'E1', 'label': 'Rough Trade',
     'description': 'A record shop in a former warehouse. It hosts live sets on Fridays. It also sells zines.'},
    {'kind': 'entity', 'entityId': 'E2', 'label': 'Pages',
     'description': 'A small independent bookshop.'},
    {'kind': 'tag', 'entityId': 'T1', 'label': 'indie', 'description': 'Ignored: not an entity.'},
    {'kind': 'entity', 'entityId': None, 'label': 'No id', 'description': 'Ignored: nothing to cite.'},
    {'kind': 'entity', 'entityId': 'E3', 'label': 'Silent', 'description': ''},
    'not a dict',
]


def _records():
    return selector._records(EVIDENCE)


def _first_ids(entity_id, count=3):
    record = next(r for r in _records() if r['entityId'] == entity_id)
    return [s['id'] for s in record['sentences']][:count]


def test_only_entities_with_an_id_and_a_description_are_offered():
    assert [r['entityId'] for r in _records()] == ['E1', 'E2']


def test_the_model_is_given_ids_with_the_servers_own_text():
    record = _records()[0]
    assert record['label'] == 'Rough Trade'
    assert all(set(s) == {'id', 'text'} for s in record['sentences'])


def test_a_valid_selection_is_rendered_from_the_servers_strings():
    ids = _first_ids('E1', 1)
    chosen = selector.validate({'records': [{'entityId': 'E1', 'sentenceIds': ids}]}, _records())
    assert chosen['E1']['sentenceIds'] == ids
    assert chosen['E1']['sentences'] == ['A record shop in a former warehouse.']


def test_an_unknown_entity_is_dropped():
    answer = {'records': [{'entityId': 'INVENTED', 'sentenceIds': ['s1']}]}
    assert selector.validate(answer, _records()) == {}


def test_a_sentence_the_entity_does_not_have_is_dropped():
    # E1 has three sentences, E2 has one: `description:2` exists for E1 and means nothing for E2.
    chosen = selector.validate({'records': [{'entityId': 'E2', 'sentenceIds': ['description:2']}]}, _records())
    assert chosen == {}
    mixed = selector.validate({'records': [{'entityId': 'E2', 'sentenceIds': ['description:2', 'description:0']}]},
                              _records())
    assert mixed['E2']['sentenceIds'] == ['description:0']
    assert mixed['E2']['sentences'] == ['A small independent bookshop.']


def test_duplicates_are_collapsed_and_the_counts_are_capped():
    ids = _first_ids('E1', 3)
    answer = {'records': [{'entityId': 'E1', 'sentenceIds': [ids[0], ids[0], ids[1], ids[2]],
                           'tagIds': ['a', 'a', 'b', 'c', 'd', 'e', 'f']}]}
    chosen = selector.validate(answer, _records())['E1']
    assert chosen['sentenceIds'] == ids[:selector.MAX_SENTENCES]
    assert chosen['tagIds'] == ['a', 'b', 'c', 'd'][:selector.MAX_TAGS]


def test_malformed_answers_choose_nothing():
    for answer in (None, 'text', [], {}, {'records': 'x'}, {'records': ['x', 3, None]},
                   {'records': [{'entityId': 7, 'sentenceIds': ['s']}]},
                   {'records': [{'entityId': 'E1', 'sentenceIds': [1, None], 'tagIds': [2]}]}):
        assert selector.validate(answer, _records()) == {}


def test_with_no_model_the_rules_stay_and_the_reason_is_stated(monkeypatch):
    monkeypatch.setattr(selector, 'select_source_items',
                        lambda records: (None, {'used': False, 'attempted': False, 'model': None,
                                                'reason': 'The model gateway is not enabled.'}))
    report = selector.select(EVIDENCE)
    assert report['source'] == 'rules' and report['selections'] == {}
    assert report['reason'] == 'The model gateway is not enabled.'


def test_a_model_answer_with_nothing_usable_falls_back_to_the_rules(monkeypatch):
    monkeypatch.setattr(selector, 'select_source_items',
                        lambda records: ({'records': [{'entityId': 'INVENTED'}]},
                                         {'used': True, 'attempted': True, 'model': 'm', 'reason': None}))
    report = selector.select(EVIDENCE)
    assert report['source'] == 'rules'
    assert report['reason'] == 'The model chose nothing that could be used.'


def test_a_usable_model_answer_is_marked_as_the_models_choice(monkeypatch):
    ids = _first_ids('E1', 1)
    monkeypatch.setattr(selector, 'select_source_items',
                        lambda records: ({'records': [{'entityId': 'E1', 'sentenceIds': ids}]},
                                         {'used': True, 'attempted': True, 'model': 'm', 'reason': None}))
    report = selector.select(EVIDENCE)
    assert report['source'] == 'model' and report['used'] is True
    assert list(report['selections']) == ['E1']


def test_nothing_to_choose_from_never_calls_the_model(monkeypatch):
    def unexpected(records):
        raise AssertionError('no evidence, no model call')
    monkeypatch.setattr(selector, 'select_source_items', unexpected)
    report = selector.select([{'kind': 'tag', 'entityId': 'T'}])
    assert report['reason'] == 'There was nothing to choose from.'
