"""The run profiles: dev enforces the local budgets, judging lifts every count
and keeps every other guard. No test here reaches Qloo or a model."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend import config, examples, llm, reasoning, research
from backend.evidence_store import canonical_key
from backend.providers import (QlooHarnessError, QlooHarnessProvider, brief_places_payload,
                               brief_tags_payload)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def judging(monkeypatch):
    monkeypatch.setenv('RUN_PROFILE', 'judging')


@pytest.fixture
def provider(monkeypatch):
    """A Qloo provider whose transport is a fake subprocess."""
    instance = QlooHarnessProvider()
    monkeypatch.setattr(instance, '_resolve_command', lambda: ['fake-qloo'])
    return instance


def _fake_cli(monkeypatch, stdout: dict, returncode: int = 0) -> list:
    calls = []

    def run(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=returncode, stdout=json.dumps(stdout), stderr='')
    monkeypatch.setattr(subprocess, 'run', run)
    return calls


# ------------------------------------------------------------------ profiles
def test_dev_is_the_default_profile_and_enforces_the_documented_defaults(monkeypatch):
    monkeypatch.delenv('RUN_PROFILE')
    for name in config.DEV_LIMITS:
        monkeypatch.delenv(name, raising=False)
    assert config.run_profile() == 'dev'
    assert config.budgets_enforced()
    assert {name: config.limit(name) for name in config.DEV_LIMITS} == config.DEV_LIMITS
    assert config.evidence_ttl_seconds() == 24 * 3600


def test_judging_lifts_every_call_count_budget(judging, monkeypatch):
    # Even an explicit cap in the environment is not enforced in judging.
    for name in config.DEV_LIMITS:
        monkeypatch.setenv(name, '1')
    assert config.run_profile() == 'judging'
    assert not config.budgets_enforced()
    assert all(config.limit(name) is None for name in config.DEV_LIMITS)
    assert config.evidence_ttl_seconds() == 14 * 24 * 3600


def test_an_unknown_profile_falls_back_to_dev_and_says_so(monkeypatch):
    monkeypatch.setenv('RUN_PROFILE', 'judgeing')
    assert config.run_profile() == 'dev'
    assert config.budgets_enforced()
    assert 'judgeing' in config.profile_warning()


def test_dev_limits_cannot_be_switched_off_by_a_typo(monkeypatch):
    monkeypatch.setenv('QLOO_MAX_CALLS_PER_HOUR', '0')
    monkeypatch.setenv('QLOO_MAX_CALLS_PER_DAY', 'lots')
    assert config.limit('QLOO_MAX_CALLS_PER_HOUR') == 1
    assert config.limit('QLOO_MAX_CALLS_PER_DAY') == config.DEV_LIMITS['QLOO_MAX_CALLS_PER_DAY']


def test_dev_analysis_allowance_can_be_lowered_but_not_raised(monkeypatch):
    monkeypatch.setenv('AI_GATEWAY_ANALYSIS_DAILY_LIMIT', '500')
    assert config.limit('AI_GATEWAY_ANALYSIS_DAILY_LIMIT') == 10
    monkeypatch.setenv('AI_GATEWAY_ANALYSIS_DAILY_LIMIT', '2')
    assert config.limit('AI_GATEWAY_ANALYSIS_DAILY_LIMIT') == 2


def test_the_evidence_ttl_can_be_set_explicitly(judging, monkeypatch):
    monkeypatch.setenv('CULTUREFORGE_EVIDENCE_TTL_HOURS', '48')
    assert config.evidence_ttl_seconds() == 48 * 3600


# ---------------------------------------------------- budgets in each profile
def test_dev_refuses_the_qloo_call_past_its_budget(provider, monkeypatch):
    monkeypatch.setenv('QLOO_MAX_CALLS_PER_HOUR', '1')
    provider._consume_call_budget()
    with pytest.raises(QlooHarnessError) as caught:
        provider._consume_call_budget()
    assert caught.value.code == 'QUOTA_EXHAUSTED'


def test_judging_raises_no_qloo_budget_and_still_counts(provider, judging):
    for _ in range(150):
        provider._consume_call_budget()
    state = QlooHarnessProvider.budget_state()
    assert state['callsToday'] == 150
    assert state['hourLimit'] == state['dayLimit'] == 'unlimited'


def test_judging_raises_no_model_budget(judging, monkeypatch, tmp_path):
    monkeypatch.setattr(llm, 'BUDGET_LOG_PATH', tmp_path / 'naming.json')
    monkeypatch.setattr(reasoning, 'BUDGET_FILE', tmp_path / 'analysis.json')
    for _ in range(60):
        llm._record_call()
        llm._check_budget()
        reasoning._reserve()
    assert llm.budget_state()['dayLimit'] == 'unlimited'
    assert reasoning.budget_state() == {'callsToday': 60, 'dayLimit': 'unlimited'}


def test_judging_tolerates_an_unreadable_analysis_ledger(judging, monkeypatch, tmp_path):
    ledger = tmp_path / 'analysis.json'
    ledger.write_text('{broken', encoding='utf-8')
    monkeypatch.setattr(reasoning, 'BUDGET_FILE', ledger)
    reasoning._reserve()


def test_a_research_run_is_bounded_by_its_deadline_in_judging(judging, monkeypatch):
    seen = {}
    monkeypatch.setattr(research.threading, 'Thread',
                        lambda target, args, daemon: SimpleNamespace(start=lambda: seen.update(allowance=args[1])))
    research.start_research(main.ProjectRequest(**examples.briefs()[0]['project']))
    assert seen['allowance'] is None


def test_a_research_run_keeps_its_workflow_allowance_in_dev(monkeypatch):
    monkeypatch.delenv('RESEARCH_RUN_MAX_WORKFLOWS', raising=False)
    seen = {}
    monkeypatch.setattr(research.threading, 'Thread',
                        lambda target, args, daemon: SimpleNamespace(start=lambda: seen.update(allowance=args[1])))
    research.start_research(main.ProjectRequest(**examples.briefs()[0]['project']))
    assert seen['allowance'] == 3


# ----------------------------------------------- guards kept in both profiles
def test_the_kill_switch_serves_held_evidence_and_fetches_nothing(provider, judging, monkeypatch, store):
    monkeypatch.setenv('QLOO_LIVE_ENABLED', 'false')
    calls = _fake_cli(monkeypatch, {'status': 'ok', 'results': []})
    held = {'operation': 'find_tags', 'status': 'ok', 'results': [{'id': 'urn:tag:x'}]}
    store.put(canonical_key('find_tags', {'query': 'held', 'limit': 3}), held)
    envelope, cached, requests = provider.run_workflow_cached('find_tags', {'query': 'held', 'limit': 3})
    assert (envelope, cached, requests) == (held, True, 0)
    with pytest.raises(QlooHarnessError) as caught:
        provider.run_workflow_cached('find_tags', {'query': 'cold', 'limit': 3})
    assert caught.value.code == 'LIVE_DISABLED'
    assert calls == []
    assert QlooHarnessProvider.budget_state()['callsToday'] == 0


def test_a_429_pauses_live_calls_without_a_retry(provider, judging, monkeypatch):
    calls = _fake_cli(monkeypatch, {'error': {'code': 'QLOO_RATE_LIMITED', 'status': 429}}, returncode=1)
    with pytest.raises(QlooHarnessError) as first:
        provider._run_workflow('find_tags', {'query': 'a', 'limit': 3})
    assert first.value.code == 'RATE_LIMITED'
    with pytest.raises(QlooHarnessError) as second:
        provider._run_workflow('find_tags', {'query': 'b', 'limit': 3})
    assert second.value.code == 'RATE_LIMITED'
    assert second.value.details['resetsInSeconds'] > 0
    assert len(calls) == 1


def test_the_cool_down_can_be_turned_off(provider, monkeypatch):
    monkeypatch.setenv('QLOO_RATE_LIMIT_COOLDOWN_SECONDS', '0')
    calls = _fake_cli(monkeypatch, {'error': {'status': 429}}, returncode=1)
    for _ in range(2):
        with pytest.raises(QlooHarnessError):
            provider._run_workflow('find_tags', {'query': 'a', 'limit': 3})
    assert len(calls) == 2


@pytest.mark.parametrize('status, code', [(401, 'UPSTREAM_UNAUTHENTICATED'), (503, 'PROVIDER_UNAVAILABLE'),
                                          (500, 'PROVIDER_UNAVAILABLE')])
def test_upstream_failures_map_to_stated_codes(provider, monkeypatch, status, code):
    calls = _fake_cli(monkeypatch, {'error': {'status': status}}, returncode=1)
    with pytest.raises(QlooHarnessError) as caught:
        provider._run_workflow('find_tags', {'query': 'a', 'limit': 3})
    assert caught.value.code == code
    assert len(calls) == 1


def test_the_kill_switch_is_a_503_with_the_error_envelope():
    response = main.error_response('LIVE_DISABLED', 'off')
    assert response.status_code == 503


# ---------------------------------------------------------------- health
def test_health_reports_the_profile_budgets_and_cache(monkeypatch):
    client = TestClient(main.app)
    body = client.get('/api/health').json()
    assert body['profile'] == 'dev'
    assert body['budgetsEnforced'] is True
    assert body['budgets']['qloo']['hourLimit'] == config.limit('QLOO_MAX_CALLS_PER_HOUR')
    assert set(body['budgets']) == {'qloo', 'llm', 'analysis', 'researchRunWorkflows'}
    assert body['cache']['entries'] == 0

    monkeypatch.setenv('RUN_PROFILE', 'judging')
    body = client.get('/api/health').json()
    assert body['profile'] == 'judging'
    assert body['budgets']['qloo']['dayLimit'] == 'unlimited'
    assert body['budgets']['llm']['dayLimit'] == 'unlimited'
    assert body['budgets']['analysis']['dayLimit'] == 'unlimited'
    assert body['budgets']['researchRunWorkflows'] == 'unlimited'


def test_health_reports_the_profile_when_qloo_is_not_configured(monkeypatch):
    monkeypatch.setenv('CULTUREFORGE_PROVIDER', 'qloo')
    monkeypatch.setattr('backend.providers._is_qloo_configured', lambda: False)
    body = TestClient(main.app).get('/api/health').json()
    assert body['providerReady'] is False
    assert body['profile'] == 'dev'
    assert 'budgets' in body


# -------------------------------------------------------------- examples
def test_there_are_at_least_eight_prepared_briefs_across_cities_and_types():
    rows = examples.briefs()
    assert len(rows) >= 8
    assert len({row['id'] for row in rows}) == len(rows)
    assert len({row['project']['location'] for row in rows}) >= 6
    assert len({row['project']['businessType'] for row in rows}) == 5


def test_the_landing_page_and_studio_run_the_first_prepared_brief():
    assert "demoBriefs.briefs[0].project" in (ROOT / 'main.js').read_text(encoding='utf-8')
    assert "demoBriefs.briefs[0].project" in (ROOT / 'src' / 'App.tsx').read_text(encoding='utf-8')


def test_a_brief_is_held_only_when_its_seeds_and_places_are(store):
    project = examples.briefs()[0]['project']
    client = TestClient(main.app)
    assert client.get('/api/examples').json()['examples'][0]['held'] is False
    tags = {'operation': 'find_tags', 'status': 'ok', 'results': [{'id': 'urn:tag:a'}, {'id': 'urn:tag:b'}]}
    store.put(canonical_key('find_tags', brief_tags_payload(project['businessType'], project['audience'])), tags)
    assert examples.held(project) is False
    store.put(canonical_key('recommend', brief_places_payload(['urn:tag:a', 'urn:tag:b'], project['location'])),
              {'operation': 'recommend', 'status': 'ok', 'results': []})
    assert client.get('/api/examples').json()['examples'][0]['held'] is True


# ----------------------------------------------------------------- drift
def _documented(path: Path, pattern: str) -> dict[str, int]:
    text = path.read_text(encoding='utf-8')
    return {match.group(1): int(match.group(2)) for match in re.finditer(pattern, text, re.MULTILINE)}


def test_env_example_states_the_dev_defaults():
    found = _documented(ROOT / '.env.example', r'^#?\s*([A-Z_]+)=(\d+)\s*$')
    assert {name: found.get(name) for name in config.DEV_LIMITS} == config.DEV_LIMITS
    assert re.search(r'^RUN_PROFILE=dev$', (ROOT / '.env.example').read_text(encoding='utf-8'), re.MULTILINE)


def test_readme_states_the_dev_defaults_and_the_judging_profile():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    found = _documented(ROOT / 'README.md', r'^\|\s*`([A-Z_]+)`\s*\|\s*(\d+)\s*\|')
    assert {name: found.get(name) for name in config.DEV_LIMITS} == config.DEV_LIMITS
    for name in config.DEV_LIMITS:
        assert re.search(rf'^\|\s*`{name}`\s*\|\s*\d+\s*\|\s*unlimited\s*\|', readme, re.MULTILINE), name
    ttl = re.search(r'^\|\s*`CULTUREFORGE_EVIDENCE_TTL_HOURS`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|', readme, re.MULTILINE)
    assert ttl and (int(ttl.group(1)), int(ttl.group(2))) == (
        config.EVIDENCE_TTL_HOURS['dev'], config.EVIDENCE_TTL_HOURS['judging'])
