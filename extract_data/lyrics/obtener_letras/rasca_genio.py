import requests
import psycopg2
import os
import re
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
from genius import buscar_cancion  # Tu función para buscar canciones en Genius

# Cargar variables de entorno
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'
API_KEY_GENIUS = os.getenv("API_KEY_GENIUS")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}"


# ==========================
# Funciones de base de datos
# ==========================

def conectar_db():
    """Conecta a la base de datos SQLite y retorna la conexión."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def crear_tabla_letras():
    """Crea la tabla de letras si no existe."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
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
    # Tabla de progreso
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progreso_letras (
            id SERIAL PRIMARY KEY,
            offset_letra INTEGER DEFAULT 0
        );
    """)
    
    # Insertar un registro si no existe
    cursor.execute("""
        INSERT INTO progreso_letras (id, offset_letra)
        VALUES (1, 0)
        ON CONFLICT (id) DO NOTHING;
    """)
    conn.commit()
    conn.close()

def cancion_existe(id_cancion):
    """Verifica si la canción ya está en letras.db para evitar duplicados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM letras WHERE id_cancion = %s", (id_cancion,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def guardar_letra(id_artista, id_cancion, artista, cancion, letra):
    """Guarda la letra en letras.db."""
    conn = conectar_db()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO letras (id_artista, id_cancion, artista, cancion, letra, fecha_guardado) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (id_artista, id_cancion, artista, cancion, letra, fecha_actual))
    conn.commit()
    conn.close()

# ==========================
# Función para leer el offset
# ==========================

def leer_offset():
    """Obtiene el offset desde la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT offset_letra FROM progreso_letras WHERE id = 1")
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 0

def guardar_offset(offset):
    """Guarda el offset en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE progreso_letras SET offset_letra = %s WHERE id = 1
    """, (offset,))
    conn.commit()
    conn.close()

# ==========================
# Función para obtener letras de Genius
# ==========================

def obtener_letra(song_url):
    """Extrae la letra de la canción desde Genius."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
        }
        page = requests.get(song_url, headers=headers, timeout=10)

        if page.status_code == 429:  # Código de respuesta de "demasiadas solicitudes"
            print("🔴 Demasiadas solicitudes. Pausando...")
            time.sleep(random.randint(30, 60))  # Esperar 30-60 segundos antes de reintentar
            return obtener_letra(song_url)  # Reintentar

        html = BeautifulSoup(page.text, 'html.parser')
        lyrics_divs = html.find_all('div', attrs={'data-lyrics-container': 'true'})

        if not lyrics_divs:
            print(f"⚠️ No se encontró letra para {song_url}")
            return "no lyric"

        lyrics = '\n'.join([div.get_text(separator="\n") for div in lyrics_divs])
        lyrics = re.sub(r'[\(\[].*?[\)\]]', '', lyrics)  # Eliminar identificadores como [Chorus]
        lyrics = os.linesep.join([s for s in lyrics.splitlines() if s])  # Quitar líneas vacías

        return lyrics

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error al obtener la letra: {e}")
        return "no lyric"

# ==========================
# Función principal
# ==========================

def obtener_letras():
    crear_tabla_letras()
    """Busca las canciones en la base de datos y obtiene sus letras desde Genius."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ID_ARTISTA, ID, artista, cancion FROM canciones")
    canciones = cursor.fetchall()
    conn.close()

    total_canciones = len(canciones)
    offset = leer_offset()  # Cargar el progreso guardado

    print(f"🎵 Canciones encontradas: {total_canciones}")
    print(f"🔄 Continuando desde la canción {offset + 1}...")

    for i, (id_artista, id_cancion, artista, cancion) in enumerate(canciones[offset:], start=offset):
        if cancion_existe(id_cancion):
            print(f"✅ {artista} - {cancion} (ID {id_cancion}) ya está en la base de datos. Saltando...")
            continue

        print(f"🔍 Buscando {artista} - {cancion}...")

        song_url = buscar_cancion(artista, cancion)

        if song_url:
            letra = obtener_letra(song_url)
            guardar_letra(id_artista, id_cancion, artista, cancion, letra)
            print(f"✅ Letra guardada ({len(letra)} caracteres).")
        else:
            print(f"❌ No se encontró la canción en Genius.")
            guardar_letra(id_artista, id_cancion, artista, cancion, "no lyric")  # Guardar como "no lyric"

        # Guardar el progreso y esperar un tiempo aleatorio
        guardar_offset(i + 1)
        sleep_time = random.randint(5, 15)
        print(f"⏳ Pausando {sleep_time} segundos para evitar bloqueos...")
        time.sleep(sleep_time)

    print("🎉 Proceso terminado. Todas las letras han sido obtenidas.")

# ==========================
# Ejecución del programa
# ==========================

obtener_letras()
