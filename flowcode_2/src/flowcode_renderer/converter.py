from __future__ import annotations

import json
from typing import Dict

from .models import FlowGraph, GraphNode


NODE_TYPE_MAP: Dict[str, str] = {
    "start": "start",
    "process": "statement",
    "call": "call",
    "decision": "conditional",
    "loop": "loop",
    "end": "end",
    "io": "statement",
}


def _map_node_kind(node: GraphNode) -> str:
    return NODE_TYPE_MAP.get(node.type.lower(), "statement")


def graph_to_stage2_module(graph: FlowGraph) -> Dict[str, object]:
    metadata = graph.metadata.copy()
    title = metadata.get("title") or "Flowchart"

    nodes_payload = []
    for node in graph.nodes.values():
        nodes_payload.append(
            {
                "id": node.id,
                "kind": _map_node_kind(node),
                "label": node.summary or node.title,
                "summary": node.summary,
                "metadata": {
                    "title": node.title,
                    "detail": node.detail,
                    "type": node.type,
                },
            }
        )

    edges_payload = []
    for edge in graph.edges:
        payload = {
            "source": edge.source,
            "target": edge.target,
        }
        if edge.label:
            payload["label"] = edge.label
        edges_payload.append(payload)

    function_payload = {
        "name": title,
        "nodes": nodes_payload,
        "edges": edges_payload,
        "parameters": [],
        "metadata": {
            "entry_node": graph.entry_node,
        },
    }

    if graph.metadata.get("summary"):
        function_payload["docstring"] = graph.metadata["summary"]

    module = {
        "language": metadata.get("language", "flowcode"),
        "metadata": metadata,
        "functions": [function_payload],
    }

    return module
