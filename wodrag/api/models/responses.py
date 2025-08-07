"""Response models for the API."""

from __future__ import annotations

from typing import Any, Generic, TypeVar, Union

from pydantic import BaseModel, Field

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


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    data: T = Field(..., description="Response data")
    meta: Union[PaginationMeta, None] = None
    status: str = Field(default="success", description="Response status")
