import requests
import os
import re
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime

from common.retry import retry
from common.config import config
from common.logging import setup_logging
from common.db import DatabaseManager
from common.progress import ProgressManager, ProgressType
from .genius import buscar_cancion

logger = setup_logging()
db_manager = DatabaseManager(config.database_url, min_conn=1, max_conn=5)
progress_manager = ProgressManager(db_manager)


def crear_tabla_letras():
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
                fecha_guardado TEXT
            )
        """)
        cur.close()


def cancion_existe(id_cancion):
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM letras WHERE id_cancion = %s", (id_cancion,))
        existe = cur.fetchone() is not None
        cur.close()
        return existe


def guardar_letra(id_artista, id_cancion, artista, cancion, letra):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO letras (id_artista, id_cancion, artista, cancion, letra, fecha_guardado) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_artista, id_cancion, artista, cancion, letra, fecha_actual))
        cur.close()


def leer_offset():
    p = progress_manager.get_progress(ProgressType.LETRAS)
    return p.get('current_offset', 0)


def guardar_offset(offset):
    progress_manager.update_progress(ProgressType.LETRAS, offset)


@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def _fetch_song_page(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TFM/1.0; +https://example.com)"}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 429:
        raise requests.exceptions.RequestException("429 Too Many Requests")
    resp.raise_for_status()
    return resp.text


def obtener_letra(song_url):
    try:
        page_text = _fetch_song_page(song_url)
    except Exception:
        logger.warning(f"Error fetching {song_url}; returning no lyric after retries.")
        return "no lyric"

    html = BeautifulSoup(page_text, 'html.parser')
    lyrics_divs = html.find_all('div', attrs={'data-lyrics-container': 'true'})
    if not lyrics_divs:
        logger.warning(f"No lyrics found for {song_url}")
        return "no lyric"

    lyrics = '\n'.join([div.get_text(separator="\n") for div in lyrics_divs])
    lyrics = re.sub(r'[\(\[].*?[\)\]]', '', lyrics)
    lyrics = os.linesep.join([s for s in lyrics.splitlines() if s])
    return lyrics


def obtener_letras():
    crear_tabla_letras()
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ID_ARTISTA, ID, artista, cancion FROM canciones")
        canciones = cur.fetchall()
        cur.close()

    total_canciones = len(canciones)
    offset = leer_offset()

    logger.info(f"🎵 Canciones encontradas: {total_canciones}")
    logger.info(f"🔄 Continuando desde la canción {offset + 1}...")

    for i, (id_artista, id_cancion, artista, cancion) in enumerate(canciones[offset:], start=offset):
        if cancion_existe(id_cancion):
            logger.debug(f"{artista} - {cancion} (ID {id_cancion}) ya existe. Saltando...")
            continue

        logger.info(f"🔍 Buscando {artista} - {cancion}...")
        try:
            song_url, _ = buscar_cancion(artista, cancion)
        except Exception:
            logger.exception("Error buscando canción en Genius")
            song_url = None

        if song_url:
            letra = obtener_letra(song_url)
            guardar_letra(id_artista, id_cancion, artista, cancion, letra)
            logger.info(f"✅ Letra guardada ({len(letra)} caracteres).")
        else:
            logger.warning(f"❌ No se encontró la canción en Genius: {artista} - {cancion}")
            guardar_letra(id_artista, id_cancion, artista, cancion, "no lyric")

        guardar_offset(i + 1)
        sleep_time = random.randint(2, 6)
        logger.debug(f"⏳ Pausando {sleep_time}s para evitar bloqueos...")
        time.sleep(sleep_time)

    logger.info("🎉 Proceso terminado. Todas las letras han sido obtenidas.")


if __name__ == '__main__':
    obtener_letras()
