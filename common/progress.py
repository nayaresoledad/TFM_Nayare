from enum import Enum

class ProgressType(Enum):
    ARTISTAS = 'artistas'
    CANCIONES = 'canciones'
    LETRAS = 'letras'
    VECTORS = 'vectors'


class ProgressManager:
    TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS progress_tracking (
        id SERIAL PRIMARY KEY,
        task_type VARCHAR(50) UNIQUE NOT NULL,
        current_offset INTEGER DEFAULT 0,
        total_items INTEGER DEFAULT 0,
        last_processed_id INTEGER,
        status VARCHAR(20) DEFAULT 'running',
        error_message TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_table()

    def _ensure_table(self):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(self.TABLE_SQL)
            cur.close()

    def get_progress(self, task_type: ProgressType):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT current_offset, total_items, last_processed_id, status, error_message FROM progress_tracking WHERE task_type = %s", (task_type.value,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return {'current_offset': 0, 'total_items': 0, 'last_processed_id': None, 'status': 'running', 'error_message': None}
            return {'current_offset': row[0], 'total_items': row[1], 'last_processed_id': row[2], 'status': row[3], 'error_message': row[4]}

    def update_progress(self, task_type: ProgressType, current_offset: int, total_items: int = None, last_processed_id: int = None, status: str = None, error_message: str = None):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO progress_tracking (task_type, current_offset, total_items, last_processed_id, status, error_message, updated_at)
                VALUES (%s, %s, %s, %s, COALESCE(%s, 'running'), %s, CURRENT_TIMESTAMP)
                ON CONFLICT (task_type) DO UPDATE SET
                    current_offset = EXCLUDED.current_offset,
                    total_items = COALESCE(EXCLUDED.total_items, progress_tracking.total_items),
                    last_processed_id = EXCLUDED.last_processed_id,
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (task_type.value, current_offset, total_items, last_processed_id, status, error_message)
            )
            cur.close()
