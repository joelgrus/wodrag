"""Workouts endpoints for FastAPI: by-date and similarity."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from wodrag.api.main_fastapi import get_workout_repository
from wodrag.api.models.responses import APIResponse
from wodrag.api.models.workouts import SearchResultModel, WorkoutResponseModel
from wodrag.database.workout_repository import WorkoutRepository

router = APIRouter(tags=["workouts"])

class WorkoutWithSimilar(BaseModel):
    workout: WorkoutResponseModel  # Frontend-optimized without embeddings
    similar: list[SearchResultModel]


@router.get(
    "/workouts/{year}/{month}/{day}",
    response_model=APIResponse[WorkoutWithSimilar],
    summary="Get workout by date with similar workouts",
)
def get_workout_by_date(
    year: int,
    month: int,
    day: int,
    similar_limit: int = Query(
        5, ge=0, le=50, description="Number of similar workouts to include"
    ),
    embedding: Literal["summary", "workout"] = Query(
        "summary", description="Embedding to use for similarity"
    ),
    repo: WorkoutRepository = Depends(get_workout_repository),  # noqa: B008
) -> Any:
    """Return the workout for a specific date plus N most similar workouts.

    Similarity is computed via cosine similarity of `summary_embedding` using pgvector.
    """
    try:
        workout_date = date(year, month, day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date") from e

    workout = repo.get_workout_by_date(workout_date)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found for date")

    # Build main workout model
    workout_model = WorkoutResponseModel(**workout.to_dict())

    similar_models: list[SearchResultModel] = []
    if similar_limit > 0 and workout.id is not None:
        try:
            similar = repo.get_similar_workouts(
                workout.id, limit=similar_limit, embedding=embedding
            )
            for s in similar:
                similar_models.append(
                    SearchResultModel(
                        workout=WorkoutResponseModel(**s.workout.to_dict()),
                        similarity_score=s.similarity_score,
                        metadata_match=True,
                    )
                )
        except Exception:  # pylint: disable=broad-except
            # Don't fail the whole endpoint if similarity fails; just omit
            similar_models = []

    return APIResponse(
        success=True,
        data=WorkoutWithSimilar(workout=workout_model, similar=similar_models),
    )
