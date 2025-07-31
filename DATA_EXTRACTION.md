# CrossFit Workout Data Extraction Strategy

## HTML Structure Analysis

After analyzing 294 HTML files spanning from 2001-02 to 2025-07, I've identified a consistent structure across all time periods:

### Key Findings

1. **Archives Section**: All pages contain a `<section id="archives" class="section">` element
2. **Container Structure**: Within archives, there's a `<div class="container-hybrid">` that holds all workouts
3. **Individual Workouts**: Each workout is contained in a `<div>` element (no specific class)
4. **Consistent Format**: The structure has remained remarkably consistent from 2001 to 2024

### DOM Structure

```
<section id="archives" class="section">
  <div class="container-hybrid">
    <div>  <!-- Individual workout block -->
      <h3>Saturday 241130</h3>  <!-- Duplicate date header -->
      <h4>Saturday 241130</h4>  <!-- Another date header -->
      <p>3 rounds for time of:...</p>  <!-- Workout content -->
      <a href="/workout/2024/11/30">link</a>  <!-- Workout permalink -->
      <!-- Additional content, videos, etc. -->
    </div>
    <div>  <!-- Next workout -->
      ...
    </div>
  </div>
</section>
```

## Data Extraction Strategy

### Phase 1: Basic Extraction

1. Parse each HTML file
2. Find the `archives > container-hybrid` section
3. Extract all direct `<div>` children
4. For each workout div:
   - Extract date from the first `<h3>` or `<h4>` tag
   - Extract workout URL from `<a>` tags containing `/workout/`
   - Extract all text content for the workout description
   - Parse the date to create a proper datetime object

### Phase 2: Content Parsing

Workout content varies but typically includes:

- **Workout Description**: The main workout (e.g., "3 rounds for time of...")
- **Scaling Options**: Alternative weights/movements for different skill levels
- **Additional Info**: Tips, videos, articles, quotes

Common workout formats to parse:
- AMRAP (As Many Rounds As Possible)
- For Time
- EMOM (Every Minute on the Minute)
- Strength work (e.g., "Back squat 3-3-3-3-3")
- Named workouts (e.g., "Fran", "Linda", "Barbara")

### Phase 3: Structured Data

## Proposed Data Structure

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Workout:
    # Core fields
    date: date
    url: str
    raw_text: str
    
    # Parsed fields (Phase 2)
    title: Optional[str] = None  # e.g., "Fran", "Rest Day"
    workout_type: Optional[str] = None  # e.g., "AMRAP", "For Time", "Strength"
    description: Optional[str] = None  # Main workout text
    scaling_notes: Optional[str] = None
    
    # Metadata
    has_video: bool = False
    has_article: bool = False
    month_file: str = ""  # Source file (e.g., "2024-11.html")
```

## Implementation Plan

### Step 1: Basic Extractor (wodrag/data_processing/extractor.py)
```python
def extract_workouts_from_file(file_path: Path) -> list[Workout]:
    """Extract all workouts from a single HTML file."""
    
def extract_all_workouts() -> list[Workout]:
    """Extract workouts from all HTML files in data/raw/."""
```

### Step 2: Content Parser (wodrag/data_processing/parser.py)
```python
def parse_workout_content(raw_text: str) -> dict[str, Any]:
    """Parse workout text to extract structured information."""
    
def identify_workout_type(text: str) -> Optional[str]:
    """Identify the type of workout from the description."""
```

### Step 3: Data Storage
- Save extracted data as JSON for initial processing
- Consider SQLite database for structured queries
- Export formats: JSON, CSV, Parquet for different use cases

### Step 4: Validation
- Ensure all dates are parsed correctly
- Verify URL patterns are consistent
- Check for missing workouts (some days might be empty)
- Validate against known workout patterns

## Special Considerations

1. **Rest Days**: Marked as "Rest Day" with optional content
2. **Multi-part Workouts**: Some days have A/B parts or multiple options
3. **Competition Workouts**: Special events like CrossFit Games workouts
4. **Hero WODs**: Special memorial workouts with background stories
5. **Benchmark Workouts**: Named workouts that repeat over time

## Next Steps

1. Implement basic extractor to pull all workouts into structured format
2. Create content parser to identify workout types and components
3. Build validation suite to ensure data quality
4. Design export formats for RAG system consumption