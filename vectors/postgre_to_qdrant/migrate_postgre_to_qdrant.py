import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, CollectionStatus
import numpy as np
import time
import os

# Conectar a PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
pg_conn = psycopg2.connect(DATABASE_URL)
pg_cursor = pg_conn.cursor()
print('Base de Postgres conectada')

# Crear columna vector_migrado si no existe
pg_cursor.execute("""
    ALTER TABLE lyrics_database
    ADD COLUMN IF NOT EXISTS vector_migrado BOOLEAN DEFAULT FALSE;
""")
pg_conn.commit()

# Conectar a Qdrant
print('Conectando a Qdrant')
qdrant = QdrantClient(host="localhost", port=6333, timeout=60.0)
print('Qdrant conectado')

# Leer datos de PostgreSQL
print('Realizando consulta')
pg_cursor.execute("SELECT track_vector, letra_vec FROM lyrics_database WHERE track_vector IS NOT NULL AND letra_vec IS NOT NULL AND vector_migrado = FALSE LIMIT 1")
example = pg_cursor.fetchone()
if not example:
    print("No hay datos para migrar.")
    exit()
print('Resultados recuperados')

# Obtener dimensiones automáticamente
dim_audio = len(np.mean(example[0], axis=0))
dim_lyrics = len(example[1])

# Crear colección con vectores múltiples
print('Creando colección...')
if not qdrant.collection_exists("TFM"):
    qdrant.create_collection(
        collection_name="TFM",
        vectors_config={
            "track_vector": VectorParams(size=dim_audio, distance=Distance.COSINE),
            "lyrics_vector": VectorParams(size=dim_lyrics, distance=Distance.COSINE),
        }
    )
else:
    print("✅ La colección 'TFM' ya existe.")
# Bucle por lotes
batch_size = 3
while True:
    print("Consultando lote...")
    pg_cursor.execute("""
        SELECT id, artista, cancion, letra, album, mbid, track_vector, letra_vec, link, bpm, initialkey, genre 
        FROM lyrics_database
        WHERE track_vector IS NOT NULL AND letra_vec IS NOT NULL AND vector_migrado = FALSE
        LIMIT %s;
    """, (batch_size,))
    rows = pg_cursor.fetchall()

    if not rows:
        print("✅ Todos los datos han sido migrados.")
        break

    points = []
    ids_to_update = []

    for row in rows:
        id_, artist, title, lyric, album, mbid, audio_vec, lyrics_vec, link, bpm, initialkey, genre = row
        try:
            mean_audio_vec = np.mean(audio_vec, axis=0).tolist() if isinstance(audio_vec[0], list) else audio_vec
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
            print(f"❌ Error procesando id {id_}: {e}")

    if points:
        print(f"Subiendo {len(points)} puntos...")
        qdrant.upsert(collection_name="TFM", points=points)
        pg_cursor.execute(
            "UPDATE lyrics_database SET vector_migrado = TRUE WHERE id = ANY(%s);",
            (ids_to_update,)
        )
        pg_conn.commit()
        print("✅ Lote procesado.")

    time.sleep(1)  # Evita sobrecargar la CPU

pg_cursor.close()
pg_conn.close()
