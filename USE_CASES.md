# CrossFit Workout RAG System Use Cases

## Primary Use Cases

### 1. Workout Programming Assistant
- "Show me workouts similar to Fran but with different movements"
- "Find workouts that combine deadlifts and box jumps"
- "What are some good 10-15 minute AMRAPs with gymnastics movements?"
- "Build me a workout similar to yesterday's but easier"

### 2. Movement Progression Finder
- "Show me workouts with pull-up progressions from beginner to advanced"
- "Find workouts that scale from ring rows to muscle-ups"
- "What's a good progression path to get my first handstand push-up?"
- "Show workouts that build up to bar muscle-ups"

### 3. Historical Trend Analysis
- "How have CrossFit workouts evolved from 2001 to 2025?"
- "When did double-unders first appear in workouts?"
- "Show the frequency of Olympic lifts over time"
- "What movements were popular in 2010 but rarely programmed now?"

### 4. Personalized Workout Recommendations
- "I can't do pull-ups, find workouts with scaling options"
- "Show me workouts without barbells (home gym friendly)"
- "Find workouts for someone recovering from knee injury"
- "I only have 20 minutes, what's a good workout?"
- "Show me workouts I can do in a hotel gym"

### 5. Benchmark/Hero WOD Reference
- "What's the workout called Murph?"
- "Show me all Hero WODs"
- "Find variations of classic benchmark workouts"
- "What are the Girls workouts?"
- "Show me memorial workouts for fallen service members"

### 6. Equipment-Based Search
- "Workouts I can do with just a kettlebell"
- "Find bodyweight-only workouts"
- "Show workouts that need a rower"
- "What can I do with dumbbells and a pull-up bar?"
- "Find workouts without any equipment"

### 7. Time Domain Queries
- "Find 5-minute sprint workouts"
- "Show me 30+ minute endurance WODs"
- "What are good workouts for a lunch break?"
- "Find workouts with 20-minute time caps"
- "Show me workouts that take exactly 10 minutes"

### 8. Coaching/Programming Insights
- "How often should I program heavy days?"
- "What's a good workout after heavy squats yesterday?"
- "Build me a week of varied programming"
- "Show examples of well-balanced weekly programming"
- "How do I program for GPP (general physical preparedness)?"

### 9. Movement Pattern Analysis
- "Find workouts with pushing and pulling balance"
- "Show me monostructural conditioning workouts"
- "Find triplets with one weightlifting, one gymnastic, one cardio"
- "What are good posterior chain focused workouts?"

### 10. Competition/Testing Prep
- "Find workouts similar to Open workout 23.1"
- "Show me workouts that test similar capacities to Fran"
- "What workouts help prepare for competitions?"
- "Find max effort strength days"

## Additional Metadata Fields Wishlist

### Critical Value (Would enable many use cases)

1. **movements[]** - Array of standardized movement names
   - Value: 🔥🔥🔥🔥🔥
   - Enables: Movement search, progression tracking, pattern analysis
   - Example: ["deadlift", "box_jump", "pull_up"]

2. **equipment[]** - Array of required equipment
   - Value: 🔥🔥🔥🔥🔥
   - Enables: Home gym search, travel workouts, equipment filtering
   - Example: ["barbell", "pull_up_bar", "box"]

3. **workout_type** - Classification of workout style
   - Value: 🔥🔥🔥🔥
   - Enables: Program variety, specific training focus
   - Values: "metcon", "strength", "hero", "benchmark", "team", "endurance", "skill"

4. **time_domain** - Expected workout duration
   - Value: 🔥🔥🔥🔥
   - Enables: Time-based programming, lunch workouts
   - Values: "sprint" (<5min), "short" (5-10min), "medium" (10-20min), "long" (20-40min), "endurance" (40min+)

### High Value

5. **workout_name** - Named workouts (Fran, Murph, etc.)
   - Value: 🔥🔥🔥🔥
   - Enables: Quick benchmark lookup, variation finding
   - Example: "Fran", "Murph", "Helen"

6. **movement_patterns[]** - Movement categories
   - Value: 🔥🔥🔥
   - Enables: Balanced programming, movement pattern search
   - Values: ["hip_hinge", "squat", "press", "pull", "carry", "lunge"]

7. **energy_systems[]** - Primary energy systems targeted
   - Value: 🔥🔥🔥
   - Enables: Specific adaptation targeting
   - Values: ["phosphagen", "glycolytic", "oxidative"]

8. **rep_scheme** - Structure of the workout
   - Value: 🔥🔥🔥
   - Enables: Workout structure search
   - Values: "rounds_for_time", "amrap", "emom", "tabata", "chipper", "ladder"

### Medium Value

9. **difficulty_level** - Approximate difficulty
   - Value: 🔥🔥🔥
   - Enables: Appropriate workout selection
   - Values: "beginner", "intermediate", "advanced", "elite"

10. **load_prescription** - How loads are prescribed
    - Value: 🔥🔥🔥
    - Enables: Understanding weight selection
    - Values: "bodyweight", "light", "moderate", "heavy", "percentage", "max_effort"

11. **skill_components[]** - Technical skills required
    - Value: 🔥🔥
    - Enables: Skill development focus
    - Example: ["kipping", "double_under", "squat_snatch"]

12. **has_complex_movements** - Contains technical lifts
    - Value: 🔥🔥
    - Enables: Filtering for coaching scenarios
    - Values: true/false

### Nice to Have

13. **estimated_duration_minutes** - Numeric estimate
    - Value: 🔥🔥
    - Enables: Precise time filtering
    - Example: 12.5

14. **movement_counts{}** - Rep counts per movement
    - Value: 🔥🔥
    - Enables: Volume analysis
    - Example: {"pull_up": 100, "push_up": 200}

15. **primary_stimulus** - Main training effect
    - Value: 🔥🔥
    - Enables: Targeted training
    - Values: "strength", "power", "endurance", "stamina", "skill"

16. **coach_notes** - Extracted coaching cues
    - Value: 🔥🔥
    - Enables: Coaching insight search
    - Example: "Focus on consistent pacing"

### Experimental/Advanced

17. **relative_intensity** - Estimated intensity level
    - Value: 🔥
    - Enables: Intensity-based programming
    - Values: 1-10 scale

18. **volume_load** - Total work calculation
    - Value: 🔥
    - Enables: Volume tracking
    - Example: Calculated from reps × load

19. **movement_combinations[]** - Common pairings
    - Value: 🔥
    - Enables: Pattern recognition
    - Example: ["thruster+pull_up", "clean+jerk"]

20. **season_tag** - When workout appeared
    - Value: 🔥
    - Enables: Seasonal programming insights
    - Values: "open_prep", "summer", "holiday", "new_year"

21. **injury_considerations[]** - Movements to avoid with injuries
    - Value: 🔥
    - Enables: Injury-aware programming
    - Example: ["knee_friendly", "shoulder_friendly"]

22. **scaling_complexity** - How detailed scaling options are
    - Value: 🔥
    - Enables: Finding well-scaled workouts
    - Values: "none", "basic", "detailed", "comprehensive"

## Implementation Priority

1. Start with movements[] and equipment[] - these unlock the most use cases
2. Add workout_type and time_domain for basic categorization  
3. Extract workout_name for benchmark searches
4. Build more sophisticated fields based on user feedback

The beauty of the current semantic search is that it already handles many of these queries reasonably well through natural language understanding, but structured metadata would make the results more precise and enable faceted search interfaces.