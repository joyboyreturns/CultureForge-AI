"""The audience bridge: the brief's tags sent to other domains, with no location.

Every envelope here is held in the test's own evidence store; conftest makes
any real Qloo CLI call fail the test.
"""
from __future__ import annotations

import pytest

from backend import config, examples
from backend.evidence_store import canonical_key
from backend.models import ProjectRequest
from backend.providers import (BRIEF_PLACE_LIMIT, QlooHarnessError, QlooHarnessProvider,
                               bridge_payload, brief_places_payload, brief_tags_payload)

TAGS = ['urn:tag:customer_segment:qloo:gen_z_foodies', 'urn:tag:interests:qloo:food_design']


def _held_brief(store, recommend_places) -> ProjectRequest:
    project = ProjectRequest(**examples.briefs()[0]['project'])
    store.put(canonical_key('find_tags', brief_tags_payload(project.businessType, project.audience)),
              {'operation': 'find_tags', 'status': 'ok', 'results': [{'id': tag} for tag in TAGS]})
    store.put(canonical_key('recommend', brief_places_payload(TAGS, project.location)), recommend_places)
    return project


def _bridge_rows(domain: str) -> dict:
    return {'operation': 'recommend', 'status': 'ok', 'results': [
        {'entity_id': f'{domain}-{n}', 'name': f'{domain.title()} {n}', 'subtype': f'urn:entity:{domain}',
         'popularity': 0.9 - n / 10, 'affinity': 0.5} for n in range(7)]}


def test_the_bridge_domains_are_switchable(monkeypatch):
    monkeypatch.delenv('CULTUREFORGE_BRIDGE_DOMAINS')
    assert config.bridge_domains() == ['artist', 'movie', 'brand']
    monkeypatch.setenv('CULTUREFORGE_BRIDGE_DOMAINS', 'off')
    assert config.bridge_domains() == []
    monkeypatch.setenv('CULTUREFORGE_BRIDGE_DOMAINS', 'podcast, place, nonsense, podcast,album')
    assert config.bridge_domains() == ['podcast', 'album']


def test_a_bridge_request_carries_the_audience_tags_and_no_location():
    payload = bridge_payload(TAGS, 'artist')
    assert payload == {'target_type': 'artist', 'signal_tags': TAGS, 'limit': 5}
    assert not any('location' in key for key in payload)


def test_the_place_sample_fits_what_the_evidence_test_can_send():
    """Qloo's rank and compare_audiences accept at most ten entities a list."""
    assert 5 < BRIEF_PLACE_LIMIT <= 10
    assert brief_places_payload(TAGS, 'Brooklyn')['limit'] == BRIEF_PLACE_LIMIT


def test_held_bridge_is_retained_without_unsupported_direction_edges(monkeypatch, store, recommend_places):
    monkeypatch.setenv('CULTUREFORGE_BRIDGE_DOMAINS', 'artist,movie,brand')
    project = _held_brief(store, recommend_places)
    for domain in ('artist', 'movie', 'brand'):
        store.put(canonical_key('recommend', bridge_payload(TAGS, domain)), _bridge_rows(domain))

    response = QlooHarnessProvider().generate(project, allow_naming=False)

    bridged = [item for item in response.evidence if item.kind == 'crossdomain']
    assert len(bridged) == 15  # five a domain, in Qloo's order
    assert {item.entityType for item in bridged} == {'urn:entity:artist', 'urn:entity:movie', 'urn:entity:brand'}
    assert all(item.location is None for item in bridged)
    trace_ids = {event.id for event in response.trace}
    assert all(item.traceId in trace_ids for item in bridged)
    assert response.delivery.transportRequests == 0
    assert response.concepts
    bridged_ids = {item.id for item in bridged}
    for concept in response.concepts:
        cross = [d for d in concept.decisions if d.field == 'cultural cross-references']
        assert not cross
        assert all(not (set(d.evidenceIds) & bridged_ids) for d in concept.decisions)
    assert all(item.relevance['relationship'] == 'indirect' for item in bridged)
    # Places stay places: a bridged artist is never a direction's anchor.
    places = {item.id for item in response.evidence if item.kind == 'entity'}
    for concept in response.concepts:
        anchoring = [d for d in concept.decisions if d.field == 'offering'][0]
        assert set(anchoring.evidenceIds) <= places
    assert 'cross-references' in response.notice


def test_one_failed_domain_is_stated_and_the_rest_still_count(monkeypatch, store, recommend_places):
    monkeypatch.setenv('CULTUREFORGE_BRIDGE_DOMAINS', 'artist,brand')
    project = _held_brief(store, recommend_places)
    store.put(canonical_key('recommend', bridge_payload(TAGS, 'artist')), _bridge_rows('artist'))
    provider = QlooHarnessProvider()

    def rate_limited(operation, payload):
        raise QlooHarnessError('Qloo rate limited this key.', code='RATE_LIMITED', retryable=True)
    monkeypatch.setattr(provider, '_run_workflow', rate_limited)

    response = provider.generate(project, allow_naming=False)
    brand = next(event for event in response.trace if event.step == 'bridge-brand')
    assert brand.status == 'error' and 'rate limited' in brand.detail
    assert response.concepts
    assert {item.entityType for item in response.evidence if item.kind == 'crossdomain'} == {'urn:entity:artist'}


def test_a_rebuild_reads_the_bridge_and_never_fetches_it(monkeypatch, store, recommend_places):
    monkeypatch.setenv('CULTUREFORGE_BRIDGE_DOMAINS', 'artist,movie')
    project = _held_brief(store, recommend_places)
    store.put(canonical_key('recommend', bridge_payload(TAGS, 'artist')), _bridge_rows('artist'))
    provider = QlooHarnessProvider()
    monkeypatch.setattr(provider, '_run_workflow',
                        lambda *_args: pytest.fail('a rebuild must not call Qloo'))

    response = provider.generate(project, allow_naming=False, bridge_held_only=True)
    movie = next(event for event in response.trace if event.step == 'bridge-movie')
    assert movie.status == 'skipped'
    assert any(item.kind == 'crossdomain' for item in response.evidence)


def test_with_the_bridge_off_nothing_changes(store, recommend_places):
    response = QlooHarnessProvider().generate(_held_brief(store, recommend_places), allow_naming=False)
    assert not any(item.kind == 'crossdomain' for item in response.evidence)
    assert not any(d.field == 'cultural cross-references' for c in response.concepts for d in c.decisions)


def test_a_brief_is_held_only_when_its_bridge_domains_are_too(monkeypatch, store, recommend_places):
    monkeypatch.setenv('CULTUREFORGE_BRIDGE_DOMAINS', 'artist,brand')
    project = _held_brief(store, recommend_places)
    assert examples.held(project.model_dump()) is False
    store.put(canonical_key('recommend', bridge_payload(TAGS, 'artist')), _bridge_rows('artist'))
    assert examples.held(project.model_dump()) is False
    store.put(canonical_key('recommend', bridge_payload(TAGS, 'brand')), _bridge_rows('brand'))
    assert examples.held(project.model_dump()) is True
