"""Test the parser on the failing example."""

from wodrag.data_processing.parser import parse_workout_content

def test_failing_example():
    """Test the parser on the example that was failing."""
    
    failing_text = """Sunday 220227
Sunday 220227
Deadlift 5-5-5-5-5 reps
Post loads to comments.
Compare to
201230
.
Scaling:
Ideally, each set will be as heavy as possible for 5 reps, but newer athletes should start light and add weight as they are comfortable."""

    print("Testing failing example:")
    print(f"Raw text: {failing_text}")
    print()
    
    result = parse_workout_content(failing_text)
    
    print("Parsed result:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    print("\nExpected:")
    print("  workout_type: Strength")
    print("  rep_scheme: 5-5-5-5-5")
    print("  movements: ['Deadlift']")
    print("  scaling_notes: 'Ideally, each set will be...'")

if __name__ == "__main__":
    test_failing_example()