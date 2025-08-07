"""Configuration for the conversation memory system."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import InMemoryConversationStore


@dataclass
class ConversationConfig:
    """Configuration for conversation memory system."""

    # Storage limits
    max_conversations: int = 1000
    max_messages_per_conversation: int = 50
    conversation_ttl_hours: int = 24

    # Context limits
    max_context_tokens: int = 8000

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
        )

    def apply_to_store(self, store: "InMemoryConversationStore") -> None:
        """Apply configuration to a conversation store."""
        if hasattr(store, "max_conversations"):
            store.max_conversations = self.max_conversations
        if hasattr(store, "max_messages_per_conversation"):
            store.max_messages_per_conversation = self.max_messages_per_conversation
        if hasattr(store, "conversation_ttl_hours"):
            store.conversation_ttl_hours = self.conversation_ttl_hours


# Global config instance
_config: ConversationConfig | None = None


def get_conversation_config() -> ConversationConfig:
    """Get the global conversation configuration."""
    global _config
    if _config is None:
        _config = ConversationConfig.from_env()
    return _config


def set_conversation_config(config: ConversationConfig) -> None:
    """Set the global conversation configuration."""
    global _config
    _config = config
