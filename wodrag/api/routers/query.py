"""Natural language query endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from wodrag.agents.text_to_sql import QueryGenerator
from wodrag.api.models import APIResponse
from wodrag.database.duckdb_client import DuckDBQueryService

router = APIRouter(prefix="/api/v1", tags=["query"])


def get_query_generator() -> QueryGenerator:
    """Dependency to get QueryGenerator instance."""
    return QueryGenerator()


def get_duckdb_service() -> DuckDBQueryService:
    """Dependency to get DuckDBQueryService instance."""
    return DuckDBQueryService()


@router.get("/query", response_model=APIResponse[list[dict[str, Any]]])
async def natural_language_query(
    q: str = Query(
        ..., description="Natural language query about workouts", min_length=1
    ),
    generator: QueryGenerator = Depends(get_query_generator),
) -> APIResponse[list[dict[str, Any]]]:
    """
    Convert natural language queries to SQL and execute them.

    This endpoint uses AI to convert your natural language questions into
    SQL queries and executes them against the workout database.

    Examples:
    - "Show me 10 workouts with burpees"
    - "How many hero workouts are there?"
    - "Find workouts from 2023 that use a barbell"
    - "What are the most common movements?"
    - "Show me strength workouts with deadlifts"
    """
    try:
        # Generate and execute the query
        results = generator.query_and_execute(q)

        return APIResponse(data=results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.get("/query/sql", response_model=dict[str, str])
async def generate_sql_only(
    q: str = Query(
        ..., description="Natural language query to convert to SQL", min_length=1
    ),
    generator: QueryGenerator = Depends(get_query_generator),
) -> dict[str, str]:
    """
    Convert natural language to SQL without executing the query.

    This endpoint is useful for seeing what SQL query would be generated
    from your natural language question without actually running it.
    """
    try:
        sql_query = generator.generate_query(q)

        return {"natural_language": q, "generated_sql": sql_query}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {str(e)}")


@router.get("/schema", response_model=APIResponse[list[dict[str, Any]]])
async def get_database_schema(
    service: DuckDBQueryService = Depends(get_duckdb_service),
) -> APIResponse[list[dict[str, Any]]]:
    """
    Get the database schema information for the workouts table.

    This endpoint returns detailed schema information including column names,
    data types, and additional context about the workout data structure.
    """
    try:
        # Get workouts table schema
        schema = service.get_table_schema("workouts")

        # Add helpful metadata
        for col in schema:
            col_name = col["column_name"]

            # Add descriptions for key columns
            if col_name == "movements":
                col["description"] = (
                    "Array of exercise movements (e.g., ['pull up', 'burpee', 'run'])"
                )
            elif col_name == "equipment":
                col["description"] = (
                    "Array of required equipment (e.g., ['barbell', 'pull_up_bar'])"
                )
            elif col_name == "workout_type":
                col["description"] = (
                    "Type of workout: metcon, strength, hero, girl, benchmark, etc."
                )
            elif col_name == "workout_name":
                col["description"] = "Named workouts like 'Fran', 'Murph', 'Cindy'"
            elif col_name == "one_sentence_summary":
                col["description"] = "AI-generated brief summary of the workout"
            elif col_name == "date":
                col["description"] = "Date the workout was posted (2001-2024)"
            elif col_name == "workout":
                col["description"] = "Full workout description/prescription"
            elif col_name == "scaling":
                col["description"] = "Scaling and modification options"

        return APIResponse(data=schema)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Schema retrieval failed: {str(e)}"
        )
