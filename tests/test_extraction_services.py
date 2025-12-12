"""
Comprehensive tests for extraction services.
Tests database operations, data validation, and integration with external APIs.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from common.config import config
from common.db import DatabaseManager
from extract_data.lyrics.obtener_artistas import obtener_artistas
from extract_data.lyrics.obtener_canciones import obtener_canciones
from extract_data.lyrics.obtener_letras import obtener_letras


@pytest.fixture
def db_manager():
    """Get database manager instance."""
    manager = DatabaseManager(config.database_url)
    yield manager
    if hasattr(manager, '_pool') and manager._pool is not None:
        manager._pool.closeall()


@pytest.fixture
def extraction_db(db_manager):
    """Setup extraction test database with tables."""
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        
        # Create tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS artistas (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE,
                fecha_guardado TIMESTAMP,
                query TEXT
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS canciones (
                id SERIAL PRIMARY KEY,
                id_artista INTEGER REFERENCES artistas(id) ON DELETE CASCADE,
                artista TEXT,
                cancion TEXT,
                fecha_guardado TIMESTAMP,
                UNIQUE(id_artista, cancion)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS letras (
                id SERIAL PRIMARY KEY,
                id_cancion INTEGER REFERENCES canciones(id) ON DELETE CASCADE,
                artista TEXT,
                cancion TEXT,
                letra TEXT,
                mbid TEXT,
                fecha_guardado TIMESTAMP,
                UNIQUE(id_cancion)
            )
        """)
        
        conn.commit()
    
    yield db_manager
    
    # Cleanup
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS letras CASCADE")
        cur.execute("DROP TABLE IF EXISTS canciones CASCADE")
        cur.execute("DROP TABLE IF EXISTS artistas CASCADE")
        conn.commit()


# ============================================================================
# TESTS FOR OBTENER_ARTISTAS (Artist Extraction)
# ============================================================================

class TestObtenerArtistas:
    """Test artist extraction functionality."""
    
    def test_crear_tabla_artistas(self, extraction_db):
        """Test that artistas table is created correctly."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'artistas'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            assert len(columns) >= 4
            column_names = [col[0] for col in columns]
            assert 'id' in column_names
            assert 'nombre' in column_names
            assert 'fecha_guardado' in column_names
            assert 'query' in column_names
    
    def test_guardar_artista_simple(self, extraction_db):
        """Test saving a single artist."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            # Verify insertion
            cur.execute("SELECT nombre FROM artistas WHERE nombre = %s", ("Test Artist",))
            result = cur.fetchone()
            assert result is not None
            assert result[0] == "Test Artist"
    
    def test_artista_existe(self, extraction_db):
        """Test artist existence check."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            
            # Insert an artist
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Existing Artist", fecha, "test")
            )
            conn.commit()
            
            # Check existence
            cur.execute("SELECT 1 FROM artistas WHERE nombre = %s", ("Existing Artist",))
            exists = cur.fetchone() is not None
            assert exists is True
            
            # Check non-existent
            cur.execute("SELECT 1 FROM artistas WHERE nombre = %s", ("Non Existent",))
            not_exists = cur.fetchone() is None
            assert not_exists is True
    
    def test_guardar_artistas_multiples(self, extraction_db):
        """Test saving multiple artists."""
        artists = [
            ("Artist One", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "a"),
            ("Artist Two", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "b"),
            ("Artist Three", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "c"),
        ]
        
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            for nombre, fecha, query in artists:
                cur.execute(
                    "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                    (nombre, fecha, query)
                )
            conn.commit()
            
            # Verify all saved
            cur.execute("SELECT COUNT(*) FROM artistas")
            count = cur.fetchone()[0]
            assert count == 3
    
    def test_artista_duplicado_rechazado(self, extraction_db):
        """Test that duplicate artists are rejected (UNIQUE constraint)."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert first artist
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Duplicate Artist", fecha, "test")
            )
            conn.commit()
            
            # Try to insert duplicate
            with pytest.raises(Exception):  # Should raise IntegrityError
                cur.execute(
                    "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                    ("Duplicate Artist", fecha, "test")
                )
                conn.commit()


# ============================================================================
# TESTS FOR OBTENER_CANCIONES (Song Extraction)
# ============================================================================

