from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict

try:
    from core.execution_simulator import ExecutionSimulator
    from core.graph_generator import GraphGenerator
    from core.graph_validator import GraphValidator
    from core.optimization_advisor import OptimizationAdvisor
    from tools.failure_detector import FailureDetector
    from tools.graph_visualizer import GraphVisualizer
    from tools.trace_analyzer import TraceAnalyzer
except ModuleNotFoundError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.execution_simulator import ExecutionSimulator
    from core.graph_generator import GraphGenerator
    from core.graph_validator import GraphValidator
    from core.optimization_advisor import OptimizationAdvisor
    from tools.failure_detector import FailureDetector
    from tools.graph_visualizer import GraphVisualizer
    from tools.trace_analyzer import TraceAnalyzer


@dataclass
class GitHubIssueInvestigatorResult:
    issue_payload: Dict[str, str]
    issue_classification: str
    suggested_fix: str
    graph: Dict[str, Any]
    validation: Dict[str, Any]
    simulation: Dict[str, Any]
    failures: Dict[str, Any]
    trace_explanation: str
    optimization: Dict[str, Any]
    graph_image_path: str | None


class GitHubIssueInvestigator:
    """Example Hive agent workflow for investigating GitHub issues."""

    def __init__(self) -> None:
        self.graph_generator = GraphGenerator()
        self.graph_validator = GraphValidator()
        self.execution_simulator = ExecutionSimulator()
        self.failure_detector = FailureDetector()
        self.trace_analyzer = TraceAnalyzer()
        self.optimization_advisor = OptimizationAdvisor()
        self.graph_visualizer = GraphVisualizer()

    def build_spec(self, issue_payload: Dict[str, str]) -> Dict[str, Any]:
        return {
            "agent_name": "GitHubIssueInvestigator",
            "agent_purpose": "Analyze a GitHub issue and suggest a likely fix path.",
            "input_sources": ["issue_title", "issue_description", "repository_context"],
            "external_tools_needed": ["repository_search_tool"],
            "reasoning_steps": [
                "Capture issue details",
                "Summarize and extract key technical signals",
                "Classify issue type",
                "Scan repository for related files",
                "Propose a fix or recommended action",
                "Aggregate findings into final output",
            ],
            "expected_output": {
                "format": "json_report",
                "artifacts": ["issue_analysis", "classification", "candidate_fix", "final_summary"],
            },
            "possible_failure_points": [
                "misclassification of issue type",
                "repository scan misses relevant files",
                "ambiguous fix recommendation",
            ],
            "observability_requirements": [
                "node-level latency and status",
                "classification confidence",
                "trace correlation id",
            ],
            "workflow_blueprint": [
                {
                    "node_id": "issue_input",
                    "node_type": "memory",
                    "description": "Issue Input Node: accepts issue title and description",
                    "inputs": ["issue_title", "issue_description"],
                    "outputs": ["issue_payload"],
                    "dependencies": [],
                    "retry_policy": {"max_retries": 0, "backoff": "none"},
                    "timeout": 3,
                },
                {
                    "node_id": "issue_understanding",
                    "node_type": "llm",
                    "description": "Issue Understanding Node (LLM): summarizes the issue and extracts key signals",
                    "inputs": ["issue_payload"],
                    "outputs": ["issue_summary", "key_signals"],
                    "dependencies": ["issue_input"],
                    "retry_policy": {"max_retries": 1, "backoff": "linear"},
                    "timeout": 18,
                },
                {
                    "node_id": "issue_classification",
                    "node_type": "decision",
                    "description": "Issue Classification Node (Decision): classify as bug, feature request, documentation, or question",
                    "inputs": ["issue_summary", "key_signals"],
                    "outputs": ["issue_type"],
                    "dependencies": ["issue_understanding"],
                    "retry_policy": {"max_retries": 0, "backoff": "none"},
                    "timeout": 6,
                },
                {
                    "node_id": "repository_scan",
                    "node_type": "tool",
                    "description": "Repository Scan Tool: simulate searching the repository for related files",
                    "inputs": ["issue_type", "key_signals"],
                    "outputs": ["related_files", "related_changes"],
                    "dependencies": ["issue_classification"],
                    "retry_policy": {"max_retries": 2, "backoff": "exponential"},
                    "timeout": 12,
                },
                {
                    "node_id": "fix_suggestion",
                    "node_type": "llm",
                    "description": "Fix Suggestion Node (LLM): propose a potential fix or action",
                    "inputs": ["issue_summary", "issue_type", "related_files", "related_changes"],
                    "outputs": ["suggested_fix", "confidence"],
                    "dependencies": ["repository_scan"],
                    "retry_policy": {"max_retries": 1, "backoff": "linear"},
                    "timeout": 20,
                },
                {
                    "node_id": "result_aggregator",
                    "node_type": "aggregator",
                    "description": "Result Aggregator: compile final analysis",
                    "inputs": ["issue_summary", "issue_type", "suggested_fix", "confidence"],
                    "outputs": ["final_analysis"],
                    "dependencies": ["fix_suggestion"],
                    "retry_policy": {"max_retries": 1, "backoff": "linear"},
                    "timeout": 8,
                },
            ],
        }

    def run(
        self,
        issue_payload: Dict[str, str],
        output_graph_path: str = "demo_artifacts/github_issue_investigator_graph",
    ) -> GitHubIssueInvestigatorResult:
        spec = self.build_spec(issue_payload)
        graph_bundle = self.graph_generator.generate(spec)
        validation = self.graph_validator.validate(graph_bundle)
        simulation = self.execution_simulator.simulate(graph_bundle)
        failures = self.failure_detector.detect(graph_bundle, simulation)
        trace_explanation = self.trace_analyzer.explain(simulation, failures)
        optimization = self.optimization_advisor.suggest(graph_bundle, simulation, failures, validation)
        graph_image_path = self.graph_visualizer.render(graph_bundle, output_graph_path)
        issue_classification = self._classify_issue(issue_payload)
        suggested_fix = self._suggest_fix(issue_payload, issue_classification)

        return GitHubIssueInvestigatorResult(
            issue_payload=issue_payload,
            issue_classification=issue_classification,
            suggested_fix=suggested_fix,
            graph=graph_bundle["graph_json"],
            validation=validation,
            simulation=simulation,
            failures=failures,
            trace_explanation=trace_explanation,
            optimization=optimization,
            graph_image_path=graph_image_path,
        )

    def _classify_issue(self, issue_payload: Dict[str, str]) -> str:
        text = (
            f"{issue_payload.get('issue_title', '')} "
            f"{issue_payload.get('issue_description', '')}"
        ).lower()
        if any(token in text for token in ("error", "exception", "fail", "500", "crash", "bug")):
            return "bug"
        if any(token in text for token in ("feature", "enhancement", "add support", "request")):
            return "feature request"
        if any(token in text for token in ("docs", "documentation", "readme", "guide")):
            return "documentation"
        return "question"

    def _suggest_fix(self, issue_payload: Dict[str, str], issue_classification: str) -> str:
        repository = issue_payload.get("repository", "target-repo")
        if issue_classification == "bug":
            return (
                "Reproduce the failure with the latest dependency lockfile, inspect recent "
                f"auth-related changes in {repository}, and add a regression test for the endpoint."
            )
        if issue_classification == "feature request":
            return (
                "Create an RFC-style implementation plan with API contract changes, estimate effort, "
                "and ship behind a feature flag."
            )
        if issue_classification == "documentation":
            return (
                "Update docs with a minimal repro and expected behavior, then add a docs lint check in CI."
            )
        return (
            "Request additional reproduction details and environment info, then triage to the responsible "
            "maintainer group."
        )


if __name__ == "__main__":
    result = GitHubIssueInvestigator().run(
        {
            "issue_title": "Login endpoint returns 500 after dependency update",
            "issue_description": "After upgrading dependencies, login requests fail with status 500.",
            "repository": "my-org/backend-api",
        }
    )
    print("GitHubIssueInvestigator finished.")
    print(f"Classification: {result.issue_classification}")
    print(f"Suggested fix: {result.suggested_fix}")
    print(f"Graph nodes: {len(result.graph.get('nodes', []))}")
    print(f"Trace export: {result.simulation.get('trace_export_path')}")
    print(f"Graph image: {result.graph_image_path}")
