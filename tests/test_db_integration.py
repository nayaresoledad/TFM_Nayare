"""
Integration tests for database connectivity and operations.
Tests real connection to PostgreSQL container and CRUD operations.
"""
import pytest
import os
from common.db import DatabaseManager
from common.config import config


@pytest.fixture
def db_manager():
    """Fixture to get a database manager instance."""
    # DatabaseManager requires database_url from config
    manager = DatabaseManager(config.database_url)
    yield manager
    # Cleanup: close connection pool after tests
    if hasattr(manager, '_pool') and manager._pool is not None:
        manager._pool.closeall()


@pytest.fixture
def test_table(db_manager):
    """Fixture to create a test table and clean up after tests."""
    table_name = "test_integration_table"
    
    # Create test table
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    yield table_name
    
    # Cleanup: drop test table
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.commit()


class TestDatabaseConnection:
    """Test basic database connectivity."""
    
    def test_connection_successful(self, db_manager):
        """Test that database connection can be established."""
        try:
            with db_manager.get_connection() as conn:
                assert conn is not None
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()
                    assert version is not None
                    assert "PostgreSQL" in version[0]
        except Exception as e:
            pytest.fail(f"Failed to connect to database: {e}")
    
    def test_connection_context_manager(self, db_manager):
        """Test that connection context manager works correctly."""
        with db_manager.get_connection() as conn:
            assert conn is not None
            # Connection should not be closed after context manager
            # (it goes back to pool)
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as num")
                result = cur.fetchone()
                assert result[0] == 1


class TestDatabaseOperations:
    """Test CRUD operations on the database."""
    
    def test_insert_single_row(self, db_manager, test_table):
        """Test inserting a single row into the test table."""
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("Test Record", "This is a test record")
                )
                conn.commit()
                
                # Verify insertion
                cur.execute(f"SELECT COUNT(*) FROM {test_table}")
                count = cur.fetchone()[0]
                assert count == 1
    
    def test_insert_multiple_rows(self, db_manager, test_table):
        """Test inserting multiple rows."""
        data = [
            ("Record 1", "First test record"),
            ("Record 2", "Second test record"),
            ("Record 3", "Third test record"),
        ]
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                for name, desc in data:
                    cur.execute(
                        f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                        (name, desc)
                    )
                conn.commit()
                
                # Verify all rows inserted
                cur.execute(f"SELECT COUNT(*) FROM {test_table}")
                count = cur.fetchone()[0]
                assert count == 3
    
    def test_select_rows(self, db_manager, test_table):
        """Test selecting rows from the table."""
        # Insert test data
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("Test 1", "Description 1")
                )
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("Test 2", "Description 2")
                )
                conn.commit()
        
        # Query the data
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT id, name, description FROM {test_table} ORDER BY id")
                rows = cur.fetchall()
                assert len(rows) == 2
                assert rows[0][1] == "Test 1"
                assert rows[1][1] == "Test 2"
    
    def test_update_row(self, db_manager, test_table):
        """Test updating a row in the table."""
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Insert
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("Original", "Original description")
                )
                conn.commit()
                
                # Update
                cur.execute(
                    f"UPDATE {test_table} SET description = %s WHERE name = %s",
                    ("Updated description", "Original")
                )
                conn.commit()
                
                # Verify update
                cur.execute(f"SELECT description FROM {test_table} WHERE name = %s", ("Original",))
                result = cur.fetchone()
                assert result[0] == "Updated description"
    
    def test_delete_row(self, db_manager, test_table):
        """Test deleting a row from the table."""
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Insert multiple rows
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("To Delete", "Will be deleted")
                )
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("To Keep", "Will be kept")
                )
                conn.commit()
                
                # Delete one row
                cur.execute(f"DELETE FROM {test_table} WHERE name = %s", ("To Delete",))
                conn.commit()
                
                # Verify deletion
                cur.execute(f"SELECT COUNT(*) FROM {test_table}")
                count = cur.fetchone()[0]
                assert count == 1
                
                cur.execute(f"SELECT name FROM {test_table}")
                remaining = cur.fetchone()[0]
                assert remaining == "To Keep"


class TestDatabaseTransactions:
    """Test transaction handling."""
    
    def test_commit_works(self, db_manager, test_table):
        """Test that commits are properly applied."""
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("Committed", "Should persist")
                )
                conn.commit()
        
        # Verify in a new connection
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT name FROM {test_table} WHERE name = %s", ("Committed",))
                result = cur.fetchone()
                assert result is not None
                assert result[0] == "Committed"
    
    def test_rollback_works(self, db_manager, test_table):
        """Test that rollbacks prevent writes."""
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("Not Committed", "Should not persist")
                )
                # Rollback without commit
                conn.rollback()
        
        # Verify in a new connection - should not exist
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT name FROM {test_table} WHERE name = %s", ("Not Committed",))
                result = cur.fetchone()
                assert result is None


class TestDatabaseErrorHandling:
    """Test error handling in database operations."""
    
    def test_invalid_table_error(self, db_manager):
        """Test that querying non-existent table raises error."""
        with pytest.raises(Exception):  # psycopg2.ProgrammingError
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM nonexistent_table")
                    cur.fetchall()
    
    def test_constraint_violation_error(self, db_manager, test_table):
        """Test that constraint violations are properly raised."""
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Insert a valid row
                cur.execute(
                    f"INSERT INTO {test_table} (name, description) VALUES (%s, %s)",
                    ("Valid", "Valid record")
                )
                conn.commit()
        
        # Try to insert NULL into NOT NULL column - should fail
        with pytest.raises(Exception):  # psycopg2.IntegrityError
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"INSERT INTO {test_table} (name) VALUES (NULL)")
                    conn.commit()
    
    def test_connection_reuse_after_error(self, db_manager, test_table):
        """Test that connection pool recovers after an error."""
        # First, cause an error
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("INVALID SQL SYNTAX HERE")
        except Exception:
            pass  # Expected error
        
        # Should still be able to use a connection from the pool
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {test_table}")
                    count = cur.fetchone()[0]
                    assert count >= 0  # Should work fine
        except Exception as e:
            pytest.fail(f"Connection pool should recover after error: {e}")