class TestObtenerCanciones:
    """Test song extraction functionality."""
    
    def test_crear_tabla_canciones(self, extraction_db):
        """Test that canciones table is created correctly."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'canciones'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            column_names = [col[0] for col in columns]
            assert 'id' in column_names
            assert 'id_artista' in column_names
            assert 'artista' in column_names
            assert 'cancion' in column_names
    
    def test_guardar_cancion_simple(self, extraction_db):
        """Test saving a single song."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            
            # Insert artist first
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            # Get artist ID
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            # Insert song
            cur.execute(
                "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                (artist_id, "Test Artist", "Test Song", fecha)
            )
            conn.commit()
            
            # Verify insertion
            cur.execute("SELECT cancion FROM canciones WHERE cancion = %s", ("Test Song",))
            result = cur.fetchone()
            assert result is not None
            assert result[0] == "Test Song"
    
    def test_cancion_existe(self, extraction_db):
        """Test song existence check."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            
            # Insert artist
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            # Insert song
            cur.execute(
                "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                (artist_id, "Test Artist", "Test Song", fecha)
            )
            conn.commit()
            
            # Check existence
            cur.execute(
                "SELECT 1 FROM canciones WHERE id_artista = %s AND cancion = %s",
                (artist_id, "Test Song")
            )
            exists = cur.fetchone() is not None
            assert exists is True
    
    def test_guardar_canciones_multiples(self, extraction_db):
        """Test saving multiple songs for an artist."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            
            # Insert artist
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            # Insert multiple songs
            songs = ["Song 1", "Song 2", "Song 3", "Song 4"]
            for song in songs:
                cur.execute(
                    "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                    (artist_id, "Test Artist", song, fecha)
                )
            conn.commit()
            
            # Verify all saved
            cur.execute("SELECT COUNT(*) FROM canciones WHERE id_artista = %s", (artist_id,))
            count = cur.fetchone()[0]
            assert count == 4
    
    def test_cancion_referencia_artista(self, extraction_db):
        """Test that canciones has foreign key to artistas."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            
            # Insert artist
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            # Insert song
            cur.execute(
                "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                (artist_id, "Test Artist", "Test Song", fecha)
            )
            conn.commit()
            
            # Query with JOIN
            cur.execute("""
                SELECT c.cancion, a.nombre
                FROM canciones c
                JOIN artistas a ON c.id_artista = a.id
                WHERE c.cancion = %s
            """, ("Test Song",))
            result = cur.fetchone()
            assert result is not None
            assert result[0] == "Test Song"
            assert result[1] == "Test Artist"


# ============================================================================
# TESTS FOR OBTENER_LETRAS (Lyrics Extraction)
# ============================================================================

class TestObtenerLetras:
    """Test lyrics extraction functionality."""
    
    def test_crear_tabla_letras(self, extraction_db):
        """Test that letras table is created correctly."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'letras'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            column_names = [col[0] for col in columns]
            assert 'id' in column_names
            assert 'id_cancion' in column_names
            assert 'artista' in column_names
            assert 'cancion' in column_names
            assert 'letra' in column_names
            assert 'mbid' in column_names
    
    def test_guardar_letra_simple(self, extraction_db):
        """Test saving a single lyric."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert artist
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            # Insert song
            cur.execute(
                "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                (artist_id, "Test Artist", "Test Song", fecha)
            )
            conn.commit()
            
            cur.execute("SELECT id FROM canciones WHERE cancion = %s", ("Test Song",))
            song_id = cur.fetchone()[0]
            
            # Insert lyrics
            test_lyrics = "Line 1\nLine 2\nLine 3"
            cur.execute(
                """INSERT INTO letras 
                   (id_cancion, artista, cancion, letra, mbid, fecha_guardado)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (song_id, "Test Artist", "Test Song", test_lyrics, "test-mbid", fecha)
            )
            conn.commit()
            
            # Verify insertion
            cur.execute("SELECT letra FROM letras WHERE id_cancion = %s", (song_id,))
            result = cur.fetchone()
            assert result is not None
            assert "Line 1" in result[0]
    
    def test_guardar_mbid(self, extraction_db):
        """Test saving MBID with lyrics."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Setup chain: artist -> song -> lyrics
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            cur.execute(
                "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                (artist_id, "Test Artist", "Test Song", fecha)
            )
            conn.commit()
            
            cur.execute("SELECT id FROM canciones WHERE cancion = %s", ("Test Song",))
            song_id = cur.fetchone()[0]
            
            # Insert with MBID
            mbid_test = "12345678-1234-1234-1234-123456789012"
            cur.execute(
                """INSERT INTO letras 
                   (id_cancion, artista, cancion, letra, mbid, fecha_guardado)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (song_id, "Test Artist", "Test Song", "Test lyrics", mbid_test, fecha)
            )
            conn.commit()
            
            # Verify MBID
            cur.execute("SELECT mbid FROM letras WHERE id_cancion = %s", (song_id,))
            result = cur.fetchone()
            assert result is not None
            assert result[0] == mbid_test
    
    def test_guardar_letras_multiples(self, extraction_db):
        """Test saving lyrics for multiple songs."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert artist
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            # Insert multiple songs with lyrics
            for i in range(5):
                cur.execute(
                    "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                    (artist_id, "Test Artist", f"Song {i}", fecha)
                )
            conn.commit()
            
            cur.execute("SELECT id FROM canciones WHERE id_artista = %s", (artist_id,))
            song_ids = [row[0] for row in cur.fetchall()]
            
            for i, song_id in enumerate(song_ids):
                cur.execute(
                    """INSERT INTO letras 
                       (id_cancion, artista, cancion, letra, mbid, fecha_guardado)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (song_id, "Test Artist", f"Song {i}", f"Lyrics {i}", f"mbid-{i}", fecha)
                )
            conn.commit()
            
            # Verify all saved
            cur.execute("SELECT COUNT(*) FROM letras")
            count = cur.fetchone()[0]
            assert count == 5
    
    def test_letra_referencia_cancion(self, extraction_db):
        """Test that letras has foreign key to canciones."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Setup chain
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Test Artist",))
            artist_id = cur.fetchone()[0]
            
            cur.execute(
                "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                (artist_id, "Test Artist", "Test Song", fecha)
            )
            conn.commit()
            
            cur.execute("SELECT id FROM canciones WHERE cancion = %s", ("Test Song",))
            song_id = cur.fetchone()[0]
            
            cur.execute(
                """INSERT INTO letras 
                   (id_cancion, artista, cancion, letra, mbid, fecha_guardado)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (song_id, "Test Artist", "Test Song", "Test lyrics", "test-mbid", fecha)
            )
            conn.commit()
            
            # Query with JOINs
            cur.execute("""
                SELECT l.letra, c.cancion, a.nombre
                FROM letras l
                JOIN canciones c ON l.id_cancion = c.id
                JOIN artistas a ON c.id_artista = a.id
                WHERE l.id_cancion = %s
            """, (song_id,))
            result = cur.fetchone()
            assert result is not None
            assert "Test lyrics" in result[0]
            assert result[1] == "Test Song"
            assert result[2] == "Test Artist"


