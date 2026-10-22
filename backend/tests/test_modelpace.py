"""Model-gateway pacing: at most N requests start in a rolling minute, and a
429's Retry-After holds everyone, not just the caller that was refused."""
from __future__ import annotations

import io
import json
import urllib.error

import pytest

from backend import modelpace, reasoning
from backend.models import AgentStepPlan


class Clock:
    def __init__(self):
        self.t = 1000.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.slept.append(round(seconds, 2))
        self.t += seconds


@pytest.fixture
def paced(monkeypatch):
    monkeypatch.setenv('LLM_REQUESTS_PER_MINUTE', '5')
    modelpace.reset()
    return Clock()


def test_five_requests_start_at_once_and_the_sixth_waits_for_the_first_to_age(paced):
    for _ in range(5):
        assert modelpace.wait_for_slot(paced.now, paced.sleep) == 0.0
    paced.t += 20          # the first request is now 20 seconds old
    waited = modelpace.wait_for_slot(paced.now, paced.sleep)
    assert 39.9 < waited < 40.2          # 60 - 20, plus a hair
    assert paced.slept and sum(paced.slept) == pytest.approx(waited)


def test_a_slot_frees_as_requests_age_out(paced):
    for _ in range(5):
        modelpace.wait_for_slot(paced.now, paced.sleep)
    paced.t += 61
    assert modelpace.wait_for_slot(paced.now, paced.sleep) == 0.0


def test_zero_switches_pacing_off(monkeypatch, paced):
    monkeypatch.setenv('LLM_REQUESTS_PER_MINUTE', '0')
    for _ in range(50):
        assert modelpace.wait_for_slot(paced.now, paced.sleep) == 0.0
    assert paced.slept == []


def test_retry_after_holds_every_caller(paced):
    assert modelpace.note_limited('27', paced.now) == 27
    waited = modelpace.wait_for_slot(paced.now, paced.sleep)
    assert 26.9 < waited < 27.2
    assert modelpace.note_limited(None, paced.now) == 15           # no header: a sensible default
    assert modelpace.note_limited('9999', paced.now) == 60         # never a stall of minutes


def test_a_wait_longer_than_the_cap_gives_up_and_lets_the_gateway_decide(paced):
    modelpace.note_limited('60', paced.now)
    modelpace._blocked_until = paced.t + 500       # far beyond MAX_WAIT_SECONDS
    assert modelpace.wait_for_slot(paced.now, paced.sleep) == 0.0 and paced.slept == []


class _Response:
    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps({'choices': [{'message': {'content': json.dumps(self.content)}}]}).encode()


def _http_429():
    return urllib.error.HTTPError('https://gateway', 429, 'Too Many Requests', {'Retry-After': '1'}, io.BytesIO(b'{}'))


def test_a_429_from_the_gateway_is_waited_out_once_and_asked_again(monkeypatch, paced):
    monkeypatch.setenv('AI_GATEWAY_MODEL', 'test/model')
    monkeypatch.setenv('AI_GATEWAY_API_KEY', 'test-only-placeholder')
    monkeypatch.setattr(reasoning, '_reserve', lambda: None)
    monkeypatch.setattr(modelpace.time, 'sleep', paced.sleep)
    monkeypatch.setattr(modelpace.time, 'time', paced.now)
    answers = [_http_429(), _Response({'tool': 'finish', 'arguments': {}, 'reason': 'Nothing more to learn.'})]
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(1)
        outcome = answers.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    monkeypatch.setattr(reasoning.urllib.request, 'urlopen', fake_urlopen)
    plan = reasoning.call_structured('p', {}, AgentStepPlan)
    assert plan.tool == 'finish' and len(calls) == 2
    assert any(0.9 < s < 1.2 for s in paced.slept)


def test_a_second_429_is_raised_as_an_unavailable_model_not_retried_again(monkeypatch, paced):
    monkeypatch.setenv('AI_GATEWAY_MODEL', 'test/model')
    monkeypatch.setenv('AI_GATEWAY_API_KEY', 'test-only-placeholder')
    monkeypatch.setattr(reasoning, '_reserve', lambda: None)
    monkeypatch.setattr(modelpace.time, 'sleep', paced.sleep)
    monkeypatch.setattr(modelpace.time, 'time', paced.now)
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(1)
        raise _http_429()
    monkeypatch.setattr(reasoning.urllib.request, 'urlopen', fake_urlopen)
    with pytest.raises(reasoning.AnalysisUnavailable):
        reasoning.call_structured('p', {}, AgentStepPlan)
    assert len(calls) == 2
