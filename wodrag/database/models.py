from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Workout:
    id: int | None = None
    date: date | None = None
    url: str | None = None
    raw_text: str | None = None
    workout: str | None = None
    scaling: str | None = None
    has_video: bool = False
    has_article: bool = False
    month_file: str | None = None
    created_at: str | None = None
    workout_search_vector: str | None = None
    workout_embedding: list[float] | None = None
    movements: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    workout_type: str | None = None
    workout_name: str | None = None
    one_sentence_summary: str | None = None
    summary_embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "date": self.date.isoformat() if self.date else None,
            "url": self.url,
            "raw_text": self.raw_text,
            "workout": self.workout,
            "scaling": self.scaling,
            "has_video": self.has_video,
            "has_article": self.has_article,
            "month_file": self.month_file,
            "created_at": self.created_at,
            "workout_search_vector": self.workout_search_vector,
            "workout_embedding": self.workout_embedding,
            "movements": self.movements,
            "equipment": self.equipment,
            "workout_type": self.workout_type,
            "workout_name": self.workout_name,
            "one_sentence_summary": self.one_sentence_summary,
            "summary_embedding": self.summary_embedding,
        }
        if self.id is not None:
            data["id"] = self.id
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workout:
        if (
            "date" in data
            and data["date"] is not None
            and isinstance(data["date"], str)
        ):
            data["date"] = date.fromisoformat(data["date"])
            # If it's already a date object (from psycopg2), leave it as-is

        # Parse string embeddings back to lists
        if "summary_embedding" in data and isinstance(data["summary_embedding"], str):
            import json

            data["summary_embedding"] = json.loads(data["summary_embedding"])

        if "workout_embedding" in data and isinstance(data["workout_embedding"], str):
            import json

            data["workout_embedding"] = json.loads(data["workout_embedding"])

        return cls(**data)


@dataclass
class WorkoutFilter:
    movements: list[str] | None = None
    equipment: list[str] | None = None
    workout_type: str | None = None
    workout_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    has_video: bool | None = None
    has_article: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if self.movements:
            filters["movements"] = self.movements
        if self.equipment:
            filters["equipment"] = self.equipment
        if self.workout_type:
            filters["workout_type"] = self.workout_type
        if self.workout_name:
            filters["workout_name"] = self.workout_name
        if self.start_date:
            filters["start_date"] = self.start_date.isoformat()
        if self.end_date:
            filters["end_date"] = self.end_date.isoformat()
        if self.has_video is not None:
            filters["has_video"] = self.has_video
        if self.has_article is not None:
            filters["has_article"] = self.has_article
        return filters


@dataclass
class SearchResult:
    workout: Workout
    similarity_score: float | None = None
    metadata_match: bool = True

    @property
    def relevance_score(self) -> float:
        if self.similarity_score is None:
            return 1.0 if self.metadata_match else 0.0
        base_score = self.similarity_score
        if self.metadata_match:
            base_score *= 1.2
        return min(base_score, 1.0)
