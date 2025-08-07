"""Master ReAct agent using DSPy's built-in ReAct implementation."""

import dspy

from wodrag.agents.text_to_sql import QueryGenerator
from wodrag.agents.workout_generator import WorkoutSearchGenerator
from wodrag.database.duckdb_client import DuckDBQueryService
from wodrag.database.workout_repository import WorkoutRepository


class MasterAgent(dspy.Module):
    """Master agent for workout queries using DSPy ReAct."""
    
    def __init__(
        self,
        workout_repo: WorkoutRepository,
        query_generator: QueryGenerator,
        duckdb_service: DuckDBQueryService,
        workout_generator: WorkoutSearchGenerator,
    ):
        super().__init__()
        
        # Store injected dependencies
        self.workout_repo = workout_repo
        self.query_generator = query_generator
        self.duckdb_service = duckdb_service
        self.workout_generator = workout_generator
        
        # Create tool functions that use the injected services
        def search_workouts(query: str) -> str:
            """Search for CrossFit workouts."""
            results = self.workout_repo.hybrid_search(query_text=query, limit=10)
            
            if not results:
                return "No workouts found."
            
            output = []
            for i, result in enumerate(results, 1):
                w = result.workout
                output.append(
                    f"{i}. {w.workout_name or 'Workout'} ({w.date}): "
                    f"{w.one_sentence_summary or (w.workout[:100] if w.workout else '')}"
                )
            return "\n".join(output)
        
        def query_database(question: str) -> str:
            """Answer questions about workouts using SQL."""
            sql = self.query_generator.generate_query(question)
            results = self.duckdb_service.execute_query(sql)
            
            if not results:
                return "No results found."
            
            # Format results
            if len(results) == 1 and len(results[0]) == 1:
                key = list(results[0].keys())[0]
                return f"{key}: {results[0][key]}"
            
            output = []
            for row in results[:10]:
                output.append(str(row))
            
            if len(results) > 10:
                output.append(f"... and {len(results) - 10} more rows")
            
            return "\n".join(output)
        
        def generate_workout(description: str) -> str:
            """Generate a new CrossFit workout."""
            result = self.workout_generator(description=description)
            return f"Workout: {result.workout_name}\n\n{result.generated_workout}"
        
        # Define tools using the closures
        self.tools = [
            dspy.Tool(
                name="search",
                desc=("Hybrid search for workouts. Input: search query. "
                      "This uses semantic similarity on one-sentence summaries "
                      "and so is suited for finding which workouts are similar to a given description."),
                func=search_workouts
            ),
            dspy.Tool(
                name="query",
                desc=("Answer data questions. Input: natural language question. "
                      "This uses a text-to-SQL generator to convert the question into SQL"
                      "and queries the DuckDB database. It is suited for answering SQL-like questions "
                      "involve (for example) aggregation, filtering, and/or ordering."),
                func=query_database
            ),
            dspy.Tool(
                name="generate",
                desc="Generate a workout. Input: workout description",
                func=generate_workout
            ),
        ]
        
        # Use DSPy's ReAct with verbose output
        self.react = dspy.ReAct(
            signature="question -> answer",
            tools=self.tools,
            max_iters=5
        )
    
    def forward(self, question: str, verbose: bool = False) -> str:
        """Answer a question using ReAct."""
        if verbose:
            # Enable DSPy's built-in verbose mode
            with dspy.context(show_guidelines=True):
                result = self.react(question=question)
        else:
            result = self.react(question=question)
        return result.answer
    
    def forward_verbose(self, question: str) -> tuple[str, list[str]]:
        """Answer a question using ReAct and return the reasoning trace."""
        # Custom implementation to capture the ReAct steps
        trace = []
        
        # Monkey-patch the tool functions to capture their calls
        original_tools = self.tools.copy()
        
        def wrap_tool(tool):
            original_func = tool.func
            def wrapped_func(*args, **kwargs):
                input_str = f"{args[0] if args else kwargs}"
                trace.append(f"ACTION: {tool.name}({input_str})")
                result = original_func(*args, **kwargs)
                trace.append(f"OBSERVATION: {result[:200]}{'...' if len(result) > 200 else ''}")
                return result
            return dspy.Tool(name=tool.name, desc=tool.desc, func=wrapped_func)
        
        # Create wrapped tools
        wrapped_tools = [wrap_tool(tool) for tool in self.tools]
        
        # Temporarily replace tools
        react_with_trace = dspy.ReAct(
            signature="question -> answer",
            tools=wrapped_tools,
            max_iters=5
        )
        
        result = react_with_trace(question=question)
        
        return result.answer, trace


if __name__ == "__main__":
    # Configure DSPy with verbose logging
    # import logging
    # logging.basicConfig(level=logging.INFO)
    
    dspy.configure(lm=dspy.LM("openrouter/google/gemini-2.5-flash-lite", max_tokens=10000))
    
    # Optional: Enable DSPy's inspection mode
    dspy.settings.configure(show_guidelines=True)
    
    # Initialize services once
    workout_repo = WorkoutRepository()
    query_generator = QueryGenerator()
    duckdb_service = DuckDBQueryService()
    workout_generator = WorkoutSearchGenerator()
    
    # Create agent with injected dependencies
    agent = MasterAgent(
        workout_repo=workout_repo,
        query_generator=query_generator,
        duckdb_service=duckdb_service,
        workout_generator=workout_generator
    )
    
    # # Example questions
    # questions = [
    #     # "How many hero workouts are there?",
    #     # "Find workouts similar to Fran",
    #     # "Generate a 20-minute AMRAP",
    #     "What is the most recent workout that involves deadlifts?"
    # ]
    
    # for q in questions:
    #     print(f"\nQ: {q}")
    #     print("=" * 50)
        
    #     # Method 1: Use built-in verbose mode
    #     answer = agent(question=q, verbose=True)
    #     print(f"A: {answer}\n")
        
    #     # Method 2: Use custom trace mode (uncomment to see)
    #     # answer, trace = agent.forward_verbose(q)
    #     # print("REASONING TRACE:")
    #     # for step in trace:
    #     #     print(f"  {step}")
    #     # print(f"\nFINAL ANSWER: {answer}\n")
    while True:
        try:
            question = input("Ask a question (or 'exit' to quit): ")
            if question.lower() == 'exit':
                break
            
            # Use the agent to answer the question
            answer = agent(question=question, verbose=True)
            print(f"Answer: {answer}\n")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")