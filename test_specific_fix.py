"""Test the specific failing example with the general parser."""

from wodrag.data_processing.general_parser import parse_workout_general

def test_failing_example():
    """Test the failing deadlift example."""
    
    failing_text = """Sunday 220227
Sunday 220227
Deadlift 5-5-5-5-5 reps
Post loads to comments.
Compare to
201230
.
Scaling:
Ideally, each set will be as heavy as possible for 5 reps, but newer athletes should start light and add weight as they are comfortable."""

    print("Testing the failing deadlift example:")
    print("="*50)
    
    result = parse_workout_general(failing_text)
    
    print("Results:")
    for key, value in result.items():
        if key != 'sections':
            print(f"  {key}: {value}")
    
    print("\nShould show:")
    print("  workout_type: Strength")
    print("  scaling_notes: 'Ideally, each set will be...'")
    print("  movements: Contains 'Deadlift'")

if __name__ == "__main__":
    test_failing_example()