from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .models import FlowGraph, GraphEdge, GraphNode

SECTION_PATTERN = re.compile(r"^\*\*(\d+)\.[^*]+\*\*")


def parse_outline_text(text: str) -> FlowGraph:
    lines = [line.rstrip() for line in text.splitlines()]
    stages: List[tuple[str, List[str]]] = []
    current_title: str | None = None
    current_steps: List[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        match = SECTION_PATTERN.match(line)
        if match:
            if current_title is not None:
                stages.append((current_title, current_steps))
            current_title = line.strip("* ")
            current_steps = []
            continue

        if line.startswith("-") and current_title is not None:
            step = line.lstrip("- ")
            current_steps.append(step)

    if current_title is not None:
        stages.append((current_title, current_steps))

    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []

    previous_node_id: str | None = None
    for index, (title, steps) in enumerate(stages, start=1):
        node_id = f"stage_{index}"
        summary = "; ".join(steps) if steps else title
        nodes[node_id] = GraphNode(id=node_id, title=title, summary=summary, detail="\n".join(steps))

        if previous_node_id is not None:
            edges.append(GraphEdge(source=previous_node_id, target=node_id))
        previous_node_id = node_id

    return FlowGraph(nodes=nodes, edges=edges, entry_node="stage_1" if nodes else None)


def parse_graph_json(text: str) -> FlowGraph:
    data = json.loads(text)

    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    entry_node = data.get("entry_node") if isinstance(data, dict) else None

    nodes_data = data.get("nodes", []) if isinstance(data, dict) else []
    edges_data = data.get("edges", []) if isinstance(data, dict) else []
    fallback_stages = data.get("stages", []) if isinstance(data, dict) else []

    nodes: Dict[str, GraphNode] = {}
    for node in nodes_data:
        node_id = str(node.get("id"))
        if not node_id:
            continue
        title = node.get("title") or node_id
        summary = node.get("summary") or title
        detail = node.get("detail")
        node_type = node.get("type", "process")
        nodes[node_id] = GraphNode(
            id=node_id,
            title=title,
            summary=summary,
            detail=detail,
            type=node_type,
        )

    edges: List[GraphEdge] = []
    for edge in edges_data:
        src = edge.get("source")
        tgt = edge.get("target")
        if not src or not tgt:
            continue
        label = edge.get("label")
        edge_metadata = edge.get("metadata")
        metadata_dict: Dict[str, Any] = {}
        if isinstance(edge_metadata, dict):
            metadata_dict = dict(edge_metadata)
        edges.append(GraphEdge(source=str(src), target=str(tgt), label=label, metadata=metadata_dict))

    if not nodes and fallback_stages:
        previous_id: str | None = None
        for index, stage in enumerate(fallback_stages, start=1):
            node_id = f"stage_{index}"
            title = stage.get("title", f"Stage {index}")
            steps = stage.get("steps", [])
            summary = " ".join(step.strip() for step in steps if step.strip()) or title
            detail = "\n".join(step for step in steps if step.strip()) or None
            nodes[node_id] = GraphNode(id=node_id, title=title, summary=summary, detail=detail)
            if previous_id:
                edges.append(GraphEdge(source=previous_id, target=node_id))
            previous_id = node_id
        if nodes and entry_node is None:
            entry_node = next(iter(nodes))

    return FlowGraph(nodes=nodes, edges=edges, entry_node=entry_node, metadata=metadata)


def autodetect_format(path: Path) -> str:
    if path.suffix.lower() == ".json":
        return "json"
    return "text"


def parse_graph(path: Path, *, input_format: str | None = None) -> FlowGraph:
    format_to_use = input_format or autodetect_format(path)
    text = path.read_text(encoding="utf-8")
    if format_to_use == "json":
        return parse_graph_json(text)
    return parse_outline_text(text)
