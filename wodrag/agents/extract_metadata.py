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
    "rest day",
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
    workout_name: str = dspy.OutputField(
        description=("The name of the workout. Some workouts have official names, e.g. Murph, Fran, etc "
                     "Some workouts have 'titles' (e.g. 'Barbell Mania') you can use those as the names. "
                     "If no official name is found, make up a name based on the workout description. "
                     "nb some workout descriptions have names of people in them, e.g. 'John Smith did this in 4:31' "
                     "those are not workout names, so don't use them.")
    )
    one_sentence_summary: str = dspy.OutputField(
        description="A one-sentence summary of the workout."
    )


extractor = dspy.Predict(ExtractMetadata)


if __name__ == "__main__":
    dspy.configure(lm=dspy.LM("openrouter/google/gemini-2.5-flash", max_tokens=100000))
    workouts = sample_workouts(n=10)
    for workout in workouts:
        extracted = extractor(workout=workout)
        # Process extracted metadata here if needed
