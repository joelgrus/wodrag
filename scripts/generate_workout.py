#!/usr/bin/env python3
"""Generate new CrossFit workouts using AI agents and the workout database."""

import os
import sys

import dspy  # type: ignore
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wodrag.agents import (
    generate_workout_from_search,
)
from wodrag.database.workout_repository import WorkoutRepository

# Load environment variables
load_dotenv()

app = typer.Typer(help="Generate CrossFit workouts using AI", no_args_is_help=True)
console = Console()


def setup_dspy_model(model: str = "openai/gpt-4o-mini") -> None:
    """Configure the DSPy language model.

    Args:
        model: Model identifier (default: openai/gpt-4o-mini)
    """
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and model.startswith("openai/"):
        console.print("❌ OPENAI_API_KEY not found in environment", style="red")
        raise typer.Exit(1)

    # Configure DSPy with the model
    dspy.configure(
        lm=dspy.LM(model, api_key=api_key, temperature=0.7),
        cache=False,  # Disable caching for variety
    )


@app.command(name="generate", help="Generate a workout from a description")
def generate(
    description: str = typer.Argument(
        ...,
        help="Description of workout to generate (e.g., 'upper body with cardio')",
    ),
    search_limit: int = typer.Option(
        10, "--limit", "-l", help="Number of similar workouts to find for inspiration"
    ),
    hybrid: bool = typer.Option(
        True,
        "--hybrid/--semantic",
        help="Use hybrid search (BM25 + semantic) vs semantic only",
    ),
    model: str = typer.Option(
        "openai/gpt-4o-mini", "--model", "-m", help="DSPy model to use for generation"
    ),
    show_examples: bool = typer.Option(
        False,
        "--show-examples",
        "-e",
        help="Show the example workouts used for inspiration",
    ),
) -> None:
    """Generate a new CrossFit workout based on a description.

    This command searches the database for similar workouts and uses them
    as inspiration to generate a new, unique workout that matches your description.
    """
    console.print(f"\n🏋️  Generating workout: [cyan]{description}[/cyan]\n")

    try:
        # Setup DSPy
        setup_dspy_model(model)

        # Create repository
        repository = WorkoutRepository()

        # Search and generate
        console.print(
            f"🔍 Searching for {search_limit} similar workouts...", style="yellow"
        )

        result = generate_workout_from_search(
            description=description,
            repository=repository,
            search_limit=search_limit,
            use_hybrid=hybrid,
        )

        # Display the generated workout
        console.print("\n✨ [bold green]Generated Workout[/bold green]\n")

        # Display workout in a nice panel with the name as title
        panel = Panel(
            result.workout,
            title=f"[bold]{result.name}[/bold]",
            border_style="green",
            expand=False,
            padding=(1, 2),
        )
        console.print(panel)

        # Show similar workouts if requested
        if show_examples and result.search_results:
            console.print("\n📚 [bold]Workouts Used for Inspiration:[/bold]\n")

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Date", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Summary")
            table.add_column("Score", justify="right", style="yellow")

            for search_result in result.search_results[:5]:  # Show top 5
                workout = search_result.workout
                score = (
                    f"{search_result.hybrid_score:.3f}"
                    if search_result.hybrid_score
                    else (
                        f"{search_result.similarity_score:.3f}"
                        if search_result.similarity_score
                        else "N/A"
                    )
                )

                table.add_row(
                    workout.date,
                    workout.workout_name or "-",
                    workout.one_sentence_summary[:60] + "..."
                    if workout.one_sentence_summary
                    and len(workout.one_sentence_summary) > 60
                    else workout.one_sentence_summary or "-",
                    score,
                )

            console.print(table)

        console.print("\n✅ [green]Workout generated successfully![/green]\n")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1) from e


@app.command()
def batch(
    descriptions_file: str = typer.Argument(
        ..., help="Path to file with workout descriptions (one per line)"
    ),
    output_file: str = typer.Option(
        "generated_workouts.txt",
        "--output",
        "-o",
        help="Output file for generated workouts",
    ),
    search_limit: int = typer.Option(
        10, "--limit", "-l", help="Number of similar workouts to find for each"
    ),
    model: str = typer.Option(
        "openai/gpt-4o-mini", "--model", "-m", help="DSPy model to use"
    ),
) -> None:
    """Generate multiple workouts from a file of descriptions."""

    # Read descriptions
    try:
        with open(descriptions_file) as f:
            descriptions = [line.strip() for line in f if line.strip()]
    except FileNotFoundError as e:
        console.print(f"❌ File not found: {descriptions_file}", style="red")
        raise typer.Exit(1) from e

    console.print(f"📋 Found {len(descriptions)} workout descriptions\n")

    # Setup DSPy
    setup_dspy_model(model)

    # Create repository
    repository = WorkoutRepository()

    # Generate workouts
    generated_workouts = []

    for i, desc in enumerate(descriptions, 1):
        console.print(
            f"[{i}/{len(descriptions)}] Generating: {desc[:50]}...", style="cyan"
        )

        try:
            result = generate_workout_from_search(
                description=desc,
                repository=repository,
                search_limit=search_limit,
                use_hybrid=True,
            )

            generated_workouts.append(
                {"description": desc, "name": result.name, "workout": result.workout}
            )

            console.print(f"    ✓ Generated: {result.name}", style="green")

        except Exception as e:
            console.print(f"    ✗ Failed: {e}", style="red")
            generated_workouts.append(
                {"description": desc, "name": None, "workout": f"ERROR: {e}"}
            )

    # Save to file
    with open(output_file, "w") as f:
        for item in generated_workouts:
            f.write(f"DESCRIPTION: {item['description']}\n")
            if item["name"]:
                f.write(f"NAME: {item['name']}\n")
            f.write(f"WORKOUT:\n{item['workout']}\n")
            f.write("-" * 80 + "\n\n")

    console.print(
        f"\n✅ Generated {len(generated_workouts)} workouts → {output_file}",
        style="green",
    )


@app.command()
def interactive() -> None:
    """Interactive workout generation mode."""
    console.print("\n🏋️  [bold cyan]Interactive Workout Generator[/bold cyan]\n")
    console.print("Enter workout descriptions and get AI-generated workouts.")
    console.print("Type 'quit' or 'exit' to stop.\n")

    # Setup
    setup_dspy_model()
    repository = WorkoutRepository()

    while True:
        try:
            # Get description from user
            description = typer.prompt("\n💭 Describe your workout")

            if description.lower() in ["quit", "exit"]:
                console.print("\n👋 Goodbye!", style="cyan")
                break

            # Generate workout
            console.print("\n⚡ Generating...", style="yellow")

            result = generate_workout_from_search(
                description=description,
                repository=repository,
                search_limit=10,
                use_hybrid=True,
            )

            # Display result
            console.print("\n" + "=" * 60)
            console.print(f"[bold cyan]{result.name}[/bold cyan]\n")
            console.print(result.workout)
            console.print("=" * 60)

        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!", style="cyan")
            break
        except Exception as e:
            console.print(f"\n❌ Error: {e}", style="red")


if __name__ == "__main__":
    app()
