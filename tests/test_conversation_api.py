"""Integration tests for conversation-enabled API."""

import pytest
from unittest.mock import Mock, patch
from litestar.testing import TestClient

from wodrag.api.main import create_app


@pytest.fixture
def mock_agent():
    """Create mock master agent."""
    mock = Mock()
    mock.forward.return_value = "This is a test response."
    mock.forward_verbose.return_value = (
        "This is a test response.", 
        ["ACTION: search", "OBSERVATION: Found results"]
    )
    return mock


@pytest.fixture
def app_with_mock_agent(mock_agent):
    """Create app with mocked dependencies."""
    with patch('wodrag.api.main.provide_master_agent', return_value=mock_agent):
        app = create_app()
        return app


@pytest.fixture 
def client(app_with_mock_agent):
    """Create test client with mocked dependencies."""
    return TestClient(app_with_mock_agent)


@patch('wodrag.api.routers.agent.get_conversation_service')
def test_agent_query_new_conversation(mock_get_service, client):
    """Test agent query creates new conversation when none provided."""
    from wodrag.conversation.service import ConversationService
    from wodrag.conversation.storage import InMemoryConversationStore
    
    # Setup mock conversation service
    storage = InMemoryConversationStore()
    service = ConversationService()
    service.store = storage
    mock_get_service.return_value = service
    
    response = client.post("/api/v1/agent/query", json={
        "question": "What is Fran?",
        "verbose": False
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["question"] == "What is Fran?"
    assert data["data"]["answer"] == "This is a test response."
    assert data["data"]["conversation_id"] is not None
    assert data["data"]["verbose"] is False


@patch('wodrag.api.routers.agent.get_conversation_service')
def test_agent_query_existing_conversation(mock_get_service, mock_agent):
    """Test agent query uses existing conversation context."""
    from wodrag.conversation.service import ConversationService
    from wodrag.conversation.storage import InMemoryConversationStore
    
    # Setup mock conversation service
    storage = InMemoryConversationStore()
    service = ConversationService()
    service.store = storage
    mock_get_service.return_value = service
    
    # Create existing conversation
    service.get_or_create_conversation("test-conv-id")
    service.add_user_message("test-conv-id", "What is Fran?")
    service.add_assistant_message("test-conv-id", "Fran is a CrossFit workout.")
    
    # Mock the agent to verify it receives context
    def mock_forward(question, conversation_context=None, verbose=False):
        # Verify context is passed
        assert conversation_context is not None
        assert len(conversation_context) == 2  # Previous user + assistant messages
        return "Based on our previous discussion, Fran has thrusters and pull-ups."
    
    mock_agent.forward.side_effect = mock_forward
    
    # Create app with this specific mock agent
    with patch('wodrag.api.main.provide_master_agent', return_value=mock_agent):
        app = create_app()
        client = TestClient(app)
        
        response = client.post("/api/v1/agent/query", json={
            "question": "What movements does it have?",
            "conversation_id": "test-conv-id",
            "verbose": False
        })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["conversation_id"] == "test-conv-id"
    assert "thrusters and pull-ups" in data["data"]["answer"]


@patch('wodrag.api.routers.agent.get_conversation_service')
def test_agent_query_verbose_with_conversation(mock_get_service, mock_agent):
    """Test verbose agent query with conversation context."""
    from wodrag.conversation.service import ConversationService
    from wodrag.conversation.storage import InMemoryConversationStore
    
    # Setup mock conversation service
    storage = InMemoryConversationStore()
    service = ConversationService()
    service.store = storage
    mock_get_service.return_value = service
    
    # Mock the agent to verify it receives context
    def mock_forward_verbose(question, conversation_context=None):
        assert conversation_context is not None
        return ("Detailed response with reasoning.", 
                ["THOUGHT: Analyzing question", "ACTION: search(Fran)"])
    
    mock_agent.forward_verbose.side_effect = mock_forward_verbose
    
    # Create existing conversation
    service.add_user_message("test-conv", "What is Fran?")
    service.add_assistant_message("test-conv", "Fran is a CrossFit workout.")
    
    # Create app with this specific mock agent
    with patch('wodrag.api.main.provide_master_agent', return_value=mock_agent):
        app = create_app()
        client = TestClient(app)
        
        response = client.post("/api/v1/agent/query", json={
            "question": "Tell me more details",
            "conversation_id": "test-conv",
            "verbose": True
        })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["verbose"] is True
    assert data["data"]["reasoning_trace"] is not None
    assert len(data["data"]["reasoning_trace"]) == 2


@patch('wodrag.api.routers.agent.get_conversation_service')
def test_conversation_persistence(mock_get_service, mock_agent):
    """Test that conversations persist across multiple requests."""
    from wodrag.conversation.service import ConversationService
    from wodrag.conversation.storage import InMemoryConversationStore
    
    # Setup mock conversation service
    storage = InMemoryConversationStore()
    service = ConversationService()
    service.store = storage
    mock_get_service.return_value = service
    
    mock_agent.forward.return_value = "Response 1"
    
    # Create app with mock agent
    with patch('wodrag.api.main.provide_master_agent', return_value=mock_agent):
        app = create_app()
        client = TestClient(app)
        
        # First request
        response1 = client.post("/api/v1/agent/query", json={
            "question": "What is Fran?",
            "verbose": False
        })
        
        conversation_id = response1.json()["data"]["conversation_id"]
        
        # Second request with same conversation
        mock_agent.forward.return_value = "Response 2"
        response2 = client.post("/api/v1/agent/query", json={
            "question": "What movements does it have?",
            "conversation_id": conversation_id,
            "verbose": False
        })
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Same conversation ID
    assert response2.json()["data"]["conversation_id"] == conversation_id
    
    # Verify conversation has all messages
    conversation = service.get_or_create_conversation(conversation_id)
    assert len(conversation.messages) == 4  # 2 user + 2 assistant messages


def test_agent_query_error_handling():
    """Test error handling in agent query."""
    # Mock agent to throw an exception
    mock_failing_agent = Mock()
    mock_failing_agent.forward.side_effect = Exception("Agent failed")
    
    with patch('wodrag.api.main.provide_master_agent', return_value=mock_failing_agent):
        app = create_app()
        client = TestClient(app)
        
        response = client.post("/api/v1/agent/query", json={
            "question": "What is Fran?",
            "verbose": False
        })
    
    assert response.status_code == 400
    data = response.json()
    
    assert data["success"] is False
    assert "Agent failed" in data["error"]


def test_agent_query_validation_errors():
    """Test request validation errors."""
    app = create_app()
    client = TestClient(app)
    
    # Empty question - Litestar returns 400 for validation errors
    response = client.post("/api/v1/agent/query", json={
        "question": "",
        "verbose": False
    })
    assert response.status_code == 400
    data = response.json()
    assert "Validation failed" in data["detail"]
    assert any("at least 1 character" in extra["message"] 
               for extra in data.get("extra", []))
    
    # Missing question - Litestar returns 400 for validation errors
    response = client.post("/api/v1/agent/query", json={
        "verbose": False
    })
    assert response.status_code == 400
    data = response.json()
    assert "Validation failed" in data["detail"]
    
    # Invalid JSON format
    response = client.post("/api/v1/agent/query", 
                         content="invalid json",
                         headers={"content-type": "application/json"})
    assert response.status_code == 400  # Bad request for malformed JSON


def test_agent_query_conversation_error_handling():
    """Test error handling when conversation operations fail."""
    mock_agent = Mock()
    mock_agent.forward.return_value = "Response"
    
    # Mock conversation service to raise an exception
    with patch('wodrag.api.main.provide_master_agent', return_value=mock_agent):
        with patch('wodrag.api.routers.agent.get_conversation_service') as mock_service:
            mock_service.side_effect = Exception("Conversation service failed")
            
            app = create_app()
            client = TestClient(app)
            
            response = client.post("/api/v1/agent/query", json={
                "question": "What is Fran?",
                "verbose": False
            })
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Conversation service failed" in data["error"]