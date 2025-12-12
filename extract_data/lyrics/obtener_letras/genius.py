import requests
import os
import time
from common.retry import retry

# Configura tus credenciales de Genius
API_KEY = os.getenv("API_KEY_GENIUS")

# Función para buscar la canción en Genius
@retry(max_attempts=4, initial_delay=1, backoff=2, exceptions=(Exception,))
def buscar_cancion(artista, cancion):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    # Realizamos la búsqueda
    search_url = f'{base_url}/search'
    params = {'q': f'{artista} {cancion}'}
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        # Verificamos si la respuesta fue exitosa
        if response.status_code == 429:
            # Force a retry via raising a RequestException
            raise requests.exceptions.RequestException('429 Too Many Requests')

        response.raise_for_status()  # Lanza un error si el status code no es 2xx
    except requests.exceptions.RequestException:
        # Re-raise to allow retry decorator to handle retries
        raise

    data = response.json()

    # Verificamos si se encontró la canción
    if data['response'].get('hits'):
        song_id = song_info['id']
        print(f'Canción encontrada: {song_info["full_title"]}')
        return song_url, song_id
    else:
        print(f"No se encontró la canción '{cancion}' de {artista}")
        return None, None




