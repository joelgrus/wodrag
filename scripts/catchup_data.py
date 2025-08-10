#!/usr/bin/env python3
"""
Catch up data from the last date in the database to today.

This script:
1. Finds the last date in the database
2. For each month from then to today:
   - Downloads the monthly workout page from crossfit.com
   - Extracts all workouts from the HTML
   - Filters to only new workouts we don't have
   - Augments with metadata and embeddings
   - Inserts into the database
"""

import logging
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

import dspy  # type: ignore
import psycopg2
import typer
from dotenv import load_dotenv

from wodrag.agents.extract_metadata import extractor
from wodrag.data_processing.downloader import download_month
from wodrag.data_processing.extractor import extract_workouts_from_file
from wodrag.services.embedding_service import EmbeddingService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def get_database_connection():
    """Get a connection to the PostgreSQL database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")
    return psycopg2.connect(database_url)


def get_last_workout_date() -> datetime:
    """Get the date of the most recent workout in the database."""
    with get_database_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(date) FROM workouts")
            result = cur.fetchone()
            if result and result[0]:
                return result[0]
            else:
                # Default to yesterday if no workouts found
                return datetime.now().date() - timedelta(days=1)


def get_months_to_process(last_date: datetime, today: datetime) -> list[tuple[int, int]]:
    """Get list of (year, month) tuples that need to be processed."""
    months = []
    current = datetime(last_date.year, last_date.month, 1)
    today_month = datetime(today.year, today.month, 1)
    
    while current <= today_month:
        months.append((current.year, current.month))
        # Move to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    
    return months


def process_month(year: int, month: int, embedding_service: EmbeddingService) -> tuple[int, int]:
    """Process a single month. Returns (added_count, skipped_count)."""
    year_month = f"{year}-{month:02d}"
    logger.info(f"Processing month: {year_month}")
    
    # 1. Download month data
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    html_file = output_dir / f"{year_month}.html"
    
    logger.info(f"📥 Downloading {year_month} workouts...")
    success = download_month(year, month, output_dir)
    if not success:
        logger.error(f"Failed to download {year_month}")
        return 0, 0
    
    # 2. Extract workouts from HTML
    logger.info(f"🔄 Extracting workouts from {year_month} HTML...")
    workouts = extract_workouts_from_file(html_file)
    if not workouts:
        logger.warning(f"No workouts found in {year_month}")
        return 0, 0
    
    logger.info(f"Found {len(workouts)} workouts in {year_month}")
    
    # 3. Process each workout
    added_count = 0
    skipped_count = 0
    
    for workout in workouts:
        workout_dict = asdict(workout)
        
        # Remove the ID field to let database auto-generate it
        if 'id' in workout_dict:
            del workout_dict['id']
        
        # Check if workout already exists
        if workout_exists(workout_dict["date"]):
            skipped_count += 1
            continue
        
        if insert_workout_complete(workout_dict, embedding_service):
            added_count += 1
        else:
            logger.error(f"Failed to insert workout for {workout_dict['date']}")
    
    return added_count, skipped_count


def insert_workout_complete(workout_data: dict, embedding_service: EmbeddingService) -> bool:
    """Insert a workout with complete metadata and embeddings."""
    try:
        # Extract metadata using AI
        metadata = extractor(workout=workout_data["workout"])
        
        # Generate summary
        movements_str = ", ".join(metadata.movements[:3]) if metadata.movements else "various movements"
        workout_type = metadata.workout_type or "CrossFit"
        
        if metadata.workout_name and metadata.workout_name != "Untitled":
            summary = f"{metadata.workout_name}: A {workout_type} workout involving {movements_str}"
        else:
            summary = f"A {workout_type} workout involving {movements_str}"
        
        # Generate embeddings
        workout_text = workout_data["workout"]
        if workout_data.get("scaling"):
            workout_text += f"\n{workout_data['scaling']}"
        
        workout_embedding = embedding_service.generate_embedding(workout_text)
        summary_embedding = embedding_service.generate_embedding(summary)

        # Insert into database
        with get_database_connection() as conn:
            with conn.cursor() as cur:
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
                cur.execute(sql, (
                    workout_data["date"],
                    workout_data.get("url", ""),
                    workout_data["raw_text"],
                    workout_data["workout"],
                    workout_data.get("scaling"),
                    workout_data.get("has_video", False),
                    workout_data.get("has_article", False),
                    workout_data.get("month_file", ""),
                    metadata.movements,
                    metadata.equipment,
                    metadata.workout_type,
                    metadata.workout_name,
                    summary,
                    workout_embedding,
                    summary_embedding,
                ))
                conn.commit()

        logger.info(f"✅ Inserted workout for {workout_data['date']}: {metadata.workout_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to insert workout for {workout_data['date']}: {e}")
        return False




def main(
    dry_run: bool = typer.Option(False, help="Show what would be done without doing it"),
    limit: int | None = typer.Option(None, help="Maximum number of months to process"),
) -> None:
    """Catch up workout data from the last date in database to today."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Configure DSPy for metadata extraction
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        dspy.configure(lm=dspy.LM("openai/gpt-4o-mini", api_key=openai_api_key))
    
    # Initialize services
    embedding_service = EmbeddingService()
    
    # Get the last workout date
    last_date = get_last_workout_date()
    today = datetime.now().date()
    
    logger.info(f"Last workout in database: {last_date}")
    logger.info(f"Today's date: {today}")
    
    # Convert to datetime objects for month calculation
    last_datetime = datetime.combine(last_date, datetime.min.time())
    today_datetime = datetime.combine(today, datetime.min.time())
    
    # Calculate months to process
    months_to_process = get_months_to_process(last_datetime, today_datetime)
    
    if limit:
        months_to_process = months_to_process[:limit]
    
    total_months = len(months_to_process)
    
    if total_months == 0:
        logger.info("✅ Database is already up to date!")
        return
    
    logger.info(f"Found {total_months} months to process")
    
    if dry_run:
        logger.info("DRY RUN - would process these months:")
        for year, month in months_to_process:
            logger.info(f"  - {year}-{month:02d}")
        return
    
    # Process each month
    total_added = 0
    total_skipped = 0
    
    for i, (year, month) in enumerate(months_to_process, 1):
        logger.info(f"Processing month {i}/{total_months}: {year}-{month:02d}")
        
        added, skipped = process_month(year, month, embedding_service)
        total_added += added
        total_skipped += skipped
        
        logger.info(f"Month {year}-{month:02d}: +{added} workouts, {skipped} skipped")
    
    # Final report
    logger.info(f"\n{'='*50}")
    logger.info(f"Catchup complete!")
    logger.info(f"✅ Successfully added: {total_added} workouts")
    logger.info(f"⏭️ Skipped (already exist): {total_skipped} workouts")
    
    # Show final count in database
    with get_database_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM workouts")
            total_count = cur.fetchone()[0]
            logger.info(f"📊 Total workouts in database: {total_count}")


if __name__ == "__main__":
    typer.run(main)