import os
import subprocess
import essentia.standard as es
from essentia.standard import YamlOutput
import os

os.environ['ESSENTIA_MODEL_PATH'] = '/home/perseis/master_big_data/tfm_similarity_canciones/vector_search/essentia-models'

def download_audio(youtube_url, output_name="audio.mp3"):
    print("⬇️  Descargando audio...")
    command = [
        "yt-dlp", "-x", "--audio-format", "mp3",
        "-o", output_name,
        youtube_url
    ]
    subprocess.run(command, check=True)
    return output_name

def analyze_audio(file_path):
    # Cargar el audio desde archivo
    #loader = es.MonoLoader(filename=file_path)
    #audio = loader()
    print("🎧 Analizando audio...")
    #features= es.Extractor()(audio)
    extractor=es.MusicExtractor(lowlevelStats=['mean', 'stdev'], rhythmStats=['mean'], tonalStats=['mean'])
    features, _ = extractor(file_path)
    print(_)

    fea=YamlOutput(filename = 'mfcc.sig', format='json')(features)
    print(fea)

    print("\n🎵 Metadatos extraídos:")
    print("  - BPM:", features['rhythm.bpm'])
    print("  - Tono (Key):", features['tonal.chords_key'])
    print("  - Duracion:", features['metadata.audio_properties.analysis.length'])
    print("  - Danceability:", features['rhythm.danceability'])

if __name__ == "__main__":
    url = input("🔗 Introduce URL de YouTube: ").strip()
    filename = "temp_audio.mp3"

    try:
        download_audio(url, filename)
        analyze_audio(filename)
    except Exception as e:
        print("❌ Error:", e)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
