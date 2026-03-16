from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from examples.github_issue_investigator import GitHubIssueInvestigator


def main() -> None:
    print("GitHubIssueInvestigator CLI")
    issue_title = input("Issue title:\n").strip()
    issue_description = input("Description:\n").strip()
    repository_name = input("Repository:\n").strip()

    payload = {
        "issue_title": issue_title,
        "issue_description": issue_description,
        "repository": repository_name,
    }

    agent = GitHubIssueInvestigator()
    result = agent.run(
        issue_payload=payload,
        output_graph_path="demo_artifacts/github_issue_investigator_graph",
    )

    print("\nAgent run completed.")
    print(f"Issue classification: {result.issue_classification}")
    print(f"Suggested fix: {result.suggested_fix}")
    print(f"Trace path: {result.simulation.get('trace_export_path')}")
    print(f"Graph image path: {result.graph_image_path}")


if __name__ == "__main__":
    main()
