# Búsqueda de canciones por temática y similitud sonora
## TFM - Nayare Montes Gavilán

## Para el máster en Big Data de IMF Business School

### Instrucciones

Para el correcto funcionamiento:
- Clona el repositorio.
- Crea en local una base de datos PostgreSQL llamada 'artistas'.
- Crea un archivo .env con las credenciales de tu base de datos.
- Añade al .env tu API token de Genius.
- Descarga los pesos del modelo Effnet Discogs (+ info en la carpeta vectors/vectorizer/track_vectorizer)
- Una vez tienes todo esto levanta cada docker-compose según tu necesidad. Se conectarán a tu base de PostgreSQL local.

### Licencias

#### Essentia
Essentia is available under an open licence, [Affero GPLv3](http://www.gnu.org/licenses/agpl.html), for non-commercial applications, thus it is possible to test the library before deciding to licence it under a comercial licence.
Contact [Music Technology Group (UPF)](https://www.upf.edu/web/mtg/technologies-licensing) for more information about licensing conditions and for consulting how Essentia can suit your application.
#### Multilingual-e5-small model
Este modelo fue creado por Wang, Liang and Yang, Nan and Huang, Xiaolong and Yang, Linjun and Majumder, Rangan and Wei, Furu bajo una licencia [MIT](https://dataloop.ai/library/model/license/mit/) para uso comercial y no comercial, distribución y modificación. Fue publicado a través del paper [Multilingual E5 Text Embeddings: A Technical Report](https://arxiv.org/pdf/2402.05672) en 2024.
#### Qdrant
Qdrant está bajo una Licencia Apache, Versión 2.0. [Aquí](https://github.com/qdrant/qdrant/blob/master/LICENSE) una copia del archivo de la licencia.
#### AcousticBrainz
All of the data contained in AcousticBrainz is licensed under the [CC0](http://creativecommons.org/publicdomain/zero/1.0/) license (public domain).
#### MusicBrainz Database
Most of the data in the MusicBrainz Database is licensed under [CC0](http://creativecommons.org/publicdomain/zero/1.0/), which effectively places the data into the Public Domain. That means that anyone can download the data and use it in any way they want. The remaining data is released under the Creative Commons [Attribution-NonCommercial-ShareAlike 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/) license.