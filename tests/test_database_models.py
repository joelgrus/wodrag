import pytest
from datetime import date
from wodrag.database.models import Workout, WorkoutFilter, SearchResult


class TestWorkout:
    def test_workout_initialization(self) -> None:
        workout = Workout(
            id=1,
            date=date(2024, 1, 1),
            url="https://crossfit.com/workout/2024/01/01",
            raw_text="Test workout",
            workout="3 rounds for time: 10 pull-ups",
            scaling="Scale to ring rows",
            has_video=True,
            has_article=False,
            month_file="2024-01.html",
            movements=["pull up"],
            equipment=["pull up bar"],
            workout_type="metcon",
            workout_name="Test WOD"
        )
        
        assert workout.id == 1
        assert workout.date == date(2024, 1, 1)
        assert workout.movements == ["pull up"]
        assert workout.equipment == ["pull up bar"]
        assert workout.workout_type == "metcon"
        assert workout.workout_name == "Test WOD"

    def test_workout_to_dict(self) -> None:
        workout = Workout(
            id=1,
            date=date(2024, 1, 1),
            workout="3 rounds for time: 10 pull-ups",
            movements=["pull up"],
            equipment=["pull up bar"]
        )
        
        result = workout.to_dict()
        
        assert result["id"] == 1
        assert result["date"] == "2024-01-01"
        assert result["workout"] == "3 rounds for time: 10 pull-ups"
        assert result["movements"] == ["pull up"]
        assert result["equipment"] == ["pull up bar"]
        assert "workout_embedding" not in result  # None values should be excluded

    def test_workout_to_dict_with_embedding(self) -> None:
        workout = Workout(
            workout="Test",
            workout_embedding=[0.1, 0.2, 0.3]
        )
        
        result = workout.to_dict()
        
        assert result["workout_embedding"] == [0.1, 0.2, 0.3]

    def test_workout_from_dict(self) -> None:
        data = {
            "id": 1,
            "date": "2024-01-01",
            "workout": "3 rounds for time: 10 pull-ups",
            "movements": ["pull up"],
            "equipment": ["pull up bar"],
            "workout_type": "metcon"
        }
        
        workout = Workout.from_dict(data)
        
        assert workout.id == 1
        assert workout.date == date(2024, 1, 1)
        assert workout.workout == "3 rounds for time: 10 pull-ups"
        assert workout.movements == ["pull up"]
        assert workout.equipment == ["pull up bar"]
        assert workout.workout_type == "metcon"

    def test_workout_from_dict_with_null_date(self) -> None:
        data = {
            "id": 1,
            "date": None,
            "workout": "Rest Day"
        }
        
        workout = Workout.from_dict(data)
        
        assert workout.id == 1
        assert workout.date is None
        assert workout.workout == "Rest Day"

    def test_workout_defaults(self) -> None:
        workout = Workout()
        
        assert workout.id is None
        assert workout.date is None
        assert workout.movements == []
        assert workout.equipment == []
        assert workout.has_video is False
        assert workout.has_article is False


class TestWorkoutFilter:
    def test_filter_initialization(self) -> None:
        filter_obj = WorkoutFilter(
            movements=["pull up", "push up"],
            equipment=["barbell"],
            workout_type="metcon",
            workout_name="Fran",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            has_video=True,
            has_article=False
        )
        
        assert filter_obj.movements == ["pull up", "push up"]
        assert filter_obj.equipment == ["barbell"]
        assert filter_obj.workout_type == "metcon"
        assert filter_obj.workout_name == "Fran"
        assert filter_obj.start_date == date(2024, 1, 1)
        assert filter_obj.end_date == date(2024, 12, 31)
        assert filter_obj.has_video is True
        assert filter_obj.has_article is False

    def test_filter_to_dict_all_fields(self) -> None:
        filter_obj = WorkoutFilter(
            movements=["pull up"],
            equipment=["barbell"],
            workout_type="metcon",
            workout_name="Fran",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            has_video=True,
            has_article=False
        )
        
        result = filter_obj.to_dict()
        
        assert result["movements"] == ["pull up"]
        assert result["equipment"] == ["barbell"]
        assert result["workout_type"] == "metcon"
        assert result["workout_name"] == "Fran"
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"
        assert result["has_video"] is True
        assert result["has_article"] is False

    def test_filter_to_dict_partial_fields(self) -> None:
        filter_obj = WorkoutFilter(
            movements=["pull up"],
            workout_type="metcon"
        )
        
        result = filter_obj.to_dict()
        
        assert result == {
            "movements": ["pull up"],
            "workout_type": "metcon"
        }
        # Ensure None values are not included
        assert "equipment" not in result
        assert "workout_name" not in result

    def test_filter_empty(self) -> None:
        filter_obj = WorkoutFilter()
        
        result = filter_obj.to_dict()
        
        assert result == {}


class TestSearchResult:
    def test_search_result_initialization(self) -> None:
        workout = Workout(id=1, workout="Test workout")
        result = SearchResult(
            workout=workout,
            similarity_score=0.85,
            metadata_match=True
        )
        
        assert result.workout.id == 1
        assert result.similarity_score == 0.85
        assert result.metadata_match is True

    def test_relevance_score_with_similarity(self) -> None:
        workout = Workout(id=1)
        
        # High similarity with metadata match
        result1 = SearchResult(workout=workout, similarity_score=0.8, metadata_match=True)
        assert result1.relevance_score == 0.96  # 0.8 * 1.2
        
        # High similarity without metadata match
        result2 = SearchResult(workout=workout, similarity_score=0.8, metadata_match=False)
        assert result2.relevance_score == 0.8
        
        # Score capped at 1.0
        result3 = SearchResult(workout=workout, similarity_score=0.9, metadata_match=True)
        assert result3.relevance_score == 1.0  # min(0.9 * 1.2, 1.0)

    def test_relevance_score_without_similarity(self) -> None:
        workout = Workout(id=1)
        
        # No similarity score, with metadata match
        result1 = SearchResult(workout=workout, similarity_score=None, metadata_match=True)
        assert result1.relevance_score == 1.0
        
        # No similarity score, without metadata match
        result2 = SearchResult(workout=workout, similarity_score=None, metadata_match=False)
        assert result2.relevance_score == 0.0

    def test_search_result_defaults(self) -> None:
        workout = Workout(id=1)
        result = SearchResult(workout=workout)
        
        assert result.similarity_score is None
        assert result.metadata_match is True
        assert result.relevance_score == 1.0