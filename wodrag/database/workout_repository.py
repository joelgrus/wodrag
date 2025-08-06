from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import date
from typing import Any

import psycopg2

from .client import get_postgres_connection
from .models import SearchResult, Workout, WorkoutFilter


class WorkoutRepository:
    """Repository for workout database operations."""

    def __init__(self) -> None:
        self.table_name = "workouts"

    @contextmanager
    def _get_pg_connection(
        self,
    ) -> Generator[psycopg2.extensions.connection, None, None]:
        """Get a direct PostgreSQL connection with proper cleanup."""
        with get_postgres_connection() as conn:
            yield conn

    # CRUD Operations

    def insert_workout(self, workout: Workout) -> Workout:
        """Insert a workout into the database using PostgreSQL."""
        # TODO: Implement PostgreSQL-based insert if needed
        raise NotImplementedError(
            "Use direct SQL or import scripts for PostgreSQL inserts"
        )

    def get_workout(self, workout_id: int) -> Workout | None:
        """Get a single workout by ID using PostgreSQL."""
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM workouts WHERE id = %s", (workout_id,)
                )
                row = cursor.fetchone()
                if row:
                    columns = (
                        [desc[0] for desc in cursor.description]
                        if cursor.description
                        else []
                    )
                    row_dict = dict(zip(columns, row, strict=False))
                    return Workout.from_dict(row_dict)
                return None
        except psycopg2.Error:
            return None

    def update_workout_metadata(
        self,
        workout_id: int,
        movements: list[str] | None = None,
        equipment: list[str] | None = None,
        workout_type: str | None = None,
        workout_name: str | None = None,
        one_sentence_summary: str | None = None,
        summary_embedding: list[float] | None = None,
    ) -> Workout | None:
        updates: dict[str, Any] = {}
        if movements is not None:
            updates["movements"] = movements
        if equipment is not None:
            updates["equipment"] = equipment
        if workout_type is not None:
            updates["workout_type"] = workout_type
        if workout_name is not None:
            updates["workout_name"] = workout_name
        if one_sentence_summary is not None:
            updates["one_sentence_summary"] = one_sentence_summary
        if summary_embedding is not None:
            updates["summary_embedding"] = summary_embedding

        if not updates:
            return self.get_workout(workout_id)

        # TODO: Implement PostgreSQL-based update if needed
        raise NotImplementedError("Use direct SQL for PostgreSQL updates")

    def delete_workout(self, workout_id: int) -> bool:
        """Delete a workout using PostgreSQL."""
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                cursor.execute("DELETE FROM workouts WHERE id = %s", (workout_id,))
                conn.commit()
                return cursor.rowcount > 0
        except psycopg2.Error:
            return False

    # Search Methods

    def _generate_query_embedding(self, query_text: str) -> list[float]:
        """Generate embedding for search query."""
        from ..services.embedding_service import EmbeddingService

        embedding_service = EmbeddingService()
        return embedding_service.generate_embedding(query_text)

    def _execute_vector_similarity_query(
        self,
        query_embedding: list[float],
        limit: int,
        similarity_threshold: float | None = None,
    ) -> list[tuple[Any, ...]]:
        """Execute vector similarity SQL query."""
        with self._get_pg_connection() as conn, conn.cursor() as cursor:
            if similarity_threshold is not None:
                sql = """
                    SELECT *, 1 - (summary_embedding <=> %s::vector) as similarity
                    FROM workouts
                    WHERE summary_embedding IS NOT NULL
                    AND 1 - (summary_embedding <=> %s::vector) >= %s
                    ORDER BY summary_embedding <=> %s::vector
                    LIMIT %s
                    """
                cursor.execute(
                    sql,
                    (
                        query_embedding,
                        query_embedding,
                        similarity_threshold,
                        query_embedding,
                        limit,
                    ),
                )
            else:
                sql = """
                    SELECT *, 1 - (summary_embedding <=> %s::vector) as similarity
                    FROM workouts
                    WHERE summary_embedding IS NOT NULL
                    ORDER BY summary_embedding <=> %s::vector
                    LIMIT %s
                    """
                cursor.execute(sql, (query_embedding, query_embedding, limit))

            rows = cursor.fetchall()
            columns = (
                [desc[0] for desc in cursor.description]
                if cursor.description
                else []
            )
            return [(row, columns) for row in rows]

    def _convert_rows_to_search_results(
        self, rows_with_columns: list[tuple[Any, ...]]
    ) -> list[SearchResult]:
        """Convert database rows to SearchResult objects."""
        search_results = []
        for row_data in rows_with_columns:
            row, columns = row_data
            row_dict = dict(zip(columns, row, strict=False))
            similarity_score = row_dict.pop("similarity", 0.0)
            workout = Workout.from_dict(row_dict)
            search_results.append(
                SearchResult(
                    workout=workout,
                    similarity_score=similarity_score,
                    metadata_match=True,
                )
            )
        return search_results

    def text_search_workouts(
        self,
        query: str,
        limit: int = 50,
    ) -> list[SearchResult]:
        """
        Full-text search using ParadeDB BM25 ranking.

        Supports:
        - "phrase search" - exact phrase matching
        - word1 OR word2 - either term
        - word1 AND word2 - both terms
        - word1 NOT word2 - exclude word2
        - Complex boolean queries

        Args:
            query: Search query text
            limit: Maximum number of results

        Returns:
            List of search results ordered by BM25 score
        """
        try:
            if not query.strip():
                return []

            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                # Use ParadeDB's BM25 search with boolean query
                sql = """
                    SELECT w.*, paradedb.score(w.id) as bm25_score
                    FROM workouts w
                    WHERE w @@@ paradedb.boolean(
                        should => ARRAY[
                            paradedb.match('workout', %s),
                            paradedb.match('one_sentence_summary', %s),
                            paradedb.match('workout_name', %s),
                            paradedb.match('scaling', %s)
                        ]
                    )
                    ORDER BY bm25_score DESC
                    LIMIT %s
                    """
                cursor.execute(sql, (query, query, query, query, limit))
                rows = cursor.fetchall()

                # Get column names
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )

            # Convert to SearchResults
            search_results = []
            for row in rows:
                row_dict = dict(zip(columns, row, strict=False))
                bm25_score = row_dict.pop("bm25_score", 0.0)
                workout = Workout.from_dict(row_dict)
                search_results.append(
                    SearchResult(
                        workout=workout,
                        similarity_score=bm25_score,
                        metadata_match=True,
                    )
                )

            return search_results

        except (psycopg2.Error, ValueError) as e:
            raise RuntimeError(f"Failed to perform BM25 search: {e}") from e

    def _merge_search_results(
        self,
        semantic_results: list[SearchResult],
        text_results: list[SearchResult],
        semantic_weight: float,
    ) -> list[SearchResult]:
        """Merge and rerank results from semantic and text search."""
        workout_scores: dict[int, dict[str, Any]] = {}

        # Add semantic scores
        for result in semantic_results:
            if result.workout.id:
                workout_scores[result.workout.id] = {
                    "workout": result.workout,
                    "semantic": result.similarity_score or 0.0,
                    "text": 0.0,
                    "combined": 0.0,
                }

        # Add text search scores (normalize rank scores)
        if text_results:
            # PostgreSQL ts_rank returns values typically between 0 and 1
            # but can be higher, so we normalize
            max_rank = max([r.similarity_score or 0 for r in text_results])
            if max_rank > 0:
                for result in text_results:
                    if result.workout.id:
                        # Normalize to 0-1 range
                        normalized_rank = (result.similarity_score or 0) / max_rank

                        if result.workout.id in workout_scores:
                            workout_scores[result.workout.id]["text"] = normalized_rank
                        else:
                            workout_scores[result.workout.id] = {
                                "workout": result.workout,
                                "semantic": 0.0,
                                "text": normalized_rank,
                                "combined": 0.0,
                            }

        # Calculate combined scores
        text_weight = 1 - semantic_weight
        for _workout_id, scores in workout_scores.items():
            scores["combined"] = (
                semantic_weight * scores["semantic"] + text_weight * scores["text"]
            )

        # Sort by combined score and convert back to SearchResults
        sorted_results = sorted(
            workout_scores.values(), key=lambda x: x["combined"], reverse=True
        )

        return [
            SearchResult(
                workout=item["workout"],
                similarity_score=item["combined"],
                metadata_match=True,
            )
            for item in sorted_results
        ]

    def hybrid_search(
        self,
        query_text: str,
        semantic_weight: float = 0.7,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Hybrid search combining semantic similarity and full-text search.

        Args:
            query_text: Text to search for
            semantic_weight: Weight for semantic scores (0-1)
            limit: Maximum number of results

        Returns:
            List of search results ordered by combined score
        """
        try:
            # Get larger result sets for merging
            semantic_limit = min(limit * 5, 50)  # Get more results for better merging
            text_limit = min(limit * 5, 50)

            # Perform both searches
            semantic_results = self.search_summaries(query_text, limit=semantic_limit)
            text_results = self.text_search_workouts(query_text, limit=text_limit)

            # Merge and rerank
            merged_results = self._merge_search_results(
                semantic_results, text_results, semantic_weight
            )

            # Return top N results
            return merged_results[:limit]

        except (psycopg2.Error, ValueError) as e:
            raise RuntimeError(f"Failed to perform hybrid search: {e}") from e

    def search_summaries(
        self,
        query_text: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """
        Search workouts by semantic similarity on one_sentence_summary field.

        Args:
            query_text: Text to search for
            limit: Maximum number of results

        Returns:
            List of search results ordered by similarity
        """
        try:
            query_embedding = self._generate_query_embedding(query_text)
            rows_with_columns = self._execute_vector_similarity_query(
                query_embedding, limit
            )
            return self._convert_rows_to_search_results(rows_with_columns)
        except (psycopg2.Error, ValueError) as e:
            raise RuntimeError(f"Failed to search summaries: {e}") from e

    def vector_search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> list[SearchResult]:
        try:
            # Execute raw SQL with vector similarity using psycopg2
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                sql = """
                    SELECT *, 1 - (summary_embedding <=> %s::vector) as similarity
                    FROM workouts
                    WHERE summary_embedding IS NOT NULL
                    AND 1 - (summary_embedding <=> %s::vector) >= %s
                    ORDER BY summary_embedding <=> %s::vector
                    LIMIT %s
                    """
                cursor.execute(
                    sql,
                    (
                        query_embedding,
                        query_embedding,
                        similarity_threshold,
                        query_embedding,
                        limit,
                    ),
                )
                rows = cursor.fetchall()

                # Get column names
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )

            search_results = []
            for row in rows:
                row_dict = dict(zip(columns, row, strict=False))
                workout = Workout.from_dict(row_dict)
                similarity_score = row_dict.get("similarity", 0.0)
                search_results.append(
                    SearchResult(
                        workout=workout,
                        similarity_score=similarity_score,
                        metadata_match=True,
                    )
                )

            return search_results
        except (psycopg2.Error, ValueError) as e:
            raise RuntimeError(f"Failed to perform vector search: {e}") from e

    def _matches_filters(self, workout: Workout, filters: WorkoutFilter | None) -> bool:
        """Check if a workout matches the provided filters."""
        if not filters:
            return True

        if filters.movements and not any(
            m in workout.movements for m in filters.movements
        ):
            return False

        if filters.equipment and not any(
            e in workout.equipment for e in filters.equipment
        ):
            return False

        if filters.workout_type and workout.workout_type != filters.workout_type:
            return False

        if filters.workout_name and workout.workout_name != filters.workout_name:
            return False

        if filters.start_date and workout.date and workout.date < filters.start_date:
            return False

        if filters.end_date and workout.date and workout.date > filters.end_date:
            return False

        if filters.has_video is not None and workout.has_video != filters.has_video:
            return False

        return not (
            filters.has_article is not None
            and workout.has_article != filters.has_article
        )

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def filter_workouts(self, filters: WorkoutFilter) -> list[Workout]:
        """Filter workouts using PostgreSQL."""
        # TODO: Implement PostgreSQL-based filtering if needed
        raise NotImplementedError("Use direct SQL for PostgreSQL filtering")

    # Listing/Browsing

    def list_workouts(
        self, page: int = 1, page_size: int = 20, filters: WorkoutFilter | None = None
    ) -> tuple[list[Workout], int]:
        """List workouts using PostgreSQL."""
        # TODO: Implement PostgreSQL-based listing if needed
        raise NotImplementedError("Use direct SQL for PostgreSQL listing")

    def get_workouts_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[Workout]:
        filters = WorkoutFilter(start_date=start_date, end_date=end_date)
        return self.filter_workouts(filters)

    def get_random_workouts(
        self, count: int = 5, filters: WorkoutFilter | None = None
    ) -> list[Workout]:
        # Get all workouts with filters, then randomize client-side
        all_workouts = (
            self.filter_workouts(filters)
            if filters
            else self.filter_workouts(WorkoutFilter())
        )
        import random

        return random.sample(all_workouts, min(count, len(all_workouts)))

    # Analytics

    def get_movement_counts(self) -> dict[str, int]:
        """Get movement usage statistics using database aggregation."""
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                sql = """
                    SELECT movement, COUNT(*) as count
                    FROM workouts, unnest(movements) as movement
                    WHERE movements IS NOT NULL
                    GROUP BY movement
                    ORDER BY count DESC
                    """
                cursor.execute(sql)
                rows = cursor.fetchall()
                return {row[0]: row[1] for row in rows}
        except (psycopg2.Error, ValueError) as e:
            raise RuntimeError(f"Failed to get movement counts: {e}") from e

    def get_equipment_usage(self) -> dict[str, int]:
        """Get equipment usage statistics using database aggregation."""
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                sql = """
                    SELECT equipment_item, COUNT(*) as count
                    FROM workouts, unnest(equipment) as equipment_item
                    WHERE equipment IS NOT NULL
                    GROUP BY equipment_item
                    ORDER BY count DESC
                    """
                cursor.execute(sql)
                rows = cursor.fetchall()
                return {row[0]: row[1] for row in rows}
        except (psycopg2.Error, ValueError) as e:
            raise RuntimeError(f"Failed to get equipment usage: {e}") from e
