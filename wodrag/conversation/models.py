"""Conversation data models for agent memory system."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class ConversationMessage:
    """A single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationMessage":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class Conversation:
    """A conversation containing multiple messages."""

    id: str
    messages: list[ConversationMessage]
    created_at: datetime
    last_updated: datetime

    def __post_init__(self) -> None:
        """Ensure ID is set if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())

    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the conversation."""
        message = ConversationMessage(
            role=role, content=content, timestamp=datetime.now(UTC)
        )
        self.messages.append(message)
        self.last_updated = datetime.now(UTC)

    def get_context_for_llm(self, max_tokens: int = 8000) -> list[dict]:
        """
        Get conversation history formatted for LLM context.

        Returns messages in format: [{"role": "user", "content": "..."}, ...]
        Truncates from oldest messages if token limit would be exceeded.
        """
        # Simple token estimation: ~4 chars per token
        estimated_tokens = 0
        context_messages: list[dict] = []

        # Add messages from newest to oldest until we hit token limit
        for message in reversed(self.messages):
            message_tokens = len(message.content) // 4 + 10  # +10 for role/metadata
            if estimated_tokens + message_tokens > max_tokens and context_messages:
                break

            context_messages.insert(
                0, {"role": message.role, "content": message.content}
            )
            estimated_tokens += message_tokens

        return context_messages

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            messages=[ConversationMessage.from_dict(msg) for msg in data["messages"]],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )

    @classmethod
    def create_new(cls, conversation_id: str | None = None) -> "Conversation":
        """Create a new conversation."""
        now = datetime.now(UTC)
        return cls(
            id=conversation_id or str(uuid.uuid4()),
            messages=[],
            created_at=now,
            last_updated=now,
        )
