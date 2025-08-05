from __future__ import annotations

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
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


def reset_client() -> None:
    global _supabase_client
    _supabase_client = None
