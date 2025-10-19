from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import FlowGraph


TYPE_STYLE = {
    "start": ("▶", "bold green"),
    "end": ("■", "red"),
    "decision": ("◆", "yellow"),
    "loop": ("🔁", "cyan"),
    "call": ("⚙", "magenta"),
    "io": ("⌨", "blue"),
    "process": ("●", "white"),
}


def render_terminal(graph: FlowGraph, *, console: Console | None = None) -> None:
    console = console or Console()

    if graph.metadata.get("summary"):
        console.print(Panel(graph.metadata["summary"], title=graph.metadata.get("title", "Flowchart")))

    adjacency = graph.adjacency()

    for node_id, node in graph.nodes.items():
        icon, color = TYPE_STYLE.get(node.type.lower(), ("●", "white"))
        title = f"{icon} {node.title} [{node.id}]"
        table = Table(title=title, title_style=color)
        table.add_column("Summary", style="bold")
        table.add_column("Leads To", style="cyan")

        outgoing = adjacency.get(node_id, [])
        if not outgoing:
            table.add_row(node.summary, "(no outgoing edges)")
        else:
            for idx, edge in enumerate(outgoing):
                target_node = graph.nodes.get(edge.target)
                target_title = target_node.title if target_node else edge.target
                label = f" — {edge.label}" if edge.label else ""
                summary_text = node.summary if idx == 0 else ""
                table.add_row(summary_text, f"{target_title}{label}")

        if node.detail:
            table.add_row(f"Detail: {node.detail}", "")

        console.print(table)


def render_graphviz(graph: FlowGraph) -> str:
    try:
        from graphviz import Digraph
    except Exception as exc:  # pragma: no cover - optional dependency missing
        raise RuntimeError("graphviz extra not installed. `pip install flowcode_2[graphviz]`") from exc

    dot = Digraph("Flowchart", graph_attr={"rankdir": "TB", "splines": "spline"})

    for node in graph.nodes.values():
        shape = "box"
        fillcolor = "#ffffff"
        if node.type.lower() == "start":
            fillcolor = "#bbf7d0"
        elif node.type.lower() == "end":
            fillcolor = "#fecaca"
        elif node.type.lower() == "decision":
            shape = "diamond"
            fillcolor = "#fde68a"
        elif node.type.lower() == "loop":
            fillcolor = "#cffafe"

        label = f"{node.title}\n{node.summary}"
        dot.node(node.id, label, shape=shape, style="filled", fillcolor=fillcolor)

    for edge in graph.edges:
        attrs = {}
        if edge.label:
            attrs["label"] = edge.label
        dot.edge(edge.source, edge.target, **attrs)

    if graph.entry_node and graph.entry_node in graph.nodes:
        dot.node("entry", "START", shape="plaintext")
        dot.edge("entry", graph.entry_node, arrowhead="normal")

    return dot.source
