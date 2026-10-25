"""Geocoding decisions on synthetic Nominatim rows; no network."""
from backend import geocode
from backend.geocode import judge

ROW = {'lat': '35.6595', 'lon': '139.7005', 'display_name': 'Shibuya, Tokyo, Japan', 'address': {'city': 'Tokyo'}}


def test_a_match_inside_the_city_is_plotted_with_its_precision_stated():
    out = judge([ROW], 'Tokyo, Japan')
    assert out['status'] == 'plotted' and out['lat'] == 35.6595
    assert 'not a surveyed venue point' in out['precision']


def test_no_match_other_city_and_ambiguity_are_not_plotted():
    assert judge([], 'Tokyo')['status'] == 'not_found'
    assert judge([{**ROW, 'display_name': 'Osaka, Japan', 'address': {'city': 'Osaka'}}], 'Tokyo')['status'] == 'outside_city'
    far = {**ROW, 'lat': '35.70', 'lon': '139.80'}
    assert judge([ROW, far], 'Tokyo')['status'] == 'ambiguous'
    assert judge([{'display_name': 'Tokyo'}], 'Tokyo')['status'] == 'not_found'


def test_missing_address_and_disabled_geocoder_never_guess(monkeypatch, tmp_path):
    monkeypatch.setenv('CULTUREFORGE_GEOCODE_CACHE', str(tmp_path / 'g.json'))
    monkeypatch.setenv('GEOCODING_ENABLED', 'false')
    out = geocode.geocode_venues([{'id': 'a', 'address': '', 'city': 'Tokyo'}, {'id': 'b', 'address': '1 Main', 'city': 'Tokyo'}])
    assert [r['status'] for r in out] == ['no_address', 'unavailable']


def test_successes_are_cached_and_transport_failures_are_not(monkeypatch, tmp_path):
    monkeypatch.setenv('CULTUREFORGE_GEOCODE_CACHE', str(tmp_path / 'g.json'))
    monkeypatch.setenv('GEOCODING_ENABLED', 'true')
    calls = []
    monkeypatch.setattr(geocode, '_fetch', lambda address: calls.append(address) or [ROW])
    venue = [{'id': 'a', 'address': '1 Main', 'city': 'Tokyo'}]
    assert geocode.geocode_venues(venue)[0]['cached'] is False
    assert geocode.geocode_venues(venue)[0]['cached'] is True and len(calls) == 1
    monkeypatch.setattr(geocode, '_fetch', lambda address: None)
    fail = geocode.geocode_venues([{'id': 'b', 'address': '2 Main', 'city': 'Tokyo'}])
    assert fail[0]['status'] == 'unavailable'
    assert '2 main|tokyo' not in (tmp_path / 'g.json').read_text()


def test_endpoint_is_typed(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)
    assert client.post('/api/geo/venues', json={'venues': 'x'}).status_code == 422
    monkeypatch.setattr(geocode, 'geocode_venues', lambda venues: [{'id': v['id'], 'status': 'no_address'} for v in venues])
    assert client.post('/api/geo/venues', json={'venues': [{'id': 'a'}]}).json()['results'][0]['status'] == 'no_address'


def test_accents_and_building_names_do_not_defeat_matching_or_fake_precision():
    assert judge([{**ROW, 'display_name': 'Shibuya, Tōkyō, Japan', 'address': {}, 'place_rank': 30}], 'Tokyo')['status'] == 'plotted'
    assert judge([{**ROW, 'place_rank': 16}], 'Tokyo')['status'] == 'area_only'
    assert geocode.clean('東京ガーデンテラス 1f 1-3 kioicho chiyoda city, tokyo 102-0094 japan') == '1-3 kioicho chiyoda city, tokyo 102-0094 japan'


def test_name_match_needs_name_city_and_point_precision():
    row = {**ROW, 'name': 'Sawamura Bakery', 'place_rank': 30}
    assert geocode.name_match([row], 'Sawamura Bakery & Restaurant', 'Tokyo')['status'] == 'plotted'
    assert geocode.name_match([{**row, 'name': 'Other Hotel'}], 'Sawamura Bakery', 'Tokyo') is None
    assert geocode.name_match([{**row, 'display_name': 'Osaka', 'address': {}}], 'Sawamura Bakery', 'Tokyo') is None
    assert geocode.name_match([{**row, 'place_rank': 16}], 'Sawamura Bakery', 'Tokyo') is None


def test_a_one_word_overlap_is_not_a_name_match():
    """Regression: "No.4" (Chiyoda) was pinned onto The Little BAKERY (Shibuya) in the shipped Tokyo demo."""
    row = {'lat': '35.6700', 'lon': '139.7060', 'display_name': 'No Bakery, Shibuya, Tokyo, Japan',
           'name': 'No Bakery', 'place_rank': 30, 'address': {'city': 'Tokyo'}}
    assert geocode.name_match([row], 'No.4', 'Tokyo') is None
    assert geocode.name_match([{**row, 'name': 'The Little BAKERY Tokyo'}], 'No.4', 'Tokyo') is None
    # Two shared words, or the same words, still match.
    assert geocode.name_match([{**row, 'name': 'Garden House Crafts'}], 'GARDEN HOUSE CRAFTS DAIKANYAMA', 'Tokyo')['status'] == 'plotted'
    assert geocode.name_match([{**row, 'name': 'Path'}], 'PATH', 'Tokyo')['status'] == 'plotted'
