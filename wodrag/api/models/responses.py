"""Response models for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar, Union

from pydantic import BaseModel, Field

# WorkoutSearchResult will be imported where needed to avoid circular imports

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class ErrorDetail(BaseModel):
    """Error detail information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )


class ErrorResponse(BaseModel):
    """Error response format."""

    error: ErrorDetail = Field(..., description="Error information")
    status: str = Field(default="error", description="Response status")


class HealthCheckData(BaseModel):
    """Health check data."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")
    database: Union[str, None] = Field(default=None, description="Database status")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Union[T, None] = Field(..., description="Response data")
    error: Union[str, None] = Field(default=None, description="Error message if any")
    meta: Union[PaginationMeta, None] = Field(
        default=None, description="Pagination metadata"
    )


class SearchResponse(BaseModel):
    """Response for search endpoints."""

    query: str = Field(..., description="Original search query")
    results: list[Any] = Field(
        ..., description="Search results"
    )  # Will be WorkoutSearchResult
    total_results: int = Field(..., description="Total number of results")
    search_type: str = Field(..., description="Type of search performed")
    semantic_weight: Union[float, None] = Field(
        default=None, description="Semantic weight used"
    )


class QueryResponse(BaseModel):
    """Response for natural language query."""

    question: str = Field(..., description="Original question")
    sql_query: str = Field(..., description="Generated SQL query")
    results: list[dict[str, Any]] = Field(..., description="Query results")
    result_count: int = Field(..., description="Number of results")


class WorkoutGenerationResponse(BaseModel):
    """Response for workout generation."""

    description: str = Field(..., description="Original workout description")
    generated_workout: str = Field(..., description="Generated workout")
    workout_name: str = Field(..., description="Generated workout name")
    use_hybrid: bool = Field(..., description="Whether hybrid search was used")


class AgentQueryResponse(BaseModel):
    """Response for master agent query."""

    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Agent's answer")
    verbose: bool = Field(..., description="Whether reasoning trace was requested")
    reasoning_trace: Union[list[str], None] = Field(
        default=None, description="Step-by-step reasoning trace (if verbose=True)"
    )
