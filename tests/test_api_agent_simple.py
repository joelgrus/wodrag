"""Simple integration tests for the master agent endpoint."""

import pytest
from litestar.testing import TestClient

from wodrag.api.main import app

client = TestClient(app)


def test_agent_query_validation_empty():
    """Test agent query validation with empty question."""
    response = client.post(
        "/api/v1/agent/query",
        json={"question": "", "verbose": False}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Validation failed" in data["detail"]


def test_agent_query_validation_missing_field():
    """Test agent query validation with missing question field."""
    response = client.post(
        "/api/v1/agent/query",
        json={"verbose": True}
    )
    assert response.status_code == 400


def test_agent_query_invalid_json():
    """Test agent query with invalid JSON."""
    response = client.post(
        "/api/v1/agent/query",
        content="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400


@pytest.mark.skip(reason="Requires DSPy configuration and database connection")
def test_agent_query_integration():
    """Integration test - requires full setup."""
    # This would test with a real agent but needs:
    # - DSPy configured
    # - Database connection
    # - OpenAI API key (optional but recommended)
    pass