"""Tests for conversation models."""

import pytest
from datetime import datetime, timedelta

from wodrag.conversation.models import Conversation, ConversationMessage


def test_conversation_message_creation():
    """Test ConversationMessage creation and serialization."""
    timestamp = datetime.now()
    message = ConversationMessage(
        role="user",
        content="What is Fran?",
        timestamp=timestamp
    )
    
    assert message.role == "user"
    assert message.content == "What is Fran?"
    assert message.timestamp == timestamp
    
    # Test serialization
    data = message.to_dict()
    assert data["role"] == "user"
    assert data["content"] == "What is Fran?"
    assert data["timestamp"] == timestamp.isoformat()
    
    # Test deserialization
    reconstructed = ConversationMessage.from_dict(data)
    assert reconstructed.role == message.role
    assert reconstructed.content == message.content
    assert reconstructed.timestamp == message.timestamp


def test_conversation_creation():
    """Test Conversation creation and basic functionality."""
    conversation = Conversation.create_new("test-id")
    
    assert conversation.id == "test-id"
    assert len(conversation.messages) == 0
    assert conversation.created_at is not None
    assert conversation.last_updated is not None


def test_conversation_add_message():
    """Test adding messages to conversation."""
    conversation = Conversation.create_new("test-id")
    
    # Add user message
    conversation.add_message("user", "What is Fran?")
    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "user"
    assert conversation.messages[0].content == "What is Fran?"
    
    # Add assistant message
    conversation.add_message("assistant", "Fran is a benchmark CrossFit workout...")
    assert len(conversation.messages) == 2
    assert conversation.messages[1].role == "assistant"


def test_conversation_context_for_llm():
    """Test getting conversation context for LLM."""
    conversation = Conversation.create_new("test-id")
    
    # Add some messages
    conversation.add_message("user", "What is Fran?")
    conversation.add_message("assistant", "Fran is a CrossFit benchmark workout with thrusters and pull-ups.")
    conversation.add_message("user", "How many rounds?")
    
    context = conversation.get_context_for_llm(max_tokens=1000)
    
    assert len(context) == 3
    assert context[0] == {"role": "user", "content": "What is Fran?"}
    assert context[1] == {"role": "assistant", "content": "Fran is a CrossFit benchmark workout with thrusters and pull-ups."}
    assert context[2] == {"role": "user", "content": "How many rounds?"}


def test_conversation_context_token_limit():
    """Test conversation context respects token limits."""
    conversation = Conversation.create_new("test-id")
    
    # Add messages that would exceed token limit
    long_message = "x" * 1000  # ~250 tokens
    for i in range(10):
        conversation.add_message("user", f"Message {i}: {long_message}")
    
    # Request context with low token limit
    context = conversation.get_context_for_llm(max_tokens=100)
    
    # Should only get the most recent messages that fit
    assert len(context) < 10
    assert len(context) > 0


def test_conversation_serialization():
    """Test conversation serialization and deserialization."""
    original = Conversation.create_new("test-id")
    original.add_message("user", "Hello")
    original.add_message("assistant", "Hi there!")
    
    # Serialize
    data = original.to_dict()
    assert data["id"] == "test-id"
    assert len(data["messages"]) == 2
    
    # Deserialize
    reconstructed = Conversation.from_dict(data)
    assert reconstructed.id == original.id
    assert len(reconstructed.messages) == len(original.messages)
    assert reconstructed.messages[0].content == original.messages[0].content
    assert reconstructed.messages[1].content == original.messages[1].content


def test_conversation_auto_id_generation():
    """Test automatic ID generation when not provided."""
    conversation = Conversation.create_new()
    
    assert conversation.id is not None
    assert len(conversation.id) > 0
    
    # Should be UUID format
    import uuid
    try:
        uuid.UUID(conversation.id)
    except ValueError:
        pytest.fail("Generated ID is not a valid UUID")