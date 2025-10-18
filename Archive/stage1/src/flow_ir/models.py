from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeKind(str, Enum):
    """Enumerates generic control-flow node types supported by the IR."""

    START = "start"
    END = "end"
    STATEMENT = "statement"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    CALL = "call"
    RETURN = "return"
    EXCEPTION = "exception"
    UNKNOWN = "unknown"


@dataclass
class SourceLocation:
    """Represents a single source location for traceability."""

    file_path: str
    line: int
    column: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
        }


@dataclass
class NodeIR:
    """A normalized control-flow node."""

    id: str
    kind: NodeKind
    label: str
    summary: Optional[str] = None
    location: Optional[SourceLocation] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "kind": self.kind.value,
            "label": self.label,
            "summary": self.summary,
            "metadata": self.metadata,
        }
        if self.location is not None:
            data["location"] = self.location.to_dict()
        return data


@dataclass
class EdgeIR:
    """A directed edge in the control-flow graph."""

    source: str
    target: str
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {"source": self.source, "target": self.target}
        if self.label is not None:
            data["label"] = self.label
        if self.metadata:
            data["metadata"] = self.metadata
        return data


@dataclass
class FunctionIR:
    """Represents the flowchart for a single function or callable."""

    name: str
    nodes: List[NodeIR]
    edges: List[EdgeIR]
    parameters: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "parameters": self.parameters,
            "returns": self.returns,
            "docstring": self.docstring,
            "metadata": self.metadata,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }


@dataclass
class ModuleIR:
    """Aggregates all function graphs for a single module or file."""

    language: str
    functions: List[FunctionIR]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "metadata": self.metadata,
            "functions": [fn.to_dict() for fn in self.functions],
        }

    def to_json(self) -> Dict[str, Any]:
        """Alias used by serializers to produce JSON payloads."""
        return self.to_dict()
