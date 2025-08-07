"""Tests for query endpoints."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from wodrag.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_query_results():
    """Create mock query results."""
    return [
        {"id": 1, "workout": "Fran", "movements": ["thruster", "pull up"]},
        {"id": 2, "workout": "Murph", "movements": ["run", "pull up", "push up", "air squat"]},
    ]


@pytest.fixture
def mock_schema_results():
    """Create mock schema results."""
    return [
        {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": None,
        },
        {
            "column_name": "workout",
            "data_type": "text",
            "is_nullable": "YES", 
            "column_default": None,
        },
        {
            "column_name": "movements",
            "data_type": "text[]",
            "is_nullable": "YES",
            "column_default": None,
        },
    ]


@patch('wodrag.api.routers.query.get_query_generator')
def test_natural_language_query_success(mock_get_generator, mock_query_results):
    """Test successful natural language query."""
    mock_generator = Mock()
    mock_generator.query_and_execute.return_value = mock_query_results
    mock_get_generator.return_value = mock_generator
    
    response = client.get("/api/v1/query?q=Show me workouts with pull ups")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "data" in data
    assert "status" in data
    assert data["status"] == "success"
    
    # Check data content
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == 1
    assert data["data"][0]["workout"] == "Fran"
    
    # Check that generator was called correctly
    mock_generator.query_and_execute.assert_called_once_with("Show me workouts with pull ups")


@patch('wodrag.api.routers.query.get_query_generator')
def test_natural_language_query_empty_results(mock_get_generator):
    """Test natural language query with empty results."""
    mock_generator = Mock()
    mock_generator.query_and_execute.return_value = []
    mock_get_generator.return_value = mock_generator
    
    response = client.get("/api/v1/query?q=Show me workouts from 2050")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert len(data["data"]) == 0


def test_natural_language_query_validation():
    """Test validation for natural language query."""
    # Empty query
    response = client.get("/api/v1/query?q=")
    assert response.status_code == 422
    
    # Missing query parameter
    response = client.get("/api/v1/query")
    assert response.status_code == 422


@patch('wodrag.api.routers.query.get_query_generator')
def test_natural_language_query_error(mock_get_generator):
    """Test error handling for natural language query."""
    mock_generator = Mock()
    mock_generator.query_and_execute.side_effect = Exception("SQL execution failed")
    mock_get_generator.return_value = mock_generator
    
    response = client.get("/api/v1/query?q=Invalid query that causes error")
    
    assert response.status_code == 500
    data = response.json()
    assert "Query execution failed" in data["detail"]


@patch('wodrag.api.routers.query.get_query_generator')
def test_generate_sql_only_success(mock_get_generator):
    """Test successful SQL generation without execution."""
    mock_generator = Mock()
    mock_generator.generate_query.return_value = "SELECT * FROM pg_db.workouts WHERE 'pull up' = ANY(movements) LIMIT 10"
    mock_get_generator.return_value = mock_generator
    
    response = client.get("/api/v1/query/sql?q=Show me workouts with pull ups")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "natural_language" in data
    assert "generated_sql" in data
    assert data["natural_language"] == "Show me workouts with pull ups"
    assert "SELECT * FROM pg_db.workouts" in data["generated_sql"]
    
    # Check that only generate_query was called, not execute
    mock_generator.generate_query.assert_called_once_with("Show me workouts with pull ups")
    mock_generator.query_and_execute.assert_not_called()


@patch('wodrag.api.routers.query.get_query_generator')
def test_generate_sql_only_error(mock_get_generator):
    """Test error handling for SQL generation."""
    mock_generator = Mock()
    mock_generator.generate_query.side_effect = Exception("AI model error")
    mock_get_generator.return_value = mock_generator
    
    response = client.get("/api/v1/query/sql?q=Complex invalid query")
    
    assert response.status_code == 500
    data = response.json()
    assert "SQL generation failed" in data["detail"]


def test_generate_sql_validation():
    """Test validation for SQL generation endpoint."""
    # Empty query
    response = client.get("/api/v1/query/sql?q=")
    assert response.status_code == 422
    
    # Missing query parameter
    response = client.get("/api/v1/query/sql")
    assert response.status_code == 422


@patch('wodrag.api.routers.query.get_duckdb_service')
def test_get_schema_success(mock_get_service, mock_schema_results):
    """Test successful schema retrieval."""
    mock_service = Mock()
    mock_service.get_table_schema.return_value = mock_schema_results
    mock_get_service.return_value = mock_service
    
    response = client.get("/api/v1/schema")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "data" in data
    assert "status" in data
    assert data["status"] == "success"
    
    # Check schema data
    schema_data = data["data"]
    assert len(schema_data) == 3
    
    # Check that descriptions were added
    movements_col = next((col for col in schema_data if col["column_name"] == "movements"), None)
    assert movements_col is not None
    assert "description" in movements_col
    assert "Array of exercise movements" in movements_col["description"]
    
    # Check that service was called correctly
    mock_service.get_table_schema.assert_called_once_with("workouts")


@patch('wodrag.api.routers.query.get_duckdb_service')
def test_get_schema_error(mock_get_service):
    """Test error handling for schema retrieval."""
    mock_service = Mock()
    mock_service.get_table_schema.side_effect = Exception("Database connection error")
    mock_get_service.return_value = mock_service
    
    response = client.get("/api/v1/schema")
    
    assert response.status_code == 500
    data = response.json()
    assert "Schema retrieval failed" in data["detail"]


@patch('wodrag.api.routers.query.get_query_generator')
def test_complex_natural_language_queries(mock_get_generator):
    """Test various complex natural language queries."""
    mock_generator = Mock()
    mock_get_generator.return_value = mock_generator
    
    test_queries = [
        "How many hero workouts are there?",
        "Show me strength workouts from 2023", 
        "What are the most common movements in metcons?",
        "Find workouts with burpees and pull ups",
        "Show me workouts that don't require equipment",
    ]
    
    for query in test_queries:
        mock_generator.query_and_execute.return_value = [{"count": 42}]
        
        response = client.get(f"/api/v1/query?q={query}")
        
        assert response.status_code == 200, f"Failed for query: {query}"
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1


@patch('wodrag.api.routers.query.get_query_generator')
def test_query_encoding_handling(mock_get_generator):
    """Test handling of special characters in queries."""
    mock_generator = Mock()
    mock_generator.query_and_execute.return_value = []
    mock_get_generator.return_value = mock_generator
    
    # Test query with special characters
    query = "Show me workouts with 'Fran' & 21-15-9 reps"
    response = client.get("/api/v1/query", params={"q": query})
    
    assert response.status_code == 200
    mock_generator.query_and_execute.assert_called_once_with(query)