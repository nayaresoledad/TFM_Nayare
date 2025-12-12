import requests
import os
import time
import random
from datetime import datetime

from common.config import config
from common.logging import setup_logging
from common.db import DatabaseManager
from common.progress import ProgressManager, ProgressType
from common.retry import retry

# Inicializaciones centrales
logger = setup_logging()
API_KEY_GENIUS = os.getenv("API_KEY_GENIUS")
db_manager = DatabaseManager(config.database_url, min_conn=1, max_conn=5)
progress_manager = ProgressManager(db_manager)


# ==========================
# Funciones de base de datos
# ==========================

def conectar_db():
    """Deprecated: usar `db_manager.get_connection()` en su lugar."""
    raise RuntimeError("Usar db_manager.get_connection() en lugar de conectar_db()")

def crear_tabla_canciones():
    """Crea la tabla de canciones si no existe (usa pool)."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS canciones (
                id SERIAL PRIMARY KEY,
                id_artista INTEGER REFERENCES artistas(id) ON DELETE CASCADE,
                artista TEXT,
                cancion TEXT,
                fecha_guardado TIMESTAMP,
                UNIQUE(id_artista, cancion)
            );
        """)
        cursor.close()

def cancion_existe(id_artista, cancion):
    """Verifica si una canción ya está guardada para evitar duplicados."""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM canciones WHERE id_artista = %s AND cancion = %s", (id_artista, cancion))
        existe = cursor.fetchone() is not None
        cursor.close()
        return existe

def guardar_cancion(id_artista, artista, cancion):
    """Guarda una canción en la base de datos usando el pool."""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s) ON CONFLICT (id_artista, cancion) DO NOTHING;", (id_artista, artista, cancion, fecha_actual))
        cursor.close()

# ==========================
# Funciones de offset
# ==========================

def leer_offset():
    """Obtiene el offset desde ProgressManager."""
    p = progress_manager.get_progress(ProgressType.CANCIONES)
    return p.get('current_offset', 0)

def guardar_offset(offset):
    """Guarda offset en ProgressManager (current_offset)."""
    progress_manager.update_progress(ProgressType.CANCIONES, offset)

# ==========================
# Función para obtener canciones de Genius
# ==========================

@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def buscar_canciones_de_artista(artista):
    """Busca canciones de un artista en Genius con manejo básico de rates.
    Retorna lista de títulos.
    """
    base_url = 'https://api.genius.com'
    headers = {'Authorization': f'Bearer {API_KEY_GENIUS}'}
    search_url = f'{base_url}/search'
    params = {'q': artista}

    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=30)
    except Exception as e:
        logger.warning(f"Error buscando en Genius para {artista}: {e}")
        return []

    if response.status_code == 429:  # Rate limit
        wait = random.randint(30, 60)
        logger.warning(f"Rate limited by Genius, esperando {wait}s")
        time.sleep(wait)
        return buscar_canciones_de_artista(artista)

    if not response.ok:
        logger.error(f"Error HTTP buscando {artista}: {response.status_code}")
        return []

    data = response.json()
    canciones = []
    for hit in data.get('response', {}).get('hits', []):
        song_info = hit.get('result')
        if song_info and song_info.get('title'):
            canciones.append(song_info['title'])

    return canciones

# ==========================
# Función principal
# ==========================

def obtener_canciones():
    crear_tabla_canciones()
    """Obtiene todas las canciones de los artistas en la base de datos.
    Utiliza pool, logging y progress manager.
    """
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM artistas ORDER BY id")
        artistas = cursor.fetchall()
        cursor.close()

    total_artistas = len(artistas)
    offset = leer_offset() or 0

    logger.info(f"🎤 Artistas encontrados: {total_artistas}")
    logger.info(f"🔄 Continuando desde el artista {offset + 1}...")

    for i, (id_artista, nombre_artista) in enumerate(artistas[offset:], start=offset):
        logger.info(f"🎵 Buscando canciones de {nombre_artista} (id={id_artista})...")

        canciones = buscar_canciones_de_artista(nombre_artista)

        if not canciones:
            logger.warning(f"❌ No se encontraron canciones para {nombre_artista}.")
            # actualizar offset para siguiente artista
            guardar_offset(i + 1)
            continue

        for j, cancion in enumerate(canciones, start=0):
            if cancion_existe(id_artista, cancion):
                logger.debug(f"✅ {cancion} ya está en la base de datos. Saltando...")
                continue

            logger.info(f"🎼 Guardando {nombre_artista} - {cancion}...")
            try:
                guardar_cancion(id_artista, nombre_artista, cancion)
            except Exception as e:
                logger.error(f"Error guardando canción {cancion}: {e}", exc_info=True)
                continue

            # Guardar el progreso (index global por artista)
            guardar_offset(i)
            sleep_time = random.randint(1, 3)
            logger.debug(f"⏳ Pausando {sleep_time}s para evitar bloqueos...")
            time.sleep(sleep_time)

        # Avanzar al siguiente artista
        guardar_offset(i + 1)

        # Espera corta entre artistas para reducir chance de bloqueos
        sleep_time = random.randint(2, 5)
        logger.debug(f"⏸️ Pausando {sleep_time}s antes del próximo artista...")
        time.sleep(sleep_time)

    logger.info("🎉 Proceso terminado. Todas las canciones han sido obtenidas.")

# ==========================
# Ejecución del programa
# ==========================
if __name__ == '__main__':
    obtener_canciones()
