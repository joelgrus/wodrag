from __future__ import annotations

from typing import Any

import dspy  # type: ignore

from wodrag.database.duckdb_client import DuckDBQueryService


class TextToSQL(dspy.Signature):
    """Convert natural language queries to DuckDB SQL queries for workout data."""

    query: str = dspy.InputField(description="Natural language query about workouts")
    db_schema: str = dspy.InputField(description="Database schema information")
    sql_query: str = dspy.OutputField(
        description="""DuckDB SQL query that answers the natural language query. 
        IMPORTANT: Use 'pg_db.workouts' as the table name (not just 'workouts').
        IMPORTANT: For array columns (movements, equipment), use PostgreSQL array syntax:
        - Use 'movement' = ANY(movements) not movements LIKE '%movement%'
        - Use 'equipment_item' = ANY(equipment) not equipment LIKE '%item%'
        IMPORTANT: Always use descriptive column aliases for aggregate and computed columns:
        - Use "AS total_count" or "AS workout_count" instead of bare COUNT(*)
        - Use "AS avg_duration" instead of bare AVG(duration)
        - Use meaningful names based on what is being counted/calculated
        Examples:
        - "SELECT * FROM pg_db.workouts WHERE 'burpees' = ANY(movements) LIMIT 10"
        - "SELECT COUNT(*) AS hero_workout_count FROM pg_db.workouts WHERE workout_type = 'hero'"
        - "SELECT workout_type, COUNT(*) AS count FROM pg_db.workouts GROUP BY workout_type ORDER BY count DESC"
        - "SELECT * FROM pg_db.workouts WHERE date >= '2023-01-01' ORDER BY date DESC"
        - "SELECT * FROM pg_db.workouts WHERE 'barbell' = ANY(equipment) AND workout_type = 'strength'"
        """
    )


class QueryGenerator:
    """DSPy-based agent for converting natural language to DuckDB SQL queries."""

    def __init__(self) -> None:
        self.text_to_sql = dspy.Predict(TextToSQL)
        self.duckdb_service = DuckDBQueryService()

    def get_schema_info(self) -> str:
        """Get formatted schema information for the workouts table."""
        schema = self.duckdb_service.get_table_schema("workouts")
        schema_text = "Workouts table schema:\n"
        for col in schema:
            schema_text += f"- {col['column_name']}: {col['data_type']}\n"

        # Add domain context with actual values (from database analysis)
        movements_list = [
            "pull up",
            "run",
            "row",
            "sit up",
            "deadlift",
            "squat",
            "push up",
            "dip",
            "bench press",
            "rope climb",
            "back extension",
            "muscle up",
            "clean and jerk",
            "bike",
            "box jump",
            "power clean",
            "handstand push up",
            "kettlebell swing",
            "back squat",
            "push press",
            "thruster",
            "snatch",
            "clean",
            "walking lunge",
            "hang clean",
            "push jerk",
            "front squat",
            "double under",
            "wall ball shot",
            "knees to elbow",
            "swim",
            "burpee",
            "single under",
            "air squat",
            "overhead squat",
        ]
        equipment_list = [
            "barbell",
            "pull_up_bar",
            "rower",
            "box",
            "rope",
            "dumbbell",
            "kettlebell",
            "bike",
            "jump rope",
            "medicine ball",
            "ghd",
            "rings",
            "dip_station",
            "wall ball",
            "bench",
            "abmat",
            "parallettes",
        ]

        schema_text += f"""
        
Domain Context:
- This is CrossFit workout data from 2001-2024
- movements: Array of exercise movements. Common movements: {movements_list}
- equipment: Array of required equipment. Common equipment: {equipment_list}
- workout_type: Type of workout ('metcon', 'strength', 'hero', 'girl', 'benchmark', etc.)
- workout_name: Named workouts (e.g., 'Fran', 'Murph', 'Cindy')
- one_sentence_summary: AI-generated summary of the workout

IMPORTANT: Movement names use spaces, not underscores (e.g., 'pull up' not 'pull_up')
        """
        return schema_text

    def generate_query(self, natural_language_query: str) -> str:
        """Generate DuckDB SQL query from natural language."""
        schema_info = self.get_schema_info()
        result = self.text_to_sql(query=natural_language_query, db_schema=schema_info)
        return str(result.sql_query)

    def query_and_execute(self, natural_language_query: str) -> list[dict[str, Any]]:
        """Generate and execute a query, returning the results."""
        sql_query = self.generate_query(natural_language_query)
        return self.duckdb_service.execute_query(sql_query)


if __name__ == "__main__":
    # Configure DSPy with your preferred model
    dspy.configure(lm=dspy.LM("openrouter/google/gemini-2.5-flash", max_tokens=100000))

    generator = QueryGenerator()

    # Test queries
    test_queries = [
        "Show me 5 workouts with burpees",
        "How many hero workouts are there?",
        "Find workouts from 2023 that use a barbell",
        "What are the most common movements in strength workouts?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            sql = generator.generate_query(query)
            print(f"Generated SQL: {sql}")

            results = generator.query_and_execute(query)
            print(f"Results: {len(results)} rows returned")
        except Exception as e:
            print(f"Error: {e}")
