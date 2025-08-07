"""Tests for API models and edge cases."""

from datetime import date

import pytest
from pydantic import ValidationError

from wodrag.api.models import (
    APIResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginationMeta,
    SearchRequest,
    SearchResultModel,
    WorkoutFilterModel,
    WorkoutModel,
)


def test_workout_model_creation():
    """Test WorkoutModel creation with valid data."""
    workout_data = {
        "id": 1,
        "date": date(2023, 1, 15),
        "workout": "21-15-9 Thrusters (95/65) Pull-ups",
        "movements": ["thruster", "pull up"],
        "equipment": ["barbell", "pull_up_bar"],
        "workout_type": "metcon",
        "has_video": True,
    }
    
    workout = WorkoutModel(**workout_data)
    
    assert workout.id == 1
    assert workout.date == date(2023, 1, 15)
    assert workout.workout == "21-15-9 Thrusters (95/65) Pull-ups"
    assert workout.movements == ["thruster", "pull up"]
    assert workout.equipment == ["barbell", "pull_up_bar"]
    assert workout.workout_type == "metcon"
    assert workout.has_video is True
    assert workout.has_article is False  # default


def test_workout_model_defaults():
    """Test WorkoutModel with default values."""
    workout = WorkoutModel()
    
    assert workout.id is None
    assert workout.date is None
    assert workout.has_video is False
    assert workout.has_article is False
    assert workout.movements == []
    assert workout.equipment == []


def test_workout_filter_model():
    """Test WorkoutFilterModel creation."""
    filter_data = {
        "movements": ["burpee", "pull up"],
        "equipment": ["barbell"],
        "workout_type": "metcon",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 12, 31),
        "has_video": True,
    }
    
    filter_model = WorkoutFilterModel(**filter_data)
    
    assert filter_model.movements == ["burpee", "pull up"]
    assert filter_model.equipment == ["barbell"]
    assert filter_model.workout_type == "metcon"
    assert filter_model.start_date == date(2023, 1, 1)
    assert filter_model.end_date == date(2023, 12, 31)
    assert filter_model.has_video is True


def test_search_result_model():
    """Test SearchResultModel creation and relevance score calculation."""
    workout = WorkoutModel(id=1, workout="Test workout")
    
    # Test with similarity score
    result = SearchResultModel(
        workout=workout,
        similarity_score=0.8,
        metadata_match=True
    )
    
    assert result.workout.id == 1
    assert result.similarity_score == 0.8
    assert result.metadata_match is True
    assert result.relevance_score == 0.96  # 0.8 * 1.2, capped at 1.0
    
    # Test with hybrid score (takes precedence)
    result_hybrid = SearchResultModel(
        workout=workout,
        similarity_score=0.8,
        hybrid_score=0.9,
        metadata_match=True
    )
    
    assert result_hybrid.relevance_score == 0.9  # hybrid_score used
    
    # Test without similarity score
    result_no_score = SearchResultModel(
        workout=workout,
        metadata_match=False
    )
    
    assert result_no_score.relevance_score == 0.0  # no match, no score


def test_search_request_validation():
    """Test SearchRequest validation."""
    # Valid request
    request = SearchRequest(
        query="burpees",
        limit=10,
        offset=5,
        semantic_weight=0.7,
        bm25_weight=0.3
    )
    
    assert request.query == "burpees"
    assert request.limit == 10
    assert request.offset == 5
    assert request.semantic_weight == 0.7
    assert request.bm25_weight == 0.3
    
    # Test validation errors
    with pytest.raises(ValidationError):
        SearchRequest(query="")  # Empty query
        
    with pytest.raises(ValidationError):
        SearchRequest(query="test", limit=200)  # Limit too high
        
    with pytest.raises(ValidationError):
        SearchRequest(query="test", offset=-1)  # Negative offset
        
    with pytest.raises(ValidationError):
        SearchRequest(query="test", semantic_weight=1.5)  # Weight > 1.0


def test_pagination_meta():
    """Test PaginationMeta creation."""
    meta = PaginationMeta(
        total=100,
        page=2,
        page_size=20,
        has_next=True,
        has_prev=True
    )
    
    assert meta.total == 100
    assert meta.page == 2
    assert meta.page_size == 20
    assert meta.has_next is True
    assert meta.has_prev is True


def test_api_response():
    """Test APIResponse wrapper."""
    data = [{"id": 1, "name": "test"}]
    meta = PaginationMeta(total=1, page=1, page_size=20, has_next=False, has_prev=False)
    
    response = APIResponse(data=data, meta=meta)
    
    assert response.data == data
    assert response.meta == meta
    assert response.status == "success"  # default


def test_error_response():
    """Test ErrorResponse and ErrorDetail models."""
    error_detail = ErrorDetail(
        code="WORKOUT_NOT_FOUND",
        message="Workout with ID 123 not found",
        details={"workout_id": 123}
    )
    
    error_response = ErrorResponse(error=error_detail)
    
    assert error_response.error.code == "WORKOUT_NOT_FOUND"
    assert error_response.error.message == "Workout with ID 123 not found"
    assert error_response.error.details == {"workout_id": 123}
    assert error_response.status == "error"  # default


def test_health_response():
    """Test HealthResponse model."""
    health = HealthResponse(status="healthy", service="wodrag-api")
    
    assert health.status == "healthy"
    assert health.service == "wodrag-api"


def test_workout_model_embedding_fields():
    """Test WorkoutModel with embedding fields."""
    embedding_data = [0.1, 0.2, 0.3, -0.4, 0.5]
    
    workout = WorkoutModel(
        id=1,
        workout_embedding=embedding_data,
        summary_embedding=embedding_data
    )
    
    assert workout.workout_embedding == embedding_data
    assert workout.summary_embedding == embedding_data


def test_date_serialization():
    """Test date field serialization in WorkoutModel."""
    workout = WorkoutModel(date=date(2023, 6, 15))
    
    # Test that the model can be created and serialized
    workout_dict = workout.model_dump()
    assert workout_dict["date"] == date(2023, 6, 15)


def test_model_json_serialization():
    """Test JSON serialization of models."""
    workout = WorkoutModel(
        id=1,
        date=date(2023, 1, 15),
        movements=["burpee", "pull up"],
        equipment=["pull_up_bar"]
    )
    
    result = SearchResultModel(
        workout=workout,
        similarity_score=0.85,
        metadata_match=True
    )
    
    # Test that models can be serialized to JSON
    json_data = result.model_dump()
    assert json_data["workout"]["id"] == 1
    assert json_data["similarity_score"] == 0.85
    assert json_data["metadata_match"] is True


def test_filter_model_edge_cases():
    """Test WorkoutFilterModel edge cases."""
    # Empty filter
    empty_filter = WorkoutFilterModel()
    assert empty_filter.movements is None
    assert empty_filter.equipment is None
    assert empty_filter.workout_type is None
    
    # Filter with empty lists
    filter_with_empty = WorkoutFilterModel(
        movements=[],
        equipment=[]
    )
    assert filter_with_empty.movements == []
    assert filter_with_empty.equipment == []