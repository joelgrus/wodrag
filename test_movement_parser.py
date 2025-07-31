"""Test the updated movement parser on specific examples."""

from wodrag.data_processing.general_parser import parse_workout_general

def test_movement_parsing():
    """Test movement parsing on the examples provided."""
    
    # Test case 1: Ladder workout (30-20-10)
    ladder_example = """Saturday 220226
Saturday 220226
30-20-10 reps for time of:
GHD sit-ups
Toes-to-bars
Wall-ball shots
♀ 14-lb ball to 9-ft target
♂ 20-lb ball to 10-ft target
Post time to comments."""
    
    print("=== LADDER WORKOUT TEST ===")
    result1 = parse_workout_general(ladder_example)
    print(f"Workout type: {result1['workout_type']}")
    print(f"Movements: {result1['movements']}")
    print(f"Expected: [(30, GHD sit-ups), (30, Toes-to-bars), (30, Wall-ball shots), (20, GHD sit-ups), ...]")
    
    # Test case 2: Muscle-up workout  
    muscle_up_example = """Monday 220228
Monday 220228
For time:
5 strict muscle-ups
50 double-unders
4 strict muscle-ups
40 double-unders
3 strict muscle-ups
30 double-unders
2 strict muscle-ups
20 double-unders
1 strict muscle-up
10 double-unders
Post time to comments."""
    
    print("\n=== MUSCLE-UP WORKOUT TEST ===")
    result2 = parse_workout_general(muscle_up_example)
    print(f"Workout type: {result2['workout_type']}")
    print(f"Movements: {result2['movements']}")
    print(f"Expected: [('5', 'strict muscle-ups'), ('50', 'double-unders'), ...]")
    
    # Test case 3: Strength workout
    strength_example = """Sunday 220227
Sunday 220227
Deadlift 5-5-5-5-5 reps
Post loads to comments."""
    
    print("\n=== STRENGTH WORKOUT TEST ===")
    result3 = parse_workout_general(strength_example)
    print(f"Workout type: {result3['workout_type']}")
    print(f"Movements: {result3['movements']}")
    print(f"Expected: [('5-5-5-5-5', 'Deadlift')]")

if __name__ == "__main__":
    test_movement_parsing()