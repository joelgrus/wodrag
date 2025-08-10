#!/usr/bin/env python3
"""Generic script to update workout fields using LLM extraction."""

import logging
import os
import time
from typing import Any

import dspy  # type: ignore
import psycopg2
import typer
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class ExtractWorkoutName(dspy.Signature):
    """Extract workout name from workout description."""
    workout: str = dspy.InputField(description="Workout description text")
    workout_name: str = dspy.OutputField(
        description="""Official workout name if it exists (e.g., 'Fran', 'Murph', 'Grace'), 
        otherwise 'Untitled'. Return ONLY the name."""
    )


class FieldUpdater:
    """Generic field updater for workout metadata."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment")
            
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        # Configure DSPy
        dspy.configure(lm=dspy.LM("openai/gpt-4o-mini", api_key=self.openai_api_key))
        
        # Initialize extractors
        self.extract_workout_name = dspy.ChainOfThought(ExtractWorkoutName)
    
    def get_workouts_missing_field(
        self, field_name: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get workouts that are missing a specific field."""
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    SELECT id, date, workout, workout_name, one_sentence_summary 
                    FROM workouts 
                    WHERE {field_name} IS NULL 
                    ORDER BY date 
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                return [dict(row) for row in cur.fetchall()]
    
    def get_total_missing_field_count(self, field_name: str) -> int:
        """Get count of workouts missing a specific field."""
        with psycopg2.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) FROM workouts WHERE {field_name} IS NULL"
                )
                return cur.fetchone()[0]
    
    def update_workout_field(
        self, workout_id: int, field_name: str, value: str
    ) -> bool:
        """Update a specific field for a workout."""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE workouts 
                        SET {field_name} = %s 
                        WHERE id = %s
                        """,
                        (value, workout_id),
                    )
            return True
        except Exception as e:
            logger.error(f"Failed to update workout {workout_id}: {e}")
            return False
    
    def extract_workout_name_dspy(self, workout_text: str) -> str:
        """Extract workout name using DSPy."""
        try:
            result = self.extract_workout_name(workout=workout_text)
            name = result.workout_name.strip()
            return name if name else "Untitled"
            
        except Exception as e:
            logger.error(f"Failed to extract workout name: {e}")
            return "Untitled"
    
    def extract_field_with_llm(self, workout_text: str, field_type: str) -> str:
        """Generic LLM field extraction (extensible for future fields)."""
        if field_type == "workout_name":
            return self.extract_workout_name(workout_text)
        else:
            raise ValueError(f"Unsupported field type: {field_type}")
    
    def update_field_batch(
        self, field_name: str, field_type: str, batch_size: int = 50
    ) -> int:
        """Update a batch of workouts for a specific field."""
        workouts = self.get_workouts_missing_field(field_name, limit=batch_size)
        
        if not workouts:
            return 0
        
        updated_count = 0
        
        for workout in workouts:
            logger.info(f"Processing workout {workout['id']} ({workout['date']})")
            
            # Extract field value using LLM
            field_value = self.extract_field_with_llm(workout["workout"], field_type)
            
            # Update database
            if self.update_workout_field(workout["id"], field_name, field_value):
                logger.info(f"Updated workout {workout['id']}: {field_name} = '{field_value}'")
                updated_count += 1
            else:
                logger.error(f"Failed to update workout {workout['id']}")
            
            # Rate limiting
            time.sleep(0.5)
        
        return updated_count
    
    def update_all_missing_fields(
        self, field_name: str, field_type: str, batch_size: int = 50, limit: int | None = None
    ) -> None:
        """Update all workouts missing a specific field."""
        total_missing = self.get_total_missing_field_count(field_name)
        logger.info(f"Found {total_missing} workouts missing {field_name}")
        
        if total_missing == 0:
            logger.info(f"✅ All workouts already have {field_name}!")
            return
        
        processed = 0
        total_updated = 0
        
        while processed < total_missing:
            if limit and processed >= limit:
                logger.info(f"Reached processing limit of {limit}")
                break
            
            logger.info(f"Processing batch {processed // batch_size + 1}...")
            
            updated = self.update_field_batch(field_name, field_type, batch_size)
            total_updated += updated
            processed += batch_size
            
            remaining = self.get_total_missing_field_count(field_name)
            logger.info(f"Batch complete: {updated} updated, {remaining} remaining")
            
            if remaining == 0:
                break
        
        logger.info(f"✅ Field update complete: {total_updated} workouts updated")


app = typer.Typer(help="Update workout fields using LLM extraction")


@app.command()
def update_workout_names(
    batch_size: int = typer.Option(50, help="Number of workouts to process per batch"),
    limit: int | None = typer.Option(None, help="Maximum number of workouts to process"),
) -> None:
    """Update workout_name field for workouts that don't have it."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger.info("🏋️ Starting workout name extraction...")
    
    updater = FieldUpdater()
    updater.update_all_missing_fields(
        field_name="workout_name",
        field_type="workout_name", 
        batch_size=batch_size,
        limit=limit
    )


@app.command()
def update_field(
    field_name: str = typer.Argument(help="Database field name to update"),
    field_type: str = typer.Argument(help="Field type for LLM extraction"),
    batch_size: int = typer.Option(50, help="Number of workouts to process per batch"),
    limit: int | None = typer.Option(None, help="Maximum number of workouts to process"),
) -> None:
    """Generic field updater (extensible for future fields)."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger.info(f"🔄 Starting {field_name} extraction...")
    
    updater = FieldUpdater()
    updater.update_all_missing_fields(
        field_name=field_name,
        field_type=field_type,
        batch_size=batch_size, 
        limit=limit
    )


if __name__ == "__main__":
    app()