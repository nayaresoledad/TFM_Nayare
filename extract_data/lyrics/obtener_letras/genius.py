import requests
import os
import time

# Configura tus credenciales de Genius
API_KEY = os.getenv("API_KEY_GENIUS")

# Función para buscar la canción en Genius
def buscar_cancion(artista, cancion):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    # Realizamos la búsqueda
    search_url = f'{base_url}/search'
    params = {'q': f'{artista} {cancion}'}
    
    try:
        response = requests.get(search_url, headers=headers, params=params)
        
        # Verificamos si la respuesta fue exitosa
        if response.status_code == 429:
            print("🔴 Límite de solicitudes alcanzado. Esperando 30 segundos...")
            time.sleep(30)  # Esperamos 30 segundos antes de reintentar
            return buscar_cancion(artista, cancion)  # Reintentar la búsqueda

        response.raise_for_status()  # Lanza un error si el status code no es 2xx
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error en la solicitud: {e}")
        return None

    data = response.json()

    # Verificamos si se encontró la canción
    if data['response']['hits']:
        # Tomamos el primer resultado
        song_info = data['response']['hits'][0]['result']
        song_url = song_info['url']
        song_id = song_info['id']
        print(f'Canción encontrada: {song_info["full_title"]}')
        return song_url, song_id
    else:
        print(f"No se encontró la canción '{cancion}' de {artista}")
        return None, None




