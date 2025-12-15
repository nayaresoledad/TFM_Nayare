# TFM Nayare - Docker Compose Architecture

Orquestación completa de todos los servicios del proyecto TFM Nayare usando Docker Compose.

## 📋 Servicios Disponibles

### 🗄️ Infraestructura
- **postgres**: PostgreSQL 15 (BD principal)
- **qdrant**: Vector database para embeddings

### 🎵 Extracción de Datos (Lyrics)
- **obtener-artistas**: Obtiene artistas de la API Genius
- **obtener-canciones**: Obtiene canciones de los artistas
- **obtener-letras**: Obtiene letras de las canciones y metadatos de MusicBrainz

### 🎼 Metadatos (Obtain Metadata)
- **get-mbid**: Obtiene MBID de MusicBrainz
- **essentia-analysis**: Análisis de audio con Essentia
- **get-features**: Obtiene features de las pistas
- **mongo-to-postgres**: Migra features de MongoDB a PostgreSQL

### 🧠 Vectorización (Vectors)
- **vectorizer-lyrics**: Vectoriza letras con SentenceTransformer
- **vectorizer-audio**: Vectoriza features de audio
- **postgre-to-qdrant**: Migra vectores de PostgreSQL a Qdrant

### 📊 Servicios Adicionales
- **monitorizacion**: Nginx para monitoreo (puerto 8080)
- **streamlit**: Dashboard Streamlit (puerto 8501)
- **tests**: Suite de tests automatizados

## 🚀 Uso

### Iniciar todos los servicios
```bash
docker compose up
```

### Iniciar solo infraestructura (PostgreSQL + Qdrant)
```bash
docker compose up postgres qdrant
```

### Iniciar solo tests
```bash
docker compose up tests
```

### Iniciar solo servicios de extracción
```bash
docker compose up obtener-artistas obtener-canciones obtener-letras
```

### Iniciar solo servicios de vectorización
```bash
docker compose up vectorizer-lyrics vectorizer-audio postgre-to-qdrant
```

### Iniciar dashboard Streamlit
```bash
docker compose up streamlit
# Accesible en http://localhost:8501
```

### Ver logs de un servicio específico
```bash
docker compose logs -f <service-name>
# Ejemplo:
docker compose logs -f obtener-artistas
```

### Ejecutar comando en un contenedor
```bash
docker compose exec <service-name> <command>
# Ejemplo:
docker compose exec postgres psql -U tfm_user -d tfm_db -c "SELECT COUNT(*) FROM artists;"
```

### Detener todos los servicios
```bash
docker compose down
```

### Detener y eliminar volúmenes (limpieza completa)
```bash
docker compose down -v
```

## 📦 Volúmenes

- **pgdata**: Datos persistentes de PostgreSQL
- **qdrant_storage**: Datos persistentes de Qdrant
- **audio_cache**: Caché de archivos de audio descargados
- **model_cache**: Caché de modelos pre-entrenados (HuggingFace)

## 🔗 Dependencias de Servicios

```
postgres ─────┬──────────────────────────────────┬────────────────────┐
              │                                  │                    │
       obtener-artistas              get-mbid, essentia, get-features, mongo-to-postgres
              │
       obtener-canciones
              │
       obtener-letras ──────┐
                            │
                    vectorizer-lyrics ──┐
                                        │
      essentia-analysis────┐            │
              │            │            │
      vectorizer-audio ────┴────────────┘
                            │
                    postgre-to-qdrant

        qdrant ────────────────────────────────────────────────────┐
                                                                   │
                                    vectorizer-lyrics, vectorizer-audio
```

## 📝 Configuración

### Variables de Entorno (.env)

```env
POSTGRES_USER=tfm_user
POSTGRES_PASSWORD=tfm_pass_test_12345
POSTGRES_DB=tfm_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

API_KEY_GENIUS=<your-genius-api-key>
```

**Nota**: El archivo `.env` debe ser creado localmente con tus credenciales reales. No se commitea al repositorio por seguridad.

## 🧪 Tests

### Ejecutar todos los tests
```bash
docker compose run tests pytest -v
```

### Ejecutar tests específicos
```bash
docker compose run tests pytest tests/test_retry.py -v
docker compose run tests pytest tests/test_db_integration.py::TestDatabaseConnection -v
```

### Ejecutar tests con cobertura
```bash
docker compose run tests pytest --cov=common --cov=extract_data
```

## 🔧 Troubleshooting

### Puerto ya en uso
```bash
# Si el puerto 5432 está en uso:
docker compose down
sudo lsof -i :5432
kill -9 <PID>
```

### Postgres no es saludable (healthcheck fails)
```bash
docker compose logs postgres
# Esperar 30 segundos y reintentar
docker compose up
```

### Errores de conexión entre servicios
```bash
# Verificar que la red está creada
docker network ls | grep tfm_network

# Inspeccionar la red
docker network inspect tfm_network
```

### Reconstruir imágenes sin caché
```bash
docker compose build --no-cache
```

## 📚 Archivos Relacionados

- [MEJORAS_TFM_NAYARE.md](../MEJORAS_TFM_NAYARE.md) - Mejoras implementadas
- [SCALA_HADOOP_SPARK.md](../SCALA_HADOOP_SPARK.md) - Información sobre Spark
- [Dockerfile.tests](../Dockerfile.tests) - Dockerfile para tests
- [common/config.py](../common/config.py) - Configuración centralizada
- [common/logging.py](../common/logging.py) - Logging con JSON
- [common/db.py](../common/db.py) - Gestor de pool de conexiones
- [common/retry.py](../common/retry.py) - Decorador de reintento
- [common/progress.py](../common/progress.py) - Gestor de progreso

## 🎯 Próximos Pasos

- [ ] Configurar CI/CD en GitHub Actions
- [ ] Añadir monitoreo con Prometheus/Grafana
- [ ] Implementar logging centralizado (ELK stack)
- [ ] Añadir api-gateway (Kong/Traefik)
- [ ] Configurar backup automático de PostgreSQL

