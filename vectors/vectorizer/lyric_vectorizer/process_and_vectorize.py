import re
import psycopg2
import nltk
from nltk.corpus import stopwords
from langdetect import detect
from sentence_transformers import SentenceTransformer
import os

# --- CONFIGURACIÓN ---
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = 'artistas'

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
# --- INICIALIZACIONES ---

# Cargar stopwords
stopwords_en = set(stopwords.words('english'))
stopwords_es = set(stopwords.words('spanish'))
stopwords_fr = set(stopwords.words('french'))

# Modelo de embeddings
model = SentenceTransformer('intfloat/multilingual-e5-small')

# --- FUNCIONES ---

def limpiar_y_preparar_texto(texto: str) -> str:
    if texto is None:
        return None
    if "____" in texto:
        texto = texto.split("____")[0]
    texto = texto.strip()
    texto = "\n".join(linea.strip() for linea in texto.splitlines() if linea.strip())
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)

    try:
        idioma = detect(texto)
    except:
        idioma = 'en'

    if idioma == 'es':
        stop_words = stopwords_es
    elif idioma == 'fr':
        stop_words = stopwords_fr
    else:
        stop_words = stopwords_en

    palabras = texto.split()
    palabras_filtradas = [palabra for palabra in palabras if palabra not in stop_words]
    return " ".join(palabras_filtradas)

def connect_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def crear_columnas_si_no_existen(cursor):
    # letra_procesada
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lyrics_database' AND column_name='letra_procesada'
            ) THEN
                ALTER TABLE lyrics_database ADD COLUMN letra_procesada TEXT;
            END IF;
        END
        $$;
    """)
    # letra_vec
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lyrics_database' AND column_name='letra_vec'
            ) THEN
                ALTER TABLE lyrics_database ADD COLUMN letra_vec float8[];
            END IF;
        END
        $$;
    """)

def procesar_y_guardar(conn):
    cursor = conn.cursor()

    print("📥 Leyendo letras...")
    cursor.execute("SELECT id, letra FROM lyrics_database WHERE letra IS NOT NULL;")
    canciones = cursor.fetchall()

    if not canciones:
        print("⚠️ No se encontraron letras.")
        return

    print(f"🧹 Procesando {len(canciones)} letras...")
    textos_procesados = []
    ids = []
    for cancion_id, letra in canciones:
        limpio = limpiar_y_preparar_texto(letra)
        textos_procesados.append(limpio)
        ids.append(cancion_id)
        cursor.execute(
            "UPDATE lyrics_database SET letra_procesada = %s WHERE id = %s;",
            (limpio, cancion_id)
        )

    print("📐 Vectorizando letras procesadas...")
    vectores = model.encode(textos_procesados)

    print("💾 Guardando vectores en letra_vec...")
    for i, vector in enumerate(vectores):
        cursor.execute(
            "UPDATE lyrics_database SET letra_vec = %s WHERE id = %s;",
            (vector.tolist(), ids[i])
        )

    cursor.close()
    print("✅ Letras procesadas y vectorizadas correctamente.")

# --- MAIN ---

if __name__ == "__main__":
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        crear_columnas_si_no_existen(cursor)
        cursor.close()
        procesar_y_guardar(conn)
        conn.close()
