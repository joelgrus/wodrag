"""Tests for conversation storage."""

from datetime import UTC, datetime, timedelta

import pytest

from wodrag.conversation.models import Conversation
from wodrag.conversation.storage import InMemoryConversationStore


@pytest.fixture
def storage():
    """Create a fresh storage instance for each test."""
    return InMemoryConversationStore(
        max_conversations=5,  # Small limit for testing
        max_messages_per_conversation=3,  # Small limit for testing
        conversation_ttl_hours=1,
    )


@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing."""
    conversation = Conversation.create_new("test-conv-1")
    conversation.add_message("user", "Hello")
    conversation.add_message("assistant", "Hi there!")
    return conversation


def test_save_and_get_conversation(storage, sample_conversation):
    """Test basic save and retrieve operations."""
    # Save conversation
    storage.save_conversation(sample_conversation)

    # Retrieve conversation
    retrieved = storage.get_conversation("test-conv-1")

    assert retrieved is not None
    assert retrieved.id == "test-conv-1"
    assert len(retrieved.messages) == 2
    assert retrieved.messages[0].content == "Hello"


def test_get_nonexistent_conversation(storage):
    """Test retrieving a conversation that doesn't exist."""
    result = storage.get_conversation("nonexistent")
    assert result is None


def test_conversation_lru_eviction(storage):
    """Test LRU eviction when max conversations exceeded."""
    # Fill storage to capacity
    for i in range(5):
        conv = Conversation.create_new(f"conv-{i}")
        conv.add_message("user", f"Message {i}")
        storage.save_conversation(conv)

    # Add one more conversation (should evict oldest)
    new_conv = Conversation.create_new("conv-new")
    new_conv.add_message("user", "New message")
    storage.save_conversation(new_conv)

    # First conversation should be evicted
    assert storage.get_conversation("conv-0") is None
    # Last conversation should still exist
    assert storage.get_conversation("conv-new") is not None


def test_conversation_message_limit(storage):
    """Test message limit enforcement per conversation."""
    conversation = Conversation.create_new("test-conv")

    # Add more messages than the limit
    for i in range(5):
        conversation.add_message("user", f"Message {i}")

    # Save conversation
    storage.save_conversation(conversation)

    # Retrieve and check message count
    retrieved = storage.get_conversation("test-conv")
    assert (
        len(retrieved.messages) == 3
    )  # Should be limited to max_messages_per_conversation

    # Should keep the most recent messages
    assert retrieved.messages[-1].content == "Message 4"
    assert retrieved.messages[-2].content == "Message 3"


def test_conversation_expiry(storage):
    """Test conversation expiry based on TTL."""
    conversation = Conversation.create_new("test-conv")
    conversation.add_message("user", "Hello")

    # Save conversation first
    storage.save_conversation(conversation)

    # Manually set timestamp to past (expired) directly in storage
    stored_conversation = storage._conversations["test-conv"]
    stored_conversation.last_updated = datetime.now(UTC) - timedelta(hours=2)

    # Should return None for expired conversation
    assert storage.get_conversation("test-conv") is None


def test_delete_conversation(storage, sample_conversation):
    """Test conversation deletion."""
    # Save conversation
    storage.save_conversation(sample_conversation)
    assert storage.get_conversation("test-conv-1") is not None

    # Delete conversation
    result = storage.delete_conversation("test-conv-1")
    assert result is True

    # Should no longer exist
    assert storage.get_conversation("test-conv-1") is None

    # Deleting non-existent conversation should return False
    result = storage.delete_conversation("test-conv-1")
    assert result is False


def test_list_conversations(storage):
    """Test listing conversations."""
    # Add some conversations
    conversations = []
    for i in range(3):
        conv = Conversation.create_new(f"conv-{i}")
        conv.add_message("user", f"Message {i}")
        conversations.append(conv)
        storage.save_conversation(conv)

    # List conversations
    conversation_ids = storage.list_conversations()

    assert len(conversation_ids) == 3
    # Should be in reverse order (most recent first)
    assert conversation_ids[0] == "conv-2"
    assert conversation_ids[1] == "conv-1"
    assert conversation_ids[2] == "conv-0"


def test_cleanup_expired(storage):
    """Test cleanup of expired conversations."""
    # Add some conversations
    for i in range(3):
        conv = Conversation.create_new(f"conv-{i}")
        conv.add_message("user", f"Message {i}")
        storage.save_conversation(conv)

    # Manually expire some conversations
    conv_0 = storage.get_conversation("conv-0")
    conv_1 = storage.get_conversation("conv-1")
    conv_0.last_updated = datetime.now(UTC) - timedelta(hours=2)
    conv_1.last_updated = datetime.now(UTC) - timedelta(hours=2)

    # Run cleanup
    expired_count = storage.cleanup_expired()

    assert expired_count == 2
    assert storage.get_conversation("conv-0") is None
    assert storage.get_conversation("conv-1") is None
    assert storage.get_conversation("conv-2") is not None


def test_storage_stats(storage):
    """Test getting storage statistics."""
    # Add some conversations with messages
    for i in range(3):
        conv = Conversation.create_new(f"conv-{i}")
        for j in range(2):
            conv.add_message("user", f"Message {i}-{j}")
        storage.save_conversation(conv)

    stats = storage.get_stats()

    assert stats["total_conversations"] == 3
    assert stats["total_messages"] == 6  # 3 conversations * 2 messages each
    assert stats["max_conversations"] == 5
    assert stats["max_messages_per_conversation"] == 3


def test_lru_access_pattern(storage):
    """Test that accessing conversations moves them to most recent."""
    # Add conversations
    for i in range(3):
        conv = Conversation.create_new(f"conv-{i}")
        conv.add_message("user", f"Message {i}")
        storage.save_conversation(conv)

    # Access conv-0 (should move to most recent)
    storage.get_conversation("conv-0")

    # List conversations - conv-0 should be first now
    conversation_ids = storage.list_conversations()
    assert conversation_ids[0] == "conv-0"
