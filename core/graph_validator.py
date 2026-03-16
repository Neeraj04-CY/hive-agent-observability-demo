from __future__ import annotations

from typing import Any, Dict, List

import networkx as nx


class GraphValidator:
    """Validates graph schema and topological correctness for execution readiness."""

    _REQUIRED_FIELDS = {
        "node_id",
        "node_type",
        "description",
        "inputs",
        "outputs",
        "dependencies",
        "retry_policy",
        "timeout",
    }

    def validate(self, graph_bundle: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        graph_nx = graph_bundle.get("graph_nx")
        graph_json = graph_bundle.get("graph_json", {})
        nodes = graph_json.get("nodes", [])

        if graph_nx is None or not isinstance(graph_nx, nx.DiGraph):
            errors.append("graph_nx is missing or invalid.")
            graph_nx = nx.DiGraph()

        node_ids = [node.get("node_id") for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Duplicate node_id values detected.")

        for node in nodes:
            missing_fields = sorted(self._REQUIRED_FIELDS - set(node.keys()))
            if missing_fields:
                errors.append(
                    f"Node '{node.get('node_id', 'unknown')}' is missing fields: {missing_fields}."
                )

            if not isinstance(node.get("dependencies", []), list):
                errors.append(f"Node '{node.get('node_id')}' dependencies must be a list.")

            timeout = node.get("timeout")
            if not isinstance(timeout, int) or timeout <= 0:
                errors.append(f"Node '{node.get('node_id')}' timeout must be a positive integer.")

            retry_policy = node.get("retry_policy", {})
            if not isinstance(retry_policy, dict) or "max_retries" not in retry_policy:
                errors.append(
                    f"Node '{node.get('node_id')}' retry_policy must include max_retries."
                )

        if graph_nx.number_of_nodes() == 0:
            errors.append("Graph has no nodes.")

        if graph_nx.number_of_edges() < max(0, graph_nx.number_of_nodes() - 1):
            warnings.append("Graph may be under-connected for sequential execution.")

        if not nx.is_directed_acyclic_graph(graph_nx):
            errors.append("Circular dependency detected in graph.")

        execution_order: List[str] = []
        if not errors:
            try:
                execution_order = list(nx.topological_sort(graph_nx))
            except nx.NetworkXUnfeasible:
                errors.append("Execution order cannot be determined.")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "execution_order": execution_order,
        }