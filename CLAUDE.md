# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Thinking Before Coding

DO NOT write code until I ask you to. If I suggest a feature or a refactoring or similar,
I am asking for thoughts / design / architecture / etc. Do not actually implement or refactor
until I give you the go-ahead.

## Project Overview

`wodrag` is a Python project in its initial stages. The project uses Python 3.11+ and has a minimal structure with a single entry point.

## Backlog

This project uses the backlog tool for managing a backlog of tasks.
Please use the `backlog` command line tool to manage the backlog.


### Installing Dependencies
Install the project with development dependencies using uv:
```bash
uv pip install -e .
uv pip install -e ".[dev]"
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

## Architecture Notes

When adding new features:
1. Consider organizing code into modules/packages as the project grows
2. Add dependencies to `pyproject.toml` as needed
3. Follow Python conventions (PEP 8) for code style

## Coding Standards

1. **Type Annotations**: Always use type annotations for all functions, methods, and class attributes
2. **Code Organization**: All code lives under `/home/joel/src/wodrag/wodrag/` - no `src/` folder
3. **Code Quality**: Always check code with:
   - `mypy` for type checking
   - `ruff` for linting and formatting
   - `pytest` for running tests