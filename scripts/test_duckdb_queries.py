#!/usr/bin/env python3
"""Test script for DuckDB text-to-SQL functionality."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import dspy

# Add the wodrag package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wodrag.agents.text_to_sql import QueryGenerator


def print_records(results: list[dict[str, Any]], max_records: int = 5, max_width: int = 80) -> None:
    """Print results as formatted records with truncation."""
    if not results:
        print("  📭 No results found")
        return
    
    display_results = results[:max_records]
    
    for i, record in enumerate(display_results, 1):
        print(f"  📄 Record {i}:")
        
        for key, value in record.items():
            if value is None:
                value_str = "NULL"
            elif isinstance(value, list):
                # Handle arrays nicely
                items = [str(item) for item in value[:10]]
                value_str = f"[{', '.join(items)}]"
                if len(value) > 10:
                    value_str = value_str[:-1] + f", ... and {len(value)-10} more]"
            else:
                value_str = str(value)
                if len(value_str) > max_width:
                    value_str = value_str[:max_width-3] + "..."
            
            print(f"    {key}: {value_str}")
        
        print()
    
    if len(results) > max_records:
        print(f"  ... and {len(results) - max_records} more records")
    print()


def main() -> None:
    """Test the DuckDB text-to-SQL functionality."""
    
    parser = argparse.ArgumentParser(description="Test DuckDB text-to-SQL queries")
    parser.add_argument("query", nargs="?", help="Natural language query to test")
    parser.add_argument("--limit", type=int, default=5, help="Maximum records to show")
    args = parser.parse_args()
    
    # Configure DSPy
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    dspy.configure(lm=dspy.LM("openai/gpt-4o-mini", api_key=openai_key))
    
    try:
        generator = QueryGenerator()
        print("✅ QueryGenerator initialized successfully")
        print()
        
        if args.query:
            # Single query mode
            print(f"🔍 Query: '{args.query}'")
            print("-" * 60)
            
            try:
                sql_query = generator.generate_query(args.query)
                print(f"Generated SQL: {sql_query}")
                print()
                
                results = generator.duckdb_service.execute_query(sql_query)
                print(f"✅ Found {len(results)} results:")
                print()
                
                print_records(results, max_records=args.limit)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            # Test mode with predefined queries
            print("📋 Available tables:")
            tables = generator.duckdb_service.get_available_tables()
            for table in tables:
                print(f"  - {table}")
            print()
            
            test_queries = [
                "Show me 3 workouts with pull ups",
                "How many hero workouts are in the database?",
                "Find workouts from 2023 that include rowing",
                "What are the different workout types available?",
                "Show me strength workouts that use barbells",
            ]
            
            print("🔍 Testing predefined queries:")
            print("=" * 60)
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n{i}. Query: '{query}'")
                print("-" * 40)
                
                try:
                    sql_query = generator.generate_query(query)
                    print(f"Generated SQL: {sql_query}")
                    print()
                    
                    results = generator.duckdb_service.execute_query(sql_query)
                    print(f"✅ Found {len(results)} results:")
                    print()
                    
                    print_records(results, max_records=3)
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
            
            print("=" * 60)
            print("🎉 Testing completed! Use --help to see usage options.")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()