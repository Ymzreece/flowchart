from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - dependency missing at runtime only
    raise SystemExit(
        "Missing dependency 'openai'. Install it with `pip install openai`."
    ) from exc


MODEL_NAME = "gpt-4.1-mini"


SYSTEM_PROMPT = """You are a senior software architect who explains codebases in clear, natural language.
Given raw source code or a textual project description, produce a flowchart-style outline that:
- Describes each step as a short sentence or phrase understandable by non-developers.
- Groups related steps logically (e.g., setup, condition, loop, clean-up).
- Mentions key conditions/branches and their outcomes.
- Includes function names only when they clarify intent; otherwise favour descriptive language.
If the user requests JSON, return an array of stages, each with a 'title' and 'steps' list.
"""

JSON_INSTRUCTION = """
Return the result as a JSON object with an array named "stages". Each stage must include a "title" string and a "steps" array of natural-language sentences. The JSON must be valid.
"""


def read_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Prompt file not found: {path}")


def write_output(path: Optional[Path], content: str) -> None:
    if path is None:
        print(content)
        return
    path.write_text(content, encoding="utf-8")
    print(f"Wrote flowchart summary to {path}")


def call_model(prompt: str, *, response_format: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "Environment variable OPENAI_API_KEY is not set. "
            "Export your API key before running this script."
        )

    client = OpenAI(api_key=api_key)

    full_prompt = prompt
    if response_format == "json":
        full_prompt = f"{prompt}\n\n{JSON_INSTRUCTION.strip()}"

    response = client.responses.create(
        model=MODEL_NAME,
        instructions=SYSTEM_PROMPT,
        input=full_prompt,
    )

    if hasattr(response, "output_text"):
        return response.output_text  # type: ignore[attr-defined]

    try:
        return response.output[0].content[0].text  # type: ignore[attr-defined]
    except (AttributeError, IndexError, KeyError) as exc:  # pragma: no cover - unexpected API shape
        raise SystemExit(f"Unexpected API response format: {response}") from exc


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a natural-language flowchart using an LLM."
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path("prompt.md"),
        help="Path to the prompt file (default: prompt.md).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Where to save the generated flowchart. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Response format (default: text).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=MODEL_NAME,
        help=f"Override the model name (default: {MODEL_NAME}).",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Print the prompt content before sending it to the model.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    prompt_path: Path = args.prompt
    output_path: Optional[Path] = args.output

    prompt_text = read_prompt(prompt_path)
    if not prompt_text.strip():
        raise SystemExit(f"Prompt file {prompt_path} is empty.")

    global MODEL_NAME
    MODEL_NAME = args.model

    print(f"Using model: {MODEL_NAME}")
    if output_path:
        print(f"Will write output to: {output_path}")
    if args.show_prompt:
        print("--- Prompt being sent ---")
        print(prompt_text)
        print("--------------------------")

    result = call_model(prompt_text, response_format=args.format)
    write_output(output_path, result)


if __name__ == "__main__":
    main(sys.argv[1:])
