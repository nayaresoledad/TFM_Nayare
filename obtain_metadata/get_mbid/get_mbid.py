import psycopg2
import musicbrainzngs
import time
import os

# Configura el User-Agent para MusicBrainz
musicbrainzngs.set_useragent("Lyrics", "1.0", "olealpaca@gmail.com")

# Función para obtener MBID
def get_mbid(artist, title):
    try:
        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=1)
        recordings = result.get("recording-list", [])
        if recordings:
            return recordings[0]["id"]
    except Exception as e:
        print(f"Error al buscar MBID para {artist} - {title}: {e}")
    return None

# Conexión a la base de datos PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
conn = psycopg2.connect(DATABASE_URL)

cursor = conn.cursor()

# Asegura que la columna "mbid" exista
cursor.execute("ALTER TABLE lyrics_database ADD COLUMN IF NOT EXISTS mbid TEXT;")
conn.commit()

# Leer las canciones sin MBID aún
cursor.execute("SELECT id, artista, cancion FROM lyrics_database WHERE mbid IS NULL;")
rows = cursor.fetchall()

for song_id, artist, title in rows:
    mbid = get_mbid(artist, title)
    print(f"{artist} - {title} => MBID: {mbid}")
    
    # Actualiza el MBID si lo encontró
    if mbid:
        cursor.execute("UPDATE lyrics_database SET mbid = %s WHERE id = %s;", (mbid, song_id))
        conn.commit()

    # Evita sobrecargar la API de MusicBrainz
    time.sleep(1.1)

cursor.close()
conn.close()
