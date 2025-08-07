"""Litestar application setup."""

import dspy
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.di import Provide

from wodrag.agents.master import MasterAgent
from wodrag.agents.text_to_sql import QueryGenerator
from wodrag.agents.workout_generator import WorkoutSearchGenerator
from wodrag.api.config import get_settings
from wodrag.api.routers import agent, health
from wodrag.conversation.config import ConversationConfig
from wodrag.conversation.security import RateLimiter
from wodrag.conversation.service import ConversationService
from wodrag.conversation.storage import ConversationStore, InMemoryConversationStore
from wodrag.database.duckdb_client import DuckDBQueryService
from wodrag.database.workout_repository import WorkoutRepository


def provide_workout_repository() -> WorkoutRepository:
    """Provide WorkoutRepository instance for dependency injection."""
    return WorkoutRepository()


def provide_query_generator() -> QueryGenerator:
    """Provide QueryGenerator instance for dependency injection."""
    return QueryGenerator()


def provide_duckdb_service() -> DuckDBQueryService:
    """Provide DuckDBQueryService instance for dependency injection."""
    return DuckDBQueryService()


def provide_workout_generator() -> WorkoutSearchGenerator:
    """Provide WorkoutSearchGenerator instance for dependency injection."""
    return WorkoutSearchGenerator()


def provide_master_agent() -> MasterAgent:
    """Provide MasterAgent instance for dependency injection."""
    # Configure DSPy if not already configured
    if not hasattr(dspy.settings, "lm") or dspy.settings.lm is None:
        dspy.configure(
            lm=dspy.LM("openrouter/google/gemini-2.5-flash-lite", max_tokens=10000)
        )

    # Initialize all services that the master agent needs
    workout_repo = WorkoutRepository()
    query_generator = QueryGenerator()
    duckdb_service = DuckDBQueryService()
    workout_generator = WorkoutSearchGenerator()

    return MasterAgent(
        workout_repo=workout_repo,
        query_generator=query_generator,
        duckdb_service=duckdb_service,
        workout_generator=workout_generator,
    )


def provide_conversation_config() -> ConversationConfig:
    """Provide ConversationConfig instance for dependency injection."""
    return ConversationConfig.from_env()


def provide_conversation_store(conversation_config: ConversationConfig) -> ConversationStore:
    """Provide ConversationStore instance for dependency injection."""
    return InMemoryConversationStore(
        max_conversations=conversation_config.max_conversations,
        max_messages_per_conversation=conversation_config.max_messages_per_conversation,
        conversation_ttl_hours=conversation_config.conversation_ttl_hours,
    )


def provide_rate_limiter(conversation_config: ConversationConfig) -> RateLimiter:
    """Provide RateLimiter instance for dependency injection."""
    return RateLimiter(
        max_requests=conversation_config.rate_limit_requests_per_hour,
        window_seconds=3600  # 1 hour in seconds
    )


def provide_conversation_service(
    conversation_store: ConversationStore,
    rate_limiter: RateLimiter
) -> ConversationService:
    """Provide ConversationService instance for dependency injection."""
    return ConversationService(store=conversation_store, rate_limiter=rate_limiter)


def provide_settings() -> dict:
    """Provide settings for dependency injection."""
    settings = get_settings()
    return {
        "database_url": settings.database_url,
        "openai_api_key": settings.openai_api_key.get_secret_value()
        if settings.openai_api_key
        else None,
    }


def create_app() -> Litestar:
    """Create and configure Litestar application."""

    # Configure CORS
    cors_config = CORSConfig(
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Combine all route handlers (only health and agent)
    route_handlers = [
        *health.route_handlers,
        *agent.route_handlers,
    ]

    # Create application with dependency injection
    app = Litestar(
        route_handlers=route_handlers,
        cors_config=cors_config,
        dependencies={
            "workout_repo": Provide(provide_workout_repository),
            "master_agent": Provide(provide_master_agent),
            "settings": Provide(provide_settings),
            "conversation_config": Provide(provide_conversation_config),
            "conversation_store": Provide(provide_conversation_store),
            "rate_limiter": Provide(provide_rate_limiter),
            "conversation_service": Provide(provide_conversation_service),
        },
        debug=False,  # Set to True for development
    )

    return app


app = create_app()
