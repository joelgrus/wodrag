"""Tests for conversation security features."""

import pytest
import time
from unittest.mock import patch

from wodrag.conversation.security import (
    MessageSanitizer,
    SecureIdGenerator,
    RateLimiter,
    get_rate_limiter,
)


class TestMessageSanitizer:
    """Test MessageSanitizer functionality."""
    
    def test_sanitize_normal_message(self):
        """Test sanitizing normal message content."""
        message = "This is a normal message with some text."
        result = MessageSanitizer.sanitize_message(message)
        assert result == message
    
    def test_sanitize_html_tags(self):
        """Test removal of HTML tags."""
        message = "This has <b>bold</b> and <i>italic</i> text."
        result = MessageSanitizer.sanitize_message(message)
        assert result == "This has bold and italic text."
    
    def test_sanitize_script_tags(self):
        """Test removal of script tags."""
        message = "Normal text <script>alert('xss')</script> more text"
        result = MessageSanitizer.sanitize_message(message)
        # Whitespace is normalized, so double space becomes single
        assert result == "Normal text more text"
        assert "script" not in result.lower()
    
    def test_sanitize_multiline_script(self):
        """Test removal of multiline script tags."""
        message = """Normal text <script>
        alert('xss');
        console.log('bad');
        </script> more text"""
        result = MessageSanitizer.sanitize_message(message)
        assert "script" not in result.lower()
        assert "alert" not in result
    
    def test_sanitize_dangerous_urls(self):
        """Test rejection of dangerous URLs."""
        dangerous_messages = [
            "Click javascript:alert('xss')",
            "Visit data:text/html,<script>alert('xss')</script>",
            "Go to vbscript:msgbox('xss')",
        ]
        
        for message in dangerous_messages:
            with pytest.raises(ValueError, match="dangerous URLs"):
                MessageSanitizer.sanitize_message(message)
    
    def test_sanitize_html_escape(self):
        """Test HTML escaping of special characters."""
        message = "This has < and > and & characters"
        result = MessageSanitizer.sanitize_message(message)
        # HTML tags are stripped first, then remaining chars are escaped
        assert result == "This has and &amp; characters"
    
    def test_sanitize_whitespace_normalization(self):
        """Test whitespace normalization."""
        message = "This  has   multiple    spaces\n\nand\t\ttabs"
        result = MessageSanitizer.sanitize_message(message)
        assert result == "This has multiple spaces and tabs"
    
    def test_sanitize_message_too_long(self):
        """Test rejection of overly long messages."""
        long_message = "x" * (MessageSanitizer.MAX_MESSAGE_LENGTH + 1)
        with pytest.raises(ValueError, match="Message too long"):
            MessageSanitizer.sanitize_message(long_message)
    
    def test_sanitize_non_string_input(self):
        """Test rejection of non-string input."""
        with pytest.raises(ValueError, match="must be string"):
            MessageSanitizer.sanitize_message(123)
    
    def test_validate_conversation_id_valid(self):
        """Test validation of valid conversation IDs."""
        valid_ids = [
            "abc123",
            "test-conversation-id",
            "conv_123_456",
            "ABC123def456",
        ]
        
        for conv_id in valid_ids:
            result = MessageSanitizer.validate_conversation_id(conv_id)
            assert result == conv_id
    
    def test_validate_conversation_id_invalid_chars(self):
        """Test rejection of invalid characters in conversation ID."""
        invalid_ids = [
            "conv/123",  # slash
            "conv@123",  # at sign
            "conv 123",  # space
            "conv#123",  # hash
            "conv.123",  # dot
        ]
        
        for conv_id in invalid_ids:
            with pytest.raises(ValueError, match="invalid characters"):
                MessageSanitizer.validate_conversation_id(conv_id)
    
    def test_validate_conversation_id_too_long(self):
        """Test rejection of overly long conversation IDs."""
        long_id = "x" * 101
        with pytest.raises(ValueError, match="too long"):
            MessageSanitizer.validate_conversation_id(long_id)
    
    def test_validate_conversation_id_non_string(self):
        """Test rejection of non-string conversation ID."""
        with pytest.raises(ValueError, match="must be string"):
            MessageSanitizer.validate_conversation_id(123)


