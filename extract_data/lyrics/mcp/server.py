from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from common.config import config
from common.logging import setup_logging
from common.db import DatabaseManager
import requests
from extract_data.lyrics.obtener_letras.genius import buscar_cancion
from extract_data.lyrics.obtener_letras.rasca_genio import obtener_letra as scrape_letra

logger = setup_logging()
app = FastAPI(title="Lyrics MCP")

db_manager = DatabaseManager(config.database_url, min_conn=1, max_conn=5)


class FetchRequest(BaseModel):
    id_artista: Optional[int] = None
    id_cancion: Optional[int] = None
    artista: str
    cancion: str


from common.retry import retry


@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def fetch_lyrics_internet(artista: str, cancion: str):
    """Intentar obtener letra desde APIs públicas y scraping.
    Estrategia:
    1. lyrics.ovh API
    2. Genius -> obtener URL y scrape
    """
    # 1) lyrics.ovh
    try:
        url = f"https://api.lyrics.ovh/v1/{artista}/{cancion}"
        r = requests.get(url, timeout=8)
        if r.ok:
            data = r.json()
            lyrics = data.get('lyrics')
            if lyrics:
                return lyrics, None, 'lyrics.ovh'
    except Exception:
        logger.debug("lyrics.ovh request failed; trying Genius")

    # 2) Genius search + scrape
    try:
        song_url, song_id = buscar_cancion(artista, cancion)
        if song_url:
            lyrics = scrape_letra(song_url)
            return lyrics, song_id, 'genius'
    except Exception:
        logger.exception("Genius lookup/scrape failed")

    return None, None, None


@app.post("/fetch_and_save")
def fetch_and_save(req: FetchRequest):
    letra, song_id, source = fetch_lyrics_internet(req.artista, req.cancion)
    if not letra:
        raise HTTPException(status_code=404, detail="lyric not found on the internet")

    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS letras (
                id SERIAL PRIMARY KEY,
                id_artista INTEGER,
                id_cancion INTEGER,
                artista TEXT,
                cancion TEXT,
                letra TEXT,
                fecha_guardado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute(
            "INSERT INTO letras (id_artista, id_cancion, artista, cancion, letra) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (req.id_artista, req.id_cancion, req.artista, req.cancion, letra),
        )
        conn.commit()
        cur.close()

    logger.info(f"Letra encontrada (source={source}) y guardada para {req.artista} - {req.cancion}")
    return {"status": "saved", "letra": letra, "source": source, "id_cancion": song_id}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)
