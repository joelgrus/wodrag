"""Tests for conversation validation and error handling."""

import pytest
from datetime import datetime

from wodrag.conversation.models import (
    Conversation,
    ConversationMessage,
    ConversationError,
    ConversationDeserializationError,
    ConversationValidationError,
)


class TestConversationMessageValidation:
    """Test ConversationMessage validation."""
    
    def test_from_dict_valid_data(self):
        """Test creating message from valid data."""
        data = {
            "role": "user",
            "content": "Hello world",
            "timestamp": "2024-01-01T12:00:00+00:00"
        }
        
        message = ConversationMessage.from_dict(data)
        assert message.role == "user"
        assert message.content == "Hello world"
        assert isinstance(message.timestamp, datetime)
    
    def test_from_dict_missing_role(self):
        """Test error handling for missing role."""
        data = {
            "content": "Hello world",
            "timestamp": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Message role is required"):
            ConversationMessage.from_dict(data)
    
    def test_from_dict_empty_role(self):
        """Test error handling for empty role."""
        data = {
            "role": "",
            "content": "Hello world",
            "timestamp": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Message role is required"):
            ConversationMessage.from_dict(data)
    
    def test_from_dict_invalid_role(self):
        """Test error handling for invalid role."""
        data = {
            "role": "system",
            "content": "Hello world",
            "timestamp": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Invalid message role: system"):
            ConversationMessage.from_dict(data)
    
    def test_from_dict_missing_content(self):
        """Test error handling for missing content."""
        data = {
            "role": "user",
            "timestamp": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Message content is required"):
            ConversationMessage.from_dict(data)
    
    def test_from_dict_empty_content_allowed(self):
        """Test that empty string content is allowed."""
        data = {
            "role": "user",
            "content": "",
            "timestamp": "2024-01-01T12:00:00+00:00"
        }
        
        message = ConversationMessage.from_dict(data)
        assert message.content == ""
    
    def test_from_dict_content_too_long(self):
        """Test error handling for content that's too long."""
        data = {
            "role": "user",
            "content": "x" * 100001,  # Exceeds 100KB limit
            "timestamp": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Message content too long"):
            ConversationMessage.from_dict(data)
    
    def test_from_dict_missing_timestamp(self):
        """Test error handling for missing timestamp."""
        data = {
            "role": "user",
            "content": "Hello world"
        }
        
        with pytest.raises(ConversationValidationError, match="Message timestamp is required"):
            ConversationMessage.from_dict(data)
    
    def test_from_dict_invalid_timestamp(self):
        """Test error handling for invalid timestamp format."""
        data = {
            "role": "user",
            "content": "Hello world",
            "timestamp": "invalid-timestamp"
        }
        
        with pytest.raises(ConversationValidationError, match="Invalid timestamp format"):
            ConversationMessage.from_dict(data)
    
    def test_from_dict_none_data(self):
        """Test error handling for None input."""
        with pytest.raises(ConversationDeserializationError):
            ConversationMessage.from_dict(None)
    
    def test_from_dict_non_dict_data(self):
        """Test error handling for non-dict input."""
        with pytest.raises(ConversationDeserializationError):
            ConversationMessage.from_dict("not a dict")


class TestConversationValidation:
    """Test Conversation validation."""
    
    def test_from_dict_valid_data(self):
        """Test creating conversation from valid data."""
        data = {
            "id": "test-conv",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T12:00:00+00:00"
                }
            ],
            "created_at": "2024-01-01T12:00:00+00:00",
            "last_updated": "2024-01-01T12:00:00+00:00"
        }
        
        conversation = Conversation.from_dict(data)
        assert conversation.id == "test-conv"
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == "Hello"
    
    def test_from_dict_missing_id(self):
        """Test error handling for missing ID."""
        data = {
            "messages": [],
            "created_at": "2024-01-01T12:00:00+00:00",
            "last_updated": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Conversation ID is required"):
            Conversation.from_dict(data)
    
    def test_from_dict_invalid_messages(self):
        """Test error handling for invalid messages format."""
        data = {
            "id": "test-conv",
            "messages": "not a list",
            "created_at": "2024-01-01T12:00:00+00:00",
            "last_updated": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Messages must be a list"):
            Conversation.from_dict(data)
    
    def test_from_dict_too_many_messages(self):
        """Test error handling for too many messages."""
        messages = []
        for i in range(1001):  # Exceeds 1000 limit
            messages.append({
                "role": "user",
                "content": f"Message {i}",
                "timestamp": "2024-01-01T12:00:00+00:00"
            })
        
        data = {
            "id": "test-conv",
            "messages": messages,
            "created_at": "2024-01-01T12:00:00+00:00",
            "last_updated": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Too many messages: 1001 > 1000"):
            Conversation.from_dict(data)
    
    def test_from_dict_invalid_message_data(self):
        """Test error handling for invalid message data."""
        data = {
            "id": "test-conv",
            "messages": [
                {
                    "role": "invalid-role",
                    "content": "Hello",
                    "timestamp": "2024-01-01T12:00:00+00:00"
                }
            ],
            "created_at": "2024-01-01T12:00:00+00:00",
            "last_updated": "2024-01-01T12:00:00+00:00"
        }
        
        with pytest.raises(ConversationValidationError, match="Invalid message data"):
            Conversation.from_dict(data)
    
    def test_add_message_invalid_role(self):
        """Test add_message validation for invalid role."""
        conversation = Conversation.create_new("test")
        
        with pytest.raises(ConversationValidationError, match="Invalid message role: system"):
            conversation.add_message("system", "Hello")
    
    def test_add_message_non_string_content(self):
        """Test add_message validation for non-string content."""
        conversation = Conversation.create_new("test")
        
        with pytest.raises(ConversationValidationError, match="Message content must be string"):
            conversation.add_message("user", 123)
    
    def test_add_message_empty_content(self):
        """Test add_message validation for empty content."""
        conversation = Conversation.create_new("test")
        
        with pytest.raises(ConversationValidationError, match="Message content cannot be empty"):
            conversation.add_message("user", "   ")  # Only whitespace
    
    def test_add_message_content_too_long(self):
        """Test add_message validation for content that's too long."""
        conversation = Conversation.create_new("test")
        
        with pytest.raises(ConversationValidationError, match="Message content too long"):
            conversation.add_message("user", "x" * 100001)


class TestExceptionHierarchy:
    """Test exception hierarchy."""
    
    def test_exception_inheritance(self):
        """Test that all conversation exceptions inherit from ConversationError."""
        assert issubclass(ConversationDeserializationError, ConversationError)
        assert issubclass(ConversationValidationError, ConversationError)
        
        # Test that they can be caught as ConversationError
        try:
            raise ConversationValidationError("test error")
        except ConversationError as e:
            assert isinstance(e, ConversationValidationError)
            assert str(e) == "test error"