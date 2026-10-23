"""Fair use for a public demo: cold work is limited, held work never is, and a refusal says what to do."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend import admission as admission_module
from backend.admission import Admission, Refusal

BRIEF = {'businessType': 'Retail', 'businessIdea': 'bookshop', 'audience': 'Readers of translated fiction',
         'location': 'Mexico City, Mexico', 'budget': '$25k – $50k', 'objectives': ['x']}


@pytest.fixture(autouse=True)
def limits(monkeypatch):
    monkeypatch.setenv('CULTUREFORGE_MAX_COLD_RUNS', '2')
    monkeypatch.setenv('CULTUREFORGE_COLD_RUNS_PER_CLIENT_HOUR', '3')
    admission_module.admission.reset()
    yield
    admission_module.admission.reset()


def test_held_work_is_never_counted_or_refused():
    gate = Admission()
    for _ in range(20):
        assert gate.enter('a', held=True) is None
    assert gate.snapshot()['coldRunsActive'] == 0


def test_only_a_few_cold_briefs_run_at_once_and_a_slot_frees_when_one_ends():
    gate = Admission()
    first, second = gate.enter('a', held=False), gate.enter('b', held=False)
    with pytest.raises(Refusal) as busy:
        gate.enter('c', held=False)
    assert busy.value.code == 'DEMO_BUSY' and 'prepared example' in busy.value.message
    gate.leave(first)
    assert gate.enter('c', held=False)
    gate.leave(second)


def test_one_visitor_has_an_hourly_allowance_and_it_comes_back():
    gate = Admission()
    for moment in (0, 10, 20):
        gate.leave(gate.enter('a', held=False, now=moment))
    with pytest.raises(Refusal) as limited:
        gate.enter('a', held=False, now=30)
    assert limited.value.code == 'CLIENT_RATE_LIMITED' and 3500 < limited.value.retry_after_seconds <= 3600
    # Another visitor is unaffected, and the first can return once the hour has passed.
    gate.leave(gate.enter('b', held=False, now=30))
    gate.leave(gate.enter('a', held=False, now=3601))


def test_limits_can_be_switched_off(monkeypatch):
    monkeypatch.setenv('CULTUREFORGE_MAX_COLD_RUNS', '0')
    monkeypatch.setenv('CULTUREFORGE_COLD_RUNS_PER_CLIENT_HOUR', '0')
    gate = Admission()
    for _ in range(30):
        assert gate.enter('a', held=False)


def test_behind_a_local_proxy_each_visitor_is_their_own_address_and_a_public_peer_cannot_forge_one(monkeypatch):
    """Caddy, a tunnel or Docker's bridge makes every request arrive from a local address. Judges must not share a budget."""
    def request(peer, forwarded='1.1.1.1, 203.0.113.9'):
        return type('Req', (), {'headers': {'x-forwarded-for': forwarded}, 'client': type('C', (), {'host': peer})()})()
    monkeypatch.delenv('CULTUREFORGE_TRUST_PROXY', raising=False)
    for peer in ('127.0.0.1', '::1', '172.18.0.1', '10.0.0.2'):
        assert admission_module.client_id(request(peer)) == '203.0.113.9', peer
    # An internet peer is itself the visitor: a forged header is not believed.
    assert admission_module.client_id(request('8.8.4.4')) == '8.8.4.4'
    # No header from a local peer: the peer.
    assert admission_module.client_id(request('127.0.0.1', '')) == '127.0.0.1'
    monkeypatch.setenv('CULTUREFORGE_TRUST_PROXY', 'true')
    assert admission_module.client_id(request('8.8.4.4')) == '203.0.113.9'
    monkeypatch.setenv('CULTUREFORGE_TRUST_PROXY', 'false')
    assert admission_module.client_id(request('127.0.0.1')) == '127.0.0.1'


def test_the_route_answers_429_with_retry_after_and_a_way_out(monkeypatch):
    monkeypatch.setattr(main.examples, 'held', lambda project: False)
    started = []
    monkeypatch.setattr(main, 'start_research', lambda *a, **k: started.append(k) or type(
        'R', (), {'id': f'run-{len(started)}', 'status': 'running'})())
    client = TestClient(main.app, raise_server_exceptions=False)
    body = {'project': BRIEF, 'audience': BRIEF['audience'], 'seedTagIds': []}
    for index in range(2):
        other = {**body, 'project': {**BRIEF, 'location': f'City {index}'}}
        assert client.post('/api/research/runs', json=other).status_code == 202
    refused = client.post('/api/research/runs', json={**body, 'project': {**BRIEF, 'location': 'Third City'}})
    assert refused.status_code == 429 and refused.headers['retry-after'] == '60'
    error = refused.json()['error']
    assert error['code'] == 'DEMO_BUSY' and error['retryable'] and 'prepared example' in error['message']
    assert len(started) == 2


def test_an_identical_running_brief_is_joined_not_started_twice(monkeypatch):
    from backend import research
    monkeypatch.setattr(main.examples, 'held', lambda project: False)
    created = []

    def fake_start(project, audience, seeds, workspace_id=None, on_finish=None):
        run = research.ResearchRun(project, audience, workspace_id)
        run.key = research.run_key(project, audience, seeds)
        research.registry.add(run)
        created.append(run)
        return run
    monkeypatch.setattr(main, 'start_research', fake_start)
    client = TestClient(main.app, raise_server_exceptions=False)
    body = {'project': BRIEF, 'audience': BRIEF['audience'], 'seedTagIds': []}
    first = client.post('/api/research/runs', json=body).json()
    second = client.post('/api/research/runs', json=body).json()
    assert second['runId'] == first['runId'] and second['joined'] is True and len(created) == 1
