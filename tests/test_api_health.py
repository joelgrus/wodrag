"""Tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient

from wodrag.api.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "wodrag-api"


def test_health_check_response_format():
    """Test health check response format."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "status" in data
    assert "service" in data
    assert isinstance(data["status"], str)
    assert isinstance(data["service"], str)


@pytest.mark.skip(reason="Requires database connection")
def test_database_health_check_success():
    """Test database health check when database is available."""
    # This test would require a running database
    response = client.get("/api/v1/health/database")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_database_health_check_failure():
    """Test database health check when database is unavailable."""
    # Mock the database connection to fail
    import psycopg2
    from unittest.mock import patch
    
    with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Connection failed")):
        response = client.get("/api/v1/health/database")
        
        assert response.status_code == 503
        data = response.json()
        assert "Database connection failed" in data["detail"]