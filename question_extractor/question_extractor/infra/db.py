import logging
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from typing import Generator, Any, List, Dict
from .settings import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self) -> None:
        self.dsn = settings.get_db_url()

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection[Any], None, None]:
        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        try:
            yield conn
        finally:
            conn.close()

    def fetch_all(self, query: str, params: tuple[Any, ...] | None = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def inspect_tables(self) -> List[str]:
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        results = self.fetch_all(query)
        return [row['table_name'] for row in results]

    def inspect_columns(self, table_name: str) -> List[Dict[str, Any]]:
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """
        return self.fetch_all(query, (table_name,))

    def execute_script(self, script_path: str) -> None:
        with open(script_path, 'r') as f:
            sql = f.read()
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                conn.commit()


db = Database()
