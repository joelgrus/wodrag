#!/usr/bin/env python3
"""
Wipe all metadata from workout records using direct SQL.

This script efficiently resets metadata fields to NULL for all workouts:
- movements, equipment, workout_type, workout_name
- one_sentence_summary, summary_embedding
- workout_embedding (optional)
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def get_stats(client):
    """Get database statistics before and after wipe."""
    result = client.table("workouts").select("id", count="exact").execute()
    total = result.count or 0
    
    # Count workouts with any metadata
    result_with_meta = (
        client.table("workouts")
        .select("id", count="exact")
        .or_(
            "movements.not.is.null,"
            "equipment.not.is.null,"
            "workout_type.not.is.null,"
            "workout_name.not.is.null,"
            "one_sentence_summary.not.is.null,"
            "summary_embedding.not.is.null"
        )
        .execute()
    )
    with_metadata = result_with_meta.count or 0
    
    return total, with_metadata


def main():
    print("🗑️  Metadata Wipe Tool (SQL)")
    print("=" * 40)
    
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    
    # Show current stats
    total_workouts, workouts_with_metadata = get_stats(client)
    print(f"Total workouts: {total_workouts}")
    print(f"Workouts with metadata: {workouts_with_metadata}")
    
    if workouts_with_metadata == 0:
        print("✅ No metadata to wipe!")
        return
    
    # Build SQL
    sql = """UPDATE workouts 
SET 
    movements = NULL,
    equipment = NULL,
    workout_type = NULL,
    workout_name = NULL,
    one_sentence_summary = NULL,
    summary_embedding = NULL"""
    
    print("\nFields to wipe:")
    print("  • movements, equipment, workout_type, workout_name") 
    print("  • one_sentence_summary, summary_embedding")
    
    include_embeddings = input("\nAlso wipe workout_embedding (full text)? (y/N): ")
    if include_embeddings.lower() == 'y':
        sql += ",\n    workout_embedding = NULL"
        print("  • workout_embedding")
    
    print(f"\n⚠️  This will wipe metadata from {workouts_with_metadata} workouts!")
    print("\nSQL to execute:")
    print(sql)
    
    confirm = input("\nType 'WIPE' to execute: ")
    if confirm != 'WIPE':
        print("❌ Aborted.")
        return
        
    try:
        # Execute the update
        client.rpc('exec_sql', {'sql': sql})
        
        # Verify results
        _, remaining = get_stats(client)
        
        print("✅ Metadata wiped successfully!")
        print(f"Workouts with metadata remaining: {remaining}")
        
        if remaining == 0:
            print("\n🎉 All metadata cleared!")
            print("\nNext steps:")
            print("1. python scripts/extract_and_populate_metadata.py")
            print("2. python scripts/generate_summary_embeddings.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if "function exec_sql() does not exist" in str(e):
            print("\n💡 You need to create the exec_sql RPC function in Supabase:")
            print("CREATE OR REPLACE FUNCTION exec_sql(sql text) RETURNS void AS $$")
            print("BEGIN EXECUTE sql; END; $$ LANGUAGE plpgsql;")

if __name__ == "__main__":
    main()