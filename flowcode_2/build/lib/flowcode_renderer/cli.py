from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from rich.console import Console

from .converter import graph_to_stage2_module
from .parser import parse_graph
from .renderer import render_graphviz, render_terminal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render flowcharts produced by flowcode_1.")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("flowchart_en.json"),
        help="Path to flowchart JSON (default: flowchart_en.json).",
    )
    parser.add_argument(
        "--input-format",
        choices=("auto", "text", "json"),
        default="auto",
        help="Input format (default: auto).",
    )
    parser.add_argument(
        "--format",
        choices=("terminal", "graphviz", "stage2"),
        default="terminal",
        help="Output format (default: terminal).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file (required for graphviz).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    format_arg = args.input_format if args.input_format != "auto" else None
    graph = parse_graph(args.input, input_format=format_arg)

    if args.format == "terminal":
        render_terminal(graph, console=Console())
        return

    if args.output is None:
        raise SystemExit("--output is required when --format graphviz or stage2")

    if args.format == "graphviz":
        dot_source = render_graphviz(graph)
        args.output.write_text(dot_source, encoding="utf-8")
        print(f"Wrote Graphviz DOT to {args.output}")
        return

    if args.format == "stage2":
        module = graph_to_stage2_module(graph)
        import json

        args.output.write_text(json.dumps(module, indent=2), encoding="utf-8")
        print(f"Wrote Stage2-compatible JSON to {args.output}")
        return


if __name__ == "__main__":  # pragma: no cover
    main()
