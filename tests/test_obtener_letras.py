import importlib


def test_obtener_mbid_en_musicbrainz(monkeypatch):
    # Ensure required env vars for common.config are present during import
    monkeypatch.setenv('POSTGRES_USER', 'test')
    monkeypatch.setenv('POSTGRES_PASSWORD', 'test')
    monkeypatch.setenv('POSTGRES_DB', 'testdb')
    mod = importlib.import_module('extract_data.lyrics.obtener_letras.obtener_letras')

    class MockResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {'recordings': [{'id': 'mbid-123'}]}

    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockResp())
    mbid = mod.obtener_mbid_en_musicbrainz('Artist', 'Song')
    assert mbid == 'mbid-123'
