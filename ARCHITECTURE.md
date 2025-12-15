# TFM Nayare - Complete Containerized Architecture

## 🏗️ Sistema Completamente Containerizado

Todos los servicios del proyecto ahora están containerizados y orquestados mediante Docker Compose.

### 📊 15 Servicios Totales

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          TFM NAYARE DOCKER ECOSYSTEM                               │
│                                   (15 containers)                                   │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE (3)                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🗄️  tfm-postgres              PostgreSQL 15 (Main Database)                       │
│  🔍  tfm-qdrant                Qdrant Vector Database                              │
│  🌐  tfm_network              Bridge network for service communication             │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ DATA EXTRACTION (3)                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  👨‍🎤 tfm-obtener-artistas       Genius API → Extract Artists                      │
│       ↓                                                                             │
│  🎵  tfm-obtener-canciones      Extract Songs per Artist                           │
│       ↓                                                                             │
│  📝  tfm-obtener-letras         Extract Lyrics + MusicBrainz Metadata              │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ METADATA COLLECTION (4)                                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🆔  tfm-get-mbid               Get MBID from MusicBrainz                          │
│  🎼  tfm-essentia-analysis      Audio Analysis (Essentia)                          │
│  🎛️  tfm-get-features           Extract Audio Features                            │
│  📊  tfm-mongo-to-postgres      Migrate MongoDB Features → PostgreSQL              │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ VECTORIZATION & EMBEDDINGS (3)                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🧠  tfm-vectorizer-lyrics      SentenceTransformer: Lyrics → Embeddings           │
│  🎵  tfm-vectorizer-audio       Audio Features → Embeddings                        │
│  ⚡  tfm-postgre-to-qdrant      Migrate Vectors: PostgreSQL → Qdrant              │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ SERVICES & MONITORING (2)                                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  📊  tfm-monitorizacion         Nginx Monitoring Dashboard (port 8080)             │
│  📈  tfm-streamlit              Streamlit Visualization (port 8501)                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ TESTING (1)                                                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ✅  tfm-tests                  Pytest Suite (17 tests passing)                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Service Dependency Flow

```
                              ┌─────────────────┐
                              │ INFRASTRUCTURE  │
                              ├─────────────────┤
                    ┌─────────┤ postgres        │
                    │         │ qdrant          │
                    │         │ tfm_network     │
                    │         └─────────────────┘
                    │
        ┌───────────┼───────────┬──────────────────────────────────┐
        │           │           │                                  │
        ▼           ▼           ▼                                  ▼
    ┌────────┐  ┌────────┐  ┌──────────┐      ┌──────────────────┐
    │Extract │  │Metadata│  │Vectorize │      │ Monitoring       │
    │Data    │  │Collect │  │Embeddings│      │ Services         │
    └────────┘  └────────┘  └──────────┘      └──────────────────┘
        ▲           ▲           ▲                  ▲
        │           │           │                  │
        └─────┬─────┴─────┬─────┴──────────────────┘
              │           │
          ┌───▼────┐  ┌───▼────┐
          │ Tests  │  │Dashboard│
          └────────┘  └────────┘
```

## 📦 Volume Persistence

| Volume            | Purpose                              | Mount Point                |
|------------------|--------------------------------------|---------------------------|
| **pgdata**        | PostgreSQL data persistence          | `/var/lib/postgresql/data` |
| **qdrant_storage**| Qdrant vector DB persistence        | `/qdrant/storage`          |
| **audio_cache**   | Downloaded audio files cache         | `/tmp/audio_cache`         |
| **model_cache**   | HuggingFace models cache             | `/root/.cache/huggingface` |

## 🚀 Quick Start Commands

```bash
# Start all services
docker compose up

# Start only infrastructure + extraction
docker compose up postgres obtener-artistas obtener-canciones obtener-letras

# Start vectorization pipeline
docker compose up vectorizer-lyrics vectorizer-audio postgre-to-qdrant

# Run tests
docker compose up tests

# View service logs
docker compose logs -f obtener-artistas

# Check service status
docker compose ps

# Clean up all services and volumes
docker compose down -v
```

## 🔐 Environment Variables

All services use `.env` file for configuration:

```env
# Database
POSTGRES_USER=tfm_user
POSTGRES_PASSWORD=tfm_pass_test_12345
POSTGRES_DB=tfm_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# APIs
API_KEY_GENIUS=your-genius-api-key
```

## 📈 Service Statistics

- **Total Containers**: 15
- **Networks**: 1 (tfm_network)
- **Volumes**: 4 (pgdata, qdrant_storage, audio_cache, model_cache)
- **Tests**: 17 passing
- **Exposed Ports**: 3 (5432, 6333, 8080, 8501)

## 🔗 Service Communication

All services communicate via internal `tfm_network`:
- Services discover each other by container name
- Example: `postgres:5432` is accessible as `postgres:5432` from any container
- No port exposure needed for internal communication

## ⚙️ Resource Management

### CPU & Memory Limits (Optional)

You can add resource limits to services in docker-compose.yml:

```yaml
services:
  postgres:
    # ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## 🛠️ Troubleshooting

### Service won't start
```bash
docker compose logs <service-name>
docker compose up --no-deps --build <service-name>
```

### Database connection refused
```bash
docker compose exec postgres pg_isready
docker compose logs postgres
```

### Restart specific service
```bash
docker compose restart <service-name>
```

## 📚 Related Documentation

- [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) - Detailed usage guide
- [MEJORAS_TFM_NAYARE.md](MEJORAS_TFM_NAYARE.md) - Implementation improvements
- [requirements-dev.txt](requirements-dev.txt) - Python dependencies
- [Dockerfile.tests](Dockerfile.tests) - Test container definition

## ✨ Key Features

✅ Complete containerization of all services  
✅ Service dependency management  
✅ Automatic healthchecks  
✅ Persistent volumes for data  
✅ Network isolation with tfm_network  
✅ Environment configuration management  
✅ Integrated testing infrastructure  
✅ Monitoring and visualization services  
✅ Production-ready architecture  