class TestSecureIdGenerator:
    """Test SecureIdGenerator functionality."""
    
    def test_generate_conversation_id(self):
        """Test conversation ID generation."""
        conv_id = SecureIdGenerator.generate_conversation_id()
        
        # Should be a string
        assert isinstance(conv_id, str)
        
        # Should be reasonable length (32 bytes -> ~43 chars base64)
        assert 30 <= len(conv_id) <= 50
        
        # Should be URL-safe
        assert all(c.isalnum() or c in '-_' for c in conv_id)
        
        # Should be unique
        conv_id2 = SecureIdGenerator.generate_conversation_id()
        assert conv_id != conv_id2
    
    def test_generate_session_token(self):
        """Test session token generation."""
        token = SecureIdGenerator.generate_session_token()
        
        # Should be longer than conversation ID
        assert len(token) > 50
        
        # Should be URL-safe
        assert all(c.isalnum() or c in '-_' for c in token)
        
        # Should be unique
        token2 = SecureIdGenerator.generate_session_token()
        assert token != token2


class TestRateLimiter:
    """Test RateLimiter functionality."""
    
    def test_rate_limiter_allows_under_limit(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Should allow first 5 requests
        for i in range(5):
            assert limiter.is_allowed("test_client") is True
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Fill the limit
        for i in range(3):
            assert limiter.is_allowed("test_client") is True
        
        # Should block the 4th request
        assert limiter.is_allowed("test_client") is False
    
    def test_rate_limiter_different_clients(self):
        """Test that different clients have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Fill limit for client1
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False
        
        # client2 should still be allowed
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client2") is False
    
    def test_rate_limiter_window_reset(self):
        """Test that rate limit resets after window expires."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)  # 1 second window
        
        # Fill the limit
        assert limiter.is_allowed("test_client") is True
        assert limiter.is_allowed("test_client") is True
        assert limiter.is_allowed("test_client") is False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.is_allowed("test_client") is True
    
    def test_rate_limiter_cleanup(self):
        """Test cleanup of old entries."""
        limiter = RateLimiter(max_requests=5, window_seconds=1)
        
        # Add some requests
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")
        
        # Verify entries exist
        assert len(limiter._requests) == 2
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Run cleanup
        limiter.cleanup_old_entries()
        
        # Should be empty now
        assert len(limiter._requests) == 0
    
    def test_global_rate_limiter(self):
        """Test global rate limiter compatibility function."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        # Both should be RateLimiter instances (but not necessarily the same object)
        assert isinstance(limiter1, RateLimiter)
        assert isinstance(limiter2, RateLimiter)
        
        # Should have same configuration
        assert limiter1.max_requests == limiter2.max_requests
        assert limiter1.window_seconds == limiter2.window_seconds


class TestSecurityIntegration:
    """Test security integration with conversation system."""
    
    def test_secure_conversation_service_integration(self):
        """Test that conversation service uses security measures."""
        from wodrag.conversation.service import ConversationService
        from wodrag.conversation.storage import InMemoryConversationStore
        
        # Create service with fresh storage
        storage = InMemoryConversationStore()
        rate_limiter = RateLimiter(max_requests=1000, window_seconds=3600)
        service = ConversationService(store=storage, rate_limiter=rate_limiter)
        
        # Test message sanitization
        raw_message = "This has <script>alert('xss')</script> dangerous content"
        conversation = service.add_user_message(
            "test-conv", raw_message, client_identifier="test-client"
        )
        
        # Should be sanitized
        assert conversation.messages[0].content != raw_message
        assert "script" not in conversation.messages[0].content.lower()
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        from wodrag.conversation.service import ConversationService
        from wodrag.conversation.storage import InMemoryConversationStore
        from wodrag.conversation import ConversationValidationError
        
        # Create service with rate-limited limiter
        storage = InMemoryConversationStore()
        rate_limiter = RateLimiter(max_requests=0, window_seconds=3600)  # No requests allowed
        service = ConversationService(store=storage, rate_limiter=rate_limiter)
        
        with pytest.raises(ConversationValidationError, match="Rate limit exceeded"):
            service.add_user_message(
                "test-conv", "Test message", client_identifier="test-client"
            )
    
    def test_conversation_id_validation_integration(self):
        """Test conversation ID validation integration."""
        from wodrag.conversation.service import ConversationService
        from wodrag.conversation.storage import InMemoryConversationStore
        from wodrag.conversation import ConversationValidationError
        
        # Create service with fresh storage
        storage = InMemoryConversationStore()
        rate_limiter = RateLimiter(max_requests=1000, window_seconds=3600)
        service = ConversationService(store=storage, rate_limiter=rate_limiter)
        
        # Test invalid conversation ID
        with pytest.raises(ConversationValidationError, match="Invalid conversation ID"):
            service.get_or_create_conversation("invalid/id", client_identifier="test")