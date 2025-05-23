import requests
import psycopg2
import os
import time
import random
from datetime import datetime

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
    """Conectar a la base de datos PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def crear_tabla_canciones():
    """Crea la tabla de artistas en PostgreSQL si no existe."""
    conn = conectar_db()
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
    # Tabla de progreso para almacenar offsets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progreso_canciones (
            id SERIAL PRIMARY KEY,
            artista_offset INTEGER DEFAULT 0,
            cancion_offset INTEGER DEFAULT 0
        );
    """)
    cursor.execute("""
        INSERT INTO progreso_canciones (id, artista_offset, cancion_offset)
        VALUES (1, 0, 0)
        ON CONFLICT (id) DO NOTHING;
    """)
    conn.commit()
    conn.close()

def cancion_existe(id_artista, cancion):
    """Verifica si una canción ya está guardada para evitar duplicados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM canciones WHERE id_artista = %s AND cancion = %s", (id_artista, cancion))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def guardar_cancion(id_artista, artista, cancion):
    """Guarda una canción en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s) ON CONFLICT (id_artista, cancion) DO NOTHING;", (id_artista, artista, cancion, fecha_actual))
    conn.commit()
    conn.close()

# ==========================
# Funciones de offset
# ==========================

def leer_offset():
    """Obtiene los offsets de artista y canción desde la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT artista_offset, cancion_offset FROM progreso_canciones WHERE id = 1")
    resultado = cursor.fetchone()
    conn.close()
    
    return resultado if resultado else (0, 0)

def guardar_offset(artista_offset, cancion_offset):
    """Guarda los offsets en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE progreso_canciones
        SET artista_offset = %s, cancion_offset = %s
        WHERE id = 1
    """, (artista_offset, cancion_offset))
    conn.commit()
    conn.close()

# ==========================
# Función para obtener canciones de Genius
# ==========================

def buscar_canciones_de_artista(artista):
    """Busca canciones de un artista en Genius."""
    base_url = 'https://api.genius.com'
    headers = {'Authorization': f'Bearer {API_KEY_GENIUS}'}
    
    search_url = f'{base_url}/search'
    params = {'q': artista}
    response = requests.get(search_url, headers=headers, params=params)
    
    if response.status_code == 429:  # Demasiadas solicitudes
        print("🔴 Demasiadas solicitudes. Esperando...")
        time.sleep(random.randint(30, 60))
        return buscar_canciones_de_artista(artista)  # Reintentar

    data = response.json()
    canciones = []

    if 'response' in data and 'hits' in data['response']:
        for hit in data['response']['hits']:
            song_info = hit['result']
            canciones.append(song_info['title'])
    
    return canciones

# ==========================
# Función principal
# ==========================

def obtener_canciones():
    crear_tabla_canciones()
    """Obtiene todas las canciones de los artistas en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM artistas")
    artistas = cursor.fetchall()
    conn.close()

    total_artistas = len(artistas)
    offset_artista, offset_cancion = leer_offset()

    print(f"🎤 Artistas encontrados: {total_artistas}")
    print(f"🔄 Continuando desde el artista {offset_artista + 1}...")

    for i, (id_artista, nombre_artista) in enumerate(artistas[offset_artista:], start=offset_artista):
        print(f"🎵 Buscando canciones de {nombre_artista}...")

        canciones = buscar_canciones_de_artista(nombre_artista)

        if not canciones:
            print(f"❌ No se encontraron canciones para {nombre_artista}.")
            continue

        for j, cancion in enumerate(canciones[offset_cancion:], start=offset_cancion):
            if cancion_existe(id_artista, cancion):
                print(f"✅ {cancion} ya está en la base de datos. Saltando...")
                continue

            print(f"🎼 Guardando {nombre_artista} - {cancion}...")
            guardar_cancion(id_artista, nombre_artista, cancion)

            # Guardar el progreso por canción
            guardar_offset(i, j + 1)
            sleep_time = random.randint(5, 15)
            print(f"⏳ Pausando {sleep_time} segundos para evitar bloqueos...")
            time.sleep(sleep_time)

        # Restablecer el offset de canciones y avanzar al siguiente artista
        guardar_offset(i + 1, 0)

        # Espera aleatoria entre artistas
        sleep_time = random.randint(20, 40)
        print(f"⏸️ Pausando {sleep_time} segundos antes de buscar el próximo artista...")
        time.sleep(sleep_time)

    print("🎉 Proceso terminado. Todas las canciones han sido obtenidas.")

# ==========================
# Ejecución del programa
# ==========================
obtener_canciones()
