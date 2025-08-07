"""Health check endpoints."""

import psycopg2
from fastapi import APIRouter, HTTPException

from wodrag.api.config import get_settings
from wodrag.api.models import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(status="healthy", service="wodrag-api")


@router.get("/health/database")
async def database_health_check() -> dict[str, str]:
    """Check database connectivity."""
    settings = get_settings()

    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()

        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Database connection failed: {str(e)}"
        )
