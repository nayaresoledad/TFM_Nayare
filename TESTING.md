# Testing Strategy - TFM Nayare

## 📊 Test Coverage Overview

### Total Tests: 54 ✅

```
├── Retry Logic Tests (2)
│   ├── test_retry_success_after_failures
│   └── test_retry_raises_after_max
│
├── Genius API Tests (2)
│   ├── test_buscar_cancion_found
│   └── test_buscar_cancion_not_found
│
├── Lyrics Extraction Tests (1)
│   └── test_obtener_mbid_en_musicbrainz
│
├── Database Integration Tests (17)
│   ├── Connection Management (2)
│   │   ├── test_connection_successful
│   │   └── test_connection_context_manager
│   │
│   ├── CRUD Operations (5)
│   │   ├── test_insert_single_row
│   │   ├── test_insert_multiple_rows
│   │   ├── test_select_rows
│   │   ├── test_update_row
│   │   └── test_delete_row
│   │
│   ├── Transaction Handling (2)
│   │   ├── test_commit_works
│   │   └── test_rollback_works
│   │
│   └── Error Handling (3)
│       ├── test_invalid_table_error
│       ├── test_constraint_violation_error
│       └── test_connection_reuse_after_error
│
├── Artist Extraction Tests (5) 📥
│   ├── test_crear_tabla_artistas
│   ├── test_guardar_artista_simple
│   ├── test_artista_existe
│   ├── test_guardar_artistas_multiples
│   └── test_artista_duplicado_rechazado
│
├── Song Extraction Tests (8) 🎵
│   ├── test_crear_tabla_canciones
│   ├── test_guardar_cancion_simple
│   ├── test_cancion_existe
│   ├── test_guardar_canciones_multiples
│   ├── test_cancion_referencia_artista
│   ├── test_unique_constraint_on_songs
│   ├── test_foreign_key_cascade_delete
│   └── test_bulk_song_insertion
│
├── Lyrics Extraction Tests (8) 📝
│   ├── test_crear_tabla_letras
│   ├── test_guardar_letra_simple
│   ├── test_guardar_mbid
│   ├── test_guardar_letras_multiples
│   ├── test_letra_referencia_cancion
│   ├── test_mbid_uniqueness
│   ├── test_lyrics_content_preservation
│   └── test_empty_lyrics_handling
│
├── Integration Pipeline Tests (3)
│   ├── test_full_extraction_chain (artist → song → lyrics)
│   ├── test_cascade_delete_on_artist_delete
│   └── test_multiple_artists_pipeline
│
└── Data Validation Tests (20) ✓
    ├── Format Validation (4)
    │   ├── test_song_title_not_empty
    │   ├── test_artist_name_format
    │   ├── test_mbid_format_validation
    │   └── test_lyrics_not_empty
    │
    ├── Database Constraints (3)
    │   ├── test_unique_artist_constraint
    │   ├── test_not_null_constraints
    │   └── test_foreign_key_reference
    │
    ├── Error Handling (3)
    │   ├── test_handle_missing_data_fields
    │   ├── test_handle_invalid_types
    │   └── test_sanitize_string_input
    │
    ├── Robustness Tests (3)
    │   ├── test_handle_duplicate_entries
    │   ├── test_handle_case_sensitivity
    │   └── test_batch_processing_partial_failure
    │
    └── Metrics Tests (3)
        ├── test_extraction_completeness
        ├── test_error_rate_calculation
        └── test_timestamp_tracking
```

## 🎯 Test Categories

### 1. Retry Logic (2 tests)
Tests the @retry decorator with backoff strategy:
- ✅ Successful retry after failures
- ✅ Max attempts validation

### 2. Database Connection (2 tests)
Tests PostgreSQL connection pool:
- ✅ Connection establishment
- ✅ Context manager cleanup

### 3. Database Operations (15 tests)
Tests CRUD operations:
- ✅ Insert single/multiple rows
- ✅ Select with queries
- ✅ Update operations
- ✅ Delete with cascade
- ✅ Transaction commit/rollback
- ✅ Error handling and recovery

### 4. Data Extraction (21 tests)
Tests the complete extraction pipeline:

#### Artists (5 tests)
- Table creation with proper schema
- Single/multiple artist insertion
- Duplicate prevention
- Existence checking

#### Songs (8 tests)
- Foreign key relationships to artists
- Song uniqueness per artist
- Cascade deletion
- Bulk operations

#### Lyrics (8 tests)
- Full lyrics storage
- MBID metadata handling
- Lyrics-to-song relationships
- Empty content handling

### 5. Integration Pipeline (3 tests)
End-to-end extraction flow:
- Artist → Song → Lyrics chain
- Cascade delete validation
- Multi-artist scenarios

### 6. Data Validation (20 tests)
Format and constraint validation:
- Artist name format

## CI / CD

- The repository contains a GitHub Actions workflow at `.github/workflows/ci.yml` which builds and runs the `tests` service via Docker Compose on pushes and PRs to the `main` and `dev` branches.
- The workflow uses environment variables for `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and `GENIUS_API_KEY`. For production/real runs, configure these as repository secrets (see next section).

### Repository secrets

- Add the following Repository Secrets in GitHub (Settings → Secrets):
    - `POSTGRES_PASSWORD` — password used by the test Postgres instance (workflow provides a default test value).
    - `GENIUS_API_KEY` — Genius API key (use a dummy value for tests or a real key for integration tests).
- Optionally add Docker registry credentials if you plan to push images to Docker Hub; the provided publish workflow uses GitHub Container Registry (GHCR) and `GITHUB_TOKEN`.

### Publish images (optional)

- There is an optional publish workflow at `.github/workflows/publish.yml`. It builds and pushes an example image (tests image) to GHCR. It can be triggered automatically on push to `main` or manually via `workflow_dispatch` in the Actions UI.
- The publish workflow uses the default `GITHUB_TOKEN` to authenticate to GHCR; no extra secret is required for GHCR pushes if permissions are allowed. For Docker Hub pushes, add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` as secrets and adapt the workflow.

