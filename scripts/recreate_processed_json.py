#!/usr/bin/env python3
"""Recreate processed JSON files from database data."""

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


def get_all_workouts_from_db() -> list[dict[str, Any]]:
    """Fetch all workouts from the database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")
    
    with psycopg2.connect(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    date,
                    url,
                    raw_text,
                    workout,
                    scaling,
                    has_video,
                    has_article,
                    month_file
                FROM workouts
                ORDER BY date
            """)
            return [dict(row) for row in cur.fetchall()]


def group_workouts_by_month(workouts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group workouts by month based on their date."""
    grouped = defaultdict(list)
    
    for workout in workouts:
        # Extract year-month from date
        date_str = workout["date"].strftime("%Y-%m")
        
        # Convert to the expected JSON format
        json_workout = {
            "date": workout["date"].strftime("%Y-%m-%d"),
            "url": workout.get("url", ""),
            "raw_text": workout["raw_text"],
            "workout": workout["workout"],
            "scaling": workout.get("scaling"),
            "has_video": workout.get("has_video", False),
            "has_article": workout.get("has_article", False),
            "month_file": workout.get("month_file", f"{date_str}.html"),
        }
        
        grouped[date_str].append(json_workout)
    
    return grouped


def recreate_processed_json(output_dir: Path = Path("data/processed/json")) -> None:
    """Recreate the processed JSON files from database data."""
    print("🔄 Fetching workouts from database...")
    workouts = get_all_workouts_from_db()
    print(f"✅ Found {len(workouts)} workouts in database")
    
    print("📅 Grouping workouts by month...")
    grouped_workouts = group_workouts_by_month(workouts)
    print(f"✅ Grouped into {len(grouped_workouts)} month files")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"💾 Writing JSON files to {output_dir}...")
    total_written = 0
    
    for month, month_workouts in sorted(grouped_workouts.items()):
        output_file = output_dir / f"{month}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(month_workouts, f, indent=2, ensure_ascii=False)
        
        print(f"  📄 {output_file.name}: {len(month_workouts)} workouts")
        total_written += len(month_workouts)
    
    print(f"✅ Successfully recreated {len(grouped_workouts)} JSON files")
    print(f"📊 Total workouts written: {total_written}")
    
    # Verify the structure
    sample_file = next(iter(grouped_workouts.keys()))
    sample_path = output_dir / f"{sample_file}.json"
    print(f"\n🔍 Sample structure from {sample_path.name}:")
    
    with open(sample_path, encoding="utf-8") as f:
        sample_data = json.load(f)
    
    if sample_data:
        print("  Fields in each workout:")
        for key in sample_data[0].keys():
            print(f"    - {key}")


if __name__ == "__main__":
    recreate_processed_json()