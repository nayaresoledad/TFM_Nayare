from contextlib import contextmanager
from psycopg2 import pool


class DatabaseManager:
    def __init__(self, database_url: str, min_conn: int = 1, max_conn: int = 10):
        # psycopg2 expects separate params; simple helper to create pool from URL
        self._pool = pool.SimpleConnectionPool(min_conn, max_conn, dsn=database_url)

    @contextmanager
    def get_connection(self):
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self):
        self._pool.closeall()
