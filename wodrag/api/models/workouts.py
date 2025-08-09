"""Workout-related Pydantic models for the API."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class WorkoutModel(BaseModel):
    """Pydantic model for Workout objects."""

    id: int | None = None
    date: date | str | None = None
    url: str | None = None
    raw_text: str | None = None
    workout: str | None = None
    scaling: str | None = None
    has_video: bool = False
    has_article: bool = False
    month_file: str | None = None
    created_at: str | datetime | None = None
    workout_search_vector: str | None = None
    workout_embedding: list[float] | None = None
    movements: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    workout_type: str | None = None
    workout_name: str | None = None
    one_sentence_summary: str | None = None
    summary_embedding: list[float] | None = None

    model_config = {"from_attributes": True}


class WorkoutResponseModel(BaseModel):
    """Frontend-optimized workout model without embedding vectors."""

    id: int | None = None
    date: date | str | None = None
    url: str | None = None
    raw_text: str | None = None
    workout: str | None = None
    scaling: str | None = None
    has_video: bool = False
    has_article: bool = False
    month_file: str | None = None
    created_at: str | datetime | None = None
    movements: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    workout_type: str | None = None
    workout_name: str | None = None
    one_sentence_summary: str | None = None
    # Note: workout_embedding and summary_embedding excluded for frontend efficiency

    model_config = {"from_attributes": True}


class WorkoutFilterModel(BaseModel):
    """Pydantic model for workout filtering parameters."""

    movements: list[str] | None = None
    equipment: list[str] | None = None
    workout_type: str | None = None
    workout_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    has_video: bool | None = None
    has_article: bool | None = None


class SearchResultModel(BaseModel):
    """Pydantic model for search results."""

    workout: WorkoutResponseModel  # Use frontend-optimized model
    similarity_score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None
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
    filters: WorkoutFilterModel | None = None


class WorkoutSearchResult(BaseModel):
    """Single workout search result with scoring information."""

    workout: WorkoutResponseModel  # Use frontend-optimized model
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

    question: str = Field(
        min_length=1, description="Natural language question or request"
    )
    verbose: bool = Field(default=False, description="Return reasoning trace")
    conversation_id: str | None = Field(
        default=None, description="Optional conversation ID for context"
    )
