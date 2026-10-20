"""The platform layer: keys, ownership, exports, and metering.

These are the rules that make the product something a partner could license.
Each one is a promise, so each one is pinned.
"""
from __future__ import annotations

import time

import pytest

from backend.platform import Platform, hash_key


@pytest.fixture
def platform(tmp_path):
    return Platform(tmp_path / 'platform.db')


def test_a_key_is_issued_and_never_stored_in_the_clear(platform):
    issued = platform.issue_key(platform.create_workspace('Acme')['id'], ['read', 'export'])

    assert issued['key'].startswith(issued['prefix'])
    stored = platform.keys(issued['workspaceId'])
    assert len(stored) == 1
    assert issued['key'] not in str(stored), 'the secret must not be recoverable'


def test_a_valid_key_authenticates_and_a_wrong_one_does_not(platform):
    workspace = platform.create_workspace('Acme')
    issued = platform.issue_key(workspace['id'], ['read'])

    identity = platform.authenticate(issued['key'])
    assert identity is not None
    assert identity['workspaceId'] == workspace['id']

    assert platform.authenticate(issued['key'].replace('cfk_', 'cfk_x')) is None
    assert platform.authenticate('not-a-key') is None
    assert platform.authenticate('') is None


def test_a_revoked_key_stops_working(platform):
    workspace = platform.create_workspace('Acme')
    issued = platform.issue_key(workspace['id'], ['read'])
    assert platform.authenticate(issued['key']) is not None

    assert platform.revoke_key(issued['id']) is True
    assert platform.authenticate(issued['key']) is None


def test_an_expired_key_stops_working(platform):
    workspace = platform.create_workspace('Acme')
    issued = platform.issue_key(workspace['id'], ['read'], expires_at=time.time() - 1)
    assert platform.authenticate(issued['key']) is None


def test_a_key_cannot_be_issued_for_a_workspace_that_does_not_exist(platform):
    with pytest.raises(ValueError):
        platform.issue_key('ws-nope', ['read'])


def test_an_exploration_is_saved_and_listed(platform):
    workspace = platform.create_workspace('Acme')
    saved = platform.save_exploration(
        workspace['id'], {'concepts': [{'name': 'The Slow Hour'}]},
        title='Food & beverage in Brooklyn', brief={'audience': 'Gen Z'})

    assert saved['id']
    listed = platform.explorations(workspace['id'])
    assert len(listed) == 1
    assert listed[0]['title'] == 'Food & beverage in Brooklyn'
    assert platform.exploration_payload(saved['id'])['concepts'][0]['name'] == 'The Slow Hour'


def test_a_new_version_is_added_when_an_exploration_is_saved_again(platform):
    workspace = platform.create_workspace('Acme')
    first = platform.save_exploration(workspace['id'], {'concepts': []}, 'First', {'audience': 'a'})
    second = platform.save_exploration(workspace['id'], {'concepts': []}, 'Second', {'audience': 'a'},
                                       exploration_id=first['id'])

    assert second['id'] == first['id']
    assert len(second['versions']) == 2
    assert second['versions'][0]['version'] == 2


def test_one_workspace_cannot_see_another_workspaces_explorations(platform):
    mine = platform.create_workspace('Mine')
    theirs = platform.create_workspace('Theirs')
    saved = platform.save_exploration(theirs['id'], {'concepts': []}, 'Theirs', {})

    assert platform.explorations(mine['id']) == []
    assert platform.exploration(saved['id'])['workspaceId'] == theirs['id']
    assert platform.delete_exploration(saved['id'], mine['id']) is False
    assert platform.exploration(saved['id']) is not None, 'another workspace cannot delete it'


def test_a_shared_snapshot_is_reachable_and_revocable(platform):
    snapshot_id = platform.save_share({'concepts': [{'name': 'The Slow Hour'}]})
    assert platform.share(snapshot_id)['concepts'][0]['name'] == 'The Slow Hour'

    assert platform.revoke_share(snapshot_id) is True
    assert platform.share(snapshot_id) is None


def test_usage_is_metered(platform):
    workspace = platform.create_workspace('Acme')
    platform.record_usage('/api/projects/generate', 'POST', 200, workspace['id'], 'cfk_abc', 2, 120)
    platform.record_usage('/api/health', 'GET', 200, workspace['id'], 'cfk_abc', 0, 4)

    usage = platform.usage(workspace['id'])
    assert usage['requests'] == 2
    assert usage['upstreamCalls'] == 2
    assert usage['byRoute']['/api/projects/generate'] == 1


def test_the_key_hash_is_salted_so_a_stolen_database_is_not_a_stolen_key_book():
    assert hash_key('secret') != hash_key('secret'.upper())
    assert len(hash_key('secret')) == 64
