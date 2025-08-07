#!/usr/bin/env python3
"""Test script for conversation-enabled API."""

import requests
import json
import time
from typing import Optional


class ConversationTester:
    """Helper class for testing conversation API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id: Optional[str] = None
    
    def query_agent(self, question: str, verbose: bool = False) -> dict:
        """Send a query to the agent."""
        url = f"{self.base_url}/api/v1/agent/query"
        payload = {
            "question": question,
            "verbose": verbose
        }
        
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if data["success"] and not self.conversation_id:
            # Store conversation ID from first response
            self.conversation_id = data["data"]["conversation_id"]
        
        return data
    
    def start_new_conversation(self) -> None:
        """Start a new conversation."""
        self.conversation_id = None
    
    def print_response(self, data: dict) -> None:
        """Pretty print API response."""
        if data["success"]:
            response_data = data["data"]
            print(f"Q: {response_data['question']}")
            print(f"A: {response_data['answer']}")
            print(f"Conversation ID: {response_data['conversation_id']}")
            
            if response_data.get("reasoning_trace"):
                print("\nReasoning Trace:")
                for step in response_data["reasoning_trace"]:
                    print(f"  {step}")
            
            print("-" * 80)
        else:
            print(f"ERROR: {data['error']}")


def test_conversation_flow():
    """Test a complete conversation flow."""
    print("Testing Conversation Flow")
    print("=" * 80)
    
    tester = ConversationTester()
    
    try:
        # Test 1: Simple question
        print("Test 1: Ask about Fran")
        response = tester.query_agent("What is Fran?")
        tester.print_response(response)
        
        # Test 2: Follow-up question (should use context)
        print("Test 2: Follow-up question")
        response = tester.query_agent("What movements does it have?")
        tester.print_response(response)
        
        # Test 3: Another follow-up
        print("Test 3: Another follow-up")
        response = tester.query_agent("How many reps?")
        tester.print_response(response)
        
        # Test 4: Verbose mode with context
        print("Test 4: Verbose mode")
        response = tester.query_agent("Make it easier for beginners", verbose=True)
        tester.print_response(response)
        
        print("✅ All tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running:")
        print("   uv run python scripts/run_api.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_multiple_conversations():
    """Test multiple separate conversations."""
    print("\nTesting Multiple Conversations")
    print("=" * 80)
    
    try:
        # Conversation 1
        tester1 = ConversationTester()
        print("Conversation 1 - About Fran")
        response = tester1.query_agent("What is Fran?")
        tester1.print_response(response)
        conv1_id = response["data"]["conversation_id"]
        
        # Conversation 2
        tester2 = ConversationTester()
        print("Conversation 2 - About Murph")
        response = tester2.query_agent("What is Murph?")
        tester2.print_response(response)
        conv2_id = response["data"]["conversation_id"]
        
        # Verify different conversation IDs
        assert conv1_id != conv2_id
        print(f"✅ Conversations have different IDs: {conv1_id[:8]}... vs {conv2_id[:8]}...")
        
        # Continue conversation 1
        print("Continuing Conversation 1")
        response = tester1.query_agent("How long does it typically take?")
        tester1.print_response(response)
        assert response["data"]["conversation_id"] == conv1_id
        
        # Continue conversation 2
        print("Continuing Conversation 2")
        response = tester2.query_agent("What equipment is needed?")
        tester2.print_response(response)
        assert response["data"]["conversation_id"] == conv2_id
        
        print("✅ Multiple conversations test passed!")
        
    except Exception as e:
        print(f"❌ Multiple conversations test failed: {e}")


def test_conversation_context():
    """Test that conversation context is properly used."""
    print("\nTesting Conversation Context")
    print("=" * 80)
    
    try:
        tester = ConversationTester()
        
        # Establish context about a specific workout
        print("Setting up context...")
        response = tester.query_agent("I want to do a workout with burpees and pull-ups")
        tester.print_response(response)
        
        # Reference should work with context
        print("Testing context reference...")
        response = tester.query_agent("Make that workout shorter")
        tester.print_response(response)
        
        # Another reference
        print("Another context reference...")
        response = tester.query_agent("What if I can't do pull-ups?")
        tester.print_response(response)
        
        print("✅ Context reference test passed!")
        
    except Exception as e:
        print(f"❌ Context reference test failed: {e}")


if __name__ == "__main__":
    print("🤖 Conversation API Test Suite")
    print("=" * 80)
    print("Make sure to start the API server first:")
    print("  uv run python scripts/run_api.py")
    print()
    
    # Run tests
    test_conversation_flow()
    test_multiple_conversations()
    test_conversation_context()
    
    print("\n🎉 All tests completed!")
    print("\nTo test interactively, run:")
    print("  python -c \"from scripts.test_conversation_api import ConversationTester; t = ConversationTester(); t.query_agent('What is Fran?')\"")