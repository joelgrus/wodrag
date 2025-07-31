"""Analyze raw workout text to understand general patterns."""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def analyze_workout_patterns() -> None:
    """Analyze patterns in workout raw text."""
    json_dir = Path("data/processed/json")
    
    # Sample files from different time periods
    sample_files = [
        "2001-02.json", "2005-06.json", "2010-03.json", 
        "2015-09.json", "2020-04.json", "2024-11.json"
    ]
    
    all_raw_texts = []
    workout_types = Counter()
    
    # Collect raw texts
    for filename in sample_files:
        file_path = json_dir / filename
        if not file_path.exists():
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            workouts = json.load(f)
        
        for workout in workouts:
            raw_text = workout.get("raw_text", "")
            if raw_text:
                all_raw_texts.append(raw_text)
    
    print(f"Analyzing {len(all_raw_texts)} workout texts...\n")
    
    # Analyze common patterns
    print("=== COMMON OPENING PATTERNS ===")
    opening_patterns = Counter()
    for text in all_raw_texts:
        lines = text.split('\n')
        for line in lines[2:6]:  # Skip date headers, look at first few content lines
            line = line.strip()
            if line and len(line) > 5:
                # Look for patterns
                if re.search(r'\d+\s*rounds?\s*(for time|of)', line.lower()):
                    opening_patterns["X rounds for time/of"] += 1
                elif re.search(r'amrap', line.lower()):
                    opening_patterns["AMRAP"] += 1
                elif re.search(r'for time', line.lower()):
                    opening_patterns["For time"] += 1
                elif re.search(r'emom', line.lower()):
                    opening_patterns["EMOM"] += 1
                elif re.search(r'rest day', line.lower()):
                    opening_patterns["Rest Day"] += 1
                elif re.search(r'\d+-\d+-\d+', line):
                    opening_patterns["Rep ladder (21-15-9)"] += 1
                elif re.search(r'\w+\s+\d+-\d+-\d+', line):
                    opening_patterns["Movement + reps"] += 1
                elif re.search(r'tabata', line.lower()):
                    opening_patterns["Tabata"] += 1
                break
    
    for pattern, count in opening_patterns.most_common(15):
        print(f"  {pattern}: {count}")
    
    print("\n=== SECTION MARKERS ===")
    section_markers = Counter()
    for text in all_raw_texts:
        # Look for section dividers
        if re.search(r'\bscaling:', text.lower()):
            section_markers["Scaling:"] += 1
        if re.search(r'\bpost.*to comments', text.lower()):
            section_markers["Post ... to comments"] += 1
        if re.search(r'\bcompare to', text.lower()):
            section_markers["Compare to"] += 1
        if re.search(r'\bfeatured', text.lower()):
            section_markers["Featured"] += 1
        if '♀' in text or '♂' in text:
            section_markers["Gender scaling (♀/♂)"] += 1
        if re.search(r'\d+\s*lb', text.lower()):
            section_markers["Weight specs (lb)"] += 1
    
    for marker, count in section_markers.most_common(10):
        print(f"  {marker}: {count}")
    
    print("\n=== SAMPLE WORKOUT TEXTS ===")
    # Show some diverse examples
    rest_day_examples = []
    strength_examples = []
    metcon_examples = []
    
    for text in all_raw_texts[:50]:  # First 50 to get variety
        text_lower = text.lower()
        if 'rest day' in text_lower:
            rest_day_examples.append(text)
        elif any(word in text_lower for word in ['squat', 'deadlift', 'press']) and 'for time' not in text_lower:
            strength_examples.append(text)
        elif any(word in text_lower for word in ['rounds', 'amrap', 'for time']):
            metcon_examples.append(text)
    
    print("\nREST DAY EXAMPLES:")
    for i, example in enumerate(rest_day_examples[:3], 1):
        print(f"\nExample {i}:")
        print(example[:200] + "..." if len(example) > 200 else example)
    
    print("\nSTRENGTH EXAMPLES:")
    for i, example in enumerate(strength_examples[:3], 1):
        print(f"\nExample {i}:")
        print(example[:200] + "..." if len(example) > 200 else example)
    
    print("\nMETCON EXAMPLES:")
    for i, example in enumerate(metcon_examples[:3], 1):
        print(f"\nExample {i}:")
        print(example[:200] + "..." if len(example) > 200 else example)
    
    print("\n=== STRUCTURE ANALYSIS ===")
    # Analyze general structure
    for i, text in enumerate(all_raw_texts[:10]):
        print(f"\nWorkout {i+1} structure:")
        lines = text.split('\n')
        for j, line in enumerate(lines[:8]):  # First 8 lines
            line = line.strip()
            if line:
                print(f"  Line {j}: {line[:80]}{'...' if len(line) > 80 else ''}")


if __name__ == "__main__":
    analyze_workout_patterns()