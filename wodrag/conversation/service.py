"""Conversation management service."""

from .models import Conversation, ConversationValidationError
from .security import (
    MessageSanitizer,
    RateLimiterProtocol,
    SecureIdGenerator,
)
from .storage import ConversationStore


class ConversationService:
    """Service for managing conversations and their context."""

    def __init__(
        self, store: ConversationStore, rate_limiter: RateLimiterProtocol
    ) -> None:
        """Initialize conversation service with explicit dependencies.

        Args:
            store: Conversation storage backend
            rate_limiter: Rate limiter instance
        """
        self.store = store
        self.rate_limiter = rate_limiter

    def get_or_create_conversation(
        self, conversation_id: str | None = None, client_identifier: str = "unknown"
    ) -> Conversation:
        """
        Get an existing conversation or create a new one.

        Args:
            conversation_id: Optional ID of existing conversation
            client_identifier: Identifier for rate limiting (e.g., IP address)

        Returns:
            Conversation object (existing or new)

        Raises:
            ConversationValidationError: If rate limited or invalid ID
        """
        # Check rate limiting
        if not self.rate_limiter.is_allowed(client_identifier):
            raise ConversationValidationError(
                "You're sending requests too quickly. Please wait a few "
                "minutes before trying again — this helps keep the service "
                "running smoothly for everyone."
            )

        if conversation_id:
            # Validate and sanitize conversation ID
            try:
                conversation_id = MessageSanitizer.validate_conversation_id(
                    conversation_id
                )
            except ValueError as e:
                raise ConversationValidationError(
                    f"Invalid conversation ID: {e}"
                ) from e

            conversation = self.store.get_conversation(conversation_id)
            if conversation:
                return conversation

        # Create new conversation with secure ID
        new_id = conversation_id or SecureIdGenerator.generate_conversation_id()
        conversation = Conversation.create_new(new_id)
        self.store.save_conversation(conversation)
        return conversation

    def add_user_message(
        self, conversation_id: str, message: str, client_identifier: str = "unknown"
    ) -> Conversation:
        """Add a user message to the conversation with sanitization.

        Args:
            conversation_id: ID of conversation
            message: Raw message content
            client_identifier: Identifier for rate limiting

        Returns:
            Updated conversation

        Raises:
            ConversationValidationError: If message is invalid or rate limited
        """
        # Check rate limiting
        if not self.rate_limiter.is_allowed(client_identifier):
            raise ConversationValidationError(
                "You're sending requests too quickly. Please wait a few "
                "minutes before trying again — this helps keep the service "
                "running smoothly for everyone."
            )

        # Sanitize message content
        try:
            sanitized_message = MessageSanitizer.sanitize_message(message)
        except ValueError as e:
            raise ConversationValidationError(f"Invalid message: {e}") from e

        conversation = self.get_or_create_conversation(
            conversation_id, client_identifier
        )
        conversation.add_message("user", sanitized_message)
        self.store.save_conversation(conversation)
        return conversation

    def add_assistant_message(
        self, conversation_id: str, message: str, client_identifier: str = "unknown"
    ) -> Conversation:
        """Add an assistant message to the conversation.

        Args:
            conversation_id: ID of conversation
            message: Assistant response (trusted, no sanitization)
            client_identifier: Identifier for context

        Returns:
            Updated conversation
        """
        # Assistant messages are trusted, but still validate length
        if len(message) > MessageSanitizer.MAX_MESSAGE_LENGTH:
            # Truncate rather than error for assistant messages
            message = message[: MessageSanitizer.MAX_MESSAGE_LENGTH - 3] + "..."

        conversation = self.get_or_create_conversation(
            conversation_id, client_identifier
        )
        conversation.add_message("assistant", message)
        self.store.save_conversation(conversation)
        return conversation

    def get_conversation_context(
        self, conversation_id: str, max_tokens: int = 8000
    ) -> list[dict]:
        """
        Get conversation history formatted for LLM context.

        Args:
            conversation_id: ID of conversation
            max_tokens: Maximum tokens to include in context

        Returns:
            List of message dicts in format [{"role": "user", "content": "..."}, ...]
        """
        conversation = self.store.get_conversation(conversation_id)
        if not conversation:
            return []

        return conversation.get_context_for_llm(max_tokens)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        return self.store.delete_conversation(conversation_id)

    def list_conversations(self, limit: int = 100) -> list[str]:
        """List conversation IDs, most recent first."""
        return self.store.list_conversations(limit)

    def get_conversation_summary(self, conversation_id: str) -> dict | None:
        """Get a summary of the conversation."""
        conversation = self.store.get_conversation(conversation_id)
        if not conversation:
            return None

        return {
            "id": conversation.id,
            "message_count": len(conversation.messages),
            "created_at": conversation.created_at.isoformat(),
            "last_updated": conversation.last_updated.isoformat(),
            "latest_message": conversation.messages[-1].content[:100] + "..."
            if conversation.messages
            else None,
        }

    def cleanup_expired_conversations(self) -> int:
        """Remove expired conversations."""
        return self.store.cleanup_expired()
