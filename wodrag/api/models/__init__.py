"""API models package."""

from .responses import APIResponse, ErrorResponse, HealthCheckData, PaginationMeta
from .workouts import (
    SearchRequest,
    SearchResultModel,
    WorkoutFilterModel,
    WorkoutModel,
)

# Models will auto-resolve forward references

__all__ = [
    "APIResponse",
    "ErrorResponse",
    "HealthCheckData",
    "PaginationMeta",
    "SearchRequest",
    "SearchResultModel",
    "WorkoutFilterModel",
    "WorkoutModel",
]
