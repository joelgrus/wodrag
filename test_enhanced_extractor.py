"""Test the enhanced extractor with parsing."""

from pathlib import Path

from wodrag.data_processing.extractor import extract_workouts_from_file


def test_sample_extraction() -> None:
    """Test extraction on a few sample files."""
    sample_files = [
        Path("data/raw/2024-11.json").with_suffix(".html"),  # Recent file
        Path("data/raw/2020-04.json").with_suffix(".html"),  # Middle period
        Path("data/raw/2010-03.json").with_suffix(".html"),  # Older period
    ]
    
    for file_path in sample_files:
        if not file_path.exists():
            print(f"Skipping {file_path.name} - not found")
            continue
            
        print(f"\n{'='*60}")
        print(f"Testing {file_path.name}")
        print('='*60)
        
        workouts = extract_workouts_from_file(file_path)
        
        # Show first few workouts with parsed data
        for i, workout in enumerate(workouts[:3], 1):
            print(f"\nWorkout {i} ({workout.date}):")
            print(f"  Type: {workout.workout_type}")
            print(f"  Time Domain: {workout.time_domain}")
            print(f"  Rep Scheme: {workout.rep_scheme}")
            print(f"  Movements: {workout.movements}")
            print(f"  Weights: {workout.weights}")
            print(f"  Raw Preview: {workout.raw_text[:100]}...")


if __name__ == "__main__":
    test_sample_extraction()