"""DSPy agents for generating CrossFit workouts based on examples."""

from dataclasses import dataclass

import dspy  # type: ignore

from wodrag.database.models import SearchResult
from wodrag.database.workout_repository import WorkoutRepository


@dataclass
class GeneratedWorkout:
    """Result of workout generation."""

    workout: str
    name: str


@dataclass
class GeneratedWorkoutWithSearch:
    """Result of workout generation with search context."""

    workout: str
    name: str
    search_results: list[SearchResult]


class GenerateWorkout(dspy.Signature):
    """Generate a new CrossFit workout based on description and example workouts."""

    description: str = dspy.InputField(
        description="Description of desired workout (e.g., 'upper body with cardio')"
    )
    example_workouts: list[str] = dspy.InputField(
        description="List of example workouts to use as inspiration"
    )
    generated_workout: str = dspy.OutputField(
        description="Generated workout in CrossFit format with rounds/reps and scaling"
    )
    workout_name: str = dspy.OutputField(
        description=(
            "A clever, creative name for the workout (always generate one). "
            "Should be short and catchy."
        )
    )


class WorkoutGenerator(dspy.Module):
    """Inner agent that generates workouts from description and examples."""

    def __init__(self) -> None:
        super().__init__()
        self.generator = dspy.Predict(GenerateWorkout)

    def forward(self, description: str, example_workouts: list[str]) -> dspy.Prediction:
        """Generate a workout based on description and examples.

        Args:
            description: What kind of workout to generate
            example_workouts: List of example workout texts for inspiration

        Returns:
            DSPy Prediction with generated_workout and optional workout_name
        """
        import time

        # Add timestamp to prevent caching
        description_with_variation = f"{description} [t:{time.time()}]"
        return self.generator(
            description=description_with_variation, example_workouts=example_workouts
        )


class WorkoutSearchGenerator(dspy.Module):
    """Outer agent that searches for similar workouts then generates new one."""

    def __init__(
        self, repository: WorkoutRepository | None = None, search_limit: int = 10
    ):
        """Initialize the search-based workout generator.

        Args:
            repository: WorkoutRepository for database access
            search_limit: Number of similar workouts to retrieve (default 10)
        """
        super().__init__()
        if repository is None:
            from wodrag.services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            repository = WorkoutRepository(embedding_service)
        self.repository = repository
        self.search_limit = search_limit
        self.generator = WorkoutGenerator()

    def forward(self, description: str, use_hybrid: bool = True) -> dspy.Prediction:
        """Search for similar workouts and generate a new one.

        Args:
            description: Description of desired workout
            use_hybrid: Whether to use hybrid search (BM25 + semantic) or semantic only

        Returns:
            DSPy Prediction with generated_workout and workout_name
        """
        # Search for similar workouts using the description
        if use_hybrid:
            search_results = self.repository.hybrid_search(
                query_text=description, limit=self.search_limit
            )
        else:
            search_results = self.repository.search_summaries(
                query_text=description, limit=self.search_limit
            )

        # Extract workout texts from search results
        example_workouts = []
        for result in search_results:
            workout_text = result.workout.workout
            if result.workout.workout_name:
                workout_text = f"{result.workout.workout_name}\n{workout_text}"
            if result.workout.scaling:
                workout_text = f"{workout_text}\n\nScaling:\n{result.workout.scaling}"
            example_workouts.append(workout_text)

        # Generate new workout using the examples
        return self.generator(
            description=description, example_workouts=example_workouts
        )


# Convenience functions for direct use
def generate_workout_from_examples(
    description: str, example_workouts: list[str]
) -> GeneratedWorkout:
    """Generate a workout from description and examples.

    Args:
        description: What kind of workout to generate
        example_workouts: List of example workout texts

    Returns:
        GeneratedWorkout with workout text and name
    """
    generator = WorkoutGenerator()
    result = generator(description, example_workouts)
    return GeneratedWorkout(workout=result.generated_workout, name=result.workout_name)


def generate_workout_from_search(
    description: str,
    repository: WorkoutRepository | None = None,
    search_limit: int = 10,
    use_hybrid: bool = True,
) -> GeneratedWorkoutWithSearch:
    """Search for similar workouts and generate a new one.

    Args:
        description: Description of desired workout
        repository: Optional WorkoutRepository (creates one if not provided)
        search_limit: Number of similar workouts to find
        use_hybrid: Whether to use hybrid search

    Returns:
        GeneratedWorkoutWithSearch with workout, name, and search results
    """
    search_generator = WorkoutSearchGenerator(repository, search_limit)

    # Get search results for transparency
    if repository is None:
        from wodrag.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        repository = WorkoutRepository(embedding_service)
    repo = repository
    if use_hybrid:
        search_results = repo.hybrid_search(description, limit=search_limit)
    else:
        search_results = repo.search_summaries(description, limit=search_limit)

    # Generate workout
    result = search_generator(description, use_hybrid)

    return GeneratedWorkoutWithSearch(
        workout=result.generated_workout,
        name=result.workout_name,
        search_results=search_results,
    )
