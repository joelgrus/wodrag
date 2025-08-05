#!/usr/bin/env python3
"""Incrementally update workout database with new workouts."""

import json
import os
from datetime import datetime, timedelta
from typing import Any, List

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

from wodrag.data_processing.downloader import download_workout_month
from wodrag.data_processing.extractor import extract_workouts_from_month
from wodrag.data_processing.simple_parser import parse_workout_simple

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY"
        )
    
    return create_client(url, key)


def get_openai_client() -> OpenAI:
    """Create and return an OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "Missing OpenAI API key. Please set OPENAI_API_KEY in your .env file"
        )
    
    return OpenAI(api_key=api_key)


def get_latest_workout_date(client: Client) -> str | None:
    """Get the date of the most recent workout in the database."""
    result = client.table("workouts").select("date").order("date", desc=True).limit(1).execute()
    
    if result.data:
        return result.data[0]["date"]
    return None


def get_months_to_update(latest_date: str | None) -> List[str]:
    """Determine which months need to be updated."""
    current_date = datetime.now()
    months_to_update = []
    
    if latest_date is None:
        # No data exists, start from 2001-02
        start_date = datetime(2001, 2, 1)
    else:
        # Start from the month of the latest workout
        latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")
        start_date = datetime(latest_dt.year, latest_dt.month, 1)
    
    # Generate months from start_date to current month
    date_iter = start_date
    while date_iter <= current_date:
        months_to_update.append(date_iter.strftime("%Y-%m"))
        # Move to next month
        if date_iter.month == 12:
            date_iter = date_iter.replace(year=date_iter.year + 1, month=1)
        else:
            date_iter = date_iter.replace(month=date_iter.month + 1)
    
    return months_to_update


def workout_exists(client: Client, date: str, url: str) -> bool:
    """Check if a workout already exists in the database."""
    result = client.table("workouts").select("id").eq("date", date).eq("url", url).execute()
    return len(result.data) > 0


def generate_embedding(openai_client: OpenAI, text: str) -> List[float]:
    """Generate embedding for a single text."""
    response = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def insert_workout_with_embedding(
    client: Client, 
    openai_client: OpenAI, 
    workout: dict[str, Any]
) -> bool:
    """Insert a single workout with its embedding."""
    try:
        # Generate embedding text (workout + scaling)
        embedding_text = workout["workout"]
        if workout.get("scaling"):
            embedding_text += f" {workout['scaling']}"
        
        # Generate embedding
        embedding = generate_embedding(openai_client, embedding_text)
        
        # Insert workout with embedding
        # Note: summary_embedding will be generated later when metadata is extracted
        client.table("workouts").insert({
            "date": workout["date"],
            "url": workout["url"],
            "raw_text": workout["raw_text"],
            "workout": workout["workout"],
            "scaling": workout["scaling"],
            "has_video": workout["has_video"],
            "has_article": workout["has_article"],
            "month_file": workout["month_file"],
            "workout_embedding": embedding
        }).execute()
        
        return True
    except Exception as e:
        print(f"Error inserting workout {workout['date']}: {e}")
        return False


def update_month(
    client: Client, 
    openai_client: OpenAI, 
    year_month: str, 
    force_redownload: bool = False
) -> int:
    """Update workouts for a specific month. Returns number of new workouts added."""
    print(f"Updating {year_month}...")
    
    year, month = year_month.split("-")
    
    # Download month data
    month_file = f"data/raw/{year_month}.html"
    
    if force_redownload or not os.path.exists(month_file):
        print(f"  Downloading {year_month}...")
        success = download_workout_month(int(year), int(month))
        if not success:
            print(f"  Failed to download {year_month}")
            return 0
    
    # Extract workouts
    workouts = extract_workouts_from_month(year_month)
    
    if not workouts:
        print(f"  No workouts found for {year_month}")
        return 0
    
    # Process each workout
    new_count = 0
    for workout_data in workouts:
        # Check if workout already exists
        if workout_exists(client, workout_data["date"], workout_data["url"]):
            continue
        
        # Parse workout
        parsed = parse_workout_simple(workout_data["raw_text"])
        
        # Prepare workout dict
        workout = {
            "date": workout_data["date"],
            "url": workout_data["url"],
            "raw_text": workout_data["raw_text"],
            "workout": parsed["workout"],
            "scaling": parsed["scaling"],
            "has_video": workout_data["has_video"],
            "has_article": workout_data["has_article"],
            "month_file": year_month,
        }
        
        # Insert with embedding
        if insert_workout_with_embedding(client, openai_client, workout):
            new_count += 1
            print(f"  Added: {workout_data['date']}")
    
    return new_count


def main() -> None:
    """Main function for incremental updates."""
    print("🔄 Starting incremental workout update...")
    
    try:
        # Initialize clients
        supabase_client = get_supabase_client()
        openai_client = get_openai_client()
        
        # Get latest workout date
        latest_date = get_latest_workout_date(supabase_client)
        print(f"Latest workout in database: {latest_date or 'None (empty database)'}")
        
        # Determine months to update
        months_to_update = get_months_to_update(latest_date)
        
        if not months_to_update:
            print("✅ Database is up to date!")
            return
        
        print(f"Months to check for updates: {len(months_to_update)}")
        print(f"Range: {months_to_update[0]} to {months_to_update[-1]}")
        
        # Update each month
        total_new = 0
        for month in months_to_update:
            new_count = update_month(supabase_client, openai_client, month)
            total_new += new_count
        
        print(f"\n🎉 Update complete! Added {total_new} new workouts.")
        
        # Show final stats
        total_result = supabase_client.table("workouts").select("id", count="exact").execute()
        print(f"Total workouts in database: {total_result.count}")
        
    except Exception as e:
        print(f"❌ Error during update: {e}")


if __name__ == "__main__":
    main()