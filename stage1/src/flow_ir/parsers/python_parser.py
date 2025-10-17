from __future__ import annotations

import ast
import textwrap
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from ..models import EdgeIR, FunctionIR, ModuleIR, NodeIR, NodeKind, SourceLocation
from ..registry import register_parser
from ..text_utils import (
    summarize_condition,
    summarize_expression,
    summarize_loop,
    summarize_statement,
)
from .base import LanguageParser


@dataclass
class _GraphSlice:
    entry_ids: List[str]
    exit_ids: List[str]


class _PythonControlFlowBuilder:
    """Builds a simplified control-flow graph for Python functions."""

    def __init__(self, code: str, file_path: Optional[str]):
        self.code = code
        self.file_path = file_path or "<memory>"
        self.nodes: List[NodeIR] = []
        self.edges: List[EdgeIR] = []
        self._counter = 0
        self._function_end_id: Optional[str] = None

    def build_function(self, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionIR:
        self.nodes.clear()
        self.edges.clear()
        self._counter = 0

        start_id = self._add_node(NodeKind.START, "Start", fn)
        end_id = self._add_node(NodeKind.END, "End", fn, metadata={"reason": "function_terminator"})
        self._function_end_id = end_id

        exits = self._build_block(fn.body, [(start_id, None)])
        for exit_id in exits:
            if exit_id != end_id:
                self.edges.append(EdgeIR(source=exit_id, target=end_id))

        parameters = [arg.arg for arg in fn.args.args]
        returns = self._format_expression(fn.returns) if getattr(fn, "returns", None) else None
        docstring = ast.get_docstring(fn)

        return FunctionIR(
            name=fn.name,
            parameters=parameters,
            returns=returns,
            docstring=docstring,
            nodes=list(self.nodes),
            edges=list(self.edges),
            metadata={
                "async": isinstance(fn, ast.AsyncFunctionDef),
            },
        )

    def _build_block(self, statements: Sequence[ast.stmt], incoming_edges: List[Tuple[str, Optional[str]]]) -> List[str]:
        if not statements:
            return [source for source, _ in incoming_edges]

        current_sources = list(incoming_edges)
        for stmt in statements:
            slice_ = self._slice_for_statement(stmt)
            self._connect_sources(current_sources, slice_.entry_ids)
            current_sources = [(exit_id, None) for exit_id in slice_.exit_ids]
            if not current_sources:
                # Return or raise terminates the flow; remaining statements are unreachable.
                break

        return [source for source, _ in current_sources]

    def _connect_sources(self, sources: List[Tuple[str, Optional[str]]], targets: List[str]) -> None:
        if not targets:
            return
        for source, label in sources:
            for target in targets:
                self.edges.append(EdgeIR(source=source, target=target, label=label))

    def _slice_for_statement(self, stmt: ast.stmt) -> _GraphSlice:
        if isinstance(stmt, ast.If):
            return self._handle_if(stmt)
        if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
            return self._handle_loop(stmt)
        if isinstance(stmt, ast.Try):
            return self._handle_try(stmt)
        if isinstance(stmt, ast.With):
            return self._handle_with(stmt)
        if isinstance(stmt, ast.Return):
            return self._handle_return(stmt)
        if isinstance(stmt, ast.Raise):
            return self._handle_raise(stmt)

        label = self._format_statement(stmt)
        node_id = self._add_node(NodeKind.STATEMENT, label, stmt)
        return _GraphSlice(entry_ids=[node_id], exit_ids=[node_id])

    def _handle_if(self, stmt: ast.If) -> _GraphSlice:
        label = f"if {self._format_expression(stmt.test)}"
        cond_id = self._add_node(NodeKind.CONDITIONAL, label, stmt.test)

        true_exits = self._build_block(stmt.body, [(cond_id, "True")])
        false_exits = self._build_block(stmt.orelse, [(cond_id, "False")]) if stmt.orelse else [cond_id]

        exit_ids = list(dict.fromkeys(true_exits + false_exits))
        return _GraphSlice(entry_ids=[cond_id], exit_ids=exit_ids)

    def _handle_loop(self, stmt: ast.stmt) -> _GraphSlice:
        if isinstance(stmt, ast.While):
            label = f"while {self._format_expression(stmt.test)}"
        else:
            target = self._format_expression(stmt.target)
            iter_ = self._format_expression(stmt.iter)
            prefix = "async for" if isinstance(stmt, ast.AsyncFor) else "for"
            label = f"{prefix} {target} in {iter_}"

        loop_id = self._add_node(NodeKind.LOOP, label, stmt)
        body_exits = self._build_block(stmt.body, [(loop_id, "Loop body")])

        # For now, connect body exits back to loop node to represent continuation.
        for exit_id in body_exits:
            self.edges.append(EdgeIR(source=exit_id, target=loop_id, label="Iterate"))

        orelse_exits = self._build_block(stmt.orelse, [(loop_id, "Loop orelse")]) if getattr(stmt, "orelse", None) else [loop_id]
        exit_ids = list(dict.fromkeys(orelse_exits + [loop_id]))
        return _GraphSlice(entry_ids=[loop_id], exit_ids=exit_ids)

    def _handle_try(self, stmt: ast.Try) -> _GraphSlice:
        try_id = self._add_node(NodeKind.STATEMENT, "try", stmt)
        body_exits = self._build_block(stmt.body, [(try_id, "Try body")])

        handler_exit_ids: List[str] = []
        for handler in stmt.handlers:
            handler_label = "except"
            if handler.type is not None:
                handler_label = f"except {self._format_expression(handler.type)}"
            if handler.name:
                handler_label += f" as {handler.name}"
            handler_id = self._add_node(NodeKind.EXCEPTION, handler_label, handler)
            self.edges.append(EdgeIR(source=try_id, target=handler_id, label="Exception"))
            exits = self._build_block(handler.body, [(handler_id, None)])
            handler_exit_ids.extend(exits)

        else_exit_ids = self._build_block(stmt.orelse, [(try_id, "Try else")]) if stmt.orelse else body_exits
        finalizer_exits = self._build_block(stmt.finalbody, [(try_id, "Finally")]) if stmt.finalbody else else_exit_ids
        exit_ids = list(dict.fromkeys(handler_exit_ids + finalizer_exits))
        return _GraphSlice(entry_ids=[try_id], exit_ids=exit_ids)

    def _handle_with(self, stmt: ast.With | ast.AsyncWith) -> _GraphSlice:
        prefix = "async with" if isinstance(stmt, ast.AsyncWith) else "with"
        items = ", ".join(self._format_withitem(item) for item in stmt.items)
        label = f"{prefix} {items}"
        with_id = self._add_node(NodeKind.STATEMENT, label, stmt)
        exits = self._build_block(stmt.body, [(with_id, None)])
        return _GraphSlice(entry_ids=[with_id], exit_ids=exits)

    def _handle_return(self, stmt: ast.Return) -> _GraphSlice:
        label = "return"
        if stmt.value is not None:
            label += f" {self._format_expression(stmt.value)}"
        node_id = self._add_node(NodeKind.RETURN, label, stmt)
        if self._function_end_id:
            self.edges.append(EdgeIR(source=node_id, target=self._function_end_id, label="Return"))
        return _GraphSlice(entry_ids=[node_id], exit_ids=[])

    def _handle_raise(self, stmt: ast.Raise) -> _GraphSlice:
        label = "raise"
        if stmt.exc is not None:
            label += f" {self._format_expression(stmt.exc)}"
        node_id = self._add_node(NodeKind.EXCEPTION, label, stmt)
        if self._function_end_id:
            self.edges.append(EdgeIR(source=node_id, target=self._function_end_id, label="Raise"))
        return _GraphSlice(entry_ids=[node_id], exit_ids=[])

    def _format_statement(self, stmt: ast.stmt) -> str:
        return self._dedent(self._get_source_segment(stmt)) or stmt.__class__.__name__

    def _format_expression(self, expr: ast.AST) -> str:
        segment = self._dedent(self._get_source_segment(expr))
        if segment:
            return segment
        if hasattr(ast, "unparse"):
            try:
                return ast.unparse(expr)
            except Exception:  # pragma: no cover - fallback for older Python versions
                pass
        return expr.__class__.__name__

    def _format_withitem(self, item: ast.withitem) -> str:
        context = self._format_expression(item.context_expr)
        if item.optional_vars:
            return f"{context} as {self._format_expression(item.optional_vars)}"
        return context

    def _add_node(self, kind: NodeKind, label: str, node: Optional[ast.AST], metadata: Optional[dict] = None) -> str:
        node_id = f"n{self._counter}"
        self._counter += 1
        location = None
        if node is not None and hasattr(node, "lineno"):
            location = SourceLocation(
                file_path=self.file_path,
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0),
            )
        summary = self._summarize(kind, label)
        self.nodes.append(
            NodeIR(
                id=node_id,
                kind=kind,
                label=label.strip(),
                summary=summary,
                location=location,
                metadata=metadata or {},
            )
        )
        return node_id

    def _get_source_segment(self, node: Optional[ast.AST]) -> str:
        if node is None:
            return ""
        try:
            return ast.get_source_segment(self.code, node) or ""
        except AttributeError:
            return ""

    def _dedent(self, text: str) -> str:
        return textwrap.dedent(text).strip()

    def _summarize(self, kind: NodeKind, label: str) -> str:
        if kind is NodeKind.START:
            return "Begin the function."
        if kind is NodeKind.END:
            return "Finish the function."
        if kind is NodeKind.CONDITIONAL:
            return summarize_expression(label)
        if kind is NodeKind.LOOP:
            return summarize_loop(label)
        if kind is NodeKind.RETURN:
            return summarize_statement(label)
        if kind is NodeKind.EXCEPTION:
            return summarize_statement(label)
        return summarize_statement(label)


class PythonParser(LanguageParser):
    """LanguageParser implementation for Python using the stdlib AST module."""

    language = "python"

    def parse_code(self, code: str, *, file_path: Optional[str] = None) -> ModuleIR:
        module = ast.parse(code)
        builder = _PythonControlFlowBuilder(code, file_path)
        functions: List[FunctionIR] = []
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(builder.build_function(node))
        return ModuleIR(language=self.language, functions=functions, metadata={"file_path": file_path})


# Register the parser on import so it is available via the registry.
register_parser(PythonParser.language, PythonParser)
