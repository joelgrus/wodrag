from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def get_postgres_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Get direct PostgreSQL connection for ParadeDB."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment")

    conn = psycopg2.connect(db_url)
    try:
        yield conn
    finally:
        conn.close()
