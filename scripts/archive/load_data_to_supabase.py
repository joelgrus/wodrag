#!/usr/bin/env python3
"""Load workout data from JSON files into Supabase."""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY "
            "in your .env file or environment variables."
        )

    return create_client(url, key)


def convert_workout_for_db(workout: dict[str, Any]) -> dict[str, Any]:
    """Convert workout data from JSON format to database format."""
    return {
        "date": workout["date"],
        "url": workout.get("url", ""),
        "raw_text": workout["raw_text"],
        "workout": workout["workout"],
        "scaling": workout.get("scaling"),
        "has_video": workout.get("has_video", False),
        "has_article": workout.get("has_article", False),
        "month_file": workout.get("month_file", ""),
    }


def load_workouts_from_json_files(json_dir: Path) -> list[dict[str, Any]]:
    """Load all workouts from JSON files in the given directory."""
    all_workouts = []
    json_files = sorted(json_dir.glob("*.json"))


    for json_file in json_files:

        with open(json_file, encoding="utf-8") as f:
            workouts = json.load(f)

        # Convert each workout to database format
        db_workouts = [convert_workout_for_db(w) for w in workouts]
        all_workouts.extend(db_workouts)

    return all_workouts


def bulk_insert_workouts(
    client: Client, workouts: list[dict[str, Any]], batch_size: int = 1000
) -> None:
    """Insert workouts into Supabase in batches."""
    total_workouts = len(workouts)

    for i in range(0, total_workouts, batch_size):
        batch = workouts[i : i + batch_size]
        i // batch_size + 1
        (total_workouts + batch_size - 1) // batch_size


        try:
            client.table("workouts").insert(batch).execute()
        except Exception:
            # You might want to save failed batches to retry later
            continue


def main() -> None:
    """Main function to load workout data into Supabase."""

    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        return

    try:
        # Initialize Supabase client
        client = get_supabase_client()

        # Load workout data from JSON files
        json_dir = Path("data/processed/json")
        if not json_dir.exists():
            return

        workouts = load_workouts_from_json_files(json_dir)

        # Check if we already have data in the database
        existing_count = client.table("workouts").select("id", count="exact").execute()
        if hasattr(existing_count, "count") and existing_count.count > 0:
            response = input(
                f"\n⚠️  Database already contains {existing_count.count} workouts. Continue? (y/N): "
            )
            if response.lower() != "y":
                return

        # Insert workouts into Supabase
        bulk_insert_workouts(client, workouts)

        # Verify insertion
        client.table("workouts").select("id", count="exact").execute()

    except Exception:
        pass


if __name__ == "__main__":
    main()
