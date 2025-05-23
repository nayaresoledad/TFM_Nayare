from pymongo import MongoClient
import psycopg2
import psycopg2.extras
import os

# === Configuración ===
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB = "musica"
MONGO_COLLECTION = "features"

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
POSTGRES_TABLE = "lyrics_database"

# === Conexión a MongoDB ===
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
mongo_col = mongo_db[MONGO_COLLECTION]

# === Conexión a PostgreSQL ===
pg_conn = psycopg2.connect(DATABASE_URL)
pg_conn.autocommit = True
pg_cur = pg_conn.cursor()

# === Crear columnas si no existen ===
for col_name, col_type in [("bpm", "FLOAT"), ("initialkey", "TEXT"), ("genre", "TEXT")]:
    pg_cur.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='{POSTGRES_TABLE}' AND column_name='{col_name}'
            ) THEN
                ALTER TABLE {POSTGRES_TABLE} ADD COLUMN {col_name} {col_type};
            END IF;
        END;
        $$;
    """)

# === Recorrer documentos en MongoDB ===
for doc in mongo_col.find(
    {"postgre_id": {"$exists": True}},
    {
        "postgre_id": 1,
        "features.metadata.tags.bpm": 1,
        "features.metadata.tags.initialkey": 1,
        "features.metadata.tags.genre": 1
    }
):
    postgre_id = doc.get("postgre_id")

    # Extraer BPM
    bpm_list = doc.get("features", {}).get("metadata", {}).get("tags", {}).get("bpm")
    bpm = float(bpm_list[0]) if bpm_list else None
    print(bpm)

    # Extraer initial key
    initialkey = doc.get("features", {}).get("metadata", {}).get("tags", {}).get("initialkey")

    # Extraer genre
    genre = doc.get("features", {}).get("metadata", {}).get("tags", {}).get("genre")

    # Actualizar PostgreSQL
    pg_cur.execute(
        f"""
        UPDATE {POSTGRES_TABLE}
        SET bpm = %s,
        initialkey = %s,
        genre = %s
        WHERE id = %s;
        """,
        (bpm, initialkey, bpm, postgre_id)
    )

print("✅ bpm, initialkey y genre actualizados en PostgreSQL.")

# === Cierre de conexiones ===
pg_cur.close()
pg_conn.close()
mongo_client.close()
