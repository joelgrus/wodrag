from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

import duckdb
from dotenv import load_dotenv

from .models import Workout

load_dotenv()


class DuckDBQueryService:
    """Service for read-only querying of the PostgreSQL database using DuckDB."""

    def __init__(self) -> None:
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment")

    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get DuckDB connection with PostgreSQL extension."""
        conn = duckdb.connect()
        try:
            # Install and load PostgreSQL extension
            conn.execute("INSTALL postgres")
            conn.execute("LOAD postgres")

            # Attach PostgreSQL database
            conn.execute(f"ATTACH '{self.db_url}' AS pg_db (TYPE postgres)")

            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a read-only query and return results as list of dictionaries."""
        with self.get_connection() as conn:
            result = conn.execute(query).fetchall()
            columns = [desc[0] for desc in conn.description] if conn.description else []
            return [dict(zip(columns, row, strict=True)) for row in result]

    def get_workouts_by_query(self, query: str) -> list[Workout]:
        """Execute a query that returns workout data and convert to Workout objects."""
        results = self.execute_query(query)
        return [Workout.from_dict(row) for row in results]

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """Get schema information for a table."""
        query = f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM pg_db.information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        return self.execute_query(query)

    def get_available_tables(self) -> list[str]:
        """Get list of available tables in the database."""
        query = """
        SELECT table_name 
        FROM pg_db.information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        results = self.execute_query(query)
        return [row["table_name"] for row in results]
