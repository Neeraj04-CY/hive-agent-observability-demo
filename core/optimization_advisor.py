from __future__ import annotations

from typing import Any, Dict, List

import networkx as nx


class OptimizationAdvisor:
    """Analyzes graph + execution trace and proposes concrete optimization actions."""

    def suggest(
        self,
        graph_bundle: Dict[str, Any],
        execution_trace: Dict[str, Any],
        failures: Dict[str, Any],
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        graph_nx = graph_bundle.get("graph_nx")
        if graph_nx is None or not isinstance(graph_nx, nx.DiGraph):
            raise ValueError("OptimizationAdvisor expected graph_bundle['graph_nx'] as nx.DiGraph.")

        suggestions: List[Dict[str, Any]] = []
        trace_nodes = execution_trace.get("nodes", [])

        if validation.get("is_valid"):
            parallel_pairs = [
                node for node in graph_nx.nodes() if graph_nx.in_degree(node) == 1 and graph_nx.out_degree(node) == 0
            ]
            if len(parallel_pairs) >= 2:
                suggestions.append(
                    self._suggestion(
                        category="parallelization",
                        suggestion="Parallelize independent leaf nodes to reduce critical path time.",
                        reasoning="Multiple nodes have no downstream dependencies and can run concurrently.",
                        priority="high",
                    )
                )

        llm_nodes = [
            node for node, data in graph_nx.nodes(data=True) if data.get("node_type") == "llm"
        ]
        if len(llm_nodes) >= 1:
            suggestions.append(
                self._suggestion(
                    category="caching",
                    suggestion="Cache repeated LLM prompts and deterministic planner outputs.",
                    reasoning="LLM nodes are latency and cost heavy; caching reduces both.",
                    priority="high",
                )
            )

        retry_gaps = [
            warning for warning in failures.get("warnings", []) if warning.get("category") == "missing_retry_logic"
        ]
        if retry_gaps:
            suggestions.append(
                self._suggestion(
                    category="retries",
                    suggestion="Add retries with exponential backoff to transient-failure nodes.",
                    reasoning="Failure analysis found nodes without retry coverage.",
                    priority="high",
                )
            )

        total_duration_ms = execution_trace.get("total_duration_ms", 0)
        if total_duration_ms > 1800:
            suggestions.append(
                self._suggestion(
                    category="latency",
                    suggestion="Reduce node timeout ceilings and move tool calls behind decision gates.",
                    reasoning="Execution duration exceeds expected interactive threshold.",
                    priority="medium",
                )
            )

        suggestions.append(
            self._suggestion(
                category="observability",
                suggestion="Emit metrics for node duration, retries, and failure categories.",
                reasoning="Improved telemetry enables targeted reliability improvements over time.",
                priority="high",
            )
        )

        suggestions.append(
            self._suggestion(
                category="observability",
                suggestion="Attach execution_id and node_id correlation tags to every event.",
                reasoning="Trace correlation simplifies debugging multi-node workflows.",
                priority="medium",
            )
        )

        return {"suggestions": suggestions}

    def _suggestion(
        self,
        category: str,
        suggestion: str,
        reasoning: str,
        priority: str,
    ) -> Dict[str, Any]:
        return {
            "category": category,
            "suggestion": suggestion,
            "reasoning": reasoning,
            "priority": priority,
        }