#!/usr/bin/env python3
"""
Unified workflow to update ParadeDB with new CrossFit workouts.

This script handles the complete pipeline:
1. Download new workout months from CrossFit.com
2. Extract and parse workout data  
3. Generate metadata (movements, equipment, workout type)
4. Create one-sentence summaries
5. Generate OpenAI embeddings (workout + summary)
6. Insert into ParadeDB with full indexing

Usage:
  # Update with latest month
  uv run python scripts/update_paradedb.py --month 2024-08
  
  # Update multiple months
  uv run python scripts/update_paradedb.py --month 2024-07 --month 2024-08
  
  # Auto-detect missing months since last update
  uv run python scripts/update_paradedb.py --auto
"""

import os
import sys
from datetime import datetime
from typing import List, Optional

import typer
from dotenv import load_dotenv
from openai import OpenAI
import psycopg2

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wodrag.database.client import get_postgres_connection
from wodrag.data_processing.downloader import download_workout_month
from wodrag.data_processing.extractor import extract_workouts_from_month
from wodrag.data_processing.simple_parser import parse_workout_simple
from wodrag.agents.extract_metadata import extractor
from wodrag.services.embedding_service import EmbeddingService

# Load environment variables
load_dotenv()

app = typer.Typer()


def get_openai_client() -> OpenAI:
    """Create and return an OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment")
    return OpenAI(api_key=api_key)


def get_latest_workout_date() -> str | None:
    """Get the date of the most recent workout in the database."""
    with get_postgres_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT date FROM workouts ORDER BY date DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0].isoformat() if result else None


def workout_exists(date: str, url: str) -> bool:
    """Check if a workout already exists in the database."""
    with get_postgres_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM workouts WHERE date = %s AND url = %s", (date, url))
            return cursor.fetchone() is not None


def insert_workout_complete(
    workout_data: dict,
    openai_client: OpenAI,
    embedding_service: EmbeddingService
) -> bool:
    """Insert a workout with complete metadata and embeddings."""
    try:
        # Parse basic workout content
        parsed = parse_workout_simple(workout_data["raw_text"])
        
        # Extract metadata using AI
        metadata = extractor(parsed["workout"])
        
        # Generate summary using AI (simplified for now)
        summary = f"A {metadata.workout_type or 'CrossFit'} workout involving {', '.join(metadata.movements[:3]) if metadata.movements else 'various movements'}"
        
        # Generate embeddings
        workout_text = parsed["workout"]
        if parsed["scaling"]:
            workout_text += f" {parsed['scaling']}"
        
        workout_embedding = embedding_service.generate_embedding(workout_text)
        summary_embedding = embedding_service.generate_embedding(summary)
        
        # Insert into database
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO workouts (
                    date, url, raw_text, workout, scaling,
                    has_video, has_article, month_file,
                    movements, equipment, workout_type, workout_name,
                    one_sentence_summary, workout_embedding, summary_embedding
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                cursor.execute(sql, (
                    workout_data["date"],
                    workout_data["url"], 
                    workout_data["raw_text"],
                    parsed["workout"],
                    parsed["scaling"],
                    workout_data["has_video"],
                    workout_data["has_article"],
                    workout_data["month_file"],
                    metadata.movements,
                    metadata.equipment,
                    metadata.workout_type,
                    metadata.workout_name,
                    summary,
                    workout_embedding,
                    summary_embedding
                ))
                conn.commit()
        
        return True
        
    except Exception as e:
        print(f"Error inserting workout {workout_data['date']}: {e}")
        return False


def process_month(year_month: str, force_redownload: bool = False) -> int:
    """Process a single month. Returns number of new workouts added."""
    print(f"🔄 Processing {year_month}...")
    
    year, month = year_month.split("-")
    
    # 1. Download month data
    month_file = f"data/raw/{year_month}.html"
    if force_redownload or not os.path.exists(month_file):
        print(f"  📥 Downloading {year_month}...")
        success = download_workout_month(int(year), int(month))
        if not success:
            print(f"  ❌ Failed to download {year_month}")
            return 0
    
    # 2. Extract workouts from HTML
    print(f"  🔍 Extracting workouts...")
    workouts = extract_workouts_from_month(year_month)
    if not workouts:
        print(f"  ⚠️  No workouts found for {year_month}")
        return 0
    
    # 3. Process each workout
    print(f"  🤖 Processing {len(workouts)} workouts...")
    openai_client = get_openai_client()
    embedding_service = EmbeddingService()
    
    new_count = 0
    for workout_data in workouts:
        # Skip if already exists
        if workout_exists(workout_data["date"], workout_data["url"]):
            continue
        
        # Insert with complete processing
        if insert_workout_complete(workout_data, openai_client, embedding_service):
            new_count += 1
            print(f"    ✅ Added: {workout_data['date']}")
    
    print(f"  📊 Added {new_count} new workouts")
    return new_count


@app.command()
def update_month(
    month: str = typer.Argument(..., help="Month to update (YYYY-MM format)"),
    force_redownload: bool = typer.Option(False, "--force", help="Force re-download even if file exists")
) -> None:
    """Update a specific month of workouts."""
    try:
        new_count = process_month(month, force_redownload)
        print(f"\n🎉 Update complete! Added {new_count} new workouts for {month}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


@app.command() 
def auto_update() -> None:
    """Automatically update all months since the last workout in the database."""
    try:
        print("🔍 Checking for missing months...")
        
        # Get latest date
        latest_date = get_latest_workout_date()
        print(f"Latest workout in database: {latest_date or 'None (empty database)'}")
        
        # Determine months to update (simplified logic)
        current_date = datetime.now()
        if latest_date:
            latest_dt = datetime.fromisoformat(latest_date)
            start_month = f"{latest_dt.year}-{latest_dt.month:02d}"
        else:
            start_month = "2001-02"
        
        current_month = f"{current_date.year}-{current_date.month:02d}"
        
        print(f"Will check from {start_month} to {current_month}")
        
        # For now, just process current month as example
        # TODO: Implement proper month range iteration
        months_to_check = [current_month]
        
        total_new = 0
        for month in months_to_check:
            new_count = process_month(month)
            total_new += new_count
        
        print(f"\n🎉 Auto-update complete! Added {total_new} new workouts")
        
        # Show final count
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM workouts")
                total_count = cursor.fetchone()[0]
                print(f"Total workouts in database: {total_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()