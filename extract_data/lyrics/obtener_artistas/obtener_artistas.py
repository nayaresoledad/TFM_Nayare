import requests
import time
import os
import psycopg2
from datetime import datetime

# Cargar variables de entorno
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}"

QUERY_BUSQUEDA = "a"  # Puedes cambiarlo para buscar con otra letra

# ==========================
# Funciones para la base de datos
# ==========================
def conectar_db():
    """Conectar a la base de datos PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def crear_tabla_artistas():
    """Crea la tabla de artistas en PostgreSQL si no existe."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artistas (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE,
            fecha_guardado TIMESTAMP,
            query TEXT
        )
    """)
    # Tabla de progreso
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progreso_artistas (
            query TEXT PRIMARY KEY,
            progress INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

def artista_existe(conn, nombre):
    """Verifica si un artista ya está en la base de datos."""
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM artistas WHERE nombre = %s", (nombre,))
    return cursor.fetchone() is not None

def guardar_artista_db(conn, nombre, query):
    """Guarda un artista en la base de datos si no existe y lo escribe en el backup."""
    if not artista_existe(conn, nombre):
        cursor = conn.cursor()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Fecha y hora actuales
        cursor.execute("INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)", 
                       (nombre, fecha_actual, query))
        conn.commit()

# ==========================
# Funciones para manejar el offset
# ==========================
def obtener_offset():
    """Obtiene el offset de la base de datos para la query actual."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT progress FROM progreso_artistas WHERE query = %s", (QUERY_BUSQUEDA,))
    resultado = cursor.fetchone()
    
    conn.close()
    
    return resultado[0] if resultado else 0  # Si no hay registro, empezamos en 0

def guardar_offset(offset):
    """Guarda el offset en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO progreso_artistas (query, progress)
        VALUES (%s, %s)
        ON CONFLICT (query) DO UPDATE
        SET progress = EXCLUDED.progress
    """, (QUERY_BUSQUEDA, offset))
    
    conn.commit()
    conn.close()
# ==========================
# Función principal
# ==========================
def obtener_artistas_musicbrainz():
    crear_tabla_artistas()
    url = 'https://musicbrainz.org/ws/2/artist/'
    print('Obteniendo offset')
    offset = obtener_offset()
    limit = 100
    print('Conectando db...')
    conn = conectar_db()  # Conectar a la base de datos
    print('db conectada!')

    try:
        while True:
            params = {
                'query': QUERY_BUSQUEDA,  # Usamos la query definida arriba
                'limit': limit,
                'offset': offset,
                'fmt': 'json'
            }
            headers = {
                'User-Agent': 'Lyrics/1.0 (olealpaca@gmail.com)'  # Usa tu app y contacto real aquí
            }

            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()  # Lanza error si la respuesta no es 200 OK
                data = response.json()

                if 'artists' not in data:
                    print("No se encontraron más artistas o hubo un error.")
                    break

                artistas = [artist['name'] for artist in data['artists']]
                
                nuevos = 0
                for artista in artistas:
                    if not artista_existe(conn, artista):
                        guardar_artista_db(conn, artista, QUERY_BUSQUEDA)
                        nuevos += 1

                print(f"Se guardaron {nuevos} artistas nuevos en la base de datos y el backup.")

                # Actualizar y guardar el offset
                offset += len(artistas)
                guardar_offset(offset)

                # Si la cantidad de artistas obtenidos es menor que el límite, no hay más páginas
                if len(artistas) < limit:
                    break

                # Evitar que la API bloquee por demasiadas solicitudes
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"Error en la solicitud: {e}. Esperando 5 segundos antes de reintentar...")
                time.sleep(5)  # Esperar antes de reintentar

    except KeyboardInterrupt:
        print("\nInterrupción manual detectada. Guardando estado y cerrando conexión...")
        guardar_offset(offset)

    finally:
        conn.close()
        print("Base de datos cerrada. Proceso finalizado.")

# Ejecutar la obtención de artistas
obtener_artistas_musicbrainz()

