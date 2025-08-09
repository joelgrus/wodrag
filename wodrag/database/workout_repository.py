from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import date
from typing import Any, TYPE_CHECKING

import psycopg2

from .client import get_postgres_connection
from .models import SearchResult, Workout, WorkoutFilter

if TYPE_CHECKING:
    from ..services.embedding_service import EmbeddingService


class WorkoutRepository:
    """Repository for workout database operations."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.table_name = "workouts"
        self.embedding_service = embedding_service

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
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                # Convert workout to dict for easier SQL generation
                workout_dict = workout.to_dict()

                # Remove id if it's None (auto-generated)
                if workout_dict.get("id") is None:
                    workout_dict.pop("id", None)

                # Prepare column names and placeholders
                columns = list(workout_dict.keys())
                placeholders = ["%s"] * len(columns)
                values = [workout_dict[col] for col in columns]

                # Build INSERT query
                columns_str = ", ".join(columns)
                placeholders_str = ", ".join(placeholders)
                query = f"""
                    INSERT INTO workouts ({columns_str})
                    VALUES ({placeholders_str})
                    RETURNING id
                """

                cursor.execute(query, values)
                result = cursor.fetchone()
                if not result:
                    raise RuntimeError("Insert failed - no ID returned")
                workout_id = result[0]
                conn.commit()

                # Return the workout with the new ID
                workout.id = workout_id
                return workout

        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to insert workout: {e}") from e

    def get_workout(self, workout_id: int) -> Workout | None:
        """Get a single workout by ID using PostgreSQL."""
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                cursor.execute("SELECT * FROM workouts WHERE id = %s", (workout_id,))
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

    def get_workout_by_date(self, workout_date: date) -> Workout | None:
        """Get a single workout by exact date using PostgreSQL.

        Args:
            workout_date: Date to look up (YYYY-MM-DD)

        Returns:
            Workout if found, otherwise None
        """
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                # Cast to date on both sides to be robust if column type differs
                cursor.execute(
                    (
                        "SELECT * FROM workouts WHERE date::date = %s::date "
                        "ORDER BY id LIMIT 1"
                    ),
                    (workout_date,),
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

    def get_similar_workouts(
        self, workout_id: int, limit: int = 5, embedding: str = "summary"
    ) -> list[SearchResult]:
        """Find workouts similar to the given workout using a chosen embedding.

        Uses pgvector distance to the target workout's embedding. If the
        target workout has no embedding, returns an empty list.

        Args:
            workout_id: ID of the anchor workout
            limit: number of similar workouts to return
            embedding: "summary" to use one_sentence_summary embedding (default),
                or "workout" to use full workout text embedding

        Returns:
            A list of SearchResult with similarity scores (cosine similarity)
        """
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                col = (
                    "summary_embedding"
                    if embedding != "workout"
                    else "workout_embedding"
                )
                # Ensure the anchor has an embedding
                cursor.execute(
                    f"SELECT {col} FROM workouts WHERE id = %s", (workout_id,)
                )
                anchor = cursor.fetchone()
                if not anchor or anchor[0] is None:
                    return []

                # Select others ordered by distance to the anchor's embedding
                sql = f"""
                    SELECT w.*, 1 - (w.{col} <=> anchor.emb) as similarity
                    FROM workouts w
                    CROSS JOIN (
                        SELECT {col} AS emb FROM workouts WHERE id = %s
                    ) AS anchor
                    WHERE w.{col} IS NOT NULL AND w.id <> %s
                    ORDER BY w.{col} <=> anchor.emb
                    LIMIT %s
                """
                cursor.execute(sql, (workout_id, workout_id, limit))
                rows = cursor.fetchall()
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )

                results: list[SearchResult] = []
                for row in rows:
                    row_dict = dict(zip(columns, row, strict=False))
                    similarity = float(row_dict.pop("similarity", 0.0) or 0.0)
                    workout = Workout.from_dict(row_dict)
                    results.append(
                        SearchResult(
                            workout=workout,
                            similarity_score=similarity,
                            metadata_match=True,
                        )
                    )
                return results
        except (psycopg2.Error, ValueError) as e:
            raise RuntimeError(f"Failed to fetch similar workouts: {e}") from e

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

        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                # Build SET clause
                set_clauses = []
                values = []

                for column, value in updates.items():
                    set_clauses.append(f"{column} = %s")
                    values.append(value)

                set_clause = ", ".join(set_clauses)
                values.append(workout_id)  # Add workout_id for WHERE clause

                query = f"""
                    UPDATE workouts
                    SET {set_clause}
                    WHERE id = %s
                """

                cursor.execute(query, values)
                conn.commit()

                if cursor.rowcount == 0:
                    return None  # Workout not found

                # Return updated workout
                return self.get_workout(workout_id)

        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to update workout {workout_id}: {e}") from e

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
        if not self.embedding_service:
            # Lazy initialization if not injected
            from ..services.embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()
        return self.embedding_service.generate_embedding(query_text)

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
                [desc[0] for desc in cursor.description] if cursor.description else []
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
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                where_clauses = []
                values: list[Any] = []

                if filters.movements:
                    # Check if any of the filter movements match
                    movement_conditions = []
                    for movement in filters.movements:
                        movement_conditions.append("%s = ANY(movements)")
                        values.append(movement)
                    where_clauses.append(f"({' OR '.join(movement_conditions)})")

                if filters.equipment:
                    # Check if any of the filter equipment match
                    equipment_conditions = []
                    for equip in filters.equipment:
                        equipment_conditions.append("%s = ANY(equipment)")
                        values.append(equip)
                    where_clauses.append(f"({' OR '.join(equipment_conditions)})")

                if filters.workout_type:
                    where_clauses.append("workout_type = %s")
                    values.append(filters.workout_type)

                if filters.workout_name:
                    where_clauses.append("workout_name ILIKE %s")
                    values.append(f"%{filters.workout_name}%")

                if filters.start_date:
                    where_clauses.append("date >= %s")
                    values.append(filters.start_date)

                if filters.end_date:
                    where_clauses.append("date <= %s")
                    values.append(filters.end_date)

                if filters.has_video is not None:
                    where_clauses.append("has_video = %s")
                    values.append(filters.has_video)

                if filters.has_article is not None:
                    where_clauses.append("has_article = %s")
                    values.append(filters.has_article)

                # Build query
                base_query = "SELECT * FROM workouts"
                if where_clauses:
                    where_clause = " AND ".join(where_clauses)
                    query = f"{base_query} WHERE {where_clause} ORDER BY date DESC"
                else:
                    query = f"{base_query} ORDER BY date DESC"

                cursor.execute(query, values)
                rows = cursor.fetchall()

                if not rows:
                    return []

                # Convert to Workout objects
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
                workouts = []
                for row in rows:
                    row_dict = dict(zip(columns, row, strict=False))
                    workouts.append(Workout.from_dict(row_dict))

                return workouts

        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to filter workouts: {e}") from e

    # Listing/Browsing

    def list_workouts(
        self, page: int = 1, page_size: int = 20, filters: WorkoutFilter | None = None
    ) -> tuple[list[Workout], int]:
        """List workouts using PostgreSQL with pagination and optional filters."""
        try:
            with self._get_pg_connection() as conn, conn.cursor() as cursor:
                # Build WHERE clause if filters provided
                where_clauses = []
                values: list[Any] = []

                if filters:
                    if filters.movements:
                        movement_conditions = []
                        for movement in filters.movements:
                            movement_conditions.append("%s = ANY(movements)")
                            values.append(movement)
                        where_clauses.append(f"({' OR '.join(movement_conditions)})")

                    if filters.equipment:
                        equipment_conditions = []
                        for equip in filters.equipment:
                            equipment_conditions.append("%s = ANY(equipment)")
                            values.append(equip)
                        where_clauses.append(f"({' OR '.join(equipment_conditions)})")

                    if filters.workout_type:
                        where_clauses.append("workout_type = %s")
                        values.append(filters.workout_type)

                    if filters.workout_name:
                        where_clauses.append("workout_name ILIKE %s")
                        values.append(f"%{filters.workout_name}%")

                    if filters.start_date:
                        where_clauses.append("date >= %s")
                        values.append(filters.start_date)

                    if filters.end_date:
                        where_clauses.append("date <= %s")
                        values.append(filters.end_date)

                    if filters.has_video is not None:
                        where_clauses.append("has_video = %s")
                        values.append(filters.has_video)

                    if filters.has_article is not None:
                        where_clauses.append("has_article = %s")
                        values.append(filters.has_article)

                # Build WHERE clause
                where_clause = ""
                if where_clauses:
                    where_clause = f"WHERE {' AND '.join(where_clauses)}"

                # Get total count
                count_query = f"SELECT COUNT(*) FROM workouts {where_clause}"
                cursor.execute(count_query, values)
                count_result = cursor.fetchone()
                if not count_result:
                    raise RuntimeError("Count query failed")
                total_count = count_result[0]

                # Calculate pagination
                offset = (page - 1) * page_size

                # Get paginated results
                data_query = f"""
                    SELECT * FROM workouts
                    {where_clause}
                    ORDER BY date DESC
                    LIMIT %s OFFSET %s
                """

                cursor.execute(data_query, values + [page_size, offset])
                rows = cursor.fetchall()

                # Convert to Workout objects
                if not rows:
                    return [], total_count

                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
                workouts = []
                for row in rows:
                    row_dict = dict(zip(columns, row, strict=False))
                    workouts.append(Workout.from_dict(row_dict))

                return workouts, total_count

        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to list workouts: {e}") from e

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
