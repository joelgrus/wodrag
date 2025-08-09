"""FastAPI application setup with global singletons."""

import logging
import os
from functools import lru_cache
import threading
from logging.handlers import RotatingFileHandler
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from wodrag.api.config import get_settings
from wodrag.api.lm_budget import reset_request_lm_budget, wrap_lm_for_budget
from wodrag.conversation.config import ConversationConfig
from wodrag.conversation.security import NoopRateLimiter, RateLimiter
from wodrag.conversation.service import ConversationService
from wodrag.conversation.storage import InMemoryConversationStore
from wodrag.database.duckdb_client import DuckDBQueryService
from wodrag.database.workout_repository import WorkoutRepository
from wodrag.services.embedding_service import EmbeddingService

# Application configuration
_logging_configured: bool = False
_singletons: dict[str, Any] = {}
_singleton_lock = threading.Lock()


def configure_logging() -> None:
    """Configure rotating file logging for the API and Uvicorn."""
    global _logging_configured
    if _logging_configured:
        return

    log_dir = os.getenv("WODRAG_LOG_DIR", "/var/log/wodrag")
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "api.log")
        handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)

        level = os.getenv("WODRAG_LOG_LEVEL", "INFO").upper()

        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(handler)

        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            logger = logging.getLogger(name)
            logger.setLevel(level)
            logger.addHandler(handler)

    except Exception:
        # If directory creation fails, fall back to stdout-only
        pass

    _logging_configured = True


@lru_cache(maxsize=1)
def get_conversation_config() -> ConversationConfig:
    """Get conversation config from environment (cached singleton)."""
    return ConversationConfig.from_env()


def get_conversation_store(
    config: ConversationConfig = Depends(get_conversation_config)
) -> InMemoryConversationStore:
    """Get conversation store with configuration dependency (thread-safe singleton)."""
    if 'conversation_store' not in _singletons:
        with _singleton_lock:
            if 'conversation_store' not in _singletons:
                _singletons['conversation_store'] = InMemoryConversationStore(
                    max_conversations=config.max_conversations,
                    max_messages_per_conversation=config.max_messages_per_conversation,
                    conversation_ttl_hours=config.conversation_ttl_hours,
                )
    return _singletons['conversation_store']


def get_rate_limiter(
    config: ConversationConfig = Depends(get_conversation_config)
) -> RateLimiter:
    """Get rate limiter with configuration dependency (thread-safe singleton)."""
    if 'rate_limiter' not in _singletons:
        with _singleton_lock:
            if 'rate_limiter' not in _singletons:
                _singletons['rate_limiter'] = RateLimiter(
                    max_requests=config.rate_limit_requests_per_hour, window_seconds=3600
                )
    return _singletons['rate_limiter']


def get_global_rate_limiter(
    config: ConversationConfig = Depends(get_conversation_config)
) -> RateLimiter:
    """Get global rate limiter with configuration dependency (thread-safe singleton)."""
    if 'global_rate_limiter' not in _singletons:
        with _singleton_lock:
            if 'global_rate_limiter' not in _singletons:
                _singletons['global_rate_limiter'] = RateLimiter(
                    max_requests=config.global_rate_limit_requests_per_day,
                    window_seconds=86400,  # 24 hours
                )
    return _singletons['global_rate_limiter']


def get_conversation_service(
    store: InMemoryConversationStore = Depends(get_conversation_store)
) -> ConversationService:
    """Get conversation service with store dependency (thread-safe singleton)."""
    if 'conversation_service' not in _singletons:
        with _singleton_lock:
            if 'conversation_service' not in _singletons:
                # Use NoopRateLimiter here to avoid double-counting; per-client checks
                # are performed at the API router layer.
                _singletons['conversation_service'] = ConversationService(
                    store=store, rate_limiter=NoopRateLimiter()
                )
    return _singletons['conversation_service']


def get_embedding_service() -> EmbeddingService:
    """Get embedding service."""
    return EmbeddingService()


def get_workout_repository(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> WorkoutRepository:
    """Get workout repository with embedding service dependency."""
    return WorkoutRepository(embedding_service)


def create_workout_repository() -> WorkoutRepository:
    """Create workout repository directly (for non-FastAPI use)."""
    embedding_service = get_embedding_service()
    return WorkoutRepository(embedding_service)


def get_master_agent(
    workout_repo: WorkoutRepository = Depends(get_workout_repository)
) -> Any:
    """Get master agent with workout repository dependency."""
    # Import DSPy-dependent modules lazily to avoid side effects during app import
    import dspy  # type: ignore[import-untyped]

    from wodrag.agents.master import MasterAgent
    from wodrag.agents.text_to_sql import QueryGenerator
    from wodrag.agents.workout_generator import (
        WorkoutSearchGenerator,
    )

    # Configure DSPy if not already configured
    if not hasattr(dspy.settings, "lm") or dspy.settings.lm is None:
        import os

        # Use OpenRouter Gemini Flash Lite (cost effective and fast)
        base_lm = dspy.LM(
            "openrouter/google/gemini-2.5-flash-lite",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            max_tokens=10000,
        )
        # Wrap LM with per-request budget enforcement and configure
        wrap_lm_for_budget(base_lm)
        dspy.configure(lm=base_lm)

    query_generator = QueryGenerator()
    duckdb_service = DuckDBQueryService()
    workout_generator = WorkoutSearchGenerator()

    return MasterAgent(
        workout_repo=workout_repo,
        query_generator=query_generator,
        duckdb_service=duckdb_service,
        workout_generator=workout_generator,
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    configure_logging()
    app = FastAPI(
        title="Wodrag CrossFit API",
        description="AI-powered CrossFit workout search and coaching API",
        version="0.1.0",
    )

    # Configure CORS
    settings = get_settings()
    allowed_origins = settings.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Include routers
    from wodrag.api.routers import agent_fastapi, health_fastapi, workouts_fastapi

    app.include_router(agent_fastapi.router, prefix="/api/v1")
    app.include_router(health_fastapi.router, prefix="/api/v1")
    app.include_router(workouts_fastapi.router, prefix="/api/v1")

    # Initialize per-request LM budget via middleware
    @app.middleware("http")
    async def lm_budget_middleware(  # noqa: ANN001
        request: Request, call_next: Any
    ) -> Any:
        # Reset the per-request counter with configured budget
        config = get_conversation_config()
        reset_request_lm_budget(config.per_request_lm_call_budget)
        response = await call_next(request)
        return response

    return app


# Create the app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "wodrag.api.main_fastapi:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
    )
