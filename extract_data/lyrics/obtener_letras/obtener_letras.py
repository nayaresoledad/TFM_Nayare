import os
import time
import requests
from datetime import datetime

from common.config import config
from common.logging import setup_logging
from common.db import DatabaseManager
from common.progress import ProgressManager, ProgressType
from common.retry import retry
from genius import buscar_cancion
from rasca_genio import obtener_letra

logger = setup_logging()
db_manager = DatabaseManager(config.database_url, min_conn=1, max_conn=5)
progress_manager = ProgressManager(db_manager)


@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def obtener_mbid_en_musicbrainz(artista, cancion):
    search_url = f'https://musicbrainz.org/ws/2/recording/'
    params = {'query': f'artist:{artista} recording:{cancion}', 'fmt': 'json'}
    r = requests.get(search_url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if 'recordings' in data and data['recordings']:
        return data['recordings'][0].get('id')
    return None


def obtener_artistas_y_canciones():
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id_artista, artista, cancion FROM canciones ORDER BY id_artista, id')
        rows = cur.fetchall()
        cur.close()
        return rows


def obtener_progreso():
    p = progress_manager.get_progress(ProgressType.LETRAS)
    # Devolver tupla (id_artista, id_cancion) si existe
    return (p.get('last_processed_id'), 0) if p.get('last_processed_id') else None


def guardar_progreso(id_artista, id_cancion):
    # Guardamos last_processed_id como id_artista (simplificado)
    progress_manager.update_progress(ProgressType.LETRAS, id_artista, last_processed_id=id_artista)


def guardar_en_db(datos):
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS canciones_resultado (
                id SERIAL PRIMARY KEY,
                id_artista INTEGER NOT NULL,
                artista TEXT NOT NULL,
                cancion TEXT NOT NULL,
                id_cancion INTEGER NOT NULL,
                mbid TEXT,
                letra TEXT,
                fecha_guardado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cur.executemany('''
            INSERT INTO canciones_resultado (id_artista, artista, cancion, id_cancion, mbid, letra, fecha_guardado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', datos)
        cur.close()


def obtener_datos_y_guardar():
    progreso = obtener_progreso()
    last_artista_id = progreso[0] if progreso else None

    if last_artista_id:
        logger.info(f"Continuando desde el artista ID: {last_artista_id}")
    else:
        logger.info("Comenzando desde el inicio.")

    artistas_canciones = obtener_artistas_y_canciones()
    datos = []

    for artista_id, artista, cancion in artistas_canciones:
        if last_artista_id and artista_id < last_artista_id:
            continue

        logger.info(f'Buscando: {artista} - {cancion}')
        try:
            song_url, song_id = buscar_cancion(artista, cancion)
        except Exception:
            logger.exception(f"Error buscando canción en Genius para {artista} - {cancion}")
            song_url, song_id = (None, None)

        if song_url and song_id:
            try:
                letra = obtener_letra(song_url)
            except Exception:
                logger.exception(f"Error obteniendo letra para {song_url}")
                letra = None

            try:
                mbid = obtener_mbid_en_musicbrainz(artista, cancion)
            except Exception:
                logger.exception(f"Error obteniendo MBID para {artista} - {cancion}")
                mbid = None

                datos.append([artista_id, artista, cancion, song_id, mbid, letra, fecha_guardado])

        if datos:
            guardar_en_db(datos)
            logger.info(f'Guardados {len(datos)} resultados en la base de datos.')
            datos.clear()

        guardar_progreso(artista_id, 0)


if __name__ == '__main__':
    obtener_datos_y_guardar()

