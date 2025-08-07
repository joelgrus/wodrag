"""Configuration for the conversation memory system."""

import os
from dataclasses import dataclass


@dataclass
class ConversationConfig:
    """Configuration for conversation memory system."""

    # Storage limits
    max_conversations: int = 1000
    max_messages_per_conversation: int = 50
    conversation_ttl_hours: int = 24

    # Context limits
    max_context_tokens: int = 8000

    # Rate limiting
    rate_limit_requests_per_hour: int = 100

    @classmethod
    def from_env(cls) -> "ConversationConfig":
        """Create configuration from environment variables."""
        return cls(
            max_conversations=int(os.getenv("MAX_CONVERSATIONS", "1000")),
            max_messages_per_conversation=int(
                os.getenv("MAX_MESSAGES_PER_CONVERSATION", "50")
            ),
            conversation_ttl_hours=int(os.getenv("CONVERSATION_TTL_HOURS", "24")),
            max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "8000")),
            rate_limit_requests_per_hour=int(
                os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "100")
            ),
        )
