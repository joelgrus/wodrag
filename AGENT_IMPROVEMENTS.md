# Agent Improvements Roadmap

This document outlines planned improvements to transform the master agent from a "workout search engine" into an "AI CrossFit coach."

## Phase 1: Table Stakes - Conversation History

### 1. Conversation Memory System
**Priority: CRITICAL (table stakes for modern AI)**

**Problem:** Agent has no memory between requests. "Make that workout easier" fails because it doesn't know what "that" refers to.

**Implementation:**
- Add `conversation_id` parameter to API endpoint
- Store conversation history with message threading
- Modify ReAct agent to accept conversation context
- Use in-memory LRU cache initially, designed for easy Redis migration

**Technical Details:**
- **Storage:** In-memory LRU cache (configurable size, default 1000 conversations)
- **Conversation Limits:** Configurable max messages per conversation (default 50)
- **Context Window:** Configurable token limit for LLM context (default 8000 tokens)
- **Thread Safety:** TODO - handle concurrent access to same conversation
- **Cache Strategy:** Abstract interface for easy Redis/database migration later

**Data Models:**
```python
@dataclass
class ConversationMessage:
    role: str  # "user" or "assistant" 
    content: str
    timestamp: datetime

@dataclass 
class Conversation:
    id: str
    messages: list[ConversationMessage]
    created_at: datetime
    last_updated: datetime
```

**API Changes:**
```python
# Request
POST /api/v1/agent/query
{
  "question": "make that workout easier",
  "conversation_id": "optional-uuid",  # creates new if missing
  "verbose": false
}

# Response includes conversation_id
{
  "conversation_id": "uuid-here",
  "data": { ... }
}
```

**Configuration:**
```python
# Environment variables
MAX_CONVERSATIONS=1000
MAX_MESSAGES_PER_CONVERSATION=50  
MAX_CONTEXT_TOKENS=8000
CONVERSATION_TTL_HOURS=24
```

**Redis Migration Path:**
- Abstract `ConversationStore` interface
- Implement `InMemoryConversationStore` first
- Later add `RedisConversationStore` with same interface
- Redis runs easily in Docker: `docker run -d redis:alpine`

---

## Phase 2: Intelligence Upgrades

### 2. WorkoutAnalyzer Agent
**Priority: HIGH (immediate intelligence boost)**

**Problem:** Agent can find workouts but can't explain WHY they're designed that way or what makes them challenging.

**Capabilities:**
- Analyze workout structure (rep schemes, time domains, movement patterns)
- Identify energy system targets (aerobic, anaerobic power/capacity)
- Explain difficulty factors and physiological demands
- Compare workouts by stimulus and adaptation

**Example Interactions:**
```
User: "Why is Fran so brutal?"
Agent: "Fran uses a 21-15-9 descending rep scheme creating severe metabolic stress. 
        Thrusters pre-fatigue legs/shoulders, making pull-ups exponentially harder. 
        Targets anaerobic power in the 3-5 minute time domain."

User: "What's the difference between Fran and Helen?"
Agent: "Fran is pure anaerobic power (3-5min), while Helen is mixed aerobic/anaerobic 
        (8-12min). Helen's running creates different metabolic demands than Fran's 
        pure gymnastics/barbell combination."
```

### 3. Movement Intelligence Agent  
**Priority: HIGH (solves daily scaling problems)**

**Problem:** Users can't do certain movements but don't know appropriate substitutions or progressions.

**Capabilities:**
- Exercise progressions (beginner → advanced)
- Movement substitutions maintaining similar patterns
- Equipment alternatives (barbell → dumbbell → bodyweight)
- Scaling for different fitness levels

**Movement Database:**
```python
@dataclass
class Movement:
    name: str
    category: str  # "squat", "pull", "push", etc.
    equipment: list[str]
    difficulty_level: int  # 1-10
    progressions: list[str]  # easier variations
    substitutions: list[str]  # equivalent alternatives
    coaching_cues: list[str]
    common_faults: list[str]
```

