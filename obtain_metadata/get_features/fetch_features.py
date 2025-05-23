import psycopg2
import requests
from pymongo import MongoClient
import time
import os

# Configuración
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"

MONGO_URI = os.getenv('MONGO_URI')

# Conexión PostgreSQL
pg_conn = psycopg2.connect(DATABASE_URL)
pg_cursor = pg_conn.cursor()

# Conexión MongoDB
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["musica"]
mongo_collection = mongo_db["features"]

# Función para obtener features desde AcousticBrainz
def get_acousticbrainz_features(mbid: str):
    url = f"https://acousticbrainz.org/api/v1/{mbid}/high-level"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Leer canciones con MBID desde PostgreSQL
pg_cursor.execute("SELECT id, mbid FROM lyrics_database WHERE mbid IS NOT NULL;")
canciones = pg_cursor.fetchall()

insertados = 0
for song_id, mbid in canciones:
    # Verificar si ya está en MongoDB
    if mongo_collection.find_one({"cancion_id": song_id}):
        continue

    features = get_acousticbrainz_features(mbid)
    if features is None:
        continue

    documento = {
        "postgre_id": song_id,
        "mbid": mbid,
        "features": features
    }

    mongo_collection.insert_one(documento)
    insertados += 1

    # Evitar abusar de la API
    time.sleep(1.0)

print(f"Insertados: {insertados} documentos nuevos en MongoDB.")

