#!/usr/bin/env python3
"""Initialize the database with workout data for Docker deployment."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wodrag.database.workout_repository import WorkoutRepository
from scripts.import_to_paradedb import main as import_workouts
from scripts.extract_and_populate_metadata import main as extract_metadata


def init_database():
    """Initialize database with all workout data."""
    print("🚀 Initializing database...")
    
    # Check if database already has data
    repo = WorkoutRepository()
    count = repo.get_workout_count()
    
    if count > 0:
        print(f"✅ Database already contains {count} workouts. Skipping initialization.")
        return
    
    print("📥 Importing workouts from JSON files...")
    import_workouts()
    
    print("🤖 Extracting metadata (this may take a while)...")
    extract_metadata()
    
    # Verify data was loaded
    final_count = repo.get_workout_count()
    print(f"✅ Database initialized with {final_count} workouts!")


if __name__ == "__main__":
    init_database()