#!/usr/bin/env python3
"""Interactive conversation CLI for testing the agent."""

import sys

import requests


class InteractiveConversationTester:
    """Interactive CLI for testing conversation functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id: str | None = None
        self.message_count = 0

    def query_agent(self, question: str, verbose: bool = False) -> dict:
        """Send a query to the agent."""
        url = f"{self.base_url}/api/v1/agent/query"
        payload = {
            "question": question,
            "verbose": verbose
        }

        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data["success"] and not self.conversation_id:
                # Store conversation ID from first response
                self.conversation_id = data["data"]["conversation_id"]
                print(f"🆕 Started new conversation: {self.conversation_id[:8]}...")  # noqa: T201

            return data

        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to API server.")
            print("   Make sure the server is running: uv run python scripts/run_api.py")
            return {"success": False, "error": "Connection failed"}
        except requests.exceptions.Timeout:
            print("❌ Request timed out. The agent might be taking too long to respond.")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {"success": False, "error": str(e)}

    def print_response(self, data: dict, show_details: bool = False) -> None:
        """Pretty print API response."""
        if data["success"]:
            response_data = data["data"]
            self.message_count += 1

            print(f"\n💬 Message {self.message_count}")
            print("─" * 60)
            print(f"🧑 You: {response_data['question']}")
            print(f"🤖 Agent: {response_data['answer']}")

            if show_details:
                print("\n📋 Details:")
                print(f"   Conversation ID: {response_data['conversation_id']}")
                print(f"   Verbose mode: {response_data['verbose']}")

            if response_data.get("reasoning_trace"):
                print("\n🧠 Reasoning Trace:")
                for i, step in enumerate(response_data["reasoning_trace"], 1):
                    print(f"   {i}. {step}")

        else:
            print(f"\n❌ Error: {data.get('error', 'Unknown error')}")

    def new_conversation(self) -> None:
        """Start a new conversation."""
        if self.conversation_id:
            print(f"🔄 Starting new conversation (was: {self.conversation_id[:8]}...)")
        self.conversation_id = None
        self.message_count = 0

    def show_help(self) -> None:
        """Show help information."""
        help_text = """
🤖 Interactive Conversation Tester

Commands:
  Just type your question and press Enter to chat with the agent
  
Special Commands:
  /help     - Show this help message
  /new      - Start a new conversation
  /verbose  - Toggle verbose mode (show reasoning trace)
  /details  - Toggle showing conversation details
  /quit     - Exit the program
  
Tips:
  • Try follow-up questions like "What movements does it have?"
  • Test context with "Make that workout easier"
  • Ask about specific workouts: "What is Fran?" then "How long does it take?"
  • The agent will remember the conversation context across messages
"""
        print(help_text)

    def run(self) -> None:
        """Run the interactive conversation loop."""
        print("🤖 Interactive Conversation Tester")
        print("=" * 60)
        print("Type your questions to chat with the agent.")
        print("Use /help for commands, /quit to exit.")
        print("\nMake sure the API server is running:")
        print("  uv run python scripts/run_api.py")
        print("=" * 60)

        verbose_mode = False
        show_details = False

        while True:
            try:
                # Get user input
                if self.conversation_id:
                    prompt = f"💬 [{self.conversation_id[:8]}...] > "
                else:
                    prompt = "💬 [new] > "

                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.startswith('/'):
                    command = user_input.lower()

                    if command == '/help':
                        self.show_help()
                    elif command == '/new':
                        self.new_conversation()
                        print("🔄 Ready for new conversation!")
                    elif command == '/verbose':
                        verbose_mode = not verbose_mode
                        print(f"🧠 Verbose mode: {'ON' if verbose_mode else 'OFF'}")
                    elif command == '/details':
                        show_details = not show_details
                        print(f"📋 Details mode: {'ON' if show_details else 'OFF'}")
                    elif command in ['/quit', '/exit', '/q']:
                        print("👋 Goodbye!")
                        break
                    else:
                        print(f"❓ Unknown command: {user_input}")
                        print("   Type /help for available commands")
                    continue

                # Send question to agent
                print("🤔 Thinking...")
                response = self.query_agent(user_input, verbose=verbose_mode)

                # Print response
                self.print_response(response, show_details=show_details)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Continuing...")


def main():
    """Main entry point."""
    # Check for custom URL
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        print(f"Using custom API URL: {base_url}")

    # Create and run the tester
    tester = InteractiveConversationTester(base_url)
    tester.run()


if __name__ == "__main__":
    main()
