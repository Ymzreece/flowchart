from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from ..models import EdgeIR, FunctionIR, ModuleIR, NodeIR, NodeKind, SourceLocation
from ..registry import register_parser
from ..text_utils import summarize_expression, summarize_loop, summarize_statement
from .base import LanguageParser


_KEYWORDS = {
    "if",
    "else",
    "for",
    "while",
    "switch",
    "case",
    "default",
    "return",
    "do",
    "sizeof",
    "goto",
    "enum",
    "struct",
    "union",
    "typedef",
    "__attribute__",
}


def _is_identifier_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _is_identifier_start(ch: str) -> bool:
    return ch.isalpha() or ch == "_"


def _count_newlines(text: str, start: int, end: int) -> int:
    return text.count("\n", start, end)


class _CodeView:
    """Holds both original and comment-stripped code while preserving indices."""

    def __init__(self, code: str):
        self.original = code
        self.cleaned = self._strip_comments(code)

    def _strip_comments(self, code: str) -> str:
        out = []
        i = 0
        n = len(code)
        state = "base"
        while i < n:
            ch = code[i]
            nx = code[i + 1] if i + 1 < n else ""
            if state == "base":
                if ch == "/" and nx == "/":
                    out.append("  ")
                    i += 2
                    state = "line_comment"
                elif ch == "/" and nx == "*":
                    out.append("  ")
                    i += 2
                    state = "block_comment"
                elif ch == '"':
                    out.append(ch)
                    i += 1
                    state = "string"
                elif ch == "'":
                    out.append(ch)
                    i += 1
                    state = "char"
                else:
                    out.append(ch)
                    i += 1
            elif state == "line_comment":
                if ch == "\n":
                    out.append("\n")
                    i += 1
                    state = "base"
                else:
                    out.append(" ")
                    i += 1
            elif state == "block_comment":
                if ch == "*" and nx == "/":
                    out.append("  ")
                    i += 2
                    state = "base"
                elif ch == "\n":
                    out.append("\n")
                    i += 1
                else:
                    out.append(" ")
                    i += 1
            elif state == "string":
                out.append(ch)
                if ch == "\\" and nx:
                    out.append(nx)
                    i += 2
                elif ch == '"':
                    i += 1
                    state = "base"
                else:
                    i += 1
            elif state == "char":
                out.append(ch)
                if ch == "\\" and nx:
                    out.append(nx)
                    i += 2
                elif ch == "'":
                    i += 1
                    state = "base"
                else:
                    i += 1
        return "".join(out)

    def skip_whitespace(self, idx: int, limit: Optional[int] = None) -> int:
        limit = len(self.cleaned) if limit is None else limit
        while idx < limit and self.cleaned[idx].isspace():
            idx += 1
        return idx

    def find_matching(self, start: int, open_char: str, close_char: str) -> int:
        depth = 0
        i = start
        n = len(self.cleaned)
        in_string = False
        in_char = False
        while i < n:
            ch = self.cleaned[i]
            if ch == '"' and not in_char:
                in_string = not in_string
            elif ch == "'" and not in_string:
                in_char = not in_char
            elif not in_string and not in_char:
                if ch == open_char:
                    depth += 1
                elif ch == close_char:
                    depth -= 1
                    if depth == 0:
                        return i
            if ch == "/" and i + 1 < n and not in_string and not in_char:
                nxt = self.cleaned[i + 1]
                if nxt == "/":  # skip to end of line
                    i += 2
                    while i < n and self.cleaned[i] != "\n":
                        i += 1
                    continue
                if nxt == "*":  # skip block
                    i += 2
                    while i + 1 < n and not (self.cleaned[i] == "*" and self.cleaned[i + 1] == "/"):
                        i += 1
                    i += 2
                    continue
            i += 1
        return -1

    def index_to_location(self, idx: int) -> SourceLocation:
        line = self.cleaned.count("\n", 0, idx) + 1
        # column: count chars after last newline in original code
        last_newline = self.cleaned.rfind("\n", 0, idx)
        col = idx - last_newline - 1 if last_newline != -1 else idx
        return SourceLocation(file_path="", line=line, column=col)


@dataclass
class Statement:
    start: int
    end: int


@dataclass
class SimpleStatement(Statement):
    text: str


@dataclass
class ReturnStatement(Statement):
    text: str


@dataclass
class IfStatement(Statement):
    condition: str
    true_block: List[Statement]
    false_block: List[Statement]


@dataclass
class LoopStatement(Statement):
    loop_type: str
    header: str
    body: List[Statement]
    else_block: List[Statement]


@dataclass
class DoWhileStatement(Statement):
    condition: str
    body: List[Statement]


class _FunctionExtractor:
    """Extracts function spans from C source using heuristic scanning."""

    def __init__(self, code: _CodeView):
        self.code = code

    def extract(self) -> List[Tuple[str, int, int, int, int]]:
        clean = self.code.cleaned
        n = len(clean)
        i = 0
        results: List[Tuple[str, int, int, int, int]] = []
        while i < n:
            ch = clean[i]
            if not _is_identifier_start(ch):
                i += 1
                continue

            ident_start = i
            while i < n and _is_identifier_char(clean[i]):
                i += 1
            ident = clean[ident_start:i]

            if ident in _KEYWORDS:
                continue

            j = self.code.skip_whitespace(i)
            if j >= n or clean[j] != "(":
                i = j
                continue

            param_end = self.code.find_matching(j, "(", ")")
            if param_end == -1:
                i = j + 1
                continue

            k = self.code.skip_whitespace(param_end + 1)
            if clean.startswith("__attribute__", k):
                attr_start = k + len("__attribute__")
                attr_start = self.code.skip_whitespace(attr_start)
                if attr_start < n and clean[attr_start] == "(":
                    attr_end = self.code.find_matching(attr_start, "(", ")")
                    if attr_end != -1:
                        k = self.code.skip_whitespace(attr_end + 1)

            if k >= n or clean[k] != "{":
                i = param_end + 1
                continue

            body_end = self.code.find_matching(k, "{", "}")
            if body_end == -1:
                break

            signature_start = self._find_signature_start(clean, ident_start)
            results.append((ident, signature_start, k, k + 1, body_end))
            i = body_end + 1
        return results

    def _find_signature_start(self, clean: str, ident_start: int) -> int:
        k = ident_start - 1
        while k > 0 and clean[k] not in ";}":
            k -= 1
        if clean[k] in ";}":
            return k + 1
        return 0


class _StatementParser:
    """Parses a function body into a hierarchical statement structure."""

    def __init__(self, code: _CodeView):
        self.code = code

    def parse_block(self, start: int, end: int) -> List[Statement]:
        statements: List[Statement] = []
        i = start
        while i < end:
            i = self.code.skip_whitespace(i, end)
            if i >= end:
                break
            snippet = self.code.cleaned[i:end]
            if snippet.startswith("if") and self._is_word_boundary(i, i + 2):
                stmt, i = self._parse_if(i, end)
                statements.append(stmt)
                continue
            if snippet.startswith("for") and self._is_word_boundary(i, i + 3):
                stmt, i = self._parse_loop(i, end, "for")
                statements.append(stmt)
                continue
            if snippet.startswith("while") and self._is_word_boundary(i, i + 5):
                stmt, i = self._parse_loop(i, end, "while")
                statements.append(stmt)
                continue
            if snippet.startswith("do") and self._is_word_boundary(i, i + 2):
                stmt, i = self._parse_do_while(i, end)
                statements.append(stmt)
                continue
            if snippet.startswith("return") and self._is_word_boundary(i, i + 6):
                semi_idx = self._find_statement_end(i, end)
                if semi_idx == -1:
                    break
                text = self.code.original[i:semi_idx + 1].strip()
                statements.append(ReturnStatement(start=i, end=semi_idx + 1, text=text))
                i = semi_idx + 1
                continue
            if snippet.startswith("{"):
                block_end = self.code.find_matching(i, "{", "}")
                if block_end == -1:
                    break
                inner = self.parse_block(i + 1, block_end)
                statements.extend(inner)
                i = block_end + 1
                continue

            semi_idx = self._find_statement_end(i, end)
            if semi_idx == -1:
                break
            text = self.code.original[i:semi_idx + 1].strip()
            statements.append(SimpleStatement(start=i, end=semi_idx + 1, text=text))
            i = semi_idx + 1
        return statements

    def _parse_if(self, start: int, limit: int) -> Tuple[IfStatement, int]:
        cond_start = self.code.skip_whitespace(start + 2, limit)
        if cond_start >= limit or self.code.cleaned[cond_start] != "(":
            raise ValueError("Malformed if statement")
        cond_end = self.code.find_matching(cond_start, "(", ")")
        condition = self.code.original[cond_start + 1 : cond_end].strip()
        body_start = self.code.skip_whitespace(cond_end + 1, limit)
        true_block, next_index, body_end = self._parse_statement_block(body_start, limit)
        false_block: List[Statement] = []
        next_index = self.code.skip_whitespace(next_index, limit)
        if self.code.cleaned.startswith("else", next_index) and self._is_word_boundary(
            next_index, next_index + 4
        ):
            else_start = self.code.skip_whitespace(next_index + 4, limit)
            false_block, next_index, _ = self._parse_statement_block(else_start, limit)
        stmt = IfStatement(
            start=start,
            end=next_index,
            condition=condition,
            true_block=true_block,
            false_block=false_block,
        )
        return stmt, next_index

    def _parse_loop(self, start: int, limit: int, loop_type: str) -> Tuple[LoopStatement, int]:
        head_start = self.code.skip_whitespace(start + len(loop_type), limit)
        if head_start >= limit or self.code.cleaned[head_start] != "(":
            raise ValueError("Malformed loop")
        head_end = self.code.find_matching(head_start, "(", ")")
        header = self.code.original[start : head_end + 1].strip()
        body_start = self.code.skip_whitespace(head_end + 1, limit)
        body, next_index, _ = self._parse_statement_block(body_start, limit)
        stmt = LoopStatement(
            start=start,
            end=next_index,
            loop_type=loop_type,
            header=header,
            body=body,
            else_block=[],
        )
        return stmt, next_index

    def _parse_do_while(self, start: int, limit: int) -> Tuple[DoWhileStatement, int]:
        body_start = self.code.skip_whitespace(start + 2, limit)
        body, next_index, body_end = self._parse_statement_block(body_start, limit)
        next_index = self.code.skip_whitespace(next_index, limit)
        if not self.code.cleaned.startswith("while", next_index):
            raise ValueError("Malformed do-while loop")
        cond_head = self.code.skip_whitespace(next_index + 5, limit)
        cond_end = self.code.find_matching(cond_head, "(", ")")
        condition = self.code.original[cond_head + 1 : cond_end].strip()
        semi = self.code.skip_whitespace(cond_end + 1, limit)
        if semi < limit and self.code.cleaned[semi] == ";":
            semi += 1
        stmt = DoWhileStatement(
            start=start,
            end=semi,
            condition=condition,
            body=body,
        )
        return stmt, semi

    def _parse_statement_block(
        self, start: int, limit: int
    ) -> Tuple[List[Statement], int, Optional[int]]:
        if start >= limit:
            return [], start, None
        if self.code.cleaned[start] == "{":
            close = self.code.find_matching(start, "{", "}")
            if close == -1:
                raise ValueError("Unclosed block")
            block_statements = self.parse_block(start + 1, close)
            return block_statements, close + 1, close
        semi = self._find_statement_end(start, limit)
        if semi == -1:
            raise ValueError("Unterminated statement")
        stmt = self.code.original[start:semi + 1].strip()
        return [SimpleStatement(start=start, end=semi + 1, text=stmt)], semi + 1, semi

    def _find_statement_end(self, start: int, limit: int) -> int:
        i = start
        depth_paren = depth_bracket = depth_brace = 0
        in_string = False
        in_char = False
        while i < limit:
            ch = self.code.cleaned[i]
            if ch == '"' and not in_char:
                in_string = not in_string
            elif ch == "'" and not in_string:
                in_char = not in_char
            elif not in_string and not in_char:
                if ch == "(":
                    depth_paren += 1
                elif ch == ")":
                    depth_paren = max(0, depth_paren - 1)
                elif ch == "[":
                    depth_bracket += 1
                elif ch == "]":
                    depth_bracket = max(0, depth_bracket - 1)
                elif ch == "{":
                    depth_brace += 1
                elif ch == "}":
                    if depth_brace == 0:
                        return i
                    depth_brace = max(0, depth_brace - 1)
                elif ch == ";" and depth_paren == depth_bracket == depth_brace == 0:
                    return i
            i += 1
        return -1

    def _is_word_boundary(self, start: int, end: int) -> bool:
        before = self.code.cleaned[start - 1] if start > 0 else " "
        after = self.code.cleaned[end] if end < len(self.code.cleaned) else " "
        return not _is_identifier_char(before) and not _is_identifier_char(after)