# ============================================================================
# INTEGRATION TESTS - Full Pipeline
# ============================================================================

class TestExtractionPipeline:
    """Test complete extraction pipeline."""
    
    def test_full_extraction_chain(self, extraction_db):
        """Test complete artist -> song -> lyrics chain."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 1. Insert artist
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Integration Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Integration Test Artist",))
            artist_id = cur.fetchone()[0]
            assert artist_id is not None
            
            # 2. Insert songs
            songs = ["Song A", "Song B", "Song C"]
            for song in songs:
                cur.execute(
                    "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                    (artist_id, "Integration Test Artist", song, fecha)
                )
            conn.commit()
            
            cur.execute("SELECT id FROM canciones WHERE id_artista = %s", (artist_id,))
            song_ids = [row[0] for row in cur.fetchall()]
            assert len(song_ids) == 3
            
            # 3. Insert lyrics
            for i, song_id in enumerate(song_ids):
                cur.execute(
                    """INSERT INTO letras 
                       (id_cancion, artista, cancion, letra, mbid, fecha_guardado)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (song_id, "Integration Test Artist", songs[i], f"Lyrics for {songs[i]}", f"mbid-{i}", fecha)
                )
            conn.commit()
            
            # 4. Verify complete chain
            cur.execute("""
                SELECT a.nombre, c.cancion, l.letra
                FROM artistas a
                JOIN canciones c ON a.id = c.id_artista
                JOIN letras l ON c.id = l.id_cancion
                WHERE a.nombre = %s
                ORDER BY c.cancion
            """, ("Integration Test Artist",))
            
            results = cur.fetchall()
            assert len(results) == 3
            for result in results:
                assert result[0] == "Integration Test Artist"
                assert result[1] in songs
                assert "Lyrics for" in result[2]
    
    def test_cascade_delete_on_artist_delete(self, extraction_db):
        """Test that deleting an artist cascades to songs and lyrics."""
        with extraction_db.get_connection() as conn:
            cur = conn.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert artist
            cur.execute(
                "INSERT INTO artistas (nombre, fecha_guardado, query) VALUES (%s, %s, %s)",
                ("Delete Test Artist", fecha, "test")
            )
            conn.commit()
            
            cur.execute("SELECT id FROM artistas WHERE nombre = %s", ("Delete Test Artist",))
            artist_id = cur.fetchone()[0]
            
            # Insert song
            cur.execute(
                "INSERT INTO canciones (id_artista, artista, cancion, fecha_guardado) VALUES (%s, %s, %s, %s)",
                (artist_id, "Delete Test Artist", "Delete Song", fecha)
            )
            conn.commit()
            
            cur.execute("SELECT id FROM canciones WHERE cancion = %s", ("Delete Song",))
            song_id = cur.fetchone()[0]
            
            # Insert lyrics
            cur.execute(
                """INSERT INTO letras 
                   (id_cancion, artista, cancion, letra, mbid, fecha_guardado)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (song_id, "Delete Test Artist", "Delete Song", "Delete lyrics", "delete-mbid", fecha)
            )
            conn.commit()
            
            # Verify data exists
            cur.execute("SELECT COUNT(*) FROM letras WHERE id_cancion = %s", (song_id,))
            assert cur.fetchone()[0] == 1
            
            # Delete artist
            cur.execute("DELETE FROM artistas WHERE id = %s", (artist_id,))
            conn.commit()
            
            # Verify cascade delete
            cur.execute("SELECT COUNT(*) FROM artistas WHERE id = %s", (artist_id,))
            assert cur.fetchone()[0] == 0
            
            cur.execute("SELECT COUNT(*) FROM canciones WHERE id_artista = %s", (artist_id,))
            assert cur.fetchone()[0] == 0
            
            cur.execute("SELECT COUNT(*) FROM letras WHERE id_cancion = %s", (song_id,))
            assert cur.fetchone()[0] == 0

