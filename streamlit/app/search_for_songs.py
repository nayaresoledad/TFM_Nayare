from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from collections import defaultdict
import numpy as np
import json
import os

# Inicializar Qdrant y modelo
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = int(os.getenv("QDRANT_PORT", 6333))

qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
model = SentenceTransformer("intfloat/multilingual-e5-small")

def buscar_canciones(json_input: str, collection_name="TFM", top_k=5):
    data = json.loads(json_input)
    combined_scores = defaultdict(lambda: {"score": 0, "count": 0, "payload": None})

    # Vector de la frase del usuario
    user_query = data.get("query")
    if not user_query:
        return {"error": "Missing 'query' field"}
    
    query_vector = model.encode(user_query, normalize_embeddings=True).tolist()

    # Filtros opcionales
    filters = []
    if genre := data.get("genre"):
        filters.append({"key": "genre", "match": {"value": genre}})
    if key := data.get("key"):
        filters.append({"key": "key", "match": {"value": key}})
    if bpm := data.get("bpm"):
        filters.append({"key": "bpm", "match": {"value": bpm}})
    
    qdrant_filter = {"must": filters} if filters else None

    # Buscar por lyrics_vector
    lyrics_hits = qdrant.search(
        collection_name=collection_name,
        query_vector=("lyrics_vector", query_vector),
        limit=top_k * 3,
        query_filter=qdrant_filter
    )

    for hit in lyrics_hits:
        combined_scores[hit.id]["score"] += hit.score * 0.5
        combined_scores[hit.id]["count"] += 1
        combined_scores[hit.id]["payload"] = hit.payload

    # Si hay referencia a canción existente
    artist_ref = data.get("artist_ref")
    title_ref = data.get("title_ref")
    if artist_ref and title_ref:
        scroll_result = qdrant.scroll(
            collection_name=collection_name,
            scroll_filter={
                "must": [
                    {"key": "artist", "match": {"value": artist_ref}},
                    {"key": "title", "match": {"value": title_ref}}
                ]
            },
            limit=1,
            with_vectors=True
        )
        if scroll_result[0]:
            ref_vector = scroll_result[0][0].vector["track_vector"]
            track_hits = qdrant.search(
                collection_name=collection_name,
                query_vector=("track_vector", ref_vector),
                limit=top_k * 3,
                query_filter=qdrant_filter
            )
            for hit in track_hits:
                if hit.id == scroll_result[0][0].id:
                    continue  # Saltar la canción original
                combined_scores[hit.id]["score"] += hit.score * 0.5
                combined_scores[hit.id]["count"] += 1
                combined_scores[hit.id]["payload"] = hit.payload

    # Ordenar resultados
    ranked = sorted(combined_scores.items(), key=lambda x: x[1]["score"], reverse=True)[:top_k]

    return {
        "query_input": data,  # devuelve toda la consulta del usuario
        "results": [
            {
                "rank": i + 1,
                "artist": item[1]["payload"].get("artist"),
                "title": item[1]["payload"].get("title"),
                "album": item[1]["payload"].get("album"),
                "letra": item[1]["payload"].get("lyric"),
                "mbid": item[1]["payload"].get("mbid"),
                "bpm": item[1]["payload"].get("bpm"),
                "key": item[1]["payload"].get("key"),
                "genre": item[1]["payload"].get("genre"),
                "link": item[1]["payload"].get("link"),
                "score": round(item[1]["score"], 4)
            } for i, item in enumerate(ranked)
        ]
    }

'''entrada = json.dumps({
    "query": "una canción sobre nostalgia y juventud",
    "artist_ref": "Executive Slacks",
    "title_ref": "Ecce Homo",
})

resultados = buscar_canciones(entrada)
print(json.dumps(resultados, indent=2, ensure_ascii=False))'''
