#!/usr/bin/env python3
"""Test the workout generation agents."""

import os
import sys

import dspy  # type: ignore
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wodrag.agents import WorkoutGenerator, WorkoutSearchGenerator
from wodrag.database.workout_repository import WorkoutRepository

# Load environment variables
load_dotenv()


def test_inner_agent():
    """Test the inner WorkoutGenerator agent with example workouts."""

    # Configure DSPy
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return

    dspy.configure(
        lm=dspy.LM("openai/gpt-4o-mini", api_key=api_key, temperature=0.7), cache=False
    )

    # Create generator
    generator = WorkoutGenerator()

    # Example workouts to use as inspiration
    example_workouts = [
        """Fran
        21-15-9 reps for time of:
        Thrusters (95/65 lb)
        Pull-ups""",
        """Cindy
        Complete as many rounds as possible in 20 minutes of:
        5 pull-ups
        10 push-ups
        15 air squats""",
        """Grace
        For time:
        30 clean and jerks (135/95 lb)""",
    ]

    # Generate a workout
    description = "A short, intense workout combining barbell work and gymnastics"

    for _i, _workout in enumerate(example_workouts, 1):
        pass


    generator(description, example_workouts)



def test_outer_agent():
    """Test the outer WorkoutSearchGenerator agent with database search."""

    # Configure DSPy
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return

    dspy.configure(
        lm=dspy.LM("openai/gpt-4o-mini", api_key=api_key, temperature=0.7), cache=False
    )

    # Create repository and generator
    repository = WorkoutRepository()
    search_generator = WorkoutSearchGenerator(repository, search_limit=5)

    # Test descriptions
    test_descriptions = [
        "Heavy deadlifts with short cardio bursts",
        "Gymnastics-focused workout with handstand work",
        "Long endurance piece with running and rowing",
    ]

    for description in test_descriptions:

        try:
            # Search for similar workouts
            search_results = repository.hybrid_search(description, limit=5)

            for _i, result in enumerate(search_results, 1):
                workout = result.workout
                if workout.one_sentence_summary:
                    pass

            # Generate new workout
            result = search_generator(description, use_hybrid=True)


        except Exception:
            pass



def main():
    """Run all tests."""

    # Test inner agent first (doesn't need database)
    test_inner_agent()


    # Test outer agent (needs database)
    test_outer_agent()



if __name__ == "__main__":
    main()
