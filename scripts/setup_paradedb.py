#!/usr/bin/env python3
"""Setup script for migrating to ParadeDB."""

import os
import subprocess
import sys
import time


def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return success status."""
    try:
        subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def wait_for_postgres(max_attempts: int = 30) -> bool:
    """Wait for PostgreSQL to be ready."""

    for _attempt in range(max_attempts):
        try:
            result = subprocess.run(
                "docker exec wodrag_paradedb pg_isready -U postgres -d wodrag",
                shell=True,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

        time.sleep(2)

    return False


def main():
    """Main setup function."""

    # Check if Docker is running
    if not run_command("docker --version", "Check Docker availability"):
        sys.exit(1)

    # Start ParadeDB
    if not run_command("docker-compose up -d postgres", "Start ParadeDB container"):
        sys.exit(1)

    # Wait for PostgreSQL to be ready
    if not wait_for_postgres():
        sys.exit(1)

    # Import data
    if not os.path.exists("data/supabase_export.json"):
        sys.exit(1)

    # Import the data
    if not run_command(
        "uv run python scripts/import_to_paradedb.py", "Import data to ParadeDB"
    ):
        sys.exit(1)



if __name__ == "__main__":
    main()
