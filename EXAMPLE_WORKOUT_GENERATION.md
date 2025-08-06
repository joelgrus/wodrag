# Workout Generation with DSPy Agents

This project includes two DSPy agents for generating CrossFit workouts:

## Architecture

### 1. Inner Agent: `WorkoutGenerator`
- **Input**: Description + list of example workouts
- **Output**: New workout inspired by the examples
- **Purpose**: Creative workout generation based on provided examples

### 2. Outer Agent: `WorkoutSearchGenerator`  
- **Input**: Description only
- **Process**: 
  1. Searches database for similar workouts using hybrid search
  2. Passes found workouts to inner agent as examples
- **Output**: New workout inspired by database matches

## Usage Examples

### Command Line Interface (for development/testing)

```bash
# Generate a single workout
uv run python scripts/generate_workout.py generate "heavy deadlifts with short cardio bursts"
uv run python scripts/generate_workout.py generate "upper body strength" --show-examples
uv run python scripts/generate_workout.py generate "running and rowing" --semantic

# Interactive mode
uv run python scripts/generate_workout.py interactive

# Batch generation from file
echo "heavy squats with cardio" > descriptions.txt
echo "gymnastics skill work" >> descriptions.txt
uv run python scripts/generate_workout.py batch descriptions.txt
```

Note: These CLI scripts are primarily for development and testing. The main interface will be through the web application.

### Python API

```python
import dspy
from wodrag.agents import (
    WorkoutGenerator, 
    WorkoutSearchGenerator,
    generate_workout_from_examples,
    generate_workout_from_search
)
from wodrag.database.workout_repository import WorkoutRepository

# Configure DSPy
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini", api_key="your_key"))

# Using convenience function with dataclass result
examples = [
    "Fran: 21-15-9 Thrusters and Pull-ups",
    "Grace: 30 Clean and Jerks for time"
]
result = generate_workout_from_examples("short barbell workout", examples)
print(f"Name: {result.name}")
print(f"Workout: {result.workout}")

# Using search-based generation with dataclass result
result = generate_workout_from_search(
    "heavy lifting with gymnastics",
    search_limit=10,
    use_hybrid=True
)
print(f"Name: {result.name}")
print(f"Workout: {result.workout}")
print(f"Based on {len(result.search_results)} similar workouts")
```

## How It Works

1. **Search Phase**: The outer agent queries the database using your description
   - Hybrid search combines BM25 text matching with semantic similarity
   - Finds the most relevant workouts from 8,861+ in the database

2. **Generation Phase**: The inner agent creates a new workout
   - Uses found workouts as creative inspiration
   - Maintains CrossFit format and conventions
   - Can generate creative workout names

3. **Output**: A complete workout with:
   - Movements and rep schemes
   - Time domains or rounds
   - Scaling options when appropriate
   - Optional creative name

## Configuration

The agents use OpenAI by default but can work with any DSPy-compatible model:

```python
# OpenAI (default)
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))

# Claude via OpenRouter
dspy.configure(lm=dspy.LM("openrouter/anthropic/claude-3-haiku"))

# Local models via Ollama
dspy.configure(lm=dspy.LM("ollama/llama2"))
```

## Testing

Run the test script to verify everything works:

```bash
uv run python scripts/test_workout_generation.py
```

This will test both agents with sample data and database queries.