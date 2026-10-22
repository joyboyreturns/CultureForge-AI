"""The shipped pack makes the three prepared demos open from held evidence on a fresh store."""
import json

from backend import demo_pack, evidence_store, examples, geocode


def test_a_fresh_store_opens_each_demo_from_the_shipped_pack(monkeypatch, tmp_path):
    monkeypatch.setenv('CULTUREFORGE_GEOCODE_CACHE', str(tmp_path / 'g.json'))
    monkeypatch.setattr(evidence_store, '_store', evidence_store.EvidenceStore(tmp_path))
    result = demo_pack.seed()
    assert result['skipped'] == '' and result['evidence'] > 10 and result['geocodes'] > 5
    listing = {row['id']: row['held'] for row in examples.listing()}
    for demo in ('tokyo-morning-bakery', 'paris-ice-cream', 'melbourne-specialty-coffee'):
        assert listing[demo], demo


def test_pinned_entries_do_not_expire_and_keep_their_original_time(monkeypatch, tmp_path):
    store = evidence_store.EvidenceStore(tmp_path)
    assert store.seed('k', {'ok': 1}, 1_700_000_000.0)
    assert store.get('k', ttl_seconds=1) == {'ok': 1}
    assert store.stored_at('k') == 1_700_000_000.0
    assert not store.seed('k', {'ok': 2}, 1_800_000_000.0)


def test_a_pack_for_another_adapter_is_refused_not_guessed(monkeypatch, tmp_path):
    pack = tmp_path / 'p.json'
    pack.write_text(json.dumps({'adapterVersion': 'other', 'evidence': {'k': {'envelope': {}, 'storedAt': 1}}}))
    monkeypatch.setattr(demo_pack, 'PACK_FILE', pack)
    monkeypatch.setattr(evidence_store, '_store', evidence_store.EvidenceStore(tmp_path / 's'))
    out = demo_pack.seed()
    assert out['evidence'] == 0 and 'adapter' in out['skipped']
