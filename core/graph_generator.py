from __future__ import annotations

from typing import Any, Dict, List, Set

import networkx as nx


class GraphGenerator:
    """Builds a dependency-aware workflow DAG from an interpreted agent specification."""

    _ALLOWED_TYPES = {"llm", "tool", "memory", "decision", "aggregator"}

    def generate(self, interpreted_goal: Dict[str, Any]) -> Dict[str, Any]:
        nodes = self._build_nodes(interpreted_goal)
        graph_nx = nx.DiGraph()

        for node in nodes:
            graph_nx.add_node(node["node_id"], **node)

        for node in nodes:
            for dependency in node["dependencies"]:
                graph_nx.add_edge(dependency, node["node_id"])

        generator_validation = self._validate(graph_nx, nodes)
        execution_order = (
            list(nx.topological_sort(graph_nx)) if generator_validation["is_valid"] else []
        )

        graph_json = {
            "nodes": nodes,
            "edges": [
                {"source": source, "target": target} for source, target in graph_nx.edges()
            ],
            "execution_order": execution_order,
            "metadata": {
                "agent_name": interpreted_goal.get("agent_name", "HiveWorkflowAgent"),
                "agent_purpose": interpreted_goal.get("agent_purpose", ""),
            },
        }

        return {
            "graph_nx": graph_nx,
            "graph_json": graph_json,
            "generator_validation": generator_validation,
        }

    def _build_nodes(self, interpreted_goal: Dict[str, Any]) -> List[Dict[str, Any]]:
        custom_nodes = interpreted_goal.get("workflow_blueprint")
        if isinstance(custom_nodes, list) and custom_nodes:
            return self._build_nodes_from_blueprint(custom_nodes)

        input_sources = interpreted_goal.get("input_sources", ["user_goal"])
        external_tools = interpreted_goal.get("external_tools_needed", [])

        nodes: List[Dict[str, Any]] = [
            self._node(
                node_id="goal_context",
                node_type="memory",
                description="Load user goal and context signals",
                inputs=input_sources,
                outputs=["normalized_goal"],
                dependencies=[],
                retry_policy={"max_retries": 0, "backoff": "none"},
                timeout=3,
            ),
            self._node(
                node_id="planner_llm",
                node_type="llm",
                description="Create structured execution plan",
                inputs=["normalized_goal"],
                outputs=["execution_plan"],
                dependencies=["goal_context"],
                retry_policy={"max_retries": 1, "backoff": "linear"},
                timeout=18,
            ),
            self._node(
                node_id="route_decision",
                node_type="decision",
                description="Route plan through optional tools and validations",
                inputs=["execution_plan"],
                outputs=["routed_plan"],
                dependencies=["planner_llm"],
                retry_policy={"max_retries": 0, "backoff": "none"},
                timeout=5,
            ),
            self._node(
                node_id="result_aggregator",
                node_type="aggregator",
                description="Aggregate outputs into final response package",
                inputs=["routed_plan", "tool_outputs"],
                outputs=["final_response"],
                dependencies=["route_decision"],
                retry_policy={"max_retries": 1, "backoff": "linear"},
                timeout=8,
            ),
        ]

        for tool_name in external_tools:
            if tool_name == "none_required":
                continue
            node_id = f"tool_{tool_name}"
            nodes.append(
                self._node(
                    node_id=node_id,
                    node_type="tool",
                    description=f"Invoke external tool: {tool_name}",
                    inputs=["routed_plan"],
                    outputs=[f"{tool_name}_output"],
                    dependencies=["route_decision"],
                    retry_policy={"max_retries": 2, "backoff": "exponential"},
                    timeout=12,
                )
            )

        # Ensure the aggregator runs after all tool nodes when they exist.
        tool_node_ids = [n["node_id"] for n in nodes if n["node_type"] == "tool"]
        for node in nodes:
            if node["node_id"] == "result_aggregator":
                node["dependencies"] = sorted(set(node["dependencies"] + tool_node_ids))
                break

        return nodes

    def _build_nodes_from_blueprint(self, blueprint: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        for raw_node in blueprint:
            nodes.append(
                self._node(
                    node_id=str(raw_node["node_id"]),
                    node_type=str(raw_node["node_type"]),
                    description=str(raw_node["description"]),
                    inputs=list(raw_node.get("inputs", [])),
                    outputs=list(raw_node.get("outputs", [])),
                    dependencies=list(raw_node.get("dependencies", [])),
                    retry_policy=dict(
                        raw_node.get(
                            "retry_policy",
                            {"max_retries": 1 if raw_node.get("node_type") in {"llm", "tool"} else 0, "backoff": "linear"},
                        )
                    ),
                    timeout=int(raw_node.get("timeout", 10)),
                )
            )
        return nodes

    def _node(
        self,
        node_id: str,
        node_type: str,
        description: str,
        inputs: List[str],
        outputs: List[str],
        dependencies: List[str],
        retry_policy: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        if node_type not in self._ALLOWED_TYPES:
            raise ValueError(f"Unsupported node_type '{node_type}'.")
        return {
            "node_id": node_id,
            "node_type": node_type,
            "description": description,
            "inputs": inputs,
            "outputs": outputs,
            "dependencies": dependencies,
            "retry_policy": retry_policy,
            "timeout": timeout,
        }

    def _validate(self, graph_nx: nx.DiGraph, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        node_ids: Set[str] = {node["node_id"] for node in nodes}
        if len(node_ids) != len(nodes):
            errors.append("Duplicate node_id values detected.")

        for node in nodes:
            for dependency in node["dependencies"]:
                if dependency not in node_ids:
                    errors.append(
                        f"Node '{node['node_id']}' has missing dependency '{dependency}'."
                    )

        if not nx.is_directed_acyclic_graph(graph_nx):
            errors.append("Circular dependency detected in workflow graph.")

        if len(graph_nx.nodes()) <= 2:
            warnings.append("Graph is very small and may not represent a realistic workflow.")

        if not errors:
            try:
                list(nx.topological_sort(graph_nx))
            except nx.NetworkXUnfeasible:
                errors.append("Execution order cannot be determined due to graph constraints.")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }