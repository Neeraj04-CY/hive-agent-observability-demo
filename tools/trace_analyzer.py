from typing import Any, Dict, List


class TraceAnalyzer:
    """
    Explains execution trace in human-readable form.
    """

    def explain(self, simulation: Dict[str, Any], failures: Dict[str, Any]) -> str:
        trace = simulation.get("nodes", [])
        lines: List[str] = []

        lines.append(f"Execution trace explanation (execution_id={simulation.get('execution_id')}):")
        for idx, step in enumerate(trace, start=1):
            node_id = step.get("node_id")
            status = step.get("status")
            latency = step.get("duration_ms")
            attempts = step.get("attempts")
            lines.append(
                f"{idx}. Node '{node_id}' completed with status '{status}' in {latency}ms "
                f"(attempts={attempts})."
            )

        if failures.get("warnings"):
            lines.append("Detected concerns:")
            for issue in failures["warnings"]:
                lines.append(f"- [{issue.get('severity')}] {issue.get('message')}")
        else:
            lines.append("No failure patterns detected.")

        return "\n".join(lines)