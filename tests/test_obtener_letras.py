import importlib


def test_obtener_mbid_en_musicbrainz(monkeypatch):
    """Test obtener_mbid_en_musicbrainz with mocked requests."""
    import pytest
    from extract_data.lyrics.obtener_letras.obtener_letras import obtener_mbid_en_musicbrainz

    class MockResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {'recordings': [{'id': 'mbid-123'}]}

    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockResp())
    mbid = obtener_mbid_en_musicbrainz('Artist', 'Song')
    assert mbid == 'mbid-123'
