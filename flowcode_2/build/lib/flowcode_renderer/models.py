from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GraphNode:
    id: str
    title: str
    summary: str
    detail: Optional[str] = None
    type: str = "process"


@dataclass
class GraphEdge:
    source: str
    target: str
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    entry_node: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def adjacency(self) -> Dict[str, List[GraphEdge]]:
        adj: Dict[str, List[GraphEdge]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            adj.setdefault(edge.source, []).append(edge)
        return adj
