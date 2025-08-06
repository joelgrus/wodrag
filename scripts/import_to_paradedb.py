#!/usr/bin/env python3
"""Import exported Supabase data into ParadeDB."""

import json
import os
import sys
from typing import Any, Dict, List

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.paradedb")


def get_database_connection():
    """Get PostgreSQL connection."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment")
    return psycopg2.connect(db_url)


def import_workouts_from_json(json_file: str = "data/supabase_export.json") -> None:
    """Import workouts from JSON export into ParadeDB."""
    print("🔄 Importing workouts into ParadeDB...")
    
    if not os.path.exists(json_file):
        print(f"❌ Export file not found: {json_file}")
        print("Run scripts/export_supabase_data.py first")
        sys.exit(1)
    
    try:
        # Load exported data
        with open(json_file, "r") as f:
            workouts = json.load(f)
        
        print(f"Loaded {len(workouts)} workouts from export")
        
        # Connect to ParadeDB
        conn = get_database_connection()
        
        try:
            with conn.cursor() as cursor:
                # Prepare insert statement
                insert_sql = """
                INSERT INTO workouts (
                    id, date, url, raw_text, workout, scaling,
                    has_video, has_article, month_file, created_at,
                    movements, equipment, workout_type, workout_name,
                    one_sentence_summary, workout_embedding, summary_embedding
                ) VALUES (
                    %(id)s, %(date)s, %(url)s, %(raw_text)s, %(workout)s, %(scaling)s,
                    %(has_video)s, %(has_article)s, %(month_file)s, %(created_at)s,
                    %(movements)s, %(equipment)s, %(workout_type)s, %(workout_name)s,
                    %(one_sentence_summary)s, %(workout_embedding)s, %(summary_embedding)s
                )
                """
                
                # Insert in batches
                batch_size = 50
                successful = 0
                errors = 0
                
                for i in range(0, len(workouts), batch_size):
                    batch = workouts[i:i + batch_size]
                    print(f"Importing batch: {i + 1}-{min(i + batch_size, len(workouts))}")
                    
                    for workout in batch:
                        try:
                            # Clean up the data
                            clean_workout = {
                                'id': workout['id'],
                                'date': workout['date'],
                                'url': workout['url'],
                                'raw_text': workout['raw_text'],
                                'workout': workout['workout'],
                                'scaling': workout.get('scaling'),
                                'has_video': workout.get('has_video', False),
                                'has_article': workout.get('has_article', False),
                                'month_file': workout.get('month_file'),
                                'created_at': workout.get('created_at'),
                                'movements': workout.get('movements'),
                                'equipment': workout.get('equipment'),
                                'workout_type': workout.get('workout_type'),
                                'workout_name': workout.get('workout_name'),
                                'one_sentence_summary': workout.get('one_sentence_summary'),
                                'workout_embedding': workout.get('workout_embedding'),
                                'summary_embedding': workout.get('summary_embedding'),
                            }
                            
                            cursor.execute(insert_sql, clean_workout)
                            successful += 1
                            
                        except Exception as e:
                            errors += 1
                            print(f"  Error importing workout {workout.get('id', 'unknown')}: {e}")
                    
                    # Commit batch
                    conn.commit()
                
                print(f"\n✅ Import complete!")
                print(f"   Successful: {successful}")
                print(f"   Errors: {errors}")
                print(f"   Total: {len(workouts)}")
                
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import_workouts_from_json()