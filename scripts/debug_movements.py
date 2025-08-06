#!/usr/bin/env python3
"""Debug script to see actual movement and equipment values in the database."""

import sys
from pathlib import Path

# Add the wodrag package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wodrag.database.duckdb_client import DuckDBQueryService


def main() -> None:
    """Debug movement and equipment values."""
    
    service = DuckDBQueryService()
    
    print("🔍 Investigating movement and equipment values...")
    print()
    
    # Check some sample movements
    print("📋 Sample movements from workouts:")
    query = """
    SELECT movements, equipment, workout_type, one_sentence_summary
    FROM pg_db.workouts 
    WHERE movements IS NOT NULL 
    AND array_length(movements, 1) > 0
    LIMIT 10
    """
    results = service.execute_query(query)
    
    for i, row in enumerate(results, 1):
        print(f"{i}. Movements: {row['movements']}")
        print(f"   Equipment: {row['equipment']}")  
        print(f"   Type: {row['workout_type']}")
        print(f"   Summary: {row['one_sentence_summary'][:80]}...")
        print()
    
    # Get unique movements
    print("📊 Most common movements:")
    query = """
    SELECT unnest(movements) as movement, COUNT(*) as count
    FROM pg_db.workouts 
    WHERE movements IS NOT NULL
    GROUP BY unnest(movements)
    ORDER BY count DESC
    LIMIT 15
    """
    movements = service.execute_query(query)
    
    for mov in movements:
        print(f"  - {mov['movement']}: {mov['count']} workouts")
    
    print()
    print("🔧 Most common equipment:")
    query = """
    SELECT unnest(equipment) as equip, COUNT(*) as count
    FROM pg_db.workouts 
    WHERE equipment IS NOT NULL
    GROUP BY unnest(equipment)
    ORDER BY count DESC
    LIMIT 15
    """
    equipment = service.execute_query(query)
    
    for eq in equipment:
        print(f"  - {eq['equip']}: {eq['count']} workouts")


if __name__ == "__main__":
    main()