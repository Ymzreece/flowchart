from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from . import serializer
from .registry import get_parser, list_languages


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Generate Flow IR from source code.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_cmd = subparsers.add_parser("parse", help="Parse a single source file into Flow IR JSON.")
    parse_cmd.add_argument("path", type=Path, help="Source file to parse.")
    parse_cmd.add_argument("--language", "-l", required=True, help="Language identifier (see list-languages).")
    parse_cmd.add_argument("--out", "-o", type=Path, help="Optional output file (defaults to stdout).")
    parse_cmd.add_argument("--indent", type=int, default=2, help="JSON indentation (default: 2).")

    subparsers.add_parser("list-languages", help="List registered languages.")

    args = parser.parse_args(argv)

    if args.command == "list-languages":
        for language in list_languages():
            print(language)
        return

    if args.command == "parse":
        module = get_parser(args.language).parse_file(args.path)
        output = serializer.module_to_json(module, indent=args.indent)
        if args.out:
            args.out.write_text(output, encoding="utf-8")
        else:
            print(output)


if __name__ == "__main__":  # pragma: no cover
    main()
