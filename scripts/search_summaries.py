#!/usr/bin/env python3
"""Search workouts using semantic similarity on one-sentence summaries."""

import os
import sys
from typing import Optional

import typer
from dotenv import load_dotenv

# Add the parent directory to Python path to import wodrag modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wodrag.database.client import get_supabase_client
from wodrag.database.models import WorkoutFilter
from wodrag.database.workout_repository import WorkoutRepository
from wodrag.services.embedding_service import EmbeddingService

# Load environment variables
load_dotenv()

app = typer.Typer()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query text"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Similarity threshold (0-1)"),
    movements: Optional[str] = typer.Option(None, "--movements", "-m", help="Filter by movements (comma-separated)"),
    equipment: Optional[str] = typer.Option(None, "--equipment", "-e", help="Filter by equipment (comma-separated)"),
    workout_type: Optional[str] = typer.Option(None, "--type", help="Filter by workout type"),
) -> None:
    """Search workouts using semantic similarity on one-sentence summaries."""
    
    try:
        # Initialize services
        client = get_supabase_client()
        repository = WorkoutRepository(client)
        
        # Build filters
        filters = WorkoutFilter()
        if movements:
            filters.movements = [m.strip() for m in movements.split(",")]
        if equipment:
            filters.equipment = [e.strip() for e in equipment.split(",")]
        if workout_type:
            filters.workout_type = workout_type
        
        # Perform semantic search
        print(f"🔍 Searching for: '{query}'")
        if filters.movements or filters.equipment or filters.workout_type:
            print(f"📋 Filters: movements={filters.movements}, equipment={filters.equipment}, type={filters.workout_type}")
        print(f"⚙️  Similarity threshold: {threshold}")
        print()
        
        results = repository.search_summaries(
            query_text=query,
            limit=limit,
        )
        
        if not results:
            print("❌ No matching workouts found.")
            print("💡 Try:")
            print("   - Lowering the similarity threshold with --threshold 0.5")
            print("   - Using different search terms")
            print("   - Removing filters")
            return
        
        print(f"✅ Found {len(results)} matching workouts:\n")
        
        for i, result in enumerate(results, 1):
            workout = result.workout
            similarity = result.similarity_score or 0.0
            
            print(f"{i}. {workout.date} - Similarity: {similarity:.3f}")
            print(f"   Summary: {workout.one_sentence_summary}")
            if workout.movements:
                print(f"   Movements: {', '.join(workout.movements[:5])}")
            if workout.equipment:
                print(f"   Equipment: {', '.join(workout.equipment[:3])}")
            print(f"   Type: {workout.workout_type}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


@app.command()
def test_vector_search() -> None:
    """Test vector search functionality with a sample query."""
    
    try:
        # Initialize services
        client = get_supabase_client()
        repository = WorkoutRepository(client)
        embedding_service = EmbeddingService()
        
        # Sample test queries
        test_queries = [
            "strength training with heavy weights",
            "cardio workout with running",
            "bodyweight exercises and pull-ups",
            "Olympic lifting movements"
        ]
        
        print("🧪 Testing semantic search on summaries...\n")
        
        for query in test_queries:
            print(f"Query: '{query}'")
            
            # Generate embedding
            query_embedding = embedding_service.generate_embedding(query)
            
            # Perform search
            results = repository.hybrid_search(
                query_embedding=query_embedding,
                limit=3,
                similarity_threshold=0.6
            )
            
            if results:
                print(f"  Found {len(results)} results:")
                for result in results:
                    similarity = result.similarity_score or 0.0
                    print(f"    • {result.workout.date} (sim: {similarity:.3f}): {result.workout.one_sentence_summary}")
            else:
                print("  No results found")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()