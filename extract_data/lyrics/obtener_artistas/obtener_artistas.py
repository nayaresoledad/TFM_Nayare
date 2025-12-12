import requests
import time
import os
from datetime import datetime

from common.config import config
from common.logging import setup_logging
from common.db import DatabaseManager
from common.progress import ProgressManager, ProgressType
from common.retry import retry

logger = setup_logging()
db_manager = DatabaseManager(config.database_url, min_conn=1, max_conn=5)
progress_manager = ProgressManager(db_manager)

QUERY_BUSQUEDA = os.getenv('QUERY_BUSQUEDA', 'a')


def crear_tabla_artistas():
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS artistas (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE,
                fecha_guardado TIMESTAMP,
                query TEXT
            )
        """)
        cur.close()


def artista_existe(nombre: str) -> bool:
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM artistas WHERE nombre = %s", (nombre,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists


def guardar_artista_db(nombre: str, query: str):
    if not artista_existe(nombre):
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                        (nombre, fecha_actual, query))
            cur.close()


def obtener_offset():
    p = progress_manager.get_progress(ProgressType.ARTISTAS)
    return p.get('current_offset', 0)


def guardar_offset(offset: int):
    progress_manager.update_progress(ProgressType.ARTISTAS, offset)


@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def buscar_artistas_musicbrainz(query: str, offset: int, limit: int = 100):
    url = 'https://musicbrainz.org/ws/2/artist/'
    params = {'query': query, 'limit': limit, 'offset': offset, 'fmt': 'json'}
    headers = {'User-Agent': 'Lyrics/1.0 (contact@example.com)'}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        return [a.get('name') for a in data.get('artists', [])]
    except Exception as e:
        logger.warning(f"Error fetching artists: {e}")
        return []


def obtener_artistas_musicbrainz():
    crear_tabla_artistas()
    offset = obtener_offset()
    limit = 100

    logger.info(f"Comenzando búsqueda de artistas con query='{QUERY_BUSQUEDA}' desde offset {offset}")

    while True:
        artistas = buscar_artistas_musicbrainz(QUERY_BUSQUEDA, offset, limit)

        if not artistas:
            logger.info("No se encontraron más artistas o hubo un error.")
            break

        nuevos = 0
        for nombre in artistas:
            try:
                if not artista_existe(nombre):
                    guardar_artista_db(nombre, QUERY_BUSQUEDA)
                    nuevos += 1
            except Exception:
                logger.exception(f"Error guardando artista: {nombre}")

        logger.info(f"Se guardaron {nuevos} artistas nuevos.")

        offset += len(artistas)
        guardar_offset(offset)

        if len(artistas) < limit:
            break

        time.sleep(1)

    logger.info("Proceso de obtención de artistas finalizado.")


if __name__ == '__main__':
    obtener_artistas_musicbrainz()

