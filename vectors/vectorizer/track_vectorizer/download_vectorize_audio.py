import os
import subprocess
import psycopg2
from essentia.standard import MonoLoader, TensorflowPredictEffnetDiscogs
import json
from datetime import datetime
import gc

# Modelo de embeddings
graph_path = "./essentia-models/discogs_track_embeddings-effnet-bs64-1.pb"
# Cargar modelo (uno por iteración para evitar OOM)
model = TensorflowPredictEffnetDiscogs(
    graphFilename=graph_path,
    output="PartitionedCall:1"
)

# Conexión a PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Crear columna 'link' si no existe
cursor.execute("""
    ALTER TABLE lyrics_database 
    ADD COLUMN IF NOT EXISTS link TEXT
""")
conn.commit()

# Crear columna track_vector si no existe
cursor.execute("""
    ALTER TABLE lyrics_database 
    ADD COLUMN IF NOT EXISTS track_vector JSONB
""")
conn.commit()

# Archivo para registrar errores
log_path = "errores_vectores.log"

def log_error(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

# Procesar en bloques de 10
while True:
    cursor.execute("SELECT id, artista, cancion FROM lyrics_database WHERE track_vector IS NULL LIMIT 10;")
    canciones = cursor.fetchall()

    if not canciones:
        print("🎉 ¡Todos los vectores han sido generados!")
        break

    for id_, artist, title in canciones:
        try:
            print(f"\n🔍 Procesando: {artist} - {title}")
            # Normalización del nombre (reemplaza slash matemático por slash estándar)
            artist_clean = artist.replace("∕", "/")
            title_clean = title.replace("∕", "/")
            query = f"ytsearch1:{artist_clean} {title_clean}"

            #query = f"ytsearch1:{artist} {title}"
            output_file = f"temp_{id_}.mp3"
            #output_template = f"temp_{id_}.%(ext)s"
            cookies_path = "cookies.txt"  # Asegúrate de tener este archivo exportado previamente

            result = subprocess.run([
                "yt-dlp", "--cookies", cookies_path,
                "--print", "%(webpage_url)s",
                query
            ], capture_output=True, text=True, check=True)

            youtube_url = result.stdout.strip()
            print(f"🔗 Enlace encontrado: {youtube_url}")

            subprocess.run([
                "yt-dlp","--cookies", cookies_path,
                "-x", "--audio-format", "mp3",
                "-o", output_file,
                query
            ], check=True)

            audio = MonoLoader(filename=output_file, sampleRate=16000, resampleQuality=4)()
            vector = model(audio)
            vector_str = json.dumps(vector.tolist())

            cursor.execute(
                "UPDATE lyrics_database SET track_vector = %s, link = %s WHERE id = %s;",
                (vector_str, youtube_url, id_)
            )
            conn.commit()

            print("✅ Vector guardado.")
            os.remove(output_file)

        except Exception as e:
            error_msg = f"❌ Error con {artist} - {title} (ID: {id_}): {e}"
            print(error_msg)
            log_error(error_msg)

        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
            gc.collect()

# Cierre
cursor.close()
conn.close()
