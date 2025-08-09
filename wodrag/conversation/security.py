"""Security utilities for conversation system."""

import html
import re
import secrets
from re import Pattern
from typing import Protocol


class MessageSanitizer:
    """Sanitizes user messages to prevent XSS and other attacks."""

    # Patterns for potentially dangerous content
    SCRIPT_PATTERN: Pattern[str] = re.compile(
        r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL
    )
    HTML_PATTERN: Pattern[str] = re.compile(r"<[^>]+>")
    URL_PATTERN: Pattern[str] = re.compile(
        r"(?:javascript:|data:|vbscript:|about:)", re.IGNORECASE
    )

    # Maximum lengths for content
    MAX_MESSAGE_LENGTH = 10000  # 10KB
    MAX_CONVERSATION_MESSAGES = 1000

    @classmethod
    def sanitize_message(cls, content: str) -> str:
        """
        Sanitize message content to prevent XSS and limit length.

        Args:
            content: Raw message content

        Returns:
            Sanitized content

        Raises:
            ValueError: If content is too long or contains dangerous patterns
        """
        if not isinstance(content, str):
            raise ValueError(f"Message content must be string, got {type(content)}")

        # Check length limit
        if len(content) > cls.MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message too long: {len(content)} > "
                f"{cls.MAX_MESSAGE_LENGTH} characters"
            )

        # Remove script tags completely
        content = cls.SCRIPT_PATTERN.sub("", content)

        # Check for dangerous URLs
        if cls.URL_PATTERN.search(content):
            raise ValueError("Message contains potentially dangerous URLs")

        # Strip HTML tags (but keep the text content)
        content = cls.HTML_PATTERN.sub("", content)

        # HTML escape any remaining special characters
        content = html.escape(content)

        # Normalize whitespace
        content = re.sub(r"\s+", " ", content).strip()

        return content

    @classmethod
    def validate_conversation_id(cls, conversation_id: str) -> str:
        """
        Validate and sanitize conversation ID.

        Args:
            conversation_id: Raw conversation ID

        Returns:
            Validated conversation ID

        Raises:
            ValueError: If ID is invalid
        """
        if not isinstance(conversation_id, str):
            raise ValueError(
                f"Conversation ID must be string, got {type(conversation_id)}"
            )

        # Check length (UUID is typically 36 chars, allow some flexibility)
        if len(conversation_id) > 100:
            raise ValueError("Conversation ID too long")

        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9\-_]+$", conversation_id):
            raise ValueError("Conversation ID contains invalid characters")

        return conversation_id


class SecureIdGenerator:
    """Generates cryptographically secure conversation IDs."""

    @staticmethod
    def generate_conversation_id() -> str:
        """Generate a secure conversation ID."""
        return secrets.token_urlsafe(32)  # 256 bits of entropy

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(48)  # 384 bits of entropy


class RateLimiter:
    """Simple in-memory rate limiter for conversation operations."""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 3600,
        max_identifiers: int = 10000,
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
            max_identifiers: Maximum number of unique identifiers to track
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_identifiers = max_identifiers
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for given identifier.

        Args:
            identifier: Unique identifier (e.g., IP address, user ID)

        Returns:
            True if request is allowed, False if rate limited
        """
        import time

        current_time = time.time()
        window_start = current_time - self.window_seconds

        # Get existing request history (do not create yet)
        existing_requests = self._requests.get(identifier, [])

        # Remove old requests outside the window
        recent_requests = [
            req_time for req_time in existing_requests if req_time > window_start
        ]

        # Check if under limit
        if len(recent_requests) >= self.max_requests:
            return False

        # If this is a new identifier and we're at capacity, evict oldest
        if (
            identifier not in self._requests
            and len(self._requests) >= self.max_identifiers
        ):
            # Remove the oldest identifier
            # (simple LRU-like eviction by oldest timestamp)
            oldest_identifier = min(
                self._requests.keys(),
                key=lambda k: min(self._requests[k]) if self._requests[k] else 0,
            )
            del self._requests[oldest_identifier]

        # Record this request
        recent_requests.append(current_time)
        self._requests[identifier] = recent_requests
        return True

    def cleanup_old_entries(self) -> None:
        """Clean up old rate limit entries to prevent memory leaks."""
        import time

        current_time = time.time()
        window_start = current_time - self.window_seconds

        # Clean up identifiers with no recent requests
        identifiers_to_remove = []
        for identifier, requests in self._requests.items():
            # Filter out old requests
            recent_requests = [
                req_time for req_time in requests if req_time > window_start
            ]

            if not recent_requests:
                identifiers_to_remove.append(identifier)
            else:
                self._requests[identifier] = recent_requests

        # Remove empty identifiers
        for identifier in identifiers_to_remove:
            del self._requests[identifier]


class NoopRateLimiter:
    """Rate limiter that always allows requests (used to avoid double counting)."""

    def is_allowed(self, identifier: str) -> bool:  # noqa: ARG002 - keep signature
        return True

    def cleanup_old_entries(self) -> None:
        return


class RateLimiterProtocol(Protocol):
    """Protocol for rate limiters used by conversation services."""

    def is_allowed(self, identifier: str) -> bool:
        ...

    def cleanup_old_entries(self) -> None:  # pragma: no cover - trivial
        ...
