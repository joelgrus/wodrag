#!/usr/bin/env python3
"""Test script for the master agent API."""

import json
import requests
import dspy

# Configure DSPy
dspy.configure(lm=dspy.LM("openrouter/google/gemini-2.5-flash-lite", max_tokens=1000))

API_BASE = "http://localhost:8000/api/v1"

def test_agent_queries():
    """Test various queries against the master agent API."""
    
    queries = [
        {
            "question": "How many hero workouts are there in the database?",
            "verbose": False,
        },
        {
            "question": "Find workouts similar to Fran",
            "verbose": True,
        },
        {
            "question": "Generate a 15-minute AMRAP with bodyweight movements",
            "verbose": False,
        },
        {
            "question": "What are the 5 most recent workouts that include deadlifts?",
            "verbose": True,
        },
    ]
    
    print("Testing Master Agent API")
    print("=" * 50)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Question: {query['question']}")
        print(f"   Verbose: {query['verbose']}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{API_BASE}/agent/query",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success!")
                print(f"Answer: {data['data']['answer']}")
                
                if query['verbose'] and data['data'].get('reasoning_trace'):
                    print("\nReasoning Trace:")
                    for step in data['data']['reasoning_trace']:
                        print(f"  {step}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print()

def test_health():
    """Test health endpoints."""
    print("Testing Health Endpoints")
    print("=" * 30)
    
    # Basic health check
    try:
        response = requests.get(f"{API_BASE}/health/")
        if response.status_code == 200:
            print("✅ Basic health check: OK")
        else:
            print(f"❌ Basic health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic health check exception: {e}")

if __name__ == "__main__":
    print("Master Agent API Test")
    print("=" * 60)
    print("Make sure to run: uv run python scripts/run_api.py")
    print("=" * 60)
    
    test_health()
    test_agent_queries()
    
    print("\nTest completed!")
    print("\nExample API usage:")
    print(f"curl -X POST {API_BASE}/agent/query \\")
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"question": "Find workouts with pull-ups", "verbose": false}\'')