"""What one visitor can see of another's work, and what an unauthenticated route may cost the disk.

The public demo gives each visitor a workspace so their ideas are never listed to the next judge;
these pin that the run list and the usage figures honour it, and that the share route is bounded.
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend.admission import SlidingWindowLimiter
from backend.models import ProjectRequest
from backend.platform import Platform
from backend.research import ResearchRegistry, ResearchRun


@pytest.fixture
def client():
    return TestClient(main.app, raise_server_exceptions=False)


def _run(workspace_id):
    project = ProjectRequest(businessType='Retail', businessIdea='Bookshop cafe', audience='Readers',
                             location='London', budget='', objectives=[])
    return ResearchRun(project, workspace_id=workspace_id)


def test_the_run_list_holds_only_the_callers_own_runs():
    registry = ResearchRegistry()
    mine, theirs = _run('ws-mine'), _run('ws-theirs')
    registry.add(mine)
    registry.add(theirs)

    assert [r['runId'] for r in registry.recent(workspace_id='ws-mine')] == [mine.id]
    assert [r['runId'] for r in registry.recent(workspace_id='ws-nobody')] == []
    assert len(registry.recent()) == 2, 'with no workspace named, the registry itself is unfiltered'


def test_the_runs_route_does_not_list_another_visitors_idea(client, monkeypatch):
    monkeypatch.setenv('RUN_PROFILE', 'judging')
    other = _run(main.get_platform().create_workspace('Visitor someone-else')['id'])
    main.research_registry.add(other)
    try:
        runs = client.get('/api/research/runs').json()['runs']
        assert other.id not in [r['runId'] for r in runs]
    finally:
        main.research_registry._runs.pop(other.id, None)
        main.research_registry._order.remove(other.id)


def test_a_missing_run_says_what_to_do_next(client):
    detail = client.get('/api/research/runs/run-gone').json()['detail']
    assert 'aged out' in detail and 'again' in detail


def test_usage_is_the_callers_workspace_and_all_of_it_is_for_the_operator(client, monkeypatch):
    platform = main.get_platform()
    stranger = platform.create_workspace('Stranger')
    platform.record_usage('/api/secret-route', 'POST', 200, stranger['id'], None, 3, 10)

    own = client.get('/api/usage').json()
    assert '/api/secret-route' not in own['byRoute'], "another workspace's traffic is not shown"

    monkeypatch.delenv('CULTUREFORGE_OPERATOR_TOKEN', raising=False)
    elsewhere = client.get('/api/usage?scope=all', headers={'x-forwarded-for': '203.0.113.9'})
    assert elsewhere.status_code == 403, 'the deployment-wide figure is closed to a proxied caller'

    monkeypatch.setenv('CULTUREFORGE_OPERATOR_TOKEN', 'letmein')
    allowed = client.get('/api/usage?scope=all', headers={'x-operator-token': 'letmein'})
    assert allowed.status_code == 200
    assert allowed.json()['byRoute']['/api/secret-route'] == 1


def test_health_probes_and_static_files_are_not_metered(client):
    platform = main.get_platform()
    before = platform.usage()['requests']
    client.get('/health')
    client.get('/api/health')
    client.get('/some-page.html')
    assert platform.usage()['requests'] == before
    client.get('/api/examples')
    assert platform.usage()['requests'] == before + 1


def test_usage_is_counted_in_the_database_and_old_rows_are_pruned(tmp_path):
    platform = Platform(tmp_path / 'p.db')
    workspace = platform.create_workspace('Acme')
    platform.record_usage('/api/a', 'GET', 200, workspace['id'], None, 2, 1)
    platform.record_usage('/api/a', 'GET', 200, workspace['id'], None, 0, 1)
    platform._execute('UPDATE usage_events SET created_at = ? WHERE id = (SELECT MIN(id) FROM usage_events)',
                      (time.time() - 200 * 86400,))

    assert platform.usage(days=365)['requests'] == 2
    assert platform.prune_usage(retention_days=90) == 1
    left = platform.usage(days=365)
    assert (left['requests'], left['upstreamCalls'], left['byRoute']) == (1, 0, {'/api/a': 1})


def test_a_workspace_is_found_by_name_without_listing_them_all(tmp_path):
    platform = Platform(tmp_path / 'p.db')
    first = platform.create_workspace('Visitor abc')
    platform.create_workspace('Visitor abc')
    assert platform.workspace_named('Visitor abc')['id'] == first['id']
    assert platform.workspace_named('Visitor nobody') is None


def test_a_snapshot_over_the_cap_is_refused_with_a_reason(client, monkeypatch):
    monkeypatch.setattr(main, 'MAX_SNAPSHOT_BYTES', 200)
    response = client.post('/api/explorations/share', json={'concepts': [{'name': 'x' * 500}]})
    assert response.status_code == 413
    assert 'too large' in response.json()['detail']


def test_sharing_is_limited_per_address(client, monkeypatch):
    monkeypatch.setattr(main, 'share_limiter', SlidingWindowLimiter(limit=2, window_seconds=3600))
    statuses = [client.post('/api/explorations/share', json={'concepts': []}).status_code for _ in range(3)]
    assert statuses == [201, 201, 429]


def test_the_sliding_window_forgets_old_events():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=10)
    assert limiter.allow('a', now=0) is True
    assert limiter.allow('a', now=5) is False
    assert limiter.allow('b', now=5) is True, 'another address has its own allowance'
    assert limiter.allow('a', now=11) is True


def test_open_localhost_cors_is_for_development_only(monkeypatch):
    monkeypatch.setenv('RUN_PROFILE', 'dev')
    assert main.cors_origin_regex()
    monkeypatch.setenv('RUN_PROFILE', 'judging')
    assert main.cors_origin_regex() is None


# --- runs survive a restart --------------------------------------------------------------------

def test_a_finished_run_is_readable_after_the_process_forgets_it(client):
    run = _run(main.get_platform().create_workspace('Visitor a')['id'])
    run.status, run.result = 'complete', {'projectId': 'p-1', 'concepts': []}
    main.get_platform().save_run(run.snapshot(), run.workspace_id)

    assert main.research_registry.get(run.id) is None, 'this process has never held it'
    body = client.get(f'/api/research/runs/{run.id}').json()
    assert body['status'] == 'complete' and body['result']['projectId'] == 'p-1'


def test_a_run_left_running_by_a_stopped_process_becomes_a_stated_failure(client):
    platform = main.get_platform()
    run = _run(platform.create_workspace('Visitor b')['id'])
    platform.save_run(run.snapshot(), run.workspace_id)       # written when it started, still "running"

    assert platform.interrupt_running_runs() == 1
    body = client.get(f'/api/research/runs/{run.id}').json()
    assert body['status'] == 'failed' and body['errorCode'] == 'RUN_INTERRUPTED'
    assert 'Start it again' in body['error']
    assert platform.interrupt_running_runs() == 0, 'a closed run is not closed twice'


def test_a_started_run_is_persisted_at_both_ends(monkeypatch):
    from backend import research
    monkeypatch.setattr(research, '_execute', lambda run, allowance: setattr(run, 'status', research.STATUS_COMPLETE))
    seen = []
    real = main.get_platform().save_run
    monkeypatch.setattr(main.get_platform(), 'save_run', lambda snap, ws: (seen.append(snap['status']), real(snap, ws)))
    run = research.start_research(_run(None).project, workspace_id=None)
    for _ in range(100):
        if 'complete' in seen:
            break
        time.sleep(0.02)
    assert seen[0] == 'running' and seen[-1] == 'complete'
    main.research_registry._runs.pop(run.id, None)
    main.research_registry._order.remove(run.id)


def test_the_run_list_includes_persisted_runs_of_the_caller_only(client):
    platform = main.get_platform()
    client.get('/api/usage')  # makes sure the local workspace exists
    mine = _run(next(w for w in platform.workspaces() if w['name'] == 'Local studio')['id'])
    other = _run(platform.create_workspace('Visitor c')['id'])
    for run in (mine, other):
        platform.save_run(run.snapshot(), run.workspace_id)
    ids = [r['runId'] for r in client.get('/api/research/runs').json()['runs']]
    assert mine.id in ids and other.id not in ids


def test_old_runs_are_pruned(tmp_path):
    platform = Platform(tmp_path / 'p.db')
    run = _run(None)
    platform.save_run(run.snapshot(), None)
    platform._execute('UPDATE run_snapshots SET updated_at = ?', (time.time() - 30 * 86400,))
    assert platform.prune_runs(retention_days=7) == 1
    assert platform.load_run(run.id) is None
