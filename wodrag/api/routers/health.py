"""Health check endpoints for Litestar API."""

from datetime import datetime

from litestar import Controller, get
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from wodrag.api.models.responses import APIResponse, HealthCheckData
from wodrag.database.workout_repository import WorkoutRepository


class HealthController(Controller):
    """Health check controller."""

    path = "/api/v1/health"

    @get("/")
    async def health_check(self) -> Response[APIResponse[HealthCheckData]]:
        """Basic health check endpoint.

        Returns:
            APIResponse with health status
        """
        data = HealthCheckData(
            status="healthy", timestamp=datetime.now(), version="0.1.0"
        )
        return Response(APIResponse(success=True, data=data), status_code=HTTP_200_OK)

    @get("/db")
    async def database_health(
        self, workout_repo: WorkoutRepository
    ) -> Response[APIResponse[HealthCheckData]]:
        """Check database connectivity.

        Args:
            workout_repo: Injected WorkoutRepository

        Returns:
            APIResponse with database health status
        """
        try:
            # Try to perform a simple database operation
            workout_repo.search_summaries("test", limit=1)

            data = HealthCheckData(
                status="healthy",
                timestamp=datetime.now(),
                version="0.1.0",
                database="connected",
            )
            return Response(
                APIResponse(success=True, data=data), status_code=HTTP_200_OK
            )
        except Exception as e:
            data = HealthCheckData(
                status="unhealthy",
                timestamp=datetime.now(),
                version="0.1.0",
                database=f"error: {str(e)}",
            )
            return Response(
                APIResponse(success=False, data=data, error=str(e)),
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
            )


# Export route handlers for main app
route_handlers = [HealthController]
