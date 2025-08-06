#!/usr/bin/env python3
"""Generate OpenAI embeddings for workout data and update Supabase."""

import os
import sys
from typing import Any, List
import time

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Add the parent directory to Python path to import wodrag modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from wodrag.database.client import get_supabase_client


def get_openai_client() -> OpenAI:
    """Create and return an OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "Missing OpenAI API key. Please set OPENAI_API_KEY in your .env file"
        )
    
    return OpenAI(api_key=api_key)


def fetch_workouts_without_embeddings(client: Client, batch_size: int = 100) -> List[dict[str, Any]]:
    """Fetch workouts that don't have embeddings yet."""
    result = client.table("workouts").select("id, workout, scaling").is_("workout_embedding", "null").limit(batch_size).execute()
    return result.data


def generate_openai_embeddings(openai_client: OpenAI, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """Generate embeddings using OpenAI API."""
    try:
        response = openai_client.embeddings.create(
            input=texts,
            model=model
        )
        return [embedding.embedding for embedding in response.data]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise


def process_workouts_batch(
    supabase_client: Client, 
    openai_client: OpenAI, 
    workouts: List[dict[str, Any]]
) -> int:
    """Process a batch of workouts - generate embeddings and update database."""
    
    # Prepare texts for embedding (combine workout + scaling)
    texts = []
    for workout in workouts:
        text = workout["workout"]
        if workout.get("scaling"):
            text += f" {workout['scaling']}"
        texts.append(text)
    
    # Generate embeddings
    embeddings = generate_openai_embeddings(openai_client, texts)
    
    # Update database
    success_count = 0
    for i, workout in enumerate(workouts):
        try:
            supabase_client.table("workouts").update({
                "workout_embedding": embeddings[i]
            }).eq("id", workout["id"]).execute()
            success_count += 1
        except Exception as e:
            print(f"Error updating workout {workout['id']}: {e}")
    
    return success_count


def estimate_cost(total_workouts: int, avg_tokens_per_workout: int = 50) -> float:
    """Estimate the cost of generating embeddings."""
    # text-embedding-3-small: $0.00002 per 1K tokens
    total_tokens = total_workouts * avg_tokens_per_workout
    cost = (total_tokens / 1000) * 0.00002
    return cost


def main() -> None:
    """Main function to generate and store embeddings."""
    print("🤖 Generating OpenAI embeddings for workout data...")
    
    try:
        # Initialize clients
        supabase_client = get_supabase_client()
        openai_client = get_openai_client()
        
        # Count total workouts without embeddings
        result = supabase_client.table("workouts").select("id", count="exact").is_("workout_embedding", "null").execute()
        total_count = result.count
        
        if total_count == 0:
            print("✅ All workouts already have embeddings!")
            return
        
        print(f"Found {total_count} workouts without embeddings")
        
        # Estimate cost
        estimated_cost = estimate_cost(total_count)
        print(f"💰 Estimated cost: ${estimated_cost:.2f} (using text-embedding-3-small)")
        
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        
        processed = 0
        success_count = 0
        batch_size = 20  # Process 20 at a time to stay within rate limits
        
        print(f"\nProcessing {total_count} workouts in batches of {batch_size}...")
        
        while True:
            # Fetch next batch
            workouts = fetch_workouts_without_embeddings(supabase_client, batch_size)
            
            if not workouts:
                break
            
            print(f"Processing batch: {processed + 1}-{processed + len(workouts)} of {total_count}")
            
            # Process batch
            batch_success = process_workouts_batch(supabase_client, openai_client, workouts)
            
            processed += len(workouts)
            success_count += batch_success
            
            # Show progress
            progress = (processed / total_count) * 100
            print(f"Progress: {progress:.1f}% ({processed}/{total_count}) - {success_count} successful")
            
            # Rate limiting - OpenAI has limits on requests per minute
            time.sleep(1)  # 1 second between batches
        
        print(f"\n🎉 Successfully generated embeddings for {success_count} workouts!")
        
        # Verify final count
        remaining = supabase_client.table("workouts").select("id", count="exact").is_("workout_embedding", "null").execute()
        print(f"Workouts without embeddings: {remaining.count}")
        
        if remaining.count == 0:
            print("✅ All workouts now have embeddings! Your database is ready for semantic search.")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()