from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import networkx as nx


class GraphVisualizer:
    """Renders a workflow DAG PNG using networkx drawing utilities."""

    _TYPE_COLOR = {
        "llm": "#f4a261",
        "tool": "#2a9d8f",
        "memory": "#577590",
        "decision": "#e9c46a",
        "aggregator": "#e76f51",
    }

    def render(self, graph_bundle: Dict[str, Any], output_path_no_ext: str = "graph_output") -> Optional[str]:
        graph_nx = graph_bundle.get("graph_nx")
        if graph_nx is None or not isinstance(graph_nx, nx.DiGraph):
            return None

        output_path = Path(output_path_no_ext)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        png_path = f"{output_path}.png"

        plt.figure(figsize=(12, 7))
        position = nx.spring_layout(graph_nx, seed=7)
        node_colors = [
            self._TYPE_COLOR.get(graph_nx.nodes[node].get("node_type", "decision"), "#8d99ae")
            for node in graph_nx.nodes()
        ]
        labels = {
            node: f"{node}\n{graph_nx.nodes[node].get('node_type', 'unknown')}"
            for node in graph_nx.nodes()
        }

        nx.draw_networkx_nodes(
            graph_nx,
            pos=position,
            node_size=2200,
            node_color=node_colors,
            edgecolors="#1f2937",
            linewidths=1.2,
        )
        nx.draw_networkx_edges(
            graph_nx,
            pos=position,
            arrows=True,
            arrowsize=18,
            edge_color="#374151",
            width=1.6,
            connectionstyle="arc3,rad=0.08",
        )
        nx.draw_networkx_labels(graph_nx, pos=position, labels=labels, font_size=8)

        plt.title("HiveDevAgent Workflow Graph", fontsize=12)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(png_path, dpi=180)
        plt.close()
        return png_path