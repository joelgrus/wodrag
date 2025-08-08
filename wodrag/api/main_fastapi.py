"""FastAPI application setup with global singletons."""

import dspy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wodrag.agents.master import MasterAgent
from wodrag.agents.text_to_sql import QueryGenerator
from wodrag.agents.workout_generator import WorkoutSearchGenerator
from wodrag.api.config import get_settings
from wodrag.conversation.config import ConversationConfig
from wodrag.conversation.security import RateLimiter
from wodrag.conversation.service import ConversationService
from wodrag.conversation.storage import InMemoryConversationStore
from wodrag.database.duckdb_client import DuckDBQueryService
from wodrag.database.workout_repository import WorkoutRepository

# Global singleton instances - simple and clear!
_conversation_config: ConversationConfig | None = None
_conversation_store: InMemoryConversationStore | None = None
_rate_limiter: RateLimiter | None = None
_conversation_service: ConversationService | None = None
_workout_repository: WorkoutRepository | None = None
_master_agent: MasterAgent | None = None

def get_conversation_config() -> ConversationConfig:
    """Get singleton conversation config."""
    global _conversation_config
    if _conversation_config is None:
        _conversation_config = ConversationConfig.from_env()
    return _conversation_config

def get_conversation_store() -> InMemoryConversationStore:
    """Get singleton conversation store."""
    global _conversation_store
    if _conversation_store is None:
        config = get_conversation_config()
        _conversation_store = InMemoryConversationStore(
            max_conversations=config.max_conversations,
            max_messages_per_conversation=config.max_messages_per_conversation,
            conversation_ttl_hours=config.conversation_ttl_hours,
        )
    return _conversation_store

def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        config = get_conversation_config()
        _rate_limiter = RateLimiter(
            max_requests=config.rate_limit_requests_per_hour,
            window_seconds=3600
        )
    return _rate_limiter

def get_conversation_service() -> ConversationService:
    """Get singleton conversation service."""
    global _conversation_service
    if _conversation_service is None:
        store = get_conversation_store()
        rate_limiter = get_rate_limiter()
        _conversation_service = ConversationService(store=store, rate_limiter=rate_limiter)
    return _conversation_service

def get_workout_repository() -> WorkoutRepository:
    """Get singleton workout repository."""
    global _workout_repository
    if _workout_repository is None:
        _workout_repository = WorkoutRepository()
    return _workout_repository

def get_master_agent() -> MasterAgent:
    """Get singleton master agent."""
    global _master_agent
    if _master_agent is None:
        # Configure DSPy if not already configured
        if not hasattr(dspy.settings, "lm") or dspy.settings.lm is None:
            import os
            # Use OpenRouter Gemini Flash Lite (cost effective)
            dspy.configure(
                lm=dspy.LM(
                    "openrouter/google/gemini-2.5-flash-lite", 
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    max_tokens=10000
                )
            )
        
        workout_repo = get_workout_repository()
        query_generator = QueryGenerator()
        duckdb_service = DuckDBQueryService()
        workout_generator = WorkoutSearchGenerator()
        
        _master_agent = MasterAgent(
            workout_repo=workout_repo,
            query_generator=query_generator,
            duckdb_service=duckdb_service,
            workout_generator=workout_generator,
        )
    return _master_agent

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
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
