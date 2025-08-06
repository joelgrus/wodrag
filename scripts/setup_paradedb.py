#!/usr/bin/env python3
"""Setup script for migrating to ParadeDB."""

import os
import subprocess
import sys
import time

def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False


def wait_for_postgres(max_attempts: int = 30) -> bool:
    """Wait for PostgreSQL to be ready."""
    print("⏳ Waiting for PostgreSQL to be ready...")
    
    for attempt in range(max_attempts):
        try:
            result = subprocess.run(
                "docker exec wodrag_paradedb pg_isready -U postgres -d wodrag",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ PostgreSQL is ready!")
                return True
        except Exception:
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ PostgreSQL failed to start")
    return False


def main():
    """Main setup function."""
    print("🚀 Setting up ParadeDB migration...")
    
    # Check if Docker is running
    if not run_command("docker --version", "Check Docker availability"):
        print("Please ensure Docker is installed and running")
        sys.exit(1)
    
    # Start ParadeDB
    if not run_command("docker-compose up -d postgres", "Start ParadeDB container"):
        sys.exit(1)
    
    # Wait for PostgreSQL to be ready
    if not wait_for_postgres():
        sys.exit(1)
    
    # Import data
    print("\n📥 Importing data...")
    print("First, make sure you have the export file:")
    if not os.path.exists("data/supabase_export.json"):
        print("❌ Export file not found. Run: uv run python scripts/export_supabase_data.py")
        sys.exit(1)
    
    # Import the data
    if not run_command("uv run python scripts/import_to_paradedb.py", "Import data to ParadeDB"):
        sys.exit(1)
    
    print("\n🎉 ParadeDB setup complete!")
    print("\nNext steps:")
    print("1. Copy .env.paradedb to .env to use ParadeDB")
    print("2. Test search functionality")
    print("3. Run: uv run python scripts/search_summaries.py search 'your query' --hybrid")


if __name__ == "__main__":
    main()