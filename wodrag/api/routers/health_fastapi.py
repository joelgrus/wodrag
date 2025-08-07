"""Health check endpoints for FastAPI."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from wodrag.api.models.responses import APIResponse, HealthCheckData
from wodrag.database.workout_repository import WorkoutRepository

# Import singleton getter
from wodrag.api.main_fastapi import get_workout_repository

router = APIRouter(tags=["health"])

@router.get("/health", response_model=APIResponse[HealthCheckData])
async def health_check():
    """Basic health check endpoint.

    Returns:
        APIResponse with health status
    """
    data = HealthCheckData(
        status="healthy", timestamp=datetime.now(UTC), version="0.1.0"
    )
    return APIResponse(success=True, data=data)

@router.get("/health/db", response_model=APIResponse[HealthCheckData])
async def database_health(
    workout_repo: WorkoutRepository = Depends(get_workout_repository)
):
    """Check database connectivity.

    Args:
        workout_repo: Injected WorkoutRepository (singleton)

    Returns:
        APIResponse with database health status
    """
    try:
        # Try to perform a simple database operation
        workout_repo.search_summaries("test", limit=1)

        data = HealthCheckData(
            status="healthy",
            timestamp=datetime.now(UTC),
            version="0.1.0",
            database="connected",
        )
        return APIResponse(success=True, data=data)
        
    except Exception as e:
        data = HealthCheckData(
            status="unhealthy",
            timestamp=datetime.now(UTC),
            version="0.1.0",
            database=f"error: {str(e)}",
        )
        raise HTTPException(
            status_code=503,
            detail=APIResponse(success=False, data=data, error=str(e)).dict()
        )