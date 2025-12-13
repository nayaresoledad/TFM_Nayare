from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from common.config import config
from common.logging import setup_logging
from common.db import DatabaseManager
import asyncio
import random
import time
from playwright.async_api import async_playwright
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


async def _fetch_lyrics_ovh_with_playwright(artista: str, cancion: str) -> Optional[str]:
    """Intenta obtener letra desde lyrics.ovh usando Playwright (navegador real)."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            page = await browser.new_page()
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            await asyncio.sleep(random.uniform(1, 3))

            url = f"https://api.lyrics.ovh/v1/{artista}/{cancion}"
            response = await page.goto(url, wait_until='networkidle')
            
            if response and response.status == 200:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                body = await page.content()
                import json
                import re
                match = re.search(r'"lyrics"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', body)
                if match:
                    lyrics = match.group(1).replace('\\n', '\n')
                    await browser.close()
                    return lyrics
            await browser.close()
    except Exception as e:
        logger.debug(f"Playwright lyrics.ovh failed: {e}")
    return None


async def _fetch_lyrics_genius_with_playwright(artista: str, cancion: str) -> Optional[str]:
    """Intenta obtener letra desde Genius usando Playwright (navegador real)."""
    try:
        song_url, song_id = buscar_cancion(artista, cancion)
        if not song_url:
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            page = await browser.new_page()
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            await asyncio.sleep(random.uniform(2, 5))

            response = await page.goto(song_url, wait_until='networkidle')
            if response and response.status == 200:
                await asyncio.sleep(random.uniform(1, 2))
                body = await page.content()
                from bs4 import BeautifulSoup
                import re as re_module
                html = BeautifulSoup(body, 'html.parser')
                lyrics_divs = html.find_all('div', attrs={'data-lyrics-container': 'true'})
                if lyrics_divs:
                    lyrics = '\n'.join([div.get_text(separator="\n") for div in lyrics_divs])
                    lyrics = re_module.sub(r'[\(\[].*?[\)\]]', '', lyrics)
                    await browser.close()
                    return lyrics

            await browser.close()
    except Exception as e:
        logger.debug(f"Playwright Genius failed: {e}")
    return None


@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def fetch_lyrics_internet(artista: str, cancion: str):
    """Intentar obtener letra usando Playwright (navegador real, humano-like).
    Estrategia:
    1. lyrics.ovh via Playwright
    2. Genius -> búsqueda y scrape via Playwright
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # 1) lyrics.ovh con Playwright
        lyrics = loop.run_until_complete(_fetch_lyrics_ovh_with_playwright(artista, cancion))
        if lyrics:
            return lyrics, None, 'lyrics.ovh'

        # 2) Genius con Playwright
        lyrics = loop.run_until_complete(_fetch_lyrics_genius_with_playwright(artista, cancion))
        if lyrics:
            return lyrics, None, 'genius'
    except Exception:
        logger.exception(f"Playwright fetch failed for {artista} - {cancion}")
    finally:
        loop.close()

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


@app.post("/process_missing")
def process_missing(limit: int = 100, offset: int = 0):
    """Procesa canciones sin letra: busca en `canciones` filas que no tienen letra en `letras`,
    obtiene la letra desde internet y la guarda en `letras`.

    Parámetros:
    - limit: número máximo de canciones a procesar en esta llamada
    - offset: desplazamiento desde el inicio (para paginar)
    """
    results = {"processed": 0, "saved": 0, "failed": []}

    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        # Selecciona canciones que no tienen una letra guardada (letra non-null)
        cur.execute(
            """
            SELECT c.id_artista, c.id AS id_cancion, c.artista, c.cancion
            FROM canciones c
            LEFT JOIN letras l ON l.id_cancion = c.id AND l.letra IS NOT NULL
            WHERE l.id IS NULL
            ORDER BY c.id
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()

        for id_artista, id_cancion, artista, cancion in rows:
            results['processed'] += 1
            try:
                letra, song_id, source = fetch_lyrics_internet(artista, cancion)
                if letra:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS letras (
                            id SERIAL PRIMARY KEY,
                            id_artista INTEGER,
                            id_cancion INTEGER,
                            artista TEXT,
                            cancion TEXT,
                            letra TEXT,
                            fecha_guardado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                    )
                    cur.execute(
                        "INSERT INTO letras (id_artista, id_cancion, artista, cancion, letra) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (id_artista, id_cancion, artista, cancion, letra),
                    )
                    conn.commit()
                    results['saved'] += 1
                    logger.info(f"Saved lyric for {artista} - {cancion} (id={id_cancion}) from {source}")
                else:
                    results['failed'].append({"id_cancion": id_cancion, "reason": "not found"})
                    logger.warning(f"No lyric found for {artista} - {cancion}")
            except Exception as e:
                conn.rollback()
                results['failed'].append({"id_cancion": id_cancion, "reason": str(e)})
                logger.exception(f"Error processing {artista} - {cancion}: {e}")

        cur.close()

    return results


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)
