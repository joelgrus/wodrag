"""API models package."""

from .responses import APIResponse, ErrorResponse, HealthResponse, PaginationMeta
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
    "HealthResponse",
    "PaginationMeta",
    "SearchRequest",
    "SearchResultModel",
    "WorkoutFilterModel",
    "WorkoutModel",
]
