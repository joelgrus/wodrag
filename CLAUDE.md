# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`wodrag` is a Python project in its initial stages. The project uses Python 3.11+ and has a minimal structure with a single entry point.

## Development Commands

### Running the Application
```bash
python main.py
```

### Setting Up Development Environment
Since this project requires Python 3.11+, ensure you have the correct Python version:
```bash
python3 --version  # Should show 3.11 or higher
```

Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

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

## Project Structure

The project currently has a minimal structure:
- `main.py` - Entry point with a simple `main()` function
- `pyproject.toml` - Python project configuration file
- `.gitignore` - Standard Python gitignore configuration

## Architecture Notes

This is a simple Python application with:
- Single entry point through `main.py`
- Basic project structure suitable for expansion

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