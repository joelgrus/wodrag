from __future__ import annotations

from typing import Any

from ..database import SearchResult, Workout, WorkoutFilter, WorkoutRepository
from .embedding_service import EmbeddingService


class WorkoutService:
    """Service for workout business logic operations."""

    def __init__(
        self, repository: WorkoutRepository, embedding_service: EmbeddingService
    ):
        """
        Initialize the workout service.

        Args:
            repository: Database repository for workout operations
            embedding_service: Service for generating embeddings
        """
        self.repository = repository
        self.embedding_service = embedding_service

    def create_workout(self, workout_data: dict[str, Any]) -> Workout:
        """
        Create a new workout with automatic embedding generation.

        Args:
            workout_data: Dictionary containing workout fields

        Returns:
            Created workout with generated embedding if applicable
        """
        workout = Workout(**workout_data)

        # Generate embedding from one-sentence summary if it exists
        if workout.one_sentence_summary and workout.one_sentence_summary.strip():
            workout.summary_embedding = self.embedding_service.generate_embedding(
                workout.one_sentence_summary.strip()
            )

        # Keep generating full text embedding for backward compatibility
        if workout.workout and workout.workout.strip():
            embedding_text = workout.workout
            if workout.scaling and workout.scaling.strip():
                embedding_text += f"\n{workout.scaling}"

            workout.workout_embedding = self.embedding_service.generate_embedding(
                embedding_text
            )

        return self.repository.insert_workout(workout)

    def update_workout(
        self, workout_id: int, updates: dict[str, Any]
    ) -> Workout | None:
        """
        Update an existing workout, regenerating embedding if text changed.

        Args:
            workout_id: ID of workout to update
            updates: Dictionary of fields to update

        Returns:
            Updated workout or None if not found
        """
        # Get current workout
        current_workout = self.repository.get_workout(workout_id)
        if not current_workout:
            return None

        # Check if embedding regeneration is needed
        text_changed = "workout" in updates or "scaling" in updates
        summary_changed = "one_sentence_summary" in updates

        # Apply updates
        for key, value in updates.items():
            if hasattr(current_workout, key):
                setattr(current_workout, key, value)

        # Regenerate summary embedding if summary changed
        if summary_changed and current_workout.one_sentence_summary:
            current_workout.summary_embedding = (
                self.embedding_service.generate_embedding(
                    current_workout.one_sentence_summary.strip()
                )
            )

        # Regenerate full text embedding if text changed (backward compatibility)
        if text_changed and current_workout.workout:
            embedding_text = current_workout.workout
            if current_workout.scaling and current_workout.scaling.strip():
                embedding_text += f"\n{current_workout.scaling}"

            current_workout.workout_embedding = (
                self.embedding_service.generate_embedding(embedding_text)
            )

        # Update in database using repository's update method
        return self.repository.update_workout_metadata(
            workout_id=workout_id,
            movements=current_workout.movements,
            equipment=current_workout.equipment,
            workout_type=current_workout.workout_type,
            workout_name=current_workout.workout_name,
            one_sentence_summary=current_workout.one_sentence_summary,
            summary_embedding=current_workout.summary_embedding,
        )

    def search_workouts(
        self, query: str, filters: WorkoutFilter | None = None, limit: int = 10
    ) -> list[SearchResult]:
        """
        Search workouts using semantic similarity.

        Args:
            query: Text query to search for
            filters: Optional metadata filters
            limit: Maximum number of results

        Returns:
            List of search results with similarity scores
        """
        if not query or not query.strip():
            # If no query, just return filtered results
            workouts = self.repository.filter_workouts(filters or WorkoutFilter())
            return [
                SearchResult(
                    workout=workout, similarity_score=None, metadata_match=True
                )
                for workout in workouts[:limit]
            ]

        # Generate embedding for query
        self.embedding_service.generate_embedding(query.strip())

        # Perform semantic search on summaries
        return self.repository.search_summaries(query_text=query.strip(), limit=limit)

    def get_workout(self, workout_id: int) -> Workout | None:
        """Get a workout by ID."""
        return self.repository.get_workout(workout_id)

    def list_workouts(
        self, page: int = 1, page_size: int = 20, filters: WorkoutFilter | None = None
    ) -> tuple[list[Workout], int]:
        """List workouts with pagination."""
        return self.repository.list_workouts(page, page_size, filters)

    def get_random_workouts(
        self, count: int = 5, filters: WorkoutFilter | None = None
    ) -> list[Workout]:
        """Get random workouts."""
        return self.repository.get_random_workouts(count, filters)

    def get_movement_counts(self) -> dict[str, int]:
        """Get movement usage statistics."""
        return self.repository.get_movement_counts()

    def get_equipment_usage(self) -> dict[str, int]:
        """Get equipment usage statistics."""
        return self.repository.get_equipment_usage()
