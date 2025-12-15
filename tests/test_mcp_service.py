import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from extract_data.lyrics.mcp import server


def test_fetch_lyrics_with_playwright_mocked(monkeypatch):
    """Mock Playwright async functions to test fetch_lyrics_internet fallback logic."""
    # Mock _fetch_lyrics_ovh_with_playwright to return None (simulating no lyrics found)
    async def mock_ovh_fail(artista, cancion):
        return None

    # Mock _fetch_lyrics_genius_with_playwright to return lyrics
    async def mock_genius_success(artista, cancion):
        return "Genius lyrics found"

    monkeypatch.setattr('extract_data.lyrics.mcp.server._fetch_lyrics_ovh_with_playwright', mock_ovh_fail)
    monkeypatch.setattr('extract_data.lyrics.mcp.server._fetch_lyrics_genius_with_playwright', mock_genius_success)

    lyrics, song_id, source = server.fetch_lyrics_internet('Artist', 'Song')
    assert lyrics == "Genius lyrics found"
    assert source == 'genius'


def test_fetch_lyrics_ovh_success(monkeypatch):
    """Test that fetch_lyrics_internet returns lyrics.ovh result if successful."""
    async def mock_ovh_success(artista, cancion):
        return "OVH lyrics"

    async def mock_genius(artista, cancion):
        return None

    monkeypatch.setattr('extract_data.lyrics.mcp.server._fetch_lyrics_ovh_with_playwright', mock_ovh_success)
    monkeypatch.setattr('extract_data.lyrics.mcp.server._fetch_lyrics_genius_with_playwright', mock_genius)

    lyrics, song_id, source = server.fetch_lyrics_internet('Artist', 'Song')
    assert lyrics == "OVH lyrics"
    assert song_id is None
    assert source == 'lyrics.ovh'


def test_fetch_lyrics_not_found(monkeypatch):
    """Test that fetch_lyrics_internet returns None when both sources fail."""
    async def mock_fail(artista, cancion):
        return None

    monkeypatch.setattr('extract_data.lyrics.mcp.server._fetch_lyrics_ovh_with_playwright', mock_fail)
    monkeypatch.setattr('extract_data.lyrics.mcp.server._fetch_lyrics_genius_with_playwright', mock_fail)

    lyrics, song_id, source = server.fetch_lyrics_internet('Artist', 'Song')
    assert lyrics is None
    assert song_id is None
    assert source is None
