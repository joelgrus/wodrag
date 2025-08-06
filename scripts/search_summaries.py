#!/usr/bin/env python3
"""Search workouts using semantic similarity on one-sentence summaries."""

import os
import sys

import typer
from dotenv import load_dotenv

# Add the parent directory to Python path to import wodrag modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# PostgreSQL-only, no Supabase needed
from wodrag.database.models import WorkoutFilter
from wodrag.database.workout_repository import WorkoutRepository
from wodrag.services.embedding_service import EmbeddingService

# Load environment variables
load_dotenv()

app = typer.Typer()


@app.command()
def search(
    query: str = typer.Argument(
        ..., help='Search query (use quotes for phrases: "pogo stick")'
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    threshold: float = typer.Option(
        0.7, "--threshold", "-t", help="Similarity threshold (0-1)"
    ),
    movements: str | None = typer.Option(
        None, "--movements", "-m", help="Filter by movements (comma-separated)"
    ),
    equipment: str | None = typer.Option(
        None, "--equipment", "-e", help="Filter by equipment (comma-separated)"
    ),
    workout_type: str | None = typer.Option(
        None, "--type", help="Filter by workout type"
    ),
    hybrid: bool = typer.Option(
        False, "--hybrid", "-h", help="Use hybrid search (semantic + keyword)"
    ),
    semantic_weight: float = typer.Option(
        0.7, "--weight", "-w", help="Semantic weight for hybrid search (0-1)"
    ),
) -> None:
    """
    Search workouts using semantic similarity on one-sentence summaries.

    For hybrid search, supports web-style syntax:
    - "exact phrase" - search for exact phrase
    - word1 OR word2 - match either term
    - word1 -word2 - exclude word2
    - word1 word2 - match both terms
    """

    try:
        # Initialize services
        repository = WorkoutRepository()

        # Build filters
        filters = WorkoutFilter()
        if movements:
            filters.movements = [m.strip() for m in movements.split(",")]
        if equipment:
            filters.equipment = [e.strip() for e in equipment.split(",")]
        if workout_type:
            filters.workout_type = workout_type

        # Perform search
        if hybrid:
            pass
        if filters.movements or filters.equipment or filters.workout_type:
            pass
        if not hybrid:
            pass

        if hybrid:
            results = repository.hybrid_search(
                query_text=query,
                semantic_weight=semantic_weight,
                limit=limit,
            )
        else:
            results = repository.search_summaries(
                query_text=query,
                limit=limit,
            )

        if not results:
            return


        for _i, result in enumerate(results, 1):
            workout = result.workout

            if workout.movements:
                pass
            if workout.equipment:
                pass

    except Exception:
        sys.exit(1)


@app.command()
def test_vector_search() -> None:
    """Test vector search functionality with a sample query."""

    try:
        # Initialize services
        repository = WorkoutRepository()
        embedding_service = EmbeddingService()

        # Sample test queries
        test_queries = [
            "strength training with heavy weights",
            "cardio workout with running",
            "bodyweight exercises and pull-ups",
            "Olympic lifting movements",
        ]


        for query in test_queries:

            # Generate embedding
            query_embedding = embedding_service.generate_embedding(query)

            # Perform search
            results = repository.hybrid_search(
                query_embedding=query_embedding, limit=3, similarity_threshold=0.6
            )

            if results:
                for _result in results:
                    pass
            else:
                pass

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    app()
