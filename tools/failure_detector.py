from __future__ import annotations

from typing import Any, Dict, List

import networkx as nx


class FailureDetector:
    """Detects reliability risks in workflow topology and simulated execution traces."""

    def detect(self, graph_bundle: Dict[str, Any], execution_trace: Dict[str, Any]) -> Dict[str, Any]:
        graph_nx = graph_bundle.get("graph_nx")
        if graph_nx is None or not isinstance(graph_nx, nx.DiGraph):
            raise ValueError("FailureDetector expected graph_bundle['graph_nx'] as nx.DiGraph.")

        warnings: List[Dict[str, Any]] = []
        node_map = {node_id: data for node_id, data in graph_nx.nodes(data=True)}
        node_trace = {entry["node_id"]: entry for entry in execution_trace.get("nodes", [])}

        for node_id, data in node_map.items():
            retry_policy = data.get("retry_policy", {})
            max_retries = int(retry_policy.get("max_retries", 0))
            if data.get("node_type") in {"llm", "tool"} and max_retries == 0:
                warnings.append(
                    self._warning(
                        warning_id=f"retry-{node_id}",
                        category="missing_retry_logic",
                        severity="medium",
                        message=f"Node '{node_id}' has no retries configured.",
                        recommendation="Set max_retries >= 1 for non-deterministic nodes.",
                        node_id=node_id,
                    )
                )

        longest_path = nx.dag_longest_path(graph_nx) if nx.is_directed_acyclic_graph(graph_nx) else []
        if len(longest_path) >= 6:
            warnings.append(
                self._warning(
                    warning_id="long-chain",
                    category="long_dependency_chain",
                    severity="medium",
                    message=f"Longest dependency chain has {len(longest_path)} nodes.",
                    recommendation="Parallelize independent nodes or collapse low-value stages.",
                )
            )

        topo_order = execution_trace.get("execution_order", [])
        sequential_llm = 0
        max_sequential_llm = 0
        for node_id in topo_order:
            node_type = node_map.get(node_id, {}).get("node_type")
            if node_type == "llm":
                sequential_llm += 1
                max_sequential_llm = max(max_sequential_llm, sequential_llm)
            else:
                sequential_llm = 0

        if max_sequential_llm >= 3:
            warnings.append(
                self._warning(
                    warning_id="llm-chain",
                    category="sequential_llm_calls",
                    severity="high",
                    message=f"Detected {max_sequential_llm} sequential LLM nodes.",
                    recommendation="Insert caching, tool offloading, or parallel branches.",
                )
            )

        for node_id, data in node_map.items():
            if data.get("node_type") != "tool":
                continue
            trace_entry = node_trace.get(node_id, {})
            status = trace_entry.get("status")
            if status in {"failure", "retry"}:
                warnings.append(
                    self._warning(
                        warning_id=f"tool-risk-{node_id}",
                        category="tool_failure_risk",
                        severity="high" if status == "failure" else "medium",
                        message=f"Tool node '{node_id}' ended with status '{status}'.",
                        recommendation="Add fallback tools and circuit breaker thresholds.",
                        node_id=node_id,
                    )
                )

        for node_id in graph_nx.nodes():
            in_degree = graph_nx.in_degree(node_id)
            out_degree = graph_nx.out_degree(node_id)
            duration_ms = node_trace.get(node_id, {}).get("duration_ms", 0)
            if (in_degree >= 2 and out_degree >= 1) or duration_ms > 850:
                warnings.append(
                    self._warning(
                        warning_id=f"bottleneck-{node_id}",
                        category="bottleneck_node",
                        severity="medium",
                        message=f"Node '{node_id}' may bottleneck flow (duration={duration_ms}ms).",
                        recommendation="Shard workload or move pre-processing earlier in graph.",
                        node_id=node_id,
                    )
                )

        return {
            "severity": self._overall_severity(warnings),
            "warnings": warnings,
        }

    def _overall_severity(self, warnings: List[Dict[str, Any]]) -> str:
        if not warnings:
            return "none"
        severities = {warning["severity"] for warning in warnings}
        if "high" in severities:
            return "high"
        if "medium" in severities:
            return "medium"
        return "low"

    def _warning(
        self,
        warning_id: str,
        category: str,
        severity: str,
        message: str,
        recommendation: str,
        node_id: str | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "warning_id": warning_id,
            "category": category,
            "severity": severity,
            "message": message,
            "recommendation": recommendation,
        }
        if node_id:
            payload["node_id"] = node_id
        return payload