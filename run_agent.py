import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.table import Table

from agents.hive_dev_agent import HiveDevAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="HiveDevAgent CLI")
    parser.add_argument(
        "--goal",
        type=str,
        default="",
        help="User goal text. If empty, reads from examples/example_agent_goals.txt",
    )
    parser.add_argument(
        "--graph-out",
        type=str,
        default="graph_output",
        help="Output file path (without extension) for rendered graph",
    )

    args = parser.parse_args()
    console = Console()

    goal = args.goal.strip()
    if not goal:
        example_path = Path("examples/example_agent_goals.txt")
        if example_path.exists():
            goal = example_path.read_text(encoding="utf-8").strip()
        else:
            goal = "Build a reliable Hive agent workflow for developer tooling"

    console.print(Panel.fit("Running HiveDevAgent", style="bold cyan"))
    console.print(f"[bold]Goal:[/bold] {goal}\n")

    agent = HiveDevAgent()
    result = agent.run(user_goal=goal, output_graph_path=args.graph_out)

    console.print(Panel.fit("1) Interpreted Goal", style="green"))
    console.print(JSON.from_data(result.interpreted_goal))

    console.print(Panel.fit("2) Generated Graph", style="blue"))
    console.print(JSON.from_data(result.graph))

    console.print(Panel.fit("3) Graph Validation", style="magenta"))
    console.print(JSON.from_data(result.validation))

    console.print(Panel.fit("4) Execution Simulation", style="yellow"))
    console.print(JSON.from_data(result.simulation))

    console.print(Panel.fit("5) Failure Detection", style="red"))
    console.print(JSON.from_data(result.failures))

    console.print(Panel.fit("6) Execution Trace Explanation", style="cyan"))
    console.print(result.trace_explanation)

    console.print(Panel.fit("7) Optimization Suggestions", style="green"))
    suggestions_table = Table(show_header=True, header_style="bold")
    suggestions_table.add_column("Priority")
    suggestions_table.add_column("Category")
    suggestions_table.add_column("Suggestion")
    suggestions_table.add_column("Reasoning")
    for suggestion in result.optimization.get("suggestions", []):
        suggestions_table.add_row(
            str(suggestion.get("priority", "n/a")),
            str(suggestion.get("category", "n/a")),
            str(suggestion.get("suggestion", "")),
            str(suggestion.get("reasoning", "")),
        )
    console.print(suggestions_table)

    console.print(Panel.fit("8) Generated Documentation", style="white"))
    console.print(result.documentation)

    if result.graph_image_path:
        console.print(f"\n[bold green]Graph image generated:[/bold green] {result.graph_image_path}")
    if result.trace_export_path:
        console.print(f"[bold green]Execution trace exported:[/bold green] {result.trace_export_path}")


if __name__ == "__main__":
    main()