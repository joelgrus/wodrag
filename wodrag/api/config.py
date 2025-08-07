"""API configuration settings."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API configuration settings."""

    # API Settings
    host: str = Field(default="127.0.0.1", description="API host")
    port: int = Field(default=8000, description="API port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    log_level: str = Field(default="info", description="Logging level")

    # CORS Settings
    cors_origins: list[str] = Field(default=["http://localhost:3000"], description="Allowed CORS origins")

    # Database Settings (inherit from existing env)
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/wodrag",
        description="Database connection URL",
    )

    # OpenAI Settings (inherit from existing env)
    openai_api_key: SecretStr | None = Field(
        default=None, description="OpenAI API key for embeddings"
    )

    model_config = {"env_prefix": "WODRAG_API_", "case_sensitive": False}


def get_settings() -> APISettings:
    """Get application settings."""
    return APISettings()
