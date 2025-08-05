import pathlib
from typing import Literal

import dspy  # type: ignore

from wodrag.utils import sample_workouts

working_directory = pathlib.Path(__file__).parent.parent.parent
reference_data_directory = working_directory / "data" / "reference"

with open(reference_data_directory / "exercises.txt") as f:
    exercises = [line.strip() for line in f if line.strip()]


WorkoutType = Literal[
    "metcon",
    "strength",
    "hero",
    "girl",
    "benchmark",
    "team",
    "endurance",
    "skill",
    "other",
]


class ExtractMetadata(dspy.Signature):
    workout: str = dspy.InputField(description="Workout description text.")
    movements: list[str] = dspy.OutputField(
        description=(f"List of extracted movements. Valid movements are: {exercises}")
    )
    equipment: list[str] = dspy.OutputField(
        description="""List of equipment used in the workout. """
        """Example: ["barbell", "pull_up_bar", "box"]"""
    )
    workout_type: WorkoutType = dspy.OutputField(
        description="Type of workout (e.g., 'strength', 'cardio')."
    )
    workout_name: str | None = dspy.OutputField(
        description="Name of the workout, if available."
    )


extractor = dspy.Predict(ExtractMetadata)


if __name__ == "__main__":
    dspy.configure(lm=dspy.LM("openrouter/google/gemini-2.5-flash", max_tokens=100000))
    workouts = sample_workouts(n=10)
    for workout in workouts:
        extracted = extractor(workout=workout)
        # Process extracted metadata here if needed
