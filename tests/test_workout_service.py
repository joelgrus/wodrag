from unittest.mock import MagicMock

import pytest

from wodrag.database.models import SearchResult, Workout
from wodrag.services.workout_service import WorkoutService


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock WorkoutRepository."""
    return MagicMock()


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Create a mock EmbeddingService."""
    return MagicMock()


@pytest.fixture
def workout_service(
    mock_repository: MagicMock, mock_embedding_service: MagicMock
) -> WorkoutService:
    """Create a WorkoutService with mocked dependencies."""
    return WorkoutService(mock_repository, mock_embedding_service)


class TestWorkoutService:
    def test_initialization(
        self, mock_repository: MagicMock, mock_embedding_service: MagicMock
    ) -> None:
        service = WorkoutService(mock_repository, mock_embedding_service)

        assert service.repository == mock_repository
        assert service.embedding_service == mock_embedding_service

    def test_create_workout_with_embedding(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        # Setup
        workout_data = {
            "workout": "3 rounds for time: 10 pull-ups",
            "scaling": "Scale to ring rows",
            "movements": ["pull up"],
            "equipment": ["pull up bar"],
            "one_sentence_summary": "Three rounds of pull-ups for time",
        }

        mock_embedding = [0.1, 0.2, 0.3]
        mock_summary_embedding = [0.4, 0.5, 0.6]
        # Set up side_effect for multiple calls
        mock_embedding_service.generate_embedding.side_effect = [
            mock_summary_embedding,  # First call for summary
            mock_embedding,  # Second call for full text
        ]

        created_workout = Workout(
            id=1,
            workout="3 rounds for time: 10 pull-ups",
            scaling="Scale to ring rows",
            movements=["pull up"],
            equipment=["pull up bar"],
            one_sentence_summary="Three rounds of pull-ups for time",
            workout_embedding=mock_embedding,
            summary_embedding=mock_summary_embedding,
        )
        mock_repository.insert_workout.return_value = created_workout

        # Execute
        result = workout_service.create_workout(workout_data)

        # Assert both embeddings were generated
        assert mock_embedding_service.generate_embedding.call_count == 2
        mock_embedding_service.generate_embedding.assert_any_call(
            "Three rounds of pull-ups for time"
        )
        mock_embedding_service.generate_embedding.assert_any_call(
            "3 rounds for time: 10 pull-ups\nScale to ring rows"
        )
        mock_repository.insert_workout.assert_called_once()

        # Check that the workout passed to repository has both embeddings
        inserted_workout = mock_repository.insert_workout.call_args[0][0]
        assert inserted_workout.workout_embedding == mock_embedding
        assert inserted_workout.summary_embedding == mock_summary_embedding

        assert result.id == 1
        assert result.workout_embedding == mock_embedding
        assert result.summary_embedding == mock_summary_embedding

    def test_create_workout_without_scaling(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        workout_data = {"workout": "Run 5k", "movements": ["running"]}

        mock_embedding = [0.4, 0.5, 0.6]
        mock_embedding_service.generate_embedding.return_value = mock_embedding

        created_workout = Workout(
            id=1, workout="Run 5k", workout_embedding=mock_embedding
        )
        mock_repository.insert_workout.return_value = created_workout

        workout_service.create_workout(workout_data)

        # Should generate embedding with just workout text
        mock_embedding_service.generate_embedding.assert_called_once_with("Run 5k")

    def test_create_workout_no_workout_text(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        workout_data = {"movements": ["pull up"], "equipment": ["pull up bar"]}

        created_workout = Workout(id=1, movements=["pull up"])
        mock_repository.insert_workout.return_value = created_workout

        result = workout_service.create_workout(workout_data)

        # Should not generate embedding
        mock_embedding_service.generate_embedding.assert_not_called()
        assert result.workout_embedding is None

    def test_update_workout_text_changed(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        # Setup current workout
        current_workout = Workout(
            id=1, workout="Old workout", scaling="Old scaling", movements=["pull up"]
        )
        mock_repository.get_workout.return_value = current_workout

        # Setup new embedding
        mock_embedding = [0.7, 0.8, 0.9]
        mock_embedding_service.generate_embedding.return_value = mock_embedding

        # Setup updated workout return
        updated_workout = Workout(
            id=1,
            workout="New workout",
            scaling="New scaling",
            movements=["pull up"],
            workout_embedding=mock_embedding,
        )
        mock_repository.update_workout_metadata.return_value = updated_workout

        # Execute
        updates = {"workout": "New workout", "scaling": "New scaling"}
        result = workout_service.update_workout(1, updates)

        # Assert
        mock_embedding_service.generate_embedding.assert_called_once_with(
            "New workout\nNew scaling"
        )
        mock_repository.update_workout_metadata.assert_called_once_with(
            workout_id=1,
            movements=["pull up"],
            equipment=[],
            workout_type=None,
            workout_name=None,
            one_sentence_summary=None,
            summary_embedding=None,
        )
        assert result == updated_workout

    def test_update_workout_summary_changed(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        # Setup current workout
        current_workout = Workout(
            id=1, workout="Existing workout", one_sentence_summary="Old summary"
        )
        mock_repository.get_workout.return_value = current_workout

        # Setup new summary embedding
        mock_summary_embedding = [0.7, 0.8, 0.9]
        mock_embedding_service.generate_embedding.return_value = mock_summary_embedding

        # Setup updated workout return
        updated_workout = Workout(
            id=1,
            workout="Existing workout",
            one_sentence_summary="New workout summary",
            summary_embedding=mock_summary_embedding,
        )
        mock_repository.update_workout_metadata.return_value = updated_workout

        # Execute
        updates = {"one_sentence_summary": "New workout summary"}
        workout_service.update_workout(1, updates)

        # Assert - should only generate summary embedding
        mock_embedding_service.generate_embedding.assert_called_once_with(
            "New workout summary"
        )
        mock_repository.update_workout_metadata.assert_called_once_with(
            workout_id=1,
            movements=[],
            equipment=[],
            workout_type=None,
            workout_name=None,
            one_sentence_summary="New workout summary",
            summary_embedding=mock_summary_embedding,
        )

    def test_update_workout_no_text_change(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        current_workout = Workout(
            id=1, workout="Existing workout", movements=["push up"]
        )
        mock_repository.get_workout.return_value = current_workout

        updated_workout = Workout(
            id=1, workout="Existing workout", movements=["pull up", "push up"]
        )
        mock_repository.update_workout_metadata.return_value = updated_workout

        updates = {"movements": ["pull up", "push up"]}
        workout_service.update_workout(1, updates)

        # Should not regenerate embedding
        mock_embedding_service.generate_embedding.assert_not_called()

    def test_update_workout_not_found(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        mock_repository.get_workout.return_value = None

        result = workout_service.update_workout(999, {"workout": "New"})

        assert result is None
        mock_repository.update_workout_metadata.assert_not_called()

    def test_search_workouts_with_query(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        query = "pull-ups and running"
        mock_embedding = [0.1, 0.2, 0.3]
        mock_embedding_service.generate_embedding.return_value = mock_embedding

        mock_results = [
            SearchResult(
                workout=Workout(id=1, workout="10 pull-ups"), similarity_score=0.9
            )
        ]
        mock_repository.search_summaries.return_value = mock_results

        results = workout_service.search_workouts(query)

        mock_embedding_service.generate_embedding.assert_called_once_with(query)
        mock_repository.search_summaries.assert_called_once_with(
            query_text=query, limit=10
        )
        assert results == mock_results

    def test_search_workouts_no_query(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock,
    ) -> None:
        mock_workouts = [
            Workout(id=1, workout="Workout 1"),
            Workout(id=2, workout="Workout 2"),
        ]
        mock_repository.filter_workouts.return_value = mock_workouts

        results = workout_service.search_workouts("")

        mock_embedding_service.generate_embedding.assert_not_called()
        mock_repository.filter_workouts.assert_called_once()

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].workout == mock_workouts[0]

    def test_get_workout(
        self, workout_service: WorkoutService, mock_repository: MagicMock
    ) -> None:
        mock_workout = Workout(id=1, workout="Test")
        mock_repository.get_workout.return_value = mock_workout

        result = workout_service.get_workout(1)

        mock_repository.get_workout.assert_called_once_with(1)
        assert result == mock_workout

    def test_list_workouts(
        self, workout_service: WorkoutService, mock_repository: MagicMock
    ) -> None:
        mock_workouts = [Workout(id=1), Workout(id=2)]
        mock_repository.list_workouts.return_value = (mock_workouts, 100)

        workouts, total = workout_service.list_workouts(page=2, page_size=10)

        mock_repository.list_workouts.assert_called_once_with(2, 10, None)
        assert workouts == mock_workouts
        assert total == 100

    def test_get_random_workouts(
        self, workout_service: WorkoutService, mock_repository: MagicMock
    ) -> None:
        mock_workouts = [Workout(id=i) for i in range(5)]
        mock_repository.get_random_workouts.return_value = mock_workouts

        results = workout_service.get_random_workouts(5)

        mock_repository.get_random_workouts.assert_called_once_with(5, None)
        assert results == mock_workouts

    def test_get_movement_counts(
        self, workout_service: WorkoutService, mock_repository: MagicMock
    ) -> None:
        mock_counts = {"pull up": 10, "push up": 5}
        mock_repository.get_movement_counts.return_value = mock_counts

        result = workout_service.get_movement_counts()

        mock_repository.get_movement_counts.assert_called_once()
        assert result == mock_counts

    def test_get_equipment_usage(
        self, workout_service: WorkoutService, mock_repository: MagicMock
    ) -> None:
        mock_usage = {"barbell": 20, "dumbbell": 15}
        mock_repository.get_equipment_usage.return_value = mock_usage

        result = workout_service.get_equipment_usage()

        mock_repository.get_equipment_usage.assert_called_once()
        assert result == mock_usage
