from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from wodrag.database.models import Workout, WorkoutFilter
from wodrag.database.workout_repository import WorkoutRepository


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock Supabase client."""
    client = MagicMock()
    # Set up the chain of method calls
    client.table.return_value = client
    client.insert.return_value = client
    client.select.return_value = client
    client.eq.return_value = client
    client.update.return_value = client
    client.delete.return_value = client
    client.single.return_value = client
    client.contains.return_value = client
    client.overlaps.return_value = client
    client.gte.return_value = client
    client.lte.return_value = client
    client.order.return_value = client
    client.limit.return_value = client
    client.offset.return_value = client
    client.rpc.return_value = client
    return client


@pytest.fixture
def repository(mock_client: MagicMock) -> WorkoutRepository:
    """Create a WorkoutRepository with mocked client."""
    return WorkoutRepository(client=mock_client)


class TestWorkoutRepositoryCRUD:
    def test_insert_workout(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        workout = Workout(
            workout="3 rounds for time: 10 pull-ups",
            scaling="Scale to ring rows",
            movements=["pull up"],
            equipment=["pull up bar"],
        )

        mock_client.execute.return_value.data = [
            {
                "id": 1,
                "date": "2024-01-01",
                "workout": "3 rounds for time: 10 pull-ups",
                "scaling": "Scale to ring rows",
                "movements": ["pull up"],
                "equipment": ["pull up bar"],
            }
        ]

        result = repository.insert_workout(workout)

        assert mock_client.insert.called
        assert result.id == 1
        assert result.movements == ["pull up"]

    def test_insert_workout_error(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        workout = Workout(workout="Test")
        mock_client.execute.side_effect = APIError({"message": "Insert failed"})

        with pytest.raises(RuntimeError) as exc_info:
            repository.insert_workout(workout)

        assert "Failed to insert workout" in str(exc_info.value)

    def test_get_workout_found(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        mock_client.execute.return_value.data = {
            "id": 1,
            "workout": "Test workout",
            "movements": ["pull up"],
        }

        result = repository.get_workout(1)

        assert result is not None
        assert result.id == 1
        assert result.workout == "Test workout"
        assert result.movements == ["pull up"]

    def test_get_workout_not_found(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        mock_client.execute.side_effect = APIError({"message": "Not found"})

        result = repository.get_workout(999)

        assert result is None

    def test_update_workout_metadata(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        mock_client.execute.return_value.data = [
            {
                "id": 1,
                "workout": "Test",
                "movements": ["pull up", "push up"],
                "equipment": ["none"],
                "workout_type": "metcon",
                "workout_name": "Test WOD",
            }
        ]

        result = repository.update_workout_metadata(
            workout_id=1,
            movements=["pull up", "push up"],
            equipment=["none"],
            workout_type="metcon",
            workout_name="Test WOD",
        )

        assert result is not None
        assert result.movements == ["pull up", "push up"]
        assert result.workout_type == "metcon"

    def test_update_workout_metadata_no_changes(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        # Mock get_workout return
        mock_client.execute.return_value.data = {"id": 1, "workout": "Test"}

        with patch.object(repository, "get_workout") as mock_get:
            mock_get.return_value = Workout(id=1, workout="Test")
            result = repository.update_workout_metadata(workout_id=1)

            mock_get.assert_called_once_with(1)
            assert result is not None
            assert result.id == 1

    def test_delete_workout_success(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        mock_client.execute.return_value = MagicMock()

        result = repository.delete_workout(1)

        assert result is True
        mock_client.delete.assert_called_once()

    def test_delete_workout_error(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        mock_client.execute.side_effect = APIError({"message": "Delete failed"})

        result = repository.delete_workout(1)

        assert result is False


class TestWorkoutRepositorySearch:
    def test_hybrid_search(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        query_embedding = [0.1, 0.2, 0.3]
        filters = WorkoutFilter(
            movements=["pull up"], equipment=["barbell"], workout_type="metcon"
        )

        mock_client.execute.return_value.data = [
            {"id": 1, "workout": "Test", "movements": ["pull up"]}
        ]

        results = repository.hybrid_search(query_embedding, filters, limit=5)

        # Check filters were applied
        mock_client.contains.assert_called_with("movements", ["pull up"])
        mock_client.overlaps.assert_called_with("equipment", ["barbell"])
        mock_client.eq.assert_called_with("workout_type", "metcon")

        assert len(results) == 1
        assert results[0].similarity_score is None  # No vector similarity yet
        assert results[0].metadata_match is True

    def test_vector_search(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        query_embedding = [0.1, 0.2, 0.3]

        mock_client.execute.return_value.data = [{"id": 1, "workout": "Test"}]

        results = repository.vector_search(query_embedding, limit=3)

        mock_client.limit.assert_called_with(3)

        assert len(results) == 1
        assert results[0].similarity_score is None  # No vector similarity yet
        assert results[0].metadata_match is True

    def test_filter_workouts(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        filters = WorkoutFilter(
            movements=["pull up"],
            equipment=["barbell", "dumbbell"],
            workout_type="strength",
            workout_name="Back Squat",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            has_video=True,
            has_article=False,
        )

        mock_client.execute.return_value.data = [
            {
                "id": 1,
                "workout": "Back squat 5-5-5-5-5",
                "workout_type": "strength",
                "movements": ["back squat"],
            }
        ]

        results = repository.filter_workouts(filters)

        # Verify all filter methods were called
        mock_client.contains.assert_called_with("movements", ["pull up"])
        mock_client.overlaps.assert_called_with("equipment", ["barbell", "dumbbell"])
        mock_client.eq.assert_any_call("workout_type", "strength")
        mock_client.eq.assert_any_call("workout_name", "Back Squat")
        mock_client.gte.assert_called_with("date", "2024-01-01")
        mock_client.lte.assert_called_with("date", "2024-12-31")

        assert len(results) == 1
        assert results[0].workout_type == "strength"


class TestWorkoutRepositoryListing:
    def test_list_workouts_with_pagination(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        mock_client.execute.return_value.data = [
            {"id": 1, "workout": "Test 1"},
            {"id": 2, "workout": "Test 2"},
        ]
        mock_client.execute.return_value.count = 50

        workouts, total = repository.list_workouts(page=2, page_size=10)

        mock_client.limit.assert_called_with(10)
        mock_client.offset.assert_called_with(10)  # (page-1) * page_size
        mock_client.order.assert_called_with("date", desc=True)

        assert len(workouts) == 2
        assert total == 50

    def test_get_workouts_by_date_range(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        mock_client.execute.return_value.data = [
            {"id": 1, "date": "2024-01-15", "workout": "Test"}
        ]

        with patch.object(repository, "filter_workouts") as mock_filter:
            mock_filter.return_value = [Workout(id=1, date=date(2024, 1, 15))]

            repository.get_workouts_by_date_range(start, end)

            # Verify filter was called with correct date range
            call_args = mock_filter.call_args[0][0]
            assert call_args.start_date == start
            assert call_args.end_date == end

    def test_get_random_workouts(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        # Mock filter_workouts to return some workouts
        with patch.object(repository, "filter_workouts") as mock_filter:
            mock_filter.return_value = [
                Workout(id=i, workout=f"Workout {i}") for i in range(1, 11)
            ]

            results = repository.get_random_workouts(count=3)

            assert len(results) == 3
            # Verify results are from the mocked list
            assert all(w.id in range(1, 11) for w in results)


class TestWorkoutRepositoryAnalytics:
    def test_get_movement_counts(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        # Mock filter_workouts
        with patch.object(repository, "filter_workouts") as mock_filter:
            mock_filter.return_value = [
                Workout(movements=["pull up", "push up"]),
                Workout(movements=["pull up", "squat"]),
                Workout(movements=["squat"]),
            ]

            counts = repository.get_movement_counts()

            assert counts["pull up"] == 2
            assert counts["push up"] == 1
            assert counts["squat"] == 2

    def test_get_equipment_usage(
        self, repository: WorkoutRepository, mock_client: MagicMock
    ) -> None:
        # Mock filter_workouts
        with patch.object(repository, "filter_workouts") as mock_filter:
            mock_filter.return_value = [
                Workout(equipment=["barbell", "plates"]),
                Workout(equipment=["barbell"]),
                Workout(equipment=["dumbbell", "pull up bar"]),
            ]

            usage = repository.get_equipment_usage()

            assert usage["barbell"] == 2
            assert usage["plates"] == 1
            assert usage["dumbbell"] == 1
            assert usage["pull up bar"] == 1
