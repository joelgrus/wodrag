#!/usr/bin/env python3
"""Export data from Supabase for migration to ParadeDB."""

import json
import os
import sys
from datetime import date

from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wodrag.database.client import get_supabase_client

# Load environment variables
load_dotenv()


def export_workouts_to_json(output_file: str = "data/supabase_export.json") -> None:
    """Export all workouts from Supabase to JSON."""

    try:
        client = get_supabase_client()

        # Get total count
        count_result = client.table("workouts").select("id", count="exact").execute()
        total_count = count_result.count

        # Export in batches to handle large datasets
        batch_size = 100
        all_workouts = []

        for offset in range(0, total_count, batch_size):

            result = (
                client.table("workouts")
                .select("*")
                .order("id")
                .limit(batch_size)
                .offset(offset)
                .execute()
            )

            # Convert date objects to strings for JSON serialization
            for workout in result.data:
                if workout.get("date") and isinstance(workout["date"], date):
                    workout["date"] = workout["date"].isoformat()

            all_workouts.extend(result.data)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Write to JSON file
        with open(output_file, "w") as f:
            json.dump(all_workouts, f, indent=2, default=str)


        # Show sample record
        if all_workouts:
            all_workouts[0]

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    export_workouts_to_json()
