import time
import subprocess
import psycopg2
import os
from psycopg2 import sql
from obtener_artistas.obtener_artistas import obtener_artistas_musicbrainz
from obtener_canciones.obtener_canciones import obtener_canciones
from obtener_letras.obtener_letras import obtener_datos_y_guardar

# Cargar variables de entorno
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}"
# Conexión a la base de datos
def conectar_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

# Comprobar si hay suficientes artistas
def hay_artistas_suficientes():
    conn = conectar_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM artistas")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count >= 100
    return False

# Comprobar si hay suficientes canciones
def hay_canciones_suficientes():
    conn = conectar_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM canciones")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count >= 10
    return False

# Orquestación
def orquestar():
    print("Iniciando la orquestación...")

    # Primero, ejecutar obtener_artistas
    print("Ejecutando obtener_artistas...")
    obtener_artistas_musicbrainz()

    # Esperar hasta que haya al menos 100 artistas
    while not hay_artistas_suficientes():
        print("Esperando que haya al menos 100 artistas...")
        time.sleep(10)

    # Ejecutar obtener_canciones
    print("Ejecutando obtener_canciones...")
    obtener_canciones()

    # Esperar hasta que haya al menos 10 canciones
    while not hay_canciones_suficientes():
        print("Esperando que haya al menos 10 canciones...")
        time.sleep(10)

    # Ejecutar obtener_letras
    print("Ejecutando obtener_letras...")
    obtener_datos_y_guardar()

if __name__ == "__main__":
    orquestar()
