#!/usr/bin/env python3
"""Generate OpenAI embeddings from one-sentence summaries and update ParadeDB."""

import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from supabase import Client, create_client

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials")
    
    return create_client(url, key)


def get_openai_client() -> OpenAI:
    """Create and return an OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing OpenAI API key. Please set OPENAI_API_KEY in your .env file"
        )

    return OpenAI(api_key=api_key)


def fetch_workouts_without_embeddings(
    client: Client, batch_size: int = 100
) -> list[dict[str, Any]]:
    """Fetch workouts that have summaries but don't have summary embeddings yet."""
    result = (
        client.table("workouts")
        .select("id, one_sentence_summary")
        .is_("summary_embedding", "null")
        .not_.is_("one_sentence_summary", "null")
        .limit(batch_size)
        .execute()
    )
    return result.data


def generate_openai_embeddings(
    openai_client: OpenAI, texts: list[str], model: str = "text-embedding-3-small"
) -> list[list[float]]:
    """Generate embeddings using OpenAI API."""
    try:
        response = openai_client.embeddings.create(input=texts, model=model)
        return [embedding.embedding for embedding in response.data]
    except Exception:
        raise


def process_workouts_batch(
    supabase_client: Client, openai_client: OpenAI, workouts: list[dict[str, Any]]
) -> int:
    """Process a batch of workouts - generate embeddings and update database."""

    # Prepare texts for embedding (use one_sentence_summary)
    texts = []
    valid_workouts = []
    for workout in workouts:
        summary = workout.get("one_sentence_summary")
        if summary and summary.strip():
            texts.append(summary.strip())
            valid_workouts.append(workout)

    if not texts:
        return 0

    # Generate embeddings
    embeddings = generate_openai_embeddings(openai_client, texts)

    # Update database
    success_count = 0
    for i, workout in enumerate(valid_workouts):
        try:
            supabase_client.table("workouts").update(
                {"summary_embedding": embeddings[i]}
            ).eq("id", workout["id"]).execute()
            success_count += 1
        except Exception:
            pass

    return success_count


def estimate_cost(total_workouts: int, avg_tokens_per_summary: int = 20) -> float:
    """Estimate the cost of generating embeddings."""
    # text-embedding-3-small: $0.00002 per 1K tokens
    # Summaries are shorter than full workout text
    total_tokens = total_workouts * avg_tokens_per_summary
    cost = (total_tokens / 1000) * 0.00002
    return cost


def main() -> None:
    """Main function to generate and store embeddings."""

    try:
        # Initialize clients
        supabase_client = get_supabase_client()
        openai_client = get_openai_client()

        # Count total workouts without summary embeddings that have summaries
        result = (
            supabase_client.table("workouts")
            .select("id", count="exact")
            .is_("summary_embedding", "null")
            .not_.is_("one_sentence_summary", "null")
            .execute()
        )
        total_count = result.count

        if total_count == 0:
            return


        # Estimate cost
        estimate_cost(total_count)

        response = input("Continue? (y/N): ")
        if response.lower() != "y":
            return

        processed = 0
        success_count = 0
        batch_size = 20  # Process 20 at a time to stay within rate limits


        while True:
            # Fetch next batch
            workouts = fetch_workouts_without_embeddings(supabase_client, batch_size)

            if not workouts:
                break


            # Process batch
            batch_success = process_workouts_batch(
                supabase_client, openai_client, workouts
            )

            processed += len(workouts)
            success_count += batch_success

            # Show progress
            (processed / total_count) * 100

            # Rate limiting - OpenAI has limits on requests per minute
            time.sleep(1)  # 1 second between batches


        # Verify final count
        remaining = (
            supabase_client.table("workouts")
            .select("id", count="exact")
            .is_("summary_embedding", "null")
            .not_.is_("one_sentence_summary", "null")
            .execute()
        )

        if remaining.count == 0:
            pass

    except Exception:
        pass


if __name__ == "__main__":
    main()
