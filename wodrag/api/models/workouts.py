"""Workout-related Pydantic models for the API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator


class WorkoutModel(BaseModel):
    """Pydantic model for Workout objects."""

    id: Union[int, None] = None
    date: Union[date, str, None] = None
    url: Union[str, None] = None
    raw_text: Union[str, None] = None
    workout: Union[str, None] = None
    scaling: Union[str, None] = None
    has_video: bool = False
    has_article: bool = False
    month_file: Union[str, None] = None
    created_at: Union[str, datetime, None] = None
    workout_search_vector: Union[str, None] = None
    workout_embedding: Union[list[float], None] = None
    movements: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    workout_type: Union[str, None] = None
    workout_name: Union[str, None] = None
    one_sentence_summary: Union[str, None] = None
    summary_embedding: Union[list[float], None] = None

    model_config = {"from_attributes": True}


class WorkoutFilterModel(BaseModel):
    """Pydantic model for workout filtering parameters."""

    movements: Union[list[str], None] = None
    equipment: Union[list[str], None] = None
    workout_type: Union[str, None] = None
    workout_name: Union[str, None] = None
    start_date: Union[date, None] = None
    end_date: Union[date, None] = None
    has_video: Union[bool, None] = None
    has_article: Union[bool, None] = None


class SearchResultModel(BaseModel):
    """Pydantic model for search results."""

    workout: WorkoutModel
    similarity_score: Union[float, None] = None
    bm25_score: Union[float, None] = None
    hybrid_score: Union[float, None] = None
    metadata_match: bool = True

    @property
    def relevance_score(self) -> float:
        """Calculate relevance score for backward compatibility."""
        if self.hybrid_score is not None:
            return self.hybrid_score
        if self.similarity_score is None:
            return 1.0 if self.metadata_match else 0.0
        base_score = self.similarity_score
        if self.metadata_match:
            base_score *= 1.2
        return min(base_score, 1.0)


class SearchRequest(BaseModel):
    """Search request parameters."""

    query: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    semantic_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    bm25_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    filters: Union[WorkoutFilterModel, None] = None


class WorkoutSearchResult(BaseModel):
    """Single workout search result with scoring information."""

    workout: WorkoutModel
    score: float
    search_type: str  # "hybrid", "semantic", "text"
    rank: int


class NaturalLanguageQueryRequest(BaseModel):
    """Request for natural language query."""

    question: str = Field(min_length=1, description="Natural language question")


class GenerateWorkoutRequest(BaseModel):
    """Request for workout generation."""

    description: str = Field(min_length=1, description="Description of desired workout")
    use_hybrid: bool = Field(default=True, description="Use hybrid search for examples")


class AgentQueryRequest(BaseModel):
    """Request for master agent query."""

    question: str = Field(min_length=1, description="Natural language question or request")
    verbose: bool = Field(default=False, description="Return reasoning trace")
