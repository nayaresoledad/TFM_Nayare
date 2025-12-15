import os
import time
import requests
import psycopg2
import pytest


RUN_LIVE = os.getenv('RUN_LIVE_TESTS', '0')
if RUN_LIVE != '1':
    pytest.skip('Skipping live integration tests (set RUN_LIVE_TESTS=1 to enable)', allow_module_level=True)


MCP_URL = os.getenv('MCP_URL', 'http://mcp:8000/fetch_and_save')


def get_db_conn():
    host = os.getenv('POSTGRES_HOST', 'postgres')
    port = int(os.getenv('POSTGRES_PORT', '5432'))
    user = os.getenv('POSTGRES_USER', 'tfm_user')
    password = os.getenv('POSTGRES_PASSWORD', 'tfm_pass')
    db = os.getenv('POSTGRES_DB', 'tfm_db')
    return psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db)


def test_lyrics_ovh_api_available():
    # A quick smoke-test against lyrics.ovh for a well-known song
    url = 'https://api.lyrics.ovh/v1/Adele/Hello'
    r = requests.get(url, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert 'lyrics' in data and isinstance(data['lyrics'], str) and len(data['lyrics']) > 0


def test_mcp_fetch_and_save_and_db():
    # Call MCP to fetch and persist a known song; then verify DB contains it
    payload = {'id_artista': 9999, 'id_cancion': 9999, 'artista': 'Adele', 'cancion': 'Hello'}
    r = requests.post(MCP_URL, json=payload, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert 'letra' in body and body['letra']

    # Wait a moment for DB commit visibility
    time.sleep(1)

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT letra FROM letras WHERE artista ILIKE %s AND cancion ILIKE %s LIMIT 1", ('%Adele%', '%Hello%'))
    row = cur.fetchone()
    cur.close()
    conn.close()
    assert row is not None and row[0]

    # Cleanup inserted test row(s)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM letras WHERE id_artista = %s AND id_cancion = %s", (9999, 9999))
    conn.commit()
    cur.close()
    conn.close()
