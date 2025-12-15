import os
import time
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from common.retry import retry

from common.config import config
from common.logging import setup_logging
from common.db import DatabaseManager

logger = setup_logging()
db_manager = DatabaseManager(config.database_url, min_conn=1, max_conn=5)
logger.info('Base de Postgres (pool) configurada')

# Crear columna vector_migrado si no existe
pg_cursor.execute("""
    ALTER TABLE lyrics_database
    ADD COLUMN IF NOT EXISTS vector_migrado BOOLEAN DEFAULT FALSE;
""")
pg_conn.commit()

# Conectar a Qdrant
logger.info('Conectando a Qdrant')
qdrant = QdrantClient(host=os.getenv('QDRANT_HOST', 'localhost'), port=int(os.getenv('QDRANT_PORT', 6333)), timeout=60.0)
logger.info('Qdrant conectado')


@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def upsert_points(qdrant_client, points):
    # Wrapper to allow retrying transient errors from Qdrant
    qdrant_client.upsert(collection_name="TFM", points=points)

# Leer un ejemplo para obtener dimensiones
with db_manager.get_connection() as conn:
    cur = conn.cursor()
    logger.info('Realizando consulta de ejemplo')
    cur.execute("SELECT track_vector, letra_vec FROM lyrics_database WHERE track_vector IS NOT NULL AND letra_vec IS NOT NULL AND vector_migrado = FALSE LIMIT 1")
    example = cur.fetchone()
    cur.close()

if not example:
    logger.info("No hay datos para migrar.")
    exit()
logger.info('Resultados recuperados')

# Obtener dimensiones automáticamente
dim_audio = len(np.mean(example[0], axis=0)) if isinstance(example[0], list) and len(example[0])>0 else len(example[0])
dim_lyrics = len(example[1])

# Crear colección con vectores múltiples
logger.info('Creando colección...')
if not qdrant.collection_exists("TFM"):
    qdrant.create_collection(
        collection_name="TFM",
        vectors_config={
            "track_vector": VectorParams(size=dim_audio, distance=Distance.COSINE),
            "lyrics_vector": VectorParams(size=dim_lyrics, distance=Distance.COSINE),
        }
    )
else:
    logger.info("✅ La colección 'TFM' ya existe.")

# Bucle por lotes más grande
batch_size = int(os.getenv('MIGRATE_BATCH_SIZE', '100'))
while True:
    logger.info("Consultando lote...")
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, artista, cancion, letra, album, mbid, track_vector, letra_vec, link, bpm, initialkey, genre 
            FROM lyrics_database
            WHERE track_vector IS NOT NULL AND letra_vec IS NOT NULL AND vector_migrado = FALSE
            LIMIT %s;
        """, (batch_size,))
        rows = cur.fetchall()
        cur.close()

    if not rows:
        logger.info("✅ Todos los datos han sido migrados.")
        break

    points = []
    ids_to_update = []

    for row in rows:
        id_, artist, title, lyric, album, mbid, audio_vec, lyrics_vec, link, bpm, initialkey, genre = row
        try:
            mean_audio_vec = np.mean(audio_vec, axis=0).tolist() if isinstance(audio_vec, list) and isinstance(audio_vec[0], list) else audio_vec
            metadata = {
                "artist": artist, "title": title,
                "lyric": lyric, "album": album, "mbid": mbid,
                "yotube_link": link, "bpm": bpm, "key": initialkey,
                "genre": genre
            }
            points.append(PointStruct(
                id=id_,
                vector={
                    "track_vector": mean_audio_vec,
                    "lyrics_vector": lyrics_vec,
                },
                payload=metadata
            ))
            ids_to_update.append(id_)
        except Exception as e:
            logger.error(f"❌ Error procesando id {id_}: {e}", exc_info=True)

    if points:
        logger.info(f"Subiendo {len(points)} puntos...")
        try:
            upsert_points(qdrant, points)
        except Exception:
            logger.exception("Error subiendo puntos a Qdrant, reintentando en el siguiente lote")
        with db_manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE lyrics_database SET vector_migrado = TRUE WHERE id = ANY(%s);",
                (ids_to_update,)
            )
            cur.close()
        logger.info("✅ Lote procesado.")

    time.sleep(0.5)  # Pequeña pausa

logger.info('Migración finalizada')
