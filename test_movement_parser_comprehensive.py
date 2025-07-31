"""Comprehensive unit tests for movement parser."""

from wodrag.data_processing.general_parser import parse_workout_general

def test_ladder_workout():
    """Test 30-20-10 ladder pattern."""
    raw_text = """Saturday 220226
Saturday 220226
30-20-10 reps for time of:
GHD sit-ups
Toes-to-bars
Wall-ball shots
♀ 14-lb ball to 9-ft target
♂ 20-lb ball to 10-ft target
Post time to comments."""
    
    result = parse_workout_general(raw_text)
    movements = result['movements']
    
    expected = [
        ('30', 'GHD sit-ups'), ('30', 'Toes-to-bars'), ('30', 'Wall-ball shots'),
        ('20', 'GHD sit-ups'), ('20', 'Toes-to-bars'), ('20', 'Wall-ball shots'),
        ('10', 'GHD sit-ups'), ('10', 'Toes-to-bars'), ('10', 'Wall-ball shots')
    ]
    
    assert movements == expected, f"Expected {expected}, got {movements}"
    print("✓ Ladder workout test passed")

def test_sequential_for_time():
    """Test sequential For time workout."""
    raw_text = """Monday 220228
Monday 220228
For time:
5 strict muscle-ups
50 double-unders
4 strict muscle-ups
40 double-unders
3 strict muscle-ups
30 double-unders
Post time to comments."""
    
    result = parse_workout_general(raw_text)
    movements = result['movements']
    
    expected = [
        ('5', 'strict muscle-ups'), ('50', 'double-unders'),
        ('4', 'strict muscle-ups'), ('40', 'double-unders'),
        ('3', 'strict muscle-ups'), ('30', 'double-unders')
    ]
    
    assert movements == expected, f"Expected {expected}, got {movements}"
    print("✓ Sequential for time test passed")

def test_strength_rep_scheme():
    """Test strength workout with rep scheme."""
    raw_text = """Sunday 220227
Sunday 220227
Deadlift 5-5-5-5-5 reps
Post loads to comments."""
    
    result = parse_workout_general(raw_text)
    movements = result['movements']
    
    expected = [('5-5-5-5-5', 'Deadlift')]
    
    assert movements == expected, f"Expected {expected}, got {movements}"
    print("✓ Strength rep scheme test passed")

def test_rounds_for_time_missing():
    """Test rounds for time that's currently missing movements."""
    raw_text = """Sunday 220220
Sunday 220220
4 rounds for time of:
20 squat cleans
800-m run
♀ 75 lb ♂ 115 lb
Post time to comments."""
    
    result = parse_workout_general(raw_text)
    movements = result['movements']
    
    expected = [
        ('20', 'squat cleans'), ('', '800-m run'),
        ('20', 'squat cleans'), ('', '800-m run'),
        ('20', 'squat cleans'), ('', '800-m run'),
        ('20', 'squat cleans'), ('', '800-m run')
    ]
    
    assert movements == expected, f"Expected {expected}, got {movements}"
    print("✓ Rounds for time test passed")

def test_strength_single_exercise():
    """Test strength workout with single exercise and rep scheme."""
    raw_text = """Tuesday 220222
Tuesday 220222
Weighted pull-up 3-3-3-3-3 reps
Post loads and body weight to comments."""
    
    result = parse_workout_general(raw_text)
    movements = result['movements']
    
    expected = [('3-3-3-3-3', 'Weighted pull-up')]
    
    assert movements == expected, f"Expected {expected}, got {movements}"
    print("✓ Strength single exercise test passed")

def test_simple_for_time():
    """Test simple for time workout."""
    raw_text = """Saturday 220219
Saturday 220219
For time:
30 rope climbs, 15 ft
Post time to comments."""
    
    result = parse_workout_general(raw_text)
    movements = result['movements']
    
    expected = [('30', 'rope climbs, 15 ft')]
    
    assert movements == expected, f"Expected {expected}, got {movements}"
    print("✓ Simple for time test passed")

def test_amrap_pattern():
    """Test AMRAP pattern."""
    raw_text = """Wednesday 241113
Wednesday 241113
Complete as many rounds and reps as possible in 8 minutes of:
4 kettlebell snatches, right arm
4 kettlebell snatches, left arm
12 medicine-ball cleans
♀ 35-lb kettlebell and 14-lb medicine ball
♂ 53-lb kettlebell and 20-lb medicine ball
Post rounds and reps to comments."""
    
    result = parse_workout_general(raw_text)
    movements = result['movements']
    
    expected = [
        ('4', 'kettlebell snatches, right arm'),
        ('4', 'kettlebell snatches, left arm'),
        ('12', 'medicine-ball cleans')
    ]
    
    assert movements == expected, f"Expected {expected}, got {movements}"
    print("✓ AMRAP pattern test passed")

def run_all_tests():
    """Run all movement parser tests."""
    print("Running comprehensive movement parser tests...")
    
    test_ladder_workout()
    test_sequential_for_time()
    test_strength_rep_scheme()
    test_rounds_for_time_missing()
    test_strength_single_exercise()
    test_simple_for_time()
    test_amrap_pattern()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    run_all_tests()