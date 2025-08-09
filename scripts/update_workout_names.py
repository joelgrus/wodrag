#!/usr/bin/env python3
"""Update workout names for all workouts using DSPy."""

import logging
import os
import time

import dspy  # type: ignore
import psycopg2
import typer
from psycopg2.extras import RealDictCursor
import litellm

logger = logging.getLogger(__name__)


class ExtractWorkoutName(dspy.Signature):
    """Extract workout name from workout description."""
    workout: str = dspy.InputField(description="Workout description text")
    workout_name: str = dspy.OutputField(
        description=("The name of the workout. Some workouts have official names, e.g. Murph, Fran, etc "
                     "Some workouts have 'titles' (e.g. 'Barbell Mania') you can use those as the names. "
                     "If no official name is found, make up a name based on the workout description. "
                     "nb some workout descriptions have names of people in them, e.g. 'John Smith did this in 4:31' "
                     "those are not workout names, so don't use them.")
    )



def main(
    batch_size: int = 50,
    limit: int | None = None,
    force: bool = False,
) -> None:
    """Update workout names for all workouts."""
    
    # Setup
    database_url = os.getenv("DATABASE_URL")

    lm = dspy.LM('openrouter/google/gemini-2.5-flash-lite', max_tokens=1000)

    dspy.configure(lm=lm)
    extract_name = dspy.Predict(ExtractWorkoutName)
    
    # Get workouts
    with psycopg2.connect(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            where_clause = "" if force else "WHERE workout_name IS NULL"
            cur.execute(f"""
                SELECT id, date, workout 
                FROM workouts {where_clause}
                ORDER BY date 
                {f'LIMIT {limit}' if limit else ''}
            """)
            workouts = cur.fetchall()
    
    logger.info(f"Found {len(workouts)} workouts to process")
    
    # Process batches
    for i in range(0, len(workouts), batch_size):
        batch = workouts[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(workouts) + batch_size - 1)//batch_size}")
        
        for workout in batch:
            try:
                result = extract_name(workout=workout["workout"])
                name = result.workout_name.strip() or "Workout"
                print(name)
                
                with psycopg2.connect(database_url) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE workouts SET workout_name = %s WHERE id = %s",
                            (name, workout["id"])
                        )
                
                logger.info(f"Updated workout {workout['id']} ({workout['date']}): '{name}'")
                time.sleep(0.1)  # Rate limit
                
            except Exception as e:
                print(f"Failed to process workout {workout['id']}: {e}")


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    typer.run(main)