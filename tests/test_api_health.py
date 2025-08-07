"""Tests for health endpoints using Litestar."""

import pytest
from litestar.testing import TestClient

from wodrag.api.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["version"] == "0.1.0"


def test_health_check_response_format():
    """Test health check response format."""
    response = client.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields in APIResponse format
    assert "success" in data
    assert "data" in data
    assert "error" in data
    
    # Check health data format
    health_data = data["data"]
    assert "status" in health_data
    assert "timestamp" in health_data
    assert "version" in health_data
    assert isinstance(health_data["status"], str)
    assert isinstance(health_data["version"], str)


@pytest.mark.skip(reason="Requires database connection")
def test_database_health_check_success():
    """Test database health check when database is available."""
    # This test would require a running database
    response = client.get("/api/v1/health/db")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["database"] == "connected"


def test_database_health_check_failure():
    """Test database health check when database is unavailable."""
    # Mock the database connection to fail
    from unittest.mock import patch
    
    with patch('wodrag.database.workout_repository.WorkoutRepository.search_summaries', 
               side_effect=Exception("Database connection failed")):
        response = client.get("/api/v1/health/db")
        
        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False
        assert "Database connection failed" in data["error"]