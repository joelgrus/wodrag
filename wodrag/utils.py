import json
import pathlib
import random

root_directory = pathlib.Path(__file__).parent.parent
json_directory = root_directory / "data" / "processed" / "json"


def sample_workouts(n: int = 500, seed: int = 12) -> list:
    random.seed(seed)
    sample = []

    for fn in json_directory.glob("*.json"):
        with open(fn, encoding="utf-8") as f:
            workouts = json.load(f)
        for workout in workouts:
            sample.append(workout["workout"])

    sample = random.sample(sample, n)

    return sample
