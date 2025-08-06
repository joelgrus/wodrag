from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Get Supabase client (for backward compatibility)."""
    global _supabase_client

    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Missing Supabase credentials. Please set SUPABASE_URL and "
                "SUPABASE_ANON_KEY environment variables."
            )

        _supabase_client = create_client(supabase_url, supabase_key)

    return _supabase_client


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


def reset_client() -> None:
    global _supabase_client
    _supabase_client = None