**Example Interactions:**
```
User: "I can't do pull-ups, what should I do instead?"
Agent: "For pull-ups: 
        - Progression: Band-assisted → Jumping → Negative → Full ROM
        - Substitutions: Ring rows, TRX rows, lat pulldowns
        - All maintain vertical pulling pattern and similar muscle activation."

User: "Scale Fran for a beginner"
Agent: "Beginner Fran: 15-10-5 reps of:
        - Thrusters: Use 15lb dumbbells instead of 95lb barbell
        - Pull-ups: Use thick resistance band or substitute ring rows
        - Maintains same movement pattern and rep scheme structure"
```

### 4. Equipment/Space Optimizer Agent
**Priority: HIGH (solves practical constraints)**

**Problem:** Workouts assume full gym access. Users train at home, hotels, small spaces with limited equipment.

**Capabilities:**
- Adapt workouts for available equipment
- Optimize for space constraints  
- Suggest equipment alternatives
- Maintain workout stimulus despite limitations

**Equipment Database:**
- Map barbell movements → dumbbell → kettlebell → bodyweight
- Space requirements for movements
- Equipment substitution matrices

**Example Interactions:**
```
User: "I only have dumbbells and 20 minutes at home"
Agent: "Here's 'Dumbbell Fran' - 15-10-5:
        - DB Thrusters (25lb each)
        - DB Bent-over Rows
        - Takes 8x8 feet space, maintains same time domain and stimulus"

User: "Do this workout in a hotel room"
Agent: "Hotel Room Helen: 3 rounds of:
        - 400 bodyweight squats (replaces 400m run)
        - 21 pike push-ups (replaces kettlebell swings) 
        - 12 single-arm floor press (replaces pull-ups)"
```

---

## Phase 3: Personalization & Progression

### 5. User Profile & Preferences System
**Priority: MEDIUM (enables true personalization)**

**Problem:** Agent treats everyone identically regardless of experience, goals, or limitations.

**User Profile Data:**
```python
@dataclass
class UserProfile:
    experience_level: str  # "beginner", "intermediate", "advanced"
    goals: list[str]  # "general fitness", "competition", "strength"
    available_equipment: list[str]
    time_constraints: dict  # preferred workout durations
    injuries_limitations: list[str]
    benchmark_times: dict[str, float]  # PR tracking
    preferred_movements: list[str]
    disliked_movements: list[str]
```

**Capabilities:**
- Automatic workout scaling based on experience
- Equipment filtering based on user setup
- Goal-specific programming recommendations
- Injury-aware exercise substitutions

### 6. WorkoutModifier Agent
**Priority: MEDIUM (intelligent adaptation)**

**Problem:** Can't modify existing workouts while preserving intended stimulus.

**Capabilities:**
- Change time domains while maintaining stimulus
- Adjust rep schemes for different loading
- Scale difficulty up/down intelligently
- Preserve movement patterns and energy systems

**Example Interactions:**
```
User: "Make this workout 20 minutes instead of 15"
Agent: "Extended version maintains aerobic base stimulus by:
        - Adding 2 more rounds (5 total instead of 3)
        - Reducing reps per round (10 instead of 15)  
        - Same total volume, longer duration, lower intensity"

User: "Make Murph more beginner-friendly"
Agent: "Beginner Murph (Half Murph Plus):
        - 800m run, 50 pull-ups, 100 push-ups, 150 squats, 800m run
        - Partition as needed, maintains Hero WOD honor and structure
        - Time cap: 45 minutes instead of elite 30-35 minutes"
```

### 7. Performance Tracking Agent
**Priority: MEDIUM (progress motivation)**

**Problem:** No tracking of personal progress, benchmark times, or improvement patterns.

**Capabilities:**
- Track benchmark workout times (Fran, Helen, Murph, etc.)
- Identify improvement trends and plateaus
- Suggest targeted weakness work
- Compare performance to standards/peers
- Generate progress reports

