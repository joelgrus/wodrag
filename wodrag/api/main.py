"""Litestar application setup."""

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.di import Provide

from wodrag.agents.master import MasterAgent
from wodrag.agents.text_to_sql import QueryGenerator
from wodrag.agents.workout_generator import WorkoutSearchGenerator
from wodrag.api.config import get_settings
from wodrag.api.routers import agent, health
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
        },
        debug=False,  # Set to True for development
    )

    return app


app = create_app()
