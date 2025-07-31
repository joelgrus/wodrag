"""Test the simple workout parser."""

from wodrag.data_processing.simple_parser import parse_workout_simple

def test_simple_parsing():
    """Test various workout formats with simple parser."""
    
    # Test 1: Basic workout with scaling
    basic_workout = """Saturday 220226
Saturday 220226
30-20-10 reps for time of:
GHD sit-ups
Toes-to-bars
Wall-ball shots
♀ 14-lb ball to 9-ft target
♂ 20-lb ball to 10-ft target
Post time to comments.
Compare to
170913
.
Scaling:
Beginner athletes can use the warm-up time to allow for controlled exposure to the GHD machine, but choose AbMat sit-ups for the workout portion. Intermediate athletes can do this workout as prescribed.
Beginner Option:
20-15-10
reps for time of:
AbMat
sit-ups
Hanging knee raises
Wall-ball shots
♀ 6-lb ball
♂ 10-lb ball"""
    
    result = parse_workout_simple(basic_workout)
    print("=== BASIC WORKOUT TEST ===")
    print(f"Workout section:\n{result['workout']}\n")
    print(f"Scaling section:\n{result['scaling']}\n")
    
    # Test 2: Strength workout without scaling
    strength_workout = """Sunday 220227
Sunday 220227
Deadlift 5-5-5-5-5 reps
Post loads to comments.
Compare to
201230
.
Scaling:
Ideally, each set will be as heavy as possible for 5 reps, but newer athletes should start light and add weight as they are comfortable."""
    
    result = parse_workout_simple(strength_workout)
    print("=== STRENGTH WORKOUT TEST ===")
    print(f"Workout section:\n{result['workout']}\n")
    print(f"Scaling section:\n{result['scaling']}\n")
    
    # Test 3: Workout without scaling
    simple_workout = """Saturday 220219
Saturday 220219
For time:
30 rope climbs, 15 ft
Post time to comments.
Compare to
170417
."""
    
    result = parse_workout_simple(simple_workout)
    print("=== SIMPLE WORKOUT TEST ===")
    print(f"Workout section:\n{result['workout']}\n")
    print(f"Scaling section: {result['scaling']}\n")
    
    # Test 4: Complex workout with multiple options
    complex_workout = """Tuesday 220222
Tuesday 220222
Weighted pull-up 3-3-3-3-3 reps
Post loads and body weight to comments.
Compare to
121130
.
Scaling:
Most athletes can perform the pull-ups as prescribed. Experienced athletes can go as heavy as possible. Athletes without strict pull-ups can use this session to practice a modification that will challenge their pulling ability.
Beginner Option:
Banded
pull-up 3-3-3-3-3 reps"""
    
    result = parse_workout_simple(complex_workout)
    print("=== COMPLEX WORKOUT TEST ===")
    print(f"Workout section:\n{result['workout']}\n")
    print(f"Scaling section:\n{result['scaling']}\n")

if __name__ == "__main__":
    test_simple_parsing()