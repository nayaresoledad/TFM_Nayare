import streamlit as st
from search_for_songs import buscar_canciones
import json

st.set_page_config(page_title="Buscador Musical", layout="centered")

st.title("🎵 Buscador de Canciones por Tema")

# Entrada principal del usuario
query = st.text_input("Introduce una frase temática para buscar canciones", placeholder="Ej. canciones sobre soledad")

# Filtros opcionales
with st.expander("Filtros opcionales"):
    genre = st.text_input("🎧 Género musical (opcional)", placeholder="Ej. rock, pop, electronic")
    key = st.text_input("🎼 Tono musical (opcional)", placeholder="Ej. C major, A minor")
    bpm = st.number_input("⏱️ BPM (opcional)", min_value=0, max_value=300, step=1)

# Entrada para canción de referencia
with st.expander("Usar canción de referencia (opcional)"):
    artist_ref = st.text_input("👤 Artista de referencia", placeholder="Ej. Radiohead")
    title_ref = st.text_input("🎵 Título de la canción", placeholder="Ej. Creep")

# Botón de búsqueda
if st.button("🔍 Buscar canciones"):
    if not query:
        st.warning("Debes introducir al menos una frase temática.")
    else:
        # Construir input JSON
        input_data = {
            "query": query,
            "genre": genre if genre else None,
            "key": key if key else None,
            "bpm": int(bpm) if bpm else None,
            "artist_ref": artist_ref if artist_ref else None,
            "title_ref": title_ref if title_ref else None
        }

        # Limpiar None
        input_data = {k: v for k, v in input_data.items() if v is not None}

        # Ejecutar búsqueda
        with st.spinner("Buscando canciones..."):
            resultados = buscar_canciones(json.dumps(input_data))

        # Mostrar resultados
        if "error" in resultados:
            st.error(resultados["error"])
        elif not resultados["results"]:
            st.info("No se encontraron resultados.")
        else:
            st.success(f"Se encontraron {len(resultados['results'])} canciones similares:")
            for r in resultados["results"]:
                st.markdown(f"""
                **🎵 {r['title']}**  
                *Artista:* {r['artist']}  
                *Álbum:* {r.get('album', 'N/A')}  
                *Género:* {r.get('genre', 'N/A')}  
                *Tono:* {r.get('key', 'N/A')}  
                *BPM:* {r.get('bpm', 'N/A')}  
                *MBID:* {r.get('mbid', 'N/A')}  
                *Link:* {r.get('link', 'N/A')}  
                *Score:* {r['score']}
                ---
                """)
                with st.expander("Ver letra"):
                    st.text(r.get("letra", "Letra no disponible."))

            with st.expander("📤 Consulta enviada"):
                st.json(resultados["query_input"])
