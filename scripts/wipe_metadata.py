#!/usr/bin/env python3
"""
Wipe all metadata from workout records using direct SQL.

This script efficiently resets metadata fields to NULL for all workouts:
- movements, equipment, workout_type, workout_name
- one_sentence_summary, summary_embedding
- workout_embedding (optional)
"""

import os
import sys

from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wodrag.database.client import get_postgres_connection

load_dotenv()


def get_stats():
    """Get database statistics before and after wipe."""
    with get_postgres_connection() as conn, conn.cursor() as cursor:
        # Total workouts
        cursor.execute("SELECT COUNT(*) FROM workouts")
        total = cursor.fetchone()[0]

        # Workouts with any metadata
        cursor.execute("""
                SELECT COUNT(*) FROM workouts
                WHERE movements IS NOT NULL
                   OR equipment IS NOT NULL
                   OR workout_type IS NOT NULL
                   OR workout_name IS NOT NULL
                   OR one_sentence_summary IS NOT NULL
                   OR summary_embedding IS NOT NULL
            """)
        with_metadata = cursor.fetchone()[0]

        return total, with_metadata


def main():

    try:
        # Show current stats
        total_workouts, workouts_with_metadata = get_stats()

        if workouts_with_metadata == 0:
            return

        # Confirm before wiping
        response = input(
            f"\n⚠️  This will wipe metadata from {workouts_with_metadata} workouts. Continue? (y/N): "
        )
        if response.lower() != "y":
            return

        # Wipe metadata
        with get_postgres_connection() as conn, conn.cursor() as cursor:
            sql = """
                UPDATE workouts
                SET
                    movements = NULL,
                    equipment = NULL,
                    workout_type = NULL,
                    workout_name = NULL,
                    one_sentence_summary = NULL,
                    summary_embedding = NULL
                """
            cursor.execute(sql)
            conn.commit()


        # Show final stats
        total_workouts, workouts_with_metadata = get_stats()

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