**Data Storage:**
```python
@dataclass
class WorkoutResult:
    workout_name: str
    time_or_reps: float
    rx_or_scaled: str
    date: datetime
    notes: str
    
@dataclass
class BenchmarkProgress:
    workout_name: str
    results: list[WorkoutResult]
    best_time: float
    improvement_rate: float  # seconds per month
    percentile_rank: float  # vs community
```

---

## Phase 4: Advanced Coaching

### 8. ProgramDesigner Agent
**Priority: LOW (advanced feature)**

**Problem:** Can find individual workouts but can't create structured multi-week programs.

**Capabilities:**
- Design periodized training programs
- Balance energy systems over time
- Program progression and deload weeks
- Competition preparation phases
- Movement pattern balancing

**Programming Concepts:**
- Macrocycles (12-16 week phases)  
- Mesocycles (3-4 week blocks)
- Microcycles (weekly structure)
- Energy system periodization
- Movement pattern frequency tracking

### 9. Competition Analyst Agent  
**Priority: LOW (niche competitive athletes)**

**Problem:** No insight into competitive CrossFit trends, Games preparation, or strategic analysis.

**Capabilities:**
- Analyze CrossFit Games/competition trends
- Predict likely test formats and movements
- Create Games-style workout programming
- Strategic preparation recommendations
- Regional/Games qualification standards

### 10. Injury/Recovery Agent
**Priority: MEDIUM (safety critical)**

**Problem:** No awareness of injuries, contraindicated movements, or recovery protocols.

**Capabilities:**
- Identify contraindicated movements for common injuries
- Suggest safe exercise modifications
- Recommend recovery protocols and load management
- Integration with physical therapy progressions
- Return-to-training guidelines

**Safety Database:**
- Common CrossFit injuries and modifications
- Movement contraindications  
- Progressive loading protocols
- Red flag symptoms requiring medical attention

---

## Phase 5: Data Integration & Advanced Features

### 11. Leaderboard & Community Data
**Priority: LOW (social features)**

**Integration with:**
- CrossFit Games leaderboard data
- Wodify/SugarWOD gym platforms
- Community benchmark databases

**Capabilities:**
- "What's a good Fran time for my age/weight?"
- Percentile rankings and goal setting
- Community challenges and comparisons

### 12. Nutrition & Recovery Integration
**Priority: LOW (holistic coaching)**

**Problem:** Performance factors beyond just workouts (nutrition, sleep, recovery) are ignored.

**Potential Integration:**
- Post-workout nutrition recommendations
- Sleep optimization for recovery
- Hydration and supplementation guidance
- Recovery protocol suggestions

### 13. Real-time Coaching Features
**Priority: FUTURE (advanced AI)**

**Ambitious Future Features:**
- Video form analysis and correction
- Real-time workout coaching via voice
- Heart rate/wearable integration
- Live adaptation based on performance

---

## Technical Implementation Notes

### Architecture Principles
- **Modular Design:** Each agent is independent and composable
- **Loose Coupling:** Abstract interfaces for easy testing and swapping
- **Configuration Driven:** All limits, thresholds, and behaviors configurable
- **Scalable Storage:** Design for easy migration from in-memory to Redis/database

### Development Priorities
1. **Phase 1:** Conversation history (table stakes)
2. **Phase 2:** Intelligence upgrades (immediate value)  
3. **Phase 3:** Personalization (user engagement)
4. **Phase 4:** Advanced coaching (differentiation)
5. **Phase 5:** Ecosystem integration (platform features)

### Success Metrics
- **Usage:** Conversation length, return users, query complexity
- **Intelligence:** Successful context resolution, appropriate responses
- **Personalization:** User profile completion, customized recommendations
- **Performance:** Response time, context accuracy, user satisfaction

The goal is transforming from a "workout search engine" into an "AI CrossFit coach" that understands users personally and helps them progress systematically over time.