from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import random
import uuid
from typing import Any, Dict, List

import networkx as nx


class ExecutionSimulator:
    """Simulates runtime behavior with retries, timings, and structured execution trace."""

    _TYPE_LATENCY_RANGE = {
        "llm": (250, 900),
        "tool": (120, 600),
        "memory": (20, 120),
        "decision": (30, 160),
        "aggregator": (80, 280),
    }

    _TYPE_FAILURE_PROBABILITY = {
        "llm": 0.08,
        "tool": 0.14,
        "memory": 0.02,
        "decision": 0.03,
        "aggregator": 0.04,
    }

    def simulate(self, graph_bundle: Dict[str, Any]) -> Dict[str, Any]:
        graph_nx = graph_bundle.get("graph_nx")
        if graph_nx is None or not isinstance(graph_nx, nx.DiGraph):
            raise ValueError("ExecutionSimulator expected graph_bundle['graph_nx'] as nx.DiGraph.")

        execution_id = str(uuid.uuid4())
        random.seed(42)
        start_clock = datetime.utcnow()

        ordered_nodes = list(nx.topological_sort(graph_nx))
        timeline_ms = 0
        nodes_trace: List[Dict[str, Any]] = []
        total_retries = 0
        overall_status = "success"

        for node_id in ordered_nodes:
            node_data = graph_nx.nodes[node_id]
            node_type = node_data.get("node_type", "decision")
            retry_policy = node_data.get("retry_policy", {})
            max_retries = int(retry_policy.get("max_retries", 0))

            attempts = 0
            final_status = "success"
            error = None
            node_start = timeline_ms
            node_end = timeline_ms

            while attempts <= max_retries:
                attempts += 1
                duration_ms = self._simulate_duration(node_type)
                failure_probability = self._TYPE_FAILURE_PROBABILITY.get(node_type, 0.05)
                failed = random.random() < failure_probability

                if failed and attempts <= max_retries:
                    total_retries += 1
                    final_status = "retry"
                    timeline_ms += duration_ms
                    continue

                timeline_ms += duration_ms
                node_end = timeline_ms

                if failed:
                    final_status = "failure"
                    error = f"{node_type} runtime failure"
                    overall_status = "failure"
                else:
                    final_status = "success"

                break

            node_end_time = start_clock + timedelta(milliseconds=node_end)
            node_start_time = start_clock + timedelta(milliseconds=node_start)
            nodes_trace.append(
                {
                    "node_id": node_id,
                    "node_type": node_type,
                    "status": final_status,
                    "attempts": attempts,
                    "start_time": node_start_time.isoformat() + "Z",
                    "end_time": node_end_time.isoformat() + "Z",
                    "duration_ms": node_end - node_start,
                    "error": error,
                }
            )

        if overall_status != "failure" and total_retries > 0:
            overall_status = "degraded"

        simulation_result = {
            "execution_id": execution_id,
            "status": overall_status,
            "execution_order": ordered_nodes,
            "total_duration_ms": timeline_ms,
            "total_retries": total_retries,
            "nodes": nodes_trace,
        }
        exported_trace_path = self._export_trace(simulation_result)
        simulation_result["trace_export_path"] = exported_trace_path
        return simulation_result

    def _simulate_duration(self, node_type: str) -> int:
        low, high = self._TYPE_LATENCY_RANGE.get(node_type, (80, 260))
        return random.randint(low, high)

    def _export_trace(self, simulation_result: Dict[str, Any]) -> str:
        payload = {
            "execution_id": simulation_result.get("execution_id"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_execution_time": simulation_result.get("total_duration_ms", 0),
            "nodes": [
                {
                    "node_id": node.get("node_id"),
                    "node_type": node.get("node_type"),
                    "status": node.get("status"),
                    "start_time": node.get("start_time"),
                    "end_time": node.get("end_time"),
                    "duration_ms": node.get("duration_ms"),
                    "attempts": node.get("attempts"),
                }
                for node in simulation_result.get("nodes", [])
            ],
        }

        output_dir = Path("demo_artifacts")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "execution_trace.json"
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(output_path)