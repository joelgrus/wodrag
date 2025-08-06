from __future__ import annotations

from datetime import date
from typing import Any

from postgrest.exceptions import APIError
from supabase import Client

from .client import get_supabase_client
from .models import SearchResult, Workout, WorkoutFilter


class WorkoutRepository:
    """Repository for workout database operations."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()
        self.table_name = "workouts"

    # CRUD Operations

    def insert_workout(self, workout: Workout) -> Workout:
        """
        Insert a workout into the database.

        Args:
            workout: Workout object to insert (should include embedding if needed)

        Returns:
            Inserted workout with database-assigned ID
        """
        data = workout.to_dict()

        try:
            result = self.client.table(self.table_name).insert(data).execute()
            return Workout.from_dict(result.data[0])
        except APIError as e:
            raise RuntimeError(f"Failed to insert workout: {e}") from e

    def get_workout(self, workout_id: int) -> Workout | None:
        try:
            result = (
                self.client.table(self.table_name)
                .select("*")
                .eq("id", workout_id)
                .single()
                .execute()
            )
            return Workout.from_dict(result.data) if result.data else None
        except APIError:
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

        try:
            result = (
                self.client.table(self.table_name)
                .update(updates)
                .eq("id", workout_id)
                .execute()
            )
            return Workout.from_dict(result.data[0]) if result.data else None
        except APIError as e:
            raise RuntimeError(f"Failed to update workout: {e}") from e

    def delete_workout(self, workout_id: int) -> bool:
        try:
            self.client.table(self.table_name).delete().eq("id", workout_id).execute()
            return True
        except APIError:
            return False

    # Search Methods

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
            # 1. Embed the user's query
            from ..services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.generate_embedding(query_text)
            
            # 2. Search database ordered by vector similarity
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            sql = f"""
            SELECT *, 1 - (summary_embedding <=> '{embedding_str}') as similarity
            FROM workouts
            WHERE summary_embedding IS NOT NULL
            ORDER BY summary_embedding <=> '{embedding_str}'
            LIMIT {limit}
            """
            
            # 3. Execute using client-side similarity calculation
            # Get all workouts with embeddings
            query = self.client.table(self.table_name).select("*")
            query = query.not_.is_("summary_embedding", "null")
            result = query.execute()
            
            # Calculate similarities and sort
            scored_results = []
            for row in result.data:
                workout = Workout.from_dict(row)
                if workout.summary_embedding:
                    similarity = self._cosine_similarity(query_embedding, workout.summary_embedding)
                    scored_results.append((workout, similarity))
            
            # Sort by similarity
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            # Convert to SearchResults
            search_results = []
            for workout, similarity in scored_results[:limit]:
                search_results.append(
                    SearchResult(
                        workout=workout,
                        similarity_score=similarity,
                        metadata_match=True,
                    )
                )
            
            return search_results
            
        except Exception as e:
            raise RuntimeError(f"Failed to search summaries: {e}") from e

    def vector_search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> list[SearchResult]:
        try:
            # Use the match_summaries function for pure vector search
            result = self.client.rpc(
                "match_summaries",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": similarity_threshold,
                    "match_count": limit,
                }
            ).execute()

            search_results = []
            for row in result.data:
                workout = Workout.from_dict(row)
                similarity_score = row.get("similarity", 0.0)
                search_results.append(
                    SearchResult(
                        workout=workout,
                        similarity_score=similarity_score,
                        metadata_match=True,
                    )
                )

            return search_results
        except APIError as e:
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

        if (
            filters.has_article is not None
            and workout.has_article != filters.has_article
        ):
            return False

        return True

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def filter_workouts(self, filters: WorkoutFilter) -> list[Workout]:
        query = self.client.table(self.table_name).select("*")

        if filters.movements:
            query = query.contains("movements", filters.movements)

        if filters.equipment:
            query = query.overlaps("equipment", filters.equipment)

        if filters.workout_type:
            query = query.eq("workout_type", filters.workout_type)

        if filters.workout_name:
            query = query.eq("workout_name", filters.workout_name)

        if filters.start_date:
            query = query.gte("date", filters.start_date.isoformat())

        if filters.end_date:
            query = query.lte("date", filters.end_date.isoformat())

        if filters.has_video is not None:
            query = query.eq("has_video", filters.has_video)

        if filters.has_article is not None:
            query = query.eq("has_article", filters.has_article)

        try:
            result = query.execute()
            return [Workout.from_dict(row) for row in result.data]
        except APIError as e:
            raise RuntimeError(f"Failed to filter workouts: {e}") from e

    # Listing/Browsing

    def list_workouts(
        self, page: int = 1, page_size: int = 20, filters: WorkoutFilter | None = None
    ) -> tuple[list[Workout], int]:
        offset = (page - 1) * page_size

        query = self.client.table(self.table_name).select("*", count="exact")

        if filters:
            if filters.movements:
                query = query.contains("movements", filters.movements)
            if filters.equipment:
                query = query.overlaps("equipment", filters.equipment)
            if filters.workout_type:
                query = query.eq("workout_type", filters.workout_type)
            if filters.workout_name:
                query = query.eq("workout_name", filters.workout_name)
            if filters.start_date:
                query = query.gte("date", filters.start_date.isoformat())
            if filters.end_date:
                query = query.lte("date", filters.end_date.isoformat())

        query = query.order("date", desc=True).limit(page_size).offset(offset)

        try:
            result = query.execute()
            workouts = [Workout.from_dict(row) for row in result.data]
            total_count = result.count or 0
            return workouts, total_count
        except APIError as e:
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
        # Client-side aggregation - simple and reliable
        all_workouts = self.filter_workouts(WorkoutFilter())
        movement_counts: dict[str, int] = {}
        for workout in all_workouts:
            for movement in workout.movements:
                movement_counts[movement] = movement_counts.get(movement, 0) + 1
        return movement_counts

    def get_equipment_usage(self) -> dict[str, int]:
        # Client-side aggregation - simple and reliable
        all_workouts = self.filter_workouts(WorkoutFilter())
        equipment_counts: dict[str, int] = {}
        for workout in all_workouts:
            for item in workout.equipment:
                equipment_counts[item] = equipment_counts.get(item, 0) + 1
        return equipment_counts
