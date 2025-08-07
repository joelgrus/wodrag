"""Search endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from wodrag.api.models import (
    APIResponse,
    PaginationMeta,
    SearchResultModel,
)
from wodrag.database.workout_repository import WorkoutRepository

router = APIRouter(prefix="/api/v1", tags=["search"])


def get_workout_repository() -> WorkoutRepository:
    """Dependency to get WorkoutRepository instance."""
    return WorkoutRepository()


def create_pagination_meta(total_found: int, offset: int, limit: int) -> PaginationMeta:
    """Create pagination metadata."""
    current_page = (offset // limit) + 1
    has_next = offset + limit < total_found
    has_prev = offset > 0

    return PaginationMeta(
        total=total_found,
        page=current_page,
        page_size=limit,
        has_next=has_next,
        has_prev=has_prev,
    )


def convert_to_search_result_model(search_results: list) -> list[SearchResultModel]:
    """Convert database SearchResult objects to API SearchResultModel objects."""
    api_results = []

    for result in search_results:
        # Convert Workout dataclass to dict, then to WorkoutModel
        from wodrag.api.models import WorkoutModel

        workout_dict = result.workout.to_dict() if hasattr(result.workout, 'to_dict') else result.workout.__dict__
        workout_model = WorkoutModel(**workout_dict)

        # Create SearchResultModel
        api_result = SearchResultModel(
            workout=workout_model,
            similarity_score=result.similarity_score,
            metadata_match=result.metadata_match,
        )

        api_results.append(api_result)

    return api_results


@router.get("/search", response_model=APIResponse[list[SearchResultModel]])
async def hybrid_search(
    q: str = Query(..., description="Search query text", min_length=1),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0),
    semantic_weight: float = Query(
        0.5, description="Weight for semantic search (0.0-1.0)", ge=0.0, le=1.0
    ),
    repo: WorkoutRepository = Depends(get_workout_repository),
) -> APIResponse[list[SearchResultModel]]:
    """
    Hybrid search combining BM25 text search with semantic similarity.

    This is the recommended search method as it combines the precision of
    text matching with the contextual understanding of semantic search.
    """
    try:
        # Calculate page for database query
        page_limit = limit + offset

        # Perform hybrid search
        search_results = repo.hybrid_search(
            query_text=q, semantic_weight=semantic_weight, limit=page_limit
        )

        # Apply pagination
        paginated_results = search_results[offset : offset + limit]

        # Convert to API models
        api_results = convert_to_search_result_model(paginated_results)

        # Create pagination metadata
        meta = create_pagination_meta(len(search_results), offset, limit)

        return APIResponse(data=api_results, meta=meta)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/semantic", response_model=APIResponse[list[SearchResultModel]])
async def semantic_search(
    q: str = Query(..., description="Search query text", min_length=1),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0),
    repo: WorkoutRepository = Depends(get_workout_repository),
) -> APIResponse[list[SearchResultModel]]:
    """
    Semantic similarity search using OpenAI embeddings.

    Best for finding conceptually similar workouts even when exact
    keywords don't match.
    """
    try:
        # Calculate page for database query
        page_limit = limit + offset

        # Perform semantic search
        search_results = repo.search_summaries(query_text=q, limit=page_limit)

        # Apply pagination
        paginated_results = search_results[offset : offset + limit]

        # Convert to API models
        api_results = convert_to_search_result_model(paginated_results)

        # Create pagination metadata
        meta = create_pagination_meta(len(search_results), offset, limit)

        return APIResponse(data=api_results, meta=meta)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.get("/search/text", response_model=APIResponse[list[SearchResultModel]])
async def text_search(
    q: str = Query(..., description="Search query text", min_length=1),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0),
    repo: WorkoutRepository = Depends(get_workout_repository),
) -> APIResponse[list[SearchResultModel]]:
    """
    BM25 full-text search using ParadeDB.

    Best for exact keyword matching and supports boolean queries:
    - "phrase search" for exact phrases
    - word1 OR word2 for either term
    - word1 AND word2 for both terms
    - word1 NOT word2 to exclude terms
    """
    try:
        # Calculate page for database query
        page_limit = limit + offset

        # Perform BM25 text search
        search_results = repo.text_search_workouts(query=q, limit=page_limit)

        # Apply pagination
        paginated_results = search_results[offset : offset + limit]

        # Convert to API models
        api_results = convert_to_search_result_model(paginated_results)

        # Create pagination metadata
        meta = create_pagination_meta(len(search_results), offset, limit)

        return APIResponse(data=api_results, meta=meta)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search failed: {str(e)}")