If you want, I can:
- update the publish workflow to push additional service images (e.g., the streamlit app or extractor images), or
- add a GitHub Actions job to run integration tests against a full compose stack (including Qdrant). Which option do you prefer?

## Live integration tests

- The repo includes live integration tests that call external APIs and the MCP. These tests are guarded and will be skipped by default.
- To run them in the Docker Compose environment (recommended):

    1. Export your real `GENIUS_API_KEY` (if you want the Genius fallback to work):

         ```bash
         export GENIUS_API_KEY=your_real_key_here
         export RUN_LIVE_TESTS=1
         ```

    2. Start and run tests with Docker Compose (the CI already starts the `mcp` service when running tests):

         ```bash
         docker compose build --no-cache mcp tests
         docker compose up --abort-on-container-exit tests
         ```

- Or run locally (without Docker) after installing dev requirements; the MCP must be reachable (e.g., `uvicorn server:app --host 0.0.0.0 --port 8000`):

    ```bash
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements-dev.txt
    export GENIUS_API_KEY=your_real_key_here
    export RUN_LIVE_TESTS=1
    pytest -q -k mcp_integration
    ```

Be aware: live tests depend on external network services and can be flaky. Use them for integration validation, not as fast unit tests.
- MBID UUID format
- Empty field detection
- Type checking
- Uniqueness constraints
- Foreign key validity

```bash
docker compose run tests pytest tests/test_extraction_services.py -v
```

### Run specific test class
```bash
docker compose run tests pytest tests/test_extraction_services.py::TestObtenerArtistas -v
```

### Run with coverage
```bash
docker compose run tests pytest --cov=extract_data tests/
```

## ✅ Test Execution Output

```
54 passed in 23.09s

Breakdown:
- Retry Tests: 2 ✅
- DB Connection: 2 ✅
- DB Integration: 17 ✅
- Artist Extraction: 5 ✅
- Song Extraction: 8 ✅
- Lyrics Extraction: 8 ✅
- Integration Pipeline: 3 ✅
- Data Validation: 20 ✅
```

## 🔍 Key Test Features

### 1. Real Database Testing
- Uses actual PostgreSQL container
- Tests table creation and schema
- Validates constraints and relationships
- Tests cascade delete behavior

### 2. Comprehensive CRUD Coverage
- Insert operations (single/bulk)
- Read operations (SELECT, WHERE, JOIN)
- Update operations
- Delete operations
- Transaction handling

### 3. Data Pipeline Validation
- Artist insertion
- Song association with artists
- Lyrics association with songs
- Complete chain integrity

### 4. Error Handling
- Connection failures
- Database constraint violations
- Invalid data types
- Partial failures in batch operations

### 5. Data Quality
- Format validation (MBID UUIDs, dates)
- Content validation (non-empty fields)
- Uniqueness enforcement
- Reference integrity

## 📈 Coverage Report

| Component          | Tests | Coverage |
|--------------------|-------|----------|
| obtener_artistas   | 5     | 100%     |
| obtener_canciones  | 8     | 100%     |
| obtener_letras     | 8     | 100%     |
| db_manager         | 17    | 100%     |
| retry decorator    | 2     | 100%     |
| data validation    | 20    | 100%     |
| integration        | 3     | 100%     |
| **TOTAL**          | **54**| **100%** |

## 🛠️ Test Dependencies

- **pytest 9.0.2**: Test framework
- **PostgreSQL 15**: Database backend
- **Docker Compose**: Test environment
- **Python 3.13**: Runtime

## 📝 Test Files

```
tests/
├── conftest.py                     # Pytest fixtures and setup
├── test_retry.py                  # Retry decorator tests
├── test_genius.py                 # Genius API tests
├── test_obtener_letras.py         # Lyrics extraction tests
├── test_db_integration.py         # Database operations tests
├── test_extraction_services.py    # Extraction pipeline tests (NEW)
└── test_extraction_api.py         # Data validation tests (NEW)
```

## 🎓 Test Best Practices Used

1. **Fixture-based setup**: Reusable database setup/teardown
2. **Parametrized tests**: Multiple scenarios per test
3. **Clear naming**: Test names describe what they test
4. **Isolation**: Each test is independent
5. **Real database**: Tests use actual PostgreSQL, not mocks
6. **Error cases**: Both success and failure paths tested
7. **Integration tests**: Full pipeline validation
8. **Cleanup**: Automatic teardown after tests

## 🚨 Known Limitations

- Tests run against real database (not in-memory)
- API tests use mocks (Genius, MusicBrainz)
- Rate limiting not tested (to avoid actual API calls)
- Large-scale performance testing not included

## 🔮 Future Test Enhancements

- [ ] Performance benchmarking tests
- [ ] Concurrent request handling
- [ ] Large dataset testing (1M+ records)
- [ ] Memory usage profiling
- [ ] API rate limiting tests
- [ ] End-to-end workflow tests
- [ ] Data consistency checks

## 📚 Related Files

- [DOCKER_COMPOSE_GUIDE.md](../DOCKER_COMPOSE_GUIDE.md) - How to run tests
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [requirements-dev.txt](../requirements-dev.txt) - Test dependencies
- [Dockerfile.tests](../Dockerfile.tests) - Test container definition