class _CFlowBuilder:
    def __init__(self, code: _CodeView, file_path: Optional[str]):
        self.code = code
        self.file_path = file_path or "<memory>"
        self.nodes: List[NodeIR] = []
        self.edges: List[EdgeIR] = []
        self._counter = 0
        self._function_end_id: Optional[str] = None

    def build_function(self, name: str, start: int, body_start: int, body_end: int) -> FunctionIR:
        parser = _StatementParser(self.code)
        statements = parser.parse_block(body_start, body_end)

        self.nodes.clear()
        self.edges.clear()
        self._counter = 0

        start_node = self._add_node(NodeKind.START, "Start", body_start)
        end_node = self._add_node(
            NodeKind.END, "End", body_end, metadata={"reason": "function_terminator"}
        )
        self._function_end_id = end_node

        exits = self._build_block(statements, [(start_node, None)])
        for exit_id in exits:
            if exit_id != end_node:
                self.edges.append(EdgeIR(source=exit_id, target=end_node))

        signature = self.code.original[start:body_start - 1].strip()
        params_match = re.search(r"\((.*)\)", signature, re.DOTALL)
        params = []
        if params_match:
            param_text = params_match.group(1).strip()
            if param_text:
                params = [p.strip() for p in param_text.split(",")]

        return FunctionIR(
            name=name,
            parameters=params,
            nodes=list(self.nodes),
            edges=list(self.edges),
            metadata={"signature": signature},
        )

    def _build_block(
        self, statements: Sequence[Statement], incoming: List[Tuple[str, Optional[str]]]
    ) -> List[str]:
        if not statements:
            return [src for src, _ in incoming]
        current = list(incoming)
        for stmt in statements:
            slice_ = self._slice_for_statement(stmt)
            self._connect(current, slice_.entry_ids)
            current = [(exit_id, None) for exit_id in slice_.exit_ids]
            if not current:
                break
        return [src for src, _ in current]

    def _slice_for_statement(self, stmt: Statement) -> "_GraphSlice":
        if isinstance(stmt, IfStatement):
            return self._handle_if(stmt)
        if isinstance(stmt, LoopStatement):
            return self._handle_loop(stmt)
        if isinstance(stmt, DoWhileStatement):
            return self._handle_do_while(stmt)
        if isinstance(stmt, ReturnStatement):
            return self._handle_return(stmt)
        label = stmt.text.strip()
        node_id = self._add_node(NodeKind.STATEMENT, label, stmt.start)
        return _GraphSlice(entry_ids=[node_id], exit_ids=[node_id])

    def _handle_if(self, stmt: IfStatement) -> "_GraphSlice":
        label = f"if ({stmt.condition})"
        cond_id = self._add_node(NodeKind.CONDITIONAL, label, stmt.start)
        true_exits = self._build_block(stmt.true_block, [(cond_id, "True")])
        false_exits = (
            self._build_block(stmt.false_block, [(cond_id, "False")])
            if stmt.false_block
            else [cond_id]
        )
        exit_ids = list(dict.fromkeys(true_exits + false_exits))
        return _GraphSlice(entry_ids=[cond_id], exit_ids=exit_ids)

    def _handle_loop(self, stmt: LoopStatement) -> "_GraphSlice":
        label = stmt.header
        loop_id = self._add_node(NodeKind.LOOP, label, stmt.start)
        body_exits = self._build_block(stmt.body, [(loop_id, "Loop body")])
        for exit_id in body_exits:
            self.edges.append(EdgeIR(source=exit_id, target=loop_id, label="Iterate"))
        exit_ids = [loop_id]
        return _GraphSlice(entry_ids=[loop_id], exit_ids=exit_ids)

    def _handle_do_while(self, stmt: DoWhileStatement) -> "_GraphSlice":
        label = f"do-while ({stmt.condition})"
        loop_id = self._add_node(NodeKind.LOOP, label, stmt.start)
        body_exits = self._build_block(stmt.body, [(loop_id, "Loop body")])
        for exit_id in body_exits:
            self.edges.append(EdgeIR(source=exit_id, target=loop_id, label="Iterate"))
        exit_ids = [loop_id]
        return _GraphSlice(entry_ids=[loop_id], exit_ids=exit_ids)

    def _handle_return(self, stmt: ReturnStatement) -> "_GraphSlice":
        node_id = self._add_node(NodeKind.RETURN, stmt.text, stmt.start)
        if self._function_end_id:
            self.edges.append(EdgeIR(source=node_id, target=self._function_end_id, label="Return"))
        return _GraphSlice(entry_ids=[node_id], exit_ids=[])

    def _add_node(
        self, kind: NodeKind, label: str, index: int, metadata: Optional[dict] = None
    ) -> str:
        node_id = f"n{self._counter}"
        self._counter += 1
        location = self.code.index_to_location(index)
        location.file_path = self.file_path
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

    def _summarize(self, kind: NodeKind, label: str) -> str:
        if kind is NodeKind.START:
            return "Begin the function."
        if kind is NodeKind.END:
            return "Finish the function."
        if kind is NodeKind.LOOP:
            return summarize_loop(label)
        if kind is NodeKind.CONDITIONAL:
            return summarize_expression(label)
        return summarize_statement(label)

    def _connect(self, sources: List[Tuple[str, Optional[str]]], targets: List[str]) -> None:
        for source, label in sources:
            for target in targets:
                self.edges.append(EdgeIR(source=source, target=target, label=label))


@dataclass
class _GraphSlice:
    entry_ids: List[str]
    exit_ids: List[str]


class CSimpleParser(LanguageParser):
    language = "c"

    def parse_code(self, code: str, *, file_path: Optional[str] = None) -> ModuleIR:
        view = _CodeView(code)
        extractor = _FunctionExtractor(view)
        functions_meta = extractor.extract()
        builder = _CFlowBuilder(view, file_path)
        functions: List[FunctionIR] = []
        for name, sig_start, brace_start, body_start, body_end in functions_meta:
            try:
                fn_ir = builder.build_function(name, sig_start, body_start, body_end)
                functions.append(fn_ir)
            except Exception:
                # Skip functions that fail to parse; they can be revisited with better heuristics.
                continue
        return ModuleIR(
            language=self.language,
            functions=functions,
            metadata={"file_path": file_path},
        )


register_parser(CSimpleParser.language, CSimpleParser)
