"""The client PDF: what it contains, what it states, and that it costs nothing."""
from __future__ import annotations

from fastapi.testclient import TestClient

import backend.main as main
from backend import examples
from backend.evidence_store import canonical_key
from backend.models import ProjectRequest
from backend.providers import QlooHarnessProvider, brief_places_payload, brief_tags_payload, where_popular_payload
from backend.report_pdf import build_pdf, plain

TAGS = ['urn:tag:customer_segment:qloo:gen_z_foodies', 'urn:tag:interests:qloo:food_design']


def _answer(store, recommend_places):
    project = ProjectRequest(**examples.briefs()[0]['project'])
    store.put(canonical_key('find_tags', brief_tags_payload(project.businessType, project.audience)),
              {'operation': 'find_tags', 'status': 'ok', 'results': [{'id': tag, 'name': tag.split(':')[-1]} for tag in TAGS]})
    store.put(canonical_key('recommend', brief_places_payload(TAGS, project.location)), recommend_places)
    return QlooHarnessProvider().generate(project, allow_naming=False)


def _text(pdf: bytes) -> str:
    """The text runs of an uncompressed PDF, joined, so wrapped lines read as one."""
    import re
    runs = re.findall(rb'\((.*?)(?<!\\)\) Tj', pdf)
    text = ' '.join(run.decode('latin-1').replace('\\(', '(').replace('\\)', ')') for run in runs)
    return ' '.join(text.split())


def test_the_pdf_carries_the_brief_directions_evidence_ids_and_limits(store, recommend_places):
    response = _answer(store, recommend_places)
    challenge = {'policyVersion': 'anchor-fit-4', 'whatThisIs': 'A policy check.',
                 'profile': {'demographic': 'gen z', 'source': 'named', 'location': 'Brooklyn, New York'},
                 'directions': [{'directionId': response.concepts[0].id, 'verdict': 'contested',
                                 'reason': 'Ranks in the bottom third.', 'claim': 'c', 'falsifier': 'f',
                                 'index': {'confidence': 'low', 'rankCheck': 'fail', 'tagCheck': 'pass',
                                           'sampleSize': 5, 'confidenceReason': 'Only five places were ranked.'}}]}
    pdf = build_pdf(response, challenge, compress=False)
    assert pdf.startswith(b'%PDF')
    text = _text(pdf)
    for needle in ('Audience seeds', 'Directions', 'Evidence', 'Limitations and non-claims',
                   response.concepts[0].name, 'contested', 'confidence low', 'anchor-fit-4',
                   TAGS[0], recommend_places['results'][0]['entity_id'], 'not evidence of demand'):
        assert plain(needle).lower() in text.lower(), needle
    assert 'Not included: interest cells' in text


def test_held_interest_cells_are_drawn_and_said_to_be_cells_not_pins(store, recommend_places):
    response = _answer(store, recommend_places)
    places = {item.id: item.entityId for item in response.evidence if item.kind == 'entity'}
    anchor_id = next(places[eid] for eid in response.concepts[0].evidenceIds if eid in places)
    store.put(canonical_key('where_popular', where_popular_payload(anchor_id, response.project.location, None, 20)),
              {'results': [{'location': {'latitude': 40.70 + n / 100, 'longitude': -73.99 + n / 100},
                            'query': {'affinity': 0.9}} for n in range(6)]})
    text = _text(build_pdf(response, None, compress=False))
    assert '6 cells' in text and 'not venue pins' in text
    assert 'evidence test was not run' in text


def test_text_outside_latin_1_is_shown_not_dropped():
    assert plain('Café “Ōmori” – 東京') == 'Café "?mori" - ??'


def test_the_route_returns_a_pdf_and_rejects_a_malformed_body(store, recommend_places):
    response = _answer(store, recommend_places)
    client = TestClient(main.app)
    ok = client.post('/api/report/pdf', json={'result': response.model_dump()})
    assert ok.status_code == 200 and ok.headers['content-type'] == 'application/pdf'
    assert ok.content.startswith(b'%PDF') and 'attachment' in ok.headers['content-disposition']
    assert client.post('/api/report/pdf', json={'result': {'projectId': 'x'}}).status_code == 422


# ---------------------------------------------------------------------------
# Non-Latin text: printed with a Unicode font when there is one, stated when not
# ---------------------------------------------------------------------------

def _tokyo(store, recommend_places):
    response = _answer(store, recommend_places)
    place = next(item for item in response.evidence if item.kind == 'entity')
    return response.model_copy(update={'evidence': [
        item.model_copy(update={'label': '資生堂パーラー 銀座本店ショップ'}) if item.id == place.id else item
        for item in response.evidence]})


def test_without_a_unicode_font_japanese_prints_as_question_marks_and_the_pdf_says_so(store, recommend_places, monkeypatch):
    from backend import report_pdf

    monkeypatch.setattr(report_pdf, 'unicode_font_path', lambda: None)
    text = _text(build_pdf(_tokyo(store, recommend_places), None, compress=False))
    assert '資' not in text and '?????' in text
    assert 'No Unicode font was available' in text


def test_with_a_unicode_font_the_pdf_embeds_it_and_drops_the_apology(store, recommend_places, monkeypatch):
    import pytest

    from backend import report_pdf

    monkeypatch.delenv('CULTUREFORGE_PDF_FONT', raising=False)
    if not report_pdf.unicode_font_path():
        pytest.skip('no Unicode font on this machine; the Dockerfile installs fonts-droid-fallback')
    pdf = build_pdf(_tokyo(store, recommend_places), None, compress=False)
    assert b'CIDFontType2' in pdf or b'FontFile2' in pdf
    assert b'No Unicode font was available' not in pdf


def test_a_latin_only_brief_keeps_the_built_in_font(store, recommend_places):
    pdf = build_pdf(_answer(store, recommend_places), None, compress=False)
    assert b'CIDFontType2' not in pdf and b'FontFile2' not in pdf
