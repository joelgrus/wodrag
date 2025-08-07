"""Conversation data models for agent memory system."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


class ConversationError(Exception):
    """Base exception for conversation-related errors."""


class ConversationDeserializationError(ConversationError):
    """Exception raised when conversation data cannot be deserialized."""


class ConversationValidationError(ConversationError):
    """Exception raised when conversation data fails validation."""


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
        """Create from dictionary with validation."""
        try:
            role = data.get("role")
            content = data.get("content")
            timestamp_str = data.get("timestamp")

            # Validate required fields
            if not role:
                raise ConversationValidationError("Message role is required")
            if content is None:
                raise ConversationValidationError("Message content is required")
            if not timestamp_str:
                raise ConversationValidationError("Message timestamp is required")

            # Validate role
            if role not in ("user", "assistant"):
                raise ConversationValidationError(
                    f"Invalid message role: {role}. Must be 'user' or 'assistant'"
                )

            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ConversationValidationError(
                    f"Invalid timestamp format: {timestamp_str}"
                ) from e

            # Validate content length (prevent DoS)
            if len(content) > 100000:  # 100KB limit
                raise ConversationValidationError(
                    f"Message content too long: {len(content)} > 100000 characters"
                )

            return cls(role=role, content=content, timestamp=timestamp)

        except KeyError as e:
            raise ConversationDeserializationError(
                f"Missing required field: {e}"
            ) from e
        except (TypeError, AttributeError) as e:
            raise ConversationDeserializationError(
                f"Invalid message data format: {e}"
            ) from e


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
        """Add a new message to the conversation with validation."""
        # Validate role
        if role not in ("user", "assistant"):
            raise ConversationValidationError(
                f"Invalid message role: {role}. Must be 'user' or 'assistant'"
            )

        # Validate content
        if not isinstance(content, str):
            raise ConversationValidationError(
                f"Message content must be string, got: {type(content)}"
            )

        if len(content.strip()) == 0:
            raise ConversationValidationError("Message content cannot be empty")

        if len(content) > 100000:  # 100KB limit
            raise ConversationValidationError(
                f"Message content too long: {len(content)} > 100000 characters"
            )

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
        """Create from dictionary with validation."""
        try:
            conversation_id = data.get("id")
            messages_data = data.get("messages", [])
            created_at_str = data.get("created_at")
            last_updated_str = data.get("last_updated")

            # Validate required fields
            if not conversation_id:
                raise ConversationValidationError("Conversation ID is required")
            if not isinstance(messages_data, list):
                raise ConversationValidationError("Messages must be a list")
            if not created_at_str:
                raise ConversationValidationError("Created at timestamp is required")
            if not last_updated_str:
                raise ConversationValidationError("Last updated timestamp is required")

            # Parse timestamps
            try:
                created_at = datetime.fromisoformat(created_at_str)
                last_updated = datetime.fromisoformat(last_updated_str)
            except ValueError as e:
                raise ConversationValidationError(
                    f"Invalid timestamp format: {e}"
                ) from e

            # Parse messages
            try:
                messages = [ConversationMessage.from_dict(msg) for msg in messages_data]
            except (ConversationError, TypeError) as e:
                raise ConversationValidationError(f"Invalid message data: {e}") from e

            # Validate conversation limits
            if len(messages) > 1000:  # Prevent memory DoS
                raise ConversationValidationError(
                    f"Too many messages: {len(messages)} > 1000"
                )

            return cls(
                id=conversation_id,
                messages=messages,
                created_at=created_at,
                last_updated=last_updated,
            )

        except KeyError as e:
            raise ConversationDeserializationError(
                f"Missing required field: {e}"
            ) from e
        except (TypeError, AttributeError) as e:
            raise ConversationDeserializationError(
                f"Invalid conversation data format: {e}"
            ) from e

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
