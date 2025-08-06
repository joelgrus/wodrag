# ParadeDB Migration Guide

This branch contains the migration from Supabase to local ParadeDB for improved BM25 search capabilities.

## Why ParadeDB?

- **Better BM25 scoring**: Superior text relevance ranking compared to PostgreSQL's ts_rank
- **No tokenization issues**: Handles "10k" vs "10 k" more intelligently  
- **Full content indexing**: Includes summary field in search index
- **Better phrase handling**: More robust quoted phrase search
- **Local control**: Full control over search configuration and tuning

## Migration Steps

### 1. Export Current Data
```bash
# Export from Supabase (already done)
uv run python scripts/export_supabase_data.py
```

### 2. Start ParadeDB
```bash
# Start the ParadeDB container
docker-compose up -d postgres

# Or use the automated setup script
uv run python scripts/setup_paradedb.py
```

### 3. Switch Environment
```bash
# Copy ParadeDB environment config
cp .env.paradedb .env
```

### 4. Import Data
```bash
# Import the exported data
uv run python scripts/import_to_paradedb.py
```

### 5. Test Search
```bash
# Test the pogo stick query that was problematic
uv run python scripts/search_summaries.py search '10k run completed "pogo stick"' --hybrid --limit 10

# Test other queries
uv run python scripts/search_summaries.py search '"pogo stick"' --hybrid
uv run python scripts/search_summaries.py search 'burpees OR pull-ups' --hybrid
```

## Key Changes

### Database Layer
- **New BM25 Index**: Replaces `workout_search_vector` with ParadeDB's BM25 index
- **Includes Summary**: Full-text index now includes `one_sentence_summary` field
- **Better Scoring**: BM25 provides more relevant text ranking than ts_rank

### Search Implementation
- **ParadeDB Integration**: `text_search_workouts()` now uses ParadeDB's BM25 API
- **Fallback Support**: Gracefully falls back to websearch_to_tsquery if ParadeDB unavailable
- **Enhanced Query Support**: Better boolean query parsing and phrase handling

### Docker Setup
- **ParadeDB Container**: Includes both pgvector and BM25 extensions
- **Persistent Storage**: Data persists across container restarts
- **Health Checks**: Ensures database is ready before operations

## Expected Improvements

The "pogo stick" search issue should be resolved because:

1. **Full Content Index**: Summary field is now indexed, so "completed" will be found
2. **Better Tokenization**: BM25 handles compound terms like "10k" more intelligently
3. **Improved Ranking**: BM25 provides better relevance scoring than ts_rank
4. **Phrase Matching**: Enhanced support for quoted phrases in complex queries

## Rollback Plan

To revert to Supabase:
```bash
git checkout master
cp .env.supabase .env  # If you have this backup
```