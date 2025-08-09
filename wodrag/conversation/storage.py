"""Conversation storage interfaces and implementations."""

from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from threading import Lock

from .models import Conversation


class ConversationStore(ABC):
    """Abstract interface for conversation storage."""

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by ID."""
        pass

    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> None:
        """Save or update a conversation."""
        pass

    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation. Returns True if existed."""
        pass

    @abstractmethod
    def list_conversations(self, limit: int = 100) -> list[str]:
        """List conversation IDs, most recent first."""
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired conversations. Returns count removed."""
        pass


class InMemoryConversationStore(ConversationStore):
    """
    In-memory conversation storage with LRU eviction.

    Features:
    - LRU cache with configurable max size
    - TTL-based expiration
    - Thread-safe operations
    - Easy migration path to Redis/database
    """

    def __init__(
        self,
        max_conversations: int = 1000,
        max_messages_per_conversation: int = 50,
        conversation_ttl_hours: int = 24,
    ):
        self.max_conversations = max_conversations
        self.max_messages_per_conversation = max_messages_per_conversation
        self.conversation_ttl = timedelta(hours=conversation_ttl_hours)

        # Use OrderedDict for LRU behavior
        self._conversations: OrderedDict[str, Conversation] = OrderedDict()
        self._lock = Lock()

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by ID, moving it to end (most recent)."""
        with self._lock:
            if conversation_id not in self._conversations:
                return None

            # Check if expired
            conversation = self._conversations[conversation_id]
            if self._is_expired(conversation):
                del self._conversations[conversation_id]
                return None

            # Move to end (most recently used)
            self._conversations.move_to_end(conversation_id)
            return conversation

    def save_conversation(self, conversation: Conversation) -> None:
        """Save or update a conversation."""
        with self._lock:
            # Enforce message limit per conversation
            if len(conversation.messages) > self.max_messages_per_conversation:
                # Keep most recent messages
                conversation.messages = conversation.messages[
                    -self.max_messages_per_conversation :
                ]

            # Update timestamp
            conversation.last_updated = datetime.now(UTC)

            # Store conversation (moves to end if existing)
            self._conversations[conversation.id] = conversation
            self._conversations.move_to_end(conversation.id)

            # Enforce max conversations limit (LRU eviction)
            while len(self._conversations) > self.max_conversations:
                # Remove oldest conversation
                oldest_id = next(iter(self._conversations))
                del self._conversations[oldest_id]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation. Returns True if existed."""
        with self._lock:
            return self._conversations.pop(conversation_id, None) is not None

    def list_conversations(self, limit: int = 100) -> list[str]:
        """List conversation IDs, most recent first."""
        with self._lock:
            # Return in reverse order (most recent first)
            conversation_ids = list(reversed(self._conversations.keys()))
            return conversation_ids[:limit]

    def cleanup_expired(self) -> int:
        """Remove expired conversations. Returns count removed."""
        with self._lock:
            expired_ids = []
            for conversation_id, conversation in self._conversations.items():
                if self._is_expired(conversation):
                    expired_ids.append(conversation_id)

            for conversation_id in expired_ids:
                del self._conversations[conversation_id]

            return len(expired_ids)

    def get_stats(self) -> dict[str, int]:
        """Get storage statistics."""
        with self._lock:
            total_messages = sum(
                len(conv.messages) for conv in self._conversations.values()
            )
            return {
                "total_conversations": len(self._conversations),
                "total_messages": total_messages,
                "max_conversations": self.max_conversations,
                "max_messages_per_conversation": self.max_messages_per_conversation,
            }

    def _is_expired(self, conversation: Conversation) -> bool:
        """Check if a conversation has expired."""
        return datetime.now(UTC) - conversation.last_updated > self.conversation_ttl
