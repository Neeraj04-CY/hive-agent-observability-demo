from dataclasses import dataclass
from typing import Any, Dict

from core.goal_interpreter import GoalInterpreter
from core.graph_generator import GraphGenerator
from core.graph_validator import GraphValidator
from core.execution_simulator import ExecutionSimulator
from core.optimization_advisor import OptimizationAdvisor
from tools.failure_detector import FailureDetector
from tools.trace_analyzer import TraceAnalyzer
from tools.graph_visualizer import GraphVisualizer


@dataclass
class HiveDevAgentResult:
    interpreted_goal: Dict[str, Any]
    graph: Dict[str, Any]
    validation: Dict[str, Any]
    simulation: Dict[str, Any]
    failures: Dict[str, Any]
    trace_explanation: str
    optimization: Dict[str, Any]
    documentation: str
    graph_image_path: str | None
    trace_export_path: str | None


class HiveDevAgent:
    def __init__(self) -> None:
        self.goal_interpreter = GoalInterpreter()
        self.graph_generator = GraphGenerator()
        self.graph_validator = GraphValidator()
        self.execution_simulator = ExecutionSimulator()
        self.failure_detector = FailureDetector()
        self.trace_analyzer = TraceAnalyzer()
        self.optimization_advisor = OptimizationAdvisor()
        self.graph_visualizer = GraphVisualizer()

    def run(self, user_goal: str, output_graph_path: str = "graph_output") -> HiveDevAgentResult:
        interpreted_goal = self.goal_interpreter.interpret(user_goal)
        graph_bundle = self.graph_generator.generate(interpreted_goal)
        validation = self.graph_validator.validate(graph_bundle)
        simulation = self.execution_simulator.simulate(graph_bundle)
        failures = self.failure_detector.detect(graph_bundle, simulation)
        trace_explanation = self.trace_analyzer.explain(simulation, failures)
        optimization = self.optimization_advisor.suggest(graph_bundle, simulation, failures, validation)
        documentation = self._generate_documentation(
            user_goal=user_goal,
            interpreted_goal=interpreted_goal,
            graph=graph_bundle["graph_json"],
            validation=validation,
            simulation=simulation,
            failures=failures,
            optimization=optimization,
        )
        graph_image_path = self.graph_visualizer.render(graph_bundle, output_graph_path)

        return HiveDevAgentResult(
            interpreted_goal=interpreted_goal,
            graph=graph_bundle["graph_json"],
            validation=validation,
            simulation=simulation,
            failures=failures,
            trace_explanation=trace_explanation,
            optimization=optimization,
            documentation=documentation,
            graph_image_path=graph_image_path,
            trace_export_path=simulation.get("trace_export_path"),
        )

    def _generate_documentation(
        self,
        user_goal: str,
        interpreted_goal: Dict[str, Any],
        graph: Dict[str, Any],
        validation: Dict[str, Any],
        simulation: Dict[str, Any],
        failures: Dict[str, Any],
        optimization: Dict[str, Any],
    ) -> str:
        lines = []
        lines.append("# HiveDevAgent Generated Documentation")
        lines.append("")
        lines.append("## 1) Original Goal")
        lines.append(user_goal)
        lines.append("")
        lines.append("## 2) Interpreted Goal")
        lines.append(f"- Agent Name: {interpreted_goal.get('agent_name')}")
        lines.append(f"- Agent Purpose: {interpreted_goal.get('agent_purpose')}")
        lines.append(f"- Input Sources: {interpreted_goal.get('input_sources')}")
        lines.append(f"- External Tools: {interpreted_goal.get('external_tools_needed')}")
        lines.append("")
        lines.append("## 3) Generated Graph")
        lines.append(f"- Nodes: {len(graph.get('nodes', []))}")
        lines.append(f"- Edges: {len(graph.get('edges', []))}")
        lines.append(f"- Execution Order: {graph.get('execution_order', [])}")
        lines.append("")
        lines.append("## 4) Validation")
        lines.append(f"- Valid: {validation.get('is_valid')}")
        lines.append(f"- Errors: {validation.get('errors')}")
        lines.append(f"- Warnings: {validation.get('warnings')}")
        lines.append("")
        lines.append("## 5) Execution Simulation")
        lines.append(f"- Status: {simulation.get('status')}")
        lines.append(f"- Execution ID: {simulation.get('execution_id')}")
        lines.append(f"- Total duration (ms): {simulation.get('total_duration_ms')}")
        lines.append(f"- Total retries: {simulation.get('total_retries')}")
        lines.append("")
        lines.append("## 6) Failure Analysis")
        lines.append(f"- Severity: {failures.get('severity')}")
        lines.append(f"- Detected warnings: {len(failures.get('warnings', []))}")
        lines.append("")
        lines.append("## 7) Optimization Suggestions")
        for idx, suggestion in enumerate(optimization.get("suggestions", []), start=1):
            lines.append(
                f"{idx}. [{suggestion.get('priority')}] {suggestion.get('suggestion')} "
                f"({suggestion.get('reasoning')})"
            )

        return "\n".join(lines)