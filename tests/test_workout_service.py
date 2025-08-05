import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from wodrag.database.models import Workout, WorkoutFilter, SearchResult
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
def workout_service(mock_repository: MagicMock, mock_embedding_service: MagicMock) -> WorkoutService:
    """Create a WorkoutService with mocked dependencies."""
    return WorkoutService(mock_repository, mock_embedding_service)


class TestWorkoutService:
    def test_initialization(self, mock_repository: MagicMock, mock_embedding_service: MagicMock) -> None:
        service = WorkoutService(mock_repository, mock_embedding_service)
        
        assert service.repository == mock_repository
        assert service.embedding_service == mock_embedding_service

    def test_create_workout_with_embedding(
        self, 
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock
    ) -> None:
        # Setup
        workout_data = {
            "workout": "3 rounds for time: 10 pull-ups",
            "scaling": "Scale to ring rows",
            "movements": ["pull up"],
            "equipment": ["pull up bar"]
        }
        
        mock_embedding = [0.1, 0.2, 0.3]
        mock_embedding_service.generate_embedding.return_value = mock_embedding
        
        created_workout = Workout(
            id=1,
            workout="3 rounds for time: 10 pull-ups",
            scaling="Scale to ring rows",
            movements=["pull up"],
            equipment=["pull up bar"],
            workout_embedding=mock_embedding
        )
        mock_repository.insert_workout.return_value = created_workout
        
        # Execute
        result = workout_service.create_workout(workout_data)
        
        # Assert
        mock_embedding_service.generate_embedding.assert_called_once_with(
            "3 rounds for time: 10 pull-ups\nScale to ring rows"
        )
        mock_repository.insert_workout.assert_called_once()
        
        # Check that the workout passed to repository has embedding
        inserted_workout = mock_repository.insert_workout.call_args[0][0]
        assert inserted_workout.workout_embedding == mock_embedding
        
        assert result.id == 1
        assert result.workout_embedding == mock_embedding

    def test_create_workout_without_scaling(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock
    ) -> None:
        workout_data = {
            "workout": "Run 5k",
            "movements": ["running"]
        }
        
        mock_embedding = [0.4, 0.5, 0.6]
        mock_embedding_service.generate_embedding.return_value = mock_embedding
        
        created_workout = Workout(id=1, workout="Run 5k", workout_embedding=mock_embedding)
        mock_repository.insert_workout.return_value = created_workout
        
        workout_service.create_workout(workout_data)
        
        # Should generate embedding with just workout text
        mock_embedding_service.generate_embedding.assert_called_once_with("Run 5k")

    def test_create_workout_no_workout_text(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock
    ) -> None:
        workout_data = {
            "movements": ["pull up"],
            "equipment": ["pull up bar"]
        }
        
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
        mock_embedding_service: MagicMock
    ) -> None:
        # Setup current workout
        current_workout = Workout(
            id=1,
            workout="Old workout",
            scaling="Old scaling",
            movements=["pull up"]
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
            workout_embedding=mock_embedding
        )
        mock_repository.update_workout_metadata.return_value = updated_workout
        
        # Execute
        updates = {
            "workout": "New workout",
            "scaling": "New scaling"
        }
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
            workout_name=None
        )
        assert result.workout_embedding == mock_embedding

    def test_update_workout_no_text_change(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock
    ) -> None:
        current_workout = Workout(
            id=1,
            workout="Existing workout",
            movements=["pull up"]
        )
        mock_repository.get_workout.return_value = current_workout
        
        updated_workout = Workout(
            id=1,
            workout="Existing workout",
            movements=["pull up", "push up"]
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
        mock_embedding_service: MagicMock
    ) -> None:
        mock_repository.get_workout.return_value = None
        
        result = workout_service.update_workout(999, {"workout": "New"})
        
        assert result is None
        mock_embedding_service.generate_embedding.assert_not_called()

    def test_search_workouts_with_query(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock
    ) -> None:
        # Setup
        query = "crossfit workouts"
        filters = WorkoutFilter(movements=["pull up"])
        
        mock_embedding = [0.1, 0.2, 0.3]
        mock_embedding_service.generate_embedding.return_value = mock_embedding
        
        search_results = [
            SearchResult(
                workout=Workout(id=1, workout="Fran"),
                similarity_score=0.9,
                metadata_match=True
            )
        ]
        mock_repository.hybrid_search.return_value = search_results
        
        # Execute
        results = workout_service.search_workouts(query, filters, limit=10)
        
        # Assert
        mock_embedding_service.generate_embedding.assert_called_once_with("crossfit workouts")
        mock_repository.hybrid_search.assert_called_once_with(
            query_embedding=mock_embedding,
            filters=filters,
            limit=10
        )
        assert len(results) == 1
        assert results[0].similarity_score == 0.9

    def test_search_workouts_empty_query(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock,
        mock_embedding_service: MagicMock
    ) -> None:
        filters = WorkoutFilter(movements=["pull up"])
        
        workouts = [
            Workout(id=1, workout="Test 1"),
            Workout(id=2, workout="Test 2")
        ]
        mock_repository.filter_workouts.return_value = workouts
        
        results = workout_service.search_workouts("", filters, limit=5)
        
        # Should not generate embedding
        mock_embedding_service.generate_embedding.assert_not_called()
        mock_repository.filter_workouts.assert_called_once_with(filters)
        
        # Should return first 5 results as SearchResult objects
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].workout.id == 1
        assert results[1].workout.id == 2

    def test_get_workout(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock
    ) -> None:
        workout = Workout(id=1, workout="Test")
        mock_repository.get_workout.return_value = workout
        
        result = workout_service.get_workout(1)
        
        mock_repository.get_workout.assert_called_once_with(1)
        assert result == workout

    def test_list_workouts(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock
    ) -> None:
        workouts = [Workout(id=1), Workout(id=2)]
        total_count = 50
        filters = WorkoutFilter(movements=["pull up"])
        
        mock_repository.list_workouts.return_value = (workouts, total_count)
        
        result_workouts, result_total = workout_service.list_workouts(
            page=2, page_size=10, filters=filters
        )
        
        mock_repository.list_workouts.assert_called_once_with(2, 10, filters)
        assert result_workouts == workouts
        assert result_total == total_count

    def test_get_random_workouts(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock
    ) -> None:
        workouts = [Workout(id=1), Workout(id=2), Workout(id=3)]
        filters = WorkoutFilter(workout_type="metcon")
        
        mock_repository.get_random_workouts.return_value = workouts
        
        result = workout_service.get_random_workouts(count=3, filters=filters)
        
        mock_repository.get_random_workouts.assert_called_once_with(3, filters)
        assert result == workouts

    def test_get_movement_counts(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock
    ) -> None:
        counts = {"pull up": 50, "push up": 30}
        mock_repository.get_movement_counts.return_value = counts
        
        result = workout_service.get_movement_counts()
        
        mock_repository.get_movement_counts.assert_called_once()
        assert result == counts

    def test_get_equipment_usage(
        self,
        workout_service: WorkoutService,
        mock_repository: MagicMock
    ) -> None:
        usage = {"barbell": 100, "pull up bar": 75}
        mock_repository.get_equipment_usage.return_value = usage
        
        result = workout_service.get_equipment_usage()
        
        mock_repository.get_equipment_usage.assert_called_once()
        assert result == usage