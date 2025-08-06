# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Thinking Before Coding

DO NOT write code until I ask you to. If I suggest a feature or a refactoring or similar,
I am asking for thoughts / design / architecture / etc. Do not actually implement or refactor
until I give you the go-ahead.

## Project Overview

`wodrag` is a CrossFit workout search system that combines semantic similarity with BM25 text search. The project provides hybrid search capabilities over 8,861+ CrossFit workouts from 2001-2024.

### Core Components

- **ParadeDB**: PostgreSQL with BM25 full-text search and pgvector extensions
- **Semantic Search**: OpenAI text-embedding-3-small for meaning-based matching  
- **BM25 Search**: Superior text relevance ranking via ParadeDB
- **Hybrid Search**: Configurable fusion of semantic + BM25 scores
- **Metadata Extraction**: AI-powered classification of movements, equipment, workout types

### Database Architecture

The system uses **ParadeDB** (PostgreSQL + BM25 + pgvector) running in Docker:

- **8,861 workouts** with full metadata and embeddings
- **BM25 index** on workout, summary, scaling, and name fields  
- **Vector indexes** for semantic similarity search
- **Hybrid queries** combining both search methods

## Backlog

This project uses the backlog tool for managing a backlog of tasks.
Please use the `backlog` command line tool to manage the backlog.


### Database Setup
Start the ParadeDB database first:
```bash
# Start ParadeDB container (PostgreSQL + BM25 + pgvector)
docker compose up -d postgres

# Verify database is ready
docker exec wodrag_paradedb psql -U postgres -d wodrag -c "SELECT COUNT(*) FROM workouts;"
```

### Installing Dependencies
Install the project with development dependencies using uv:
```bash
uv pip install -e .
uv pip install -e ".[dev]"
```

### Environment Configuration
Use the ParadeDB environment variables:
```bash
# Main environment file should contain:
DATABASE_URL=postgresql://postgres:password@localhost:5432/wodrag
OPENAI_API_KEY=your_openai_api_key
```

### Code Quality Checks
Always run these checks before committing code:
```bash
# Type checking
uv run mypy wodrag

# Linting and formatting
uv run ruff check wodrag
uv run ruff format wodrag

# Run tests
uv run pytest
```

### Important: Always Use UV
**ALWAYS use `uv` for ALL Python-related commands:**
- `uv pip install` instead of `pip install`
- `uv run <command>` instead of `python -m <command>` or direct command
- `uv run python` instead of `python` or `python3`
- Examples:
  - `uv run mypy wodrag`
  - `uv run ruff check`
  - `uv run pytest`
  - `uv run python scripts/download_all.py`

### Search Testing
Test the search functionality:
```bash
# Test semantic search
uv run python scripts/search_summaries.py search "strength training" --limit 5

# Test hybrid search (recommended)
uv run python scripts/search_summaries.py search "burpees pull-ups" --hybrid --limit 10

# Test exact phrases
uv run python scripts/search_summaries.py search '"pogo stick"' --hybrid --limit 5

# Test complex queries
uv run python scripts/search_summaries.py search '10k run completed "pogo stick"' --hybrid --limit 10
```

## Architecture Notes

### Search System
- **Hybrid Architecture**: Combines BM25 text search with semantic embeddings
- **ParadeDB Integration**: Uses native BM25 algorithms for superior text ranking
- **Vector Similarity**: OpenAI embeddings with cosine similarity via pgvector
- **Score Fusion**: Configurable weighting between semantic and text scores

### Data Pipeline
1. **Extraction**: Parse CrossFit.com workout HTML content
2. **Metadata**: AI-powered classification of movements, equipment, types
3. **Embeddings**: Generate semantic vectors for workout text and summaries  
4. **Indexing**: Create BM25 and vector indexes for fast search

When adding new features:
1. Use the ParadeDB-based search methods in `WorkoutRepository`
2. Add dependencies to `pyproject.toml` as needed
3. Follow Python conventions (PEP 8) for code style
4. Always test both semantic and hybrid search functionality

## Coding Standards

1. **Type Annotations**: Always use type annotations for all functions, methods, and class attributes
2. **Code Organization**: All code lives under `/home/joel/src/wodrag/wodrag/` - no `src/` folder
3. **Code Quality**: Always check code with:
   - `mypy` for type checking
   - `ruff` for linting and formatting
   - `pytest` for running tests