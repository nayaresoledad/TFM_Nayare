from contextlib import contextmanager

try:
    from psycopg2 import pool
except Exception:
    pool = None


class DatabaseManager:
    """Manages a psycopg2 connection pool. Pool is created lazily on first use.

    This avoids requiring a running Postgres instance at module import time (useful for tests).
    """
    def __init__(self, database_url: str, min_conn: int = 1, max_conn: int = 10):
        self._database_url = database_url
        self._min_conn = min_conn
        self._max_conn = max_conn
        self._pool = None

    def _ensure_pool(self):
        if self._pool is None:
            if pool is None:
                raise RuntimeError("psycopg2.pool is not available; install psycopg2-binary")
            self._pool = pool.SimpleConnectionPool(self._min_conn, self._max_conn, dsn=self._database_url)

    @contextmanager
    def get_connection(self):
        self._ensure_pool()
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
        if self._pool:
            self._pool.closeall()
