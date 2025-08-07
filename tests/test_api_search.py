"""Tests for search endpoints."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from wodrag.api.main import app
from wodrag.database.models import SearchResult, Workout

client = TestClient(app)


@pytest.fixture
def mock_workout():
    """Create a mock workout for testing."""
    return Workout(
        id=1,
        workout="21-15-9 Burpees Pull-ups",
        one_sentence_summary="Fast bodyweight couplet with burpees and pull-ups",
        movements=["burpee", "pull up"],
        equipment=["pull_up_bar"],
        workout_type="metcon"
    )


@pytest.fixture
def mock_search_results(mock_workout):
    """Create mock search results."""
    return [
        SearchResult(
            workout=mock_workout,
            similarity_score=0.9,
            metadata_match=True
        )
    ]


@patch('wodrag.api.routers.search.get_workout_repository')
def test_hybrid_search_success(mock_get_repo, mock_search_results):
    """Test successful hybrid search."""
    # Mock repository
    mock_repo = Mock()
    mock_repo.hybrid_search.return_value = mock_search_results
    mock_get_repo.return_value = mock_repo
    
    response = client.get("/api/v1/search?q=burpees")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "data" in data
    assert "meta" in data
    assert "status" in data
    assert data["status"] == "success"
    
    # Check data content
    assert len(data["data"]) == 1
    result = data["data"][0]
    assert "workout" in result
    assert "similarity_score" in result
    assert result["workout"]["id"] == 1
    assert result["similarity_score"] == 0.9
    
    # Check pagination metadata
    meta = data["meta"]
    assert meta["total"] == 1
    assert meta["page"] == 1
    assert meta["page_size"] == 20


@patch('wodrag.api.routers.search.get_workout_repository')
def test_hybrid_search_with_parameters(mock_get_repo, mock_search_results):
    """Test hybrid search with custom parameters."""
    mock_repo = Mock()
    mock_repo.hybrid_search.return_value = mock_search_results
    mock_get_repo.return_value = mock_repo
    
    response = client.get("/api/v1/search?q=burpees&limit=10&offset=5&semantic_weight=0.7")
    
    assert response.status_code == 200
    
    # Check that repository was called with correct parameters
    mock_repo.hybrid_search.assert_called_once_with(
        query_text="burpees",
        semantic_weight=0.7,
        limit=15  # limit + offset
    )


def test_hybrid_search_validation_errors():
    """Test validation errors for hybrid search."""
    # Empty query
    response = client.get("/api/v1/search?q=")
    assert response.status_code == 422
    
    # Invalid limit
    response = client.get("/api/v1/search?q=test&limit=200")
    assert response.status_code == 422
    
    # Invalid semantic_weight
    response = client.get("/api/v1/search?q=test&semantic_weight=2.0")
    assert response.status_code == 422


@patch('wodrag.api.routers.search.get_workout_repository')
def test_hybrid_search_error_handling(mock_get_repo):
    """Test error handling in hybrid search."""
    mock_repo = Mock()
    mock_repo.hybrid_search.side_effect = Exception("Database error")
    mock_get_repo.return_value = mock_repo
    
    response = client.get("/api/v1/search?q=burpees")
    
    assert response.status_code == 500
    data = response.json()
    assert "Search failed" in data["detail"]


@patch('wodrag.api.routers.search.get_workout_repository')
def test_semantic_search_success(mock_get_repo, mock_search_results):
    """Test successful semantic search."""
    mock_repo = Mock()
    mock_repo.search_summaries.return_value = mock_search_results
    mock_get_repo.return_value = mock_repo
    
    response = client.get("/api/v1/search/semantic?q=cardio workout")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert len(data["data"]) == 1
    
    # Check that correct repository method was called
    mock_repo.search_summaries.assert_called_once_with(
        query_text="cardio workout",
        limit=20
    )


@patch('wodrag.api.routers.search.get_workout_repository')
def test_text_search_success(mock_get_repo, mock_search_results):
    """Test successful BM25 text search."""
    mock_repo = Mock()
    mock_repo.text_search_workouts.return_value = mock_search_results
    mock_get_repo.return_value = mock_repo
    
    response = client.get("/api/v1/search/text?q=burpees OR pullups")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert len(data["data"]) == 1
    
    # Check that correct repository method was called
    mock_repo.text_search_workouts.assert_called_once_with(
        query="burpees OR pullups",
        limit=20
    )


@patch('wodrag.api.routers.search.get_workout_repository')
def test_search_pagination(mock_get_repo, mock_workout):
    """Test search pagination logic."""
    # Create multiple mock results
    mock_results = [
        SearchResult(workout=mock_workout, similarity_score=0.9, metadata_match=True)
        for _ in range(25)  # More than default page size
    ]
    
    mock_repo = Mock()
    mock_repo.hybrid_search.return_value = mock_results
    mock_get_repo.return_value = mock_repo
    
    # Test first page
    response = client.get("/api/v1/search?q=test&limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["data"]) == 10
    meta = data["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 10
    assert meta["total"] == 25
    assert meta["has_next"] is True
    assert meta["has_prev"] is False
    
    # Test second page
    response = client.get("/api/v1/search?q=test&limit=10&offset=10")
    assert response.status_code == 200
    data = response.json()
    
    meta = data["meta"]
    assert meta["page"] == 2
    assert meta["has_next"] is True
    assert meta["has_prev"] is True


@patch('wodrag.api.routers.search.get_workout_repository')
def test_search_empty_results(mock_get_repo):
    """Test search with no results."""
    mock_repo = Mock()
    mock_repo.hybrid_search.return_value = []
    mock_get_repo.return_value = mock_repo
    
    response = client.get("/api/v1/search?q=nonexistent")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert len(data["data"]) == 0
    assert data["meta"]["total"] == 0