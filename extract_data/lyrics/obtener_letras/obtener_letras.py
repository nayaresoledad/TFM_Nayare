import requests
import psycopg2
import os
from datetime import datetime
from genius import buscar_cancion
from rasca_genio import obtener_letra

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'
API_KEY_GENIUS = os.getenv("API_KEY_GENIUS")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}"

# Función para obtener el MBID de MusicBrainz
def obtener_mbid_en_musicbrainz(artista, cancion):
    search_url = f'https://musicbrainz.org/ws/2/recording/'
    params = {'query': f'artist:{artista} recording:{cancion}', 'fmt': 'json'}
    
    response = requests.get(search_url, params=params)
    data = response.json()
    
    if 'recordings' in data and data['recordings']:
        mbid = data['recordings'][0]['id']
        return mbid
    else:
        return None

# Función para obtener los artistas y canciones desde la base de datos
def conectar_db():
    """Conectar a la base de datos PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def obtener_artistas_y_canciones():
    conn = conectar_db()
    cursor = conn.cursor()
    # Obtenemos los artistas y las canciones en orden
    cursor.execute('SELECT id_artista, artista, cancion FROM canciones ORDER BY id_artista, id')
    artistas_canciones = cursor.fetchall()
    
    conn.close()
    
    return artistas_canciones

# Función para obtener el progreso y continuar desde el último punto
def obtener_progreso():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Crear la tabla de progreso si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS progreso_actual_cancion (
        id SERIAL PRIMARY KEY,
        id_artista INTEGER,
        id_cancion INTEGER
    );
    ''')
    
    # Obtener el último progreso guardado
    cursor.execute('SELECT id_artista, id_cancion FROM progreso_actual_cancion ORDER BY id_artista DESC, id_cancion DESC LIMIT 1')
    progreso = cursor.fetchone()
    
    conn.close()
    
    return progreso

# Función para guardar el progreso
def guardar_progreso(id_artista, id_cancion):
    conn = conectar_db()
    cursor = conn.cursor()

    # Crear la tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progreso_actual_cancion (
            id SERIAL PRIMARY KEY,
            id_artista INTEGER NOT NULL,
            id_cancion INTEGER NOT NULL
        );
    ''')

    # Insertar el progreso
    cursor.execute('''
        INSERT INTO progreso_actual_cancion (id_artista, id_cancion) VALUES (%s, %s)
    ''', (id_artista, id_cancion))

    conn.commit()
    cursor.close()
    conn.close()

# Función para guardar los resultados en la tabla 'canciones_resultado'
def guardar_en_db(datos):
    conn = conectar_db()
    cursor = conn.cursor()

    # Crear la tabla si no existe
    cursor.execute('''
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

    # Insertar los datos en la base de datos
    cursor.executemany('''
        INSERT INTO canciones_resultado (id_artista, artista, cancion, id_cancion, mbid, letra, fecha_guardado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', datos)

    conn.commit()
    cursor.close()
    conn.close()

# Función para obtener los datos y guardarlos
def obtener_datos_y_guardar():
    # Verificamos el progreso para continuar desde el último punto
    progreso = obtener_progreso()
    
    if progreso:
        # Continuamos desde el último artista y canción procesados
        last_artista_id, last_cancion_id = progreso
        print(f"Continuando desde el artista ID: {last_artista_id} y la canción ID: {last_cancion_id}")
    else:
        print("Comenzando desde el inicio.")
        last_artista_id, last_cancion_id = None, None

    # Obtenemos los artistas y canciones desde la base de datos
    artistas_canciones = obtener_artistas_y_canciones()
    
    # Lista para almacenar los resultados
    datos = []
    
    # Iterar sobre los artistas y canciones
    for artista_id, artista, cancion in artistas_canciones:
        if last_artista_id and (artista_id < last_artista_id or (artista_id == last_artista_id and cancion < last_cancion_id)):
            # Si ya hemos procesado este artista y canción, lo saltamos
            continue
        
        print(f'Buscando: {artista} - {cancion}')
        
        # Obtener la URL de la canción y el ID de Genius
        song_url, song_id = buscar_cancion(artista, cancion)
        
        if song_url and song_id:
            # Obtener la letra de la canción
            letra = obtener_letra(song_url)
            
            # Obtener el MBID de MusicBrainz
            mbid = obtener_mbid_en_musicbrainz(artista, cancion)
            
            # Guardar la información si se tiene la letra y MBID
            if letra or mbid:
                fecha_guardado = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                datos.append([artista_id, artista, cancion, song_id, mbid, letra, fecha_guardado])
        
        # Guardar los resultados en la base de datos después de cada artista/canción
        if datos:
            guardar_en_db(datos)
            print(f'Guardados {len(datos)} resultados en la base de datos.')
            datos.clear()  # Limpiar la lista de datos después de cada inserción
        
        # Actualizar el progreso después de cada canción procesada
        guardar_progreso(artista_id, cancion)

# Función principal que se ejecuta
obtener_datos_y_guardar()

