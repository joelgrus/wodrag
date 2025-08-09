"""Tests for conversation service."""

from unittest.mock import Mock

import pytest

from wodrag.conversation.security import RateLimiter
from wodrag.conversation.service import ConversationService
from wodrag.conversation.storage import InMemoryConversationStore


@pytest.fixture
def service():
    """Create a conversation service with fresh storage for each test."""
    storage = InMemoryConversationStore()
    rate_limiter = RateLimiter(
        max_requests=1000, window_seconds=3600
    )  # High limit for tests
    service = ConversationService(store=storage, rate_limiter=rate_limiter)
    return service


def test_get_or_create_conversation_new(service):
    """Test creating a new conversation."""
    conversation = service.get_or_create_conversation()

    assert conversation is not None
    assert conversation.id is not None
    assert len(conversation.messages) == 0


def test_get_or_create_conversation_existing(service):
    """Test retrieving an existing conversation."""
    # Create initial conversation
    conv1 = service.get_or_create_conversation("test-id")

    # Get same conversation
    conv2 = service.get_or_create_conversation("test-id")

    assert conv1.id == conv2.id == "test-id"


def test_get_or_create_conversation_with_invalid_id(service):
    """Test creating new conversation when provided ID doesn't exist."""
    # Try to get conversation with non-existent ID
    conversation = service.get_or_create_conversation("nonexistent")

    # Should create new conversation with the provided ID
    assert conversation.id == "nonexistent"
    assert len(conversation.messages) == 0


def test_add_user_message(service):
    """Test adding user message to conversation."""
    conversation = service.add_user_message("test-conv", "Hello there!")

    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "user"
    assert conversation.messages[0].content == "Hello there!"


def test_add_assistant_message(service):
    """Test adding assistant message to conversation."""
    # Add user message first
    service.add_user_message("test-conv", "Hello")

    # Add assistant response
    conversation = service.add_assistant_message("test-conv", "Hi! How can I help?")

    assert len(conversation.messages) == 2
    assert conversation.messages[1].role == "assistant"
    assert conversation.messages[1].content == "Hi! How can I help?"


def test_get_conversation_context(service):
    """Test getting conversation context."""
    # Add some messages
    service.add_user_message("test-conv", "What is Fran?")
    service.add_assistant_message("test-conv", "Fran is a CrossFit benchmark workout.")
    service.add_user_message("test-conv", "What movements does it have?")

    context = service.get_conversation_context("test-conv")

    assert len(context) == 3
    assert context[0] == {"role": "user", "content": "What is Fran?"}
    assert context[1] == {
        "role": "assistant",
        "content": "Fran is a CrossFit benchmark workout.",
    }
    assert context[2] == {"role": "user", "content": "What movements does it have?"}


def test_get_conversation_context_nonexistent(service):
    """Test getting context for non-existent conversation."""
    context = service.get_conversation_context("nonexistent")
    assert context == []


def test_get_conversation_context_with_token_limit(service):
    """Test getting conversation context with token limit."""
    # Add messages
    service.add_user_message("test-conv", "What is Fran?")
    service.add_assistant_message("test-conv", "Fran is a CrossFit benchmark workout.")

    # Get context with very low token limit
    context = service.get_conversation_context("test-conv", max_tokens=10)

    # Should return fewer messages due to token limit
    assert len(context) <= 2


def test_delete_conversation(service):
    """Test deleting a conversation."""
    # Create conversation
    service.add_user_message("test-conv", "Hello")

    # Delete it
    result = service.delete_conversation("test-conv")
    assert result is True

    # Should no longer exist
    context = service.get_conversation_context("test-conv")
    assert context == []


def test_list_conversations(service):
    """Test listing conversations."""
    # Create some conversations
    service.add_user_message("conv-1", "Hello 1")
    service.add_user_message("conv-2", "Hello 2")
    service.add_user_message("conv-3", "Hello 3")

    conversation_ids = service.list_conversations()

    assert len(conversation_ids) == 3
    assert "conv-1" in conversation_ids
    assert "conv-2" in conversation_ids
    assert "conv-3" in conversation_ids


def test_get_conversation_summary(service):
    """Test getting conversation summary."""
    # Create conversation with messages
    service.add_user_message("test-conv", "What is Fran?")
    service.add_assistant_message(
        "test-conv", "Fran is a CrossFit benchmark workout with thrusters and pull-ups."
    )

    summary = service.get_conversation_summary("test-conv")

    assert summary is not None
    assert summary["id"] == "test-conv"
    assert summary["message_count"] == 2
    assert "created_at" in summary
    assert "last_updated" in summary
    assert "Fran is a CrossFit benchmark" in summary["latest_message"]


def test_get_conversation_summary_nonexistent(service):
    """Test getting summary for non-existent conversation."""
    summary = service.get_conversation_summary("nonexistent")
    assert summary is None


def test_cleanup_expired_conversations(service):
    """Test cleanup of expired conversations."""
    # Mock the storage cleanup method
    service.store.cleanup_expired = Mock(return_value=3)

    result = service.cleanup_expired_conversations()

    assert result == 3
    service.store.cleanup_expired.assert_called_once()


def test_message_threading(service):
    """Test that messages are properly threaded in conversations."""
    # Simulate a multi-turn conversation
    service.add_user_message("conv-1", "What is Fran?")
    service.add_assistant_message("conv-1", "Fran is a CrossFit workout.")
    service.add_user_message("conv-1", "What movements?")
    service.add_assistant_message("conv-1", "Thrusters and pull-ups.")
    service.add_user_message("conv-1", "How many reps?")

    context = service.get_conversation_context("conv-1")

    # Check proper threading
    assert len(context) == 5
    assert context[0]["role"] == "user"
    assert context[1]["role"] == "assistant"
    assert context[2]["role"] == "user"
    assert context[3]["role"] == "assistant"
    assert context[4]["role"] == "user"

    # Check content progression
    assert "Fran" in context[0]["content"]
    assert "CrossFit workout" in context[1]["content"]
    assert "movements" in context[2]["content"]
    assert "Thrusters" in context[3]["content"]
    assert "reps" in context[4]["content"]
