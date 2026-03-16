from __future__ import annotations

from typing import Any, Dict, List


class GoalInterpreter:
    """Interprets a free-form goal into an architect-level agent specification."""

    _TOOL_HINTS = {
        "api": "http_client",
        "web": "web_retriever",
        "document": "document_parser",
        "pdf": "document_parser",
        "database": "sql_client",
        "sql": "sql_client",
        "slack": "slack_notifier",
        "email": "email_sender",
    }

    def interpret(self, user_goal: str) -> Dict[str, Any]:
        cleaned_goal = (user_goal or "").strip()
        if not cleaned_goal:
            cleaned_goal = "Build a reliable Hive agent for developer workflows"

        goal_lower = cleaned_goal.lower()
        input_sources = self._extract_input_sources(goal_lower)
        external_tools = self._extract_external_tools(goal_lower)
        reasoning_steps = self._build_reasoning_steps(goal_lower)
        expected_output = self._derive_expected_output(goal_lower)
        failures = self._derive_failure_points(goal_lower)
        observability = self._derive_observability_requirements(goal_lower)

        return {
            "agent_name": self._derive_agent_name(cleaned_goal),
            "agent_purpose": cleaned_goal,
            "input_sources": input_sources,
            "external_tools_needed": external_tools,
            "reasoning_steps": reasoning_steps,
            "expected_output": expected_output,
            "possible_failure_points": failures,
            "observability_requirements": observability,
        }

    def _derive_agent_name(self, goal: str) -> str:
        tokens = [token for token in goal.replace("-", " ").split() if token.isalpha()]
        if not tokens:
            return "HiveWorkflowAgent"
        stem = "".join(token.capitalize() for token in tokens[:3])
        return f"{stem}Agent"

    def _extract_input_sources(self, goal_lower: str) -> List[str]:
        sources: List[str] = ["user_goal"]
        if any(word in goal_lower for word in ("api", "web", "endpoint")):
            sources.append("external_api")
        if any(word in goal_lower for word in ("document", "pdf", "knowledge base")):
            sources.append("documents")
        if any(word in goal_lower for word in ("database", "sql", "warehouse")):
            sources.append("database")
        if "trace" in goal_lower or "log" in goal_lower:
            sources.append("runtime_logs")
        return sorted(set(sources))

    def _extract_external_tools(self, goal_lower: str) -> List[str]:
        tools: List[str] = []
        for keyword, tool_name in self._TOOL_HINTS.items():
            if keyword in goal_lower:
                tools.append(tool_name)

        if "visual" in goal_lower or "graph" in goal_lower:
            tools.append("graph_visualizer")

        if "monitor" in goal_lower or "observability" in goal_lower:
            tools.append("metrics_exporter")

        return sorted(set(tools)) or ["none_required"]

    def _build_reasoning_steps(self, goal_lower: str) -> List[str]:
        steps = [
            "Interpret the developer goal and constraints",
            "Design a dependency-aware workflow graph",
            "Validate graph structure and execution order",
            "Execute or simulate the plan with reliability controls",
            "Analyze failures, latency, and quality signals",
            "Return actionable output and operational recommendations",
        ]

        if "optimiz" in goal_lower or "latency" in goal_lower:
            steps.insert(5, "Propose optimization opportunities and trade-offs")
        if "doc" in goal_lower:
            steps.append("Generate developer-facing architecture documentation")
        return steps

    def _derive_expected_output(self, goal_lower: str) -> Dict[str, Any]:
        output_format = "json_report"
        if "markdown" in goal_lower or "doc" in goal_lower:
            output_format = "markdown_and_json"

        return {
            "format": output_format,
            "artifacts": [
                "workflow_graph",
                "validation_summary",
                "execution_trace",
                "optimization_recommendations",
            ],
        }

    def _derive_failure_points(self, goal_lower: str) -> List[str]:
        risks = [
            "external tool timeout",
            "invalid dependency references",
            "unhandled node retry exhaustion",
            "observability signal gaps",
        ]
        if "api" in goal_lower:
            risks.append("third-party API rate limits")
        if "database" in goal_lower or "sql" in goal_lower:
            risks.append("database query latency spikes")
        return sorted(set(risks))

    def _derive_observability_requirements(self, goal_lower: str) -> List[str]:
        requirements = [
            "per-node start/end timestamps",
            "node status and retry counters",
            "end-to-end latency metric",
            "correlation id for each execution",
        ]
        if "cost" in goal_lower:
            requirements.append("token and tool cost breakdown")
        if "reliable" in goal_lower or "robust" in goal_lower:
            requirements.append("alerting for repeated failures")
        return sorted(set(requirements))