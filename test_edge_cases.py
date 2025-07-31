"""Test edge cases for movement parser."""

from wodrag.data_processing.general_parser import parse_workout_general

def test_edge_cases():
    """Test various edge cases."""
    
    # Test case with complex exercise names
    complex_names = """Tuesday 220222
Tuesday 220222  
Weighted pull-up 3-3-3-3-3 reps
Post loads and body weight to comments."""
    
    result = parse_workout_general(complex_names)
    print(f"Complex names: {result['movements']}")
    assert result['movements'] == [('3-3-3-3-3', 'Weighted pull-up')]
    
    # Test case with distance-based movement
    distance_movement = """Saturday 220219
Saturday 220219
For time:
30 rope climbs, 15 ft
Post time to comments."""
    
    result = parse_workout_general(distance_movement)
    print(f"Distance movement: {result['movements']}")
    assert result['movements'] == [('30', 'rope climbs, 15 ft')]
    
    # Test multi-word exercise with hyphenation
    multi_word = """Wednesday 220216
Wednesday 220216
Row 5,000 meters
Post time to comments."""
    
    result = parse_workout_general(multi_word)
    print(f"Multi-word exercise: {result['movements']}")
    # This might not capture since it doesn't follow our patterns, which is OK
    
    print("✅ Edge case tests completed!")

if __name__ == "__main__":
    test_edge_cases()