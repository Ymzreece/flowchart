from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..models import EdgeIR, FunctionIR, ModuleIR, NodeIR, NodeKind, SourceLocation
from ..registry import register_parser
from .base import LanguageParser

try:  # Optional dependency
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language
except Exception:  # pragma: no cover - optional dependency
    Language = None  # type: ignore
    Parser = None  # type: ignore
    get_language = None  # type: ignore


@dataclass(frozen=True)
class TreeSitterLanguageConfig:
    """Configuration for adapting a Tree-sitter grammar into the flow IR."""

    language: str
    tree_sitter_language: str
    function_query: str
    function_name_capture: str = "name"
    function_body_capture: str = "body"


_TREE_SITTER_REGISTRY: Dict[str, TreeSitterLanguageConfig] = {}


def register_tree_sitter_language(config: TreeSitterLanguageConfig) -> None:
    """Register a Tree-sitter powered parser for a language."""
    _TREE_SITTER_REGISTRY[config.language.lower()] = config

    def factory(config: TreeSitterLanguageConfig = config) -> TreeSitterAdapter:
        return TreeSitterAdapter(config)

    register_parser(config.language, factory)


class TreeSitterAdapter(LanguageParser):
    """Generic Tree-sitter adapter that emits a simplified flow graph."""

    def __init__(self, config: TreeSitterLanguageConfig):
        if Parser is None or get_language is None:
            raise RuntimeError(
                "tree_sitter and tree_sitter_languages are required for TreeSitterAdapter. "
                "Install them via the 'treesitter' extra (pip install flow-ir[treesitter])."
            )
        self.config = config
        language = get_language(config.tree_sitter_language)
        self._parser = Parser()
        self._parser.set_language(language)
        self._query = language.query(config.function_query)
        self.language = config.language
        super().__init__()

    def parse_code(self, code: str, *, file_path: Optional[str] = None) -> ModuleIR:
        tree = self._parser.parse(code.encode("utf-8"))
        matches = self._query.matches(tree.root_node)

        functions: List[FunctionIR] = []
        for match in matches:
            capture_map: Dict[str, List] = {}
            for capture in match.captures:
                name = getattr(capture, "name", None)
                node = getattr(capture, "node", None)
                if name is None or node is None:
                    continue
                capture_map.setdefault(name, []).append(node)

            name_nodes = capture_map.get(self.config.function_name_capture)
            body_nodes = capture_map.get(self.config.function_body_capture)
            if not name_nodes or not body_nodes:
                continue

            name_text = self._slice(code, name_nodes[0])
            functions.append(self._build_function(name_text, body_nodes[0], code, file_path))

        return ModuleIR(language=self.language, functions=functions, metadata={"file_path": file_path})

    def _build_function(self, name: str, body_node, code: str, file_path: Optional[str]) -> FunctionIR:
        nodes: List[NodeIR] = []
        edges: List[EdgeIR] = []

        def add_node(kind: NodeKind, label: str, node) -> str:
            node_id = f"n{len(nodes)}"
            location = SourceLocation(
                file_path=file_path or "<unknown>",
                line=node.start_point[0] + 1,
                column=node.start_point[1],
            ) if node is not None else None
            nodes.append(
                NodeIR(
                    id=node_id,
                    kind=kind,
                    label=label.strip(),
                    location=location,
                )
            )
            return node_id

        start_id = add_node(NodeKind.START, "Start", body_node)
        prev_ids = [start_id]

        statements = [child for child in body_node.named_children if child.is_named]
        for stmt in statements:
            label = self._normalize_label(self._slice(code, stmt))
            stmt_id = add_node(NodeKind.STATEMENT, label, stmt)
            for prev in prev_ids:
                edges.append(EdgeIR(source=prev, target=stmt_id))
            prev_ids = [stmt_id]

        end_id = add_node(NodeKind.END, "End", body_node)
        for prev in prev_ids:
            edges.append(EdgeIR(source=prev, target=end_id))

        return FunctionIR(
            name=name,
            nodes=nodes,
            edges=edges,
        )

    def _slice(self, code: str, node) -> str:
        start_byte = node.start_byte
        end_byte = node.end_byte
        return code.encode("utf-8")[start_byte:end_byte].decode("utf-8")

    def _normalize_label(self, text: str) -> str:
        return textwrap.dedent(text).strip().replace("\n", " ")


__all__ = [
    "TreeSitterAdapter",
    "TreeSitterLanguageConfig",
    "register_tree_sitter_language",
]
