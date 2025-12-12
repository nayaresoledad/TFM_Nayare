import pytest
from unittest.mock import patch

from extract_data.lyrics.mcp import server


def test_fetch_lyrics_lyrics_ovh_success(monkeypatch):
    # Mock requests.get for lyrics.ovh
    class MockResp:
        ok = True

        def json(self):
            return {'lyrics': 'La la la'}

    monkeypatch.setattr('extract_data.lyrics.mcp.server.requests.get', lambda *a, **k: MockResp())

    lyrics, song_id, source = server.fetch_lyrics_internet('Artist', 'Song')
    assert lyrics == 'La la la'
    assert song_id is None
    assert source == 'lyrics.ovh'


def test_fetch_lyrics_fallback_to_genius(monkeypatch):
    # First call to lyrics.ovh fails
    def fake_get(url, timeout=8):
        class R:
            ok = False

            def json(self):
                return {}

        return R()

    monkeypatch.setattr('extract_data.lyrics.mcp.server.requests.get', fake_get)

    # Mock buscar_cancion to return a URL and id
    monkeypatch.setattr('extract_data.lyrics.mcp.server.buscar_cancion', lambda a, c: ('http://song', 123))
    # Mock scrape_letra to return lyrics
    monkeypatch.setattr('extract_data.lyrics.mcp.server.scrape_letra', lambda url: 'Scraped lyrics')

    lyrics, song_id, source = server.fetch_lyrics_internet('Artist', 'Song')
    assert lyrics == 'Scraped lyrics'
    assert song_id == 123
    assert source == 'genius'


def test_fetch_lyrics_not_found(monkeypatch):
    monkeypatch.setattr('extract_data.lyrics.mcp.server.requests.get', lambda *a, **k: (_ for _ in ()).throw(Exception('fail')))
    monkeypatch.setattr('extract_data.lyrics.mcp.server.buscar_cancion', lambda a, c: (None, None))

    lyrics, song_id, source = server.fetch_lyrics_internet('Artist', 'Song')
    assert lyrics is None
    assert song_id is None
    assert source is None
