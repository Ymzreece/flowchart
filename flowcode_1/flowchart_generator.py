from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - dependency missing at runtime only
    raise SystemExit("Missing dependency 'openai'. Install it with `pip install openai`.") from exc


DEFAULT_MODEL = "gpt-5-nano"


TEXT_SYSTEM_PROMPT = """You are a senior software architect tasked with documenting codebases for cross-functional teams.
Analyse the provided source code or description thoroughly and produce a comprehensive, natural-language walkthrough that includes:
- A concise overview of the system's purpose and context.
- A description of the high-level pipeline or flow from inputs to outputs.
- Detailed sections that explain each major component, function, menu, or background task, how they interact, and why they exist.
- Explicit explanations of important branches, menu options, loops, state transitions, and error handling.
- Notes on data storage, external integrations, and any assumptions or limitations.
Write in clear paragraphs and bullet lists so non-developers can follow the logic.
Avoid dumping large blocks of raw code unless necessary to illustrate intent.
"""

JSON_SYSTEM_PROMPT = """You are a senior software architect converting prose into a structured flowchart graph.
Only return valid JSON that captures all major steps, decisions, loops, and transitions present in the text."""

JSON_INSTRUCTION = """
Return ONLY JSON matching this structure:
{
  "metadata": {
    "title": "Concise title for the system",
    "summary": "1-2 sentence overview",
    "language": "text"
  },
  "entry_node": "node_id",
  "nodes": [
    {
      "id": "unique string id",
      "title": "Short descriptive title",
      "summary": "One-sentence description of this step",
      "detail": "Optional longer explanation (can be null)",
      "type": "start|process|decision|loop|end|io|call"
    }
  ],
  "edges": [
    {
      "source": "node id",
      "target": "node id",
      "label": "Condition or trigger for this transition (optional)"
    }
  ]
}
Rules:
- Represent every significant branch, menu option, or background path as a separate node and connect them with labelled edges.
- Use `type="decision"` for branching points, `type="loop"` for repeated actions, and `type="process"` for regular steps.
- Ensure every edge references valid node IDs and the graph is connected from the entry node.
- Do not wrap the JSON in code fences or include commentary.
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
    print(f"Wrote output to {path}")


def call_model(prompt: str, *, response_format: str, model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "Environment variable OPENAI_API_KEY is not set. "
            "Export your API key before running this script."
        )

    client = OpenAI(api_key=api_key)

    if response_format == "json":
        instructions = JSON_SYSTEM_PROMPT
        payload = f"{prompt}\n\n{JSON_INSTRUCTION.strip()}"
    else:
        instructions = TEXT_SYSTEM_PROMPT
        payload = prompt

    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=payload,
    )

    if hasattr(response, "output_text"):
        return response.output_text  # type: ignore[attr-defined]

    try:
        return response.output[0].content[0].text  # type: ignore[attr-defined]
    except (AttributeError, IndexError, KeyError) as exc:  # pragma: no cover - unexpected API response shape
        raise SystemExit(f"Unexpected API response format: {response}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a natural-language explanation using an LLM.")
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path("prompt.md"),
        help="Path to the prompt file (default: prompt.md).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Where to save the generated explanation. If omitted, prints to stdout.",
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
        default=DEFAULT_MODEL,
        help=f"Override the model name (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Print the prompt content before sending it to the model.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt_text = read_prompt(args.prompt)
    if not prompt_text.strip():
        raise SystemExit(f"Prompt file {args.prompt} is empty.")

    print(f"Using model: {args.model}")
    if args.output:
        print(f"Will write output to: {args.output}")
    if args.show_prompt:
        print("--- Prompt being sent ---")
        print(prompt_text)
        print("--------------------------")

    result = call_model(prompt_text, response_format=args.format, model=args.model)

    if args.format == "json":
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Model did not return valid JSON: {exc}\nRaw output:\n{result}") from exc
        formatted = json.dumps(parsed, indent=2)
        write_output(args.output, formatted)
    else:
        write_output(args.output, result.strip())


if __name__ == "__main__":
    main(sys.argv[1:])
