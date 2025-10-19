from __future__ import annotations

import argparse
import json
import os
from importlib import resources
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency 'openai'. Install it with `pip install openai`.") from exc

from .parser import parse_graph
from .converter import graph_to_stage2_module


DEFAULT_STAGE1_MODEL = "gpt-5"
DEFAULT_STAGE2_MODEL = "gpt-5-nano"


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

GRAPH_SYSTEM_PROMPT_EN = """You are a senior software architect converting prose explanations into a structured flowchart graph.
Given a detailed natural-language walkthrough of a system, extract every major step, branch, loop, and background activity into nodes and edges that describe control flow.
All textual descriptions must be in English and understandable to non-developers."""

GRAPH_OUTPUT_INSTRUCTION_EN = """
Return ONLY JSON matching this schema:
{
  "metadata": {"title": "Concise title", "summary": "1-2 sentence overview", "language": "en"},
  "entry_node": "node id",
  "nodes": [{
    "id": "unique string id",
    "title": "Short descriptive title",
    "summary": "One-sentence description of this step",
    "detail": "Optional longer explanation (can be null)",
    "type": "start|process|decision|loop|end|io|call"
  }],
  "edges": [{"source": "node id", "target": "node id", "label": "optional"}]
}
Guidelines:
- Include start and end nodes where appropriate.
- Capture each branch or menu option as its own node and label edges with the condition/key press triggering the transition.
- Represent loops explicitly with nodes of type `loop` and show how they iterate and exit.
- Ensure the graph is connected from the entry node and all IDs remain consistent.
- Do not wrap the JSON in code fences or add commentary.
"""

TRANSLATION_SYSTEM_PROMPT_ZH = """You are a meticulous technical translator.
Preserve the structure of a flowchart JSON object while translating every human-readable string into Simplified Chinese.
Keep IDs, node types, and all structural fields exactly the same."""

TRANSLATION_INSTRUCTION_ZH = """
You will receive a flowchart JSON object in English. Return the same JSON structure, but translate these fields into Simplified Chinese:
- metadata.title, metadata.summary (set metadata.language to "zh")
- nodes[].title, nodes[].summary, nodes[].detail
- edges[].label
Do not alter IDs, node types, or add/remove fields. Return only JSON without code fences.
"""


def _ensure_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    # Best-effort fallback: parse a .env in current working directory
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("OPENAI_API_KEY="):
                key = s.split("=", 1)[1].strip()
                break
            if s.lower().startswith("openai_api_key:"):
                key = s.split(":", 1)[1].strip()
                break
            if s.startswith("sk-"):
                key = s
                break
    if not key:
        raise SystemExit("OPENAI_API_KEY not set. Export it or provide it in a .env file.")
    os.environ["OPENAI_API_KEY"] = key
    return key


def _openai_client() -> OpenAI:
    _ensure_api_key()
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])  # type: ignore[literal-required]


def _stage1_generate_narrative(include_file: Path, *, model: str, show_prompt: bool) -> str:
    # Load default prompt from package data
    try:
        with resources.files("flowcode_renderer.data").joinpath("prompt.md").open("r", encoding="utf-8") as f:
            base_prompt = f.read()
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"Failed to load packaged prompt: {exc}")

    try:
        included = include_file.read_text(encoding="utf-8")
    except Exception as exc:
        raise SystemExit(f"Failed to read include file {include_file}: {exc}")

    prompt = f"{base_prompt}\n\n===== Included File: {include_file} =====\n{included}\n===== End Included File =====\n"

    client = _openai_client()
    if show_prompt:
        print("--- Stage 1 Prompt ---")
        print(prompt)
        print("----------------------")
    response = client.responses.create(model=model, instructions=TEXT_SYSTEM_PROMPT, input=prompt)
    text = getattr(response, "output_text", None)
    if not text:
        # fallback
        try:
            text = response.output[0].content[0].text  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"Unexpected API response format: {response}") from exc
    return text.strip()


def _call_model(prompt: str, instructions: str, *, model: str, show_prompt: bool) -> str:
    client = _openai_client()
    if show_prompt:
        print("--- Prompt being sent ---")
        print(prompt)
        print("--------------------------")
    response = client.responses.create(model=model, instructions=instructions, input=prompt)
    text = getattr(response, "output_text", None)
    if text:
        return text
    try:
        return response.output[0].content[0].text  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"Unexpected API response format: {response}") from exc


def _stage2_generate_graphs(explanation: str, *, model: str, show_prompt: bool) -> tuple[dict, dict]:
    prompt_en = f"{explanation}\n\n{GRAPH_OUTPUT_INSTRUCTION_EN.strip()}"
    raw_en = _call_model(prompt_en, GRAPH_SYSTEM_PROMPT_EN, model=model, show_prompt=show_prompt)
    try:
        data_en = json.loads(raw_en)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"English graph generation failed: {exc}\nRaw output:\n{raw_en}") from exc
    if isinstance(data_en, dict):
        data_en.setdefault("metadata", {}).update({"language": "en"})

    english_json = json.dumps(data_en, ensure_ascii=False, indent=2)
    prompt_zh = f"Here is a flowchart JSON object in English:\n{english_json}\n\n{TRANSLATION_INSTRUCTION_ZH.strip()}"
    raw_zh = _call_model(prompt_zh, TRANSLATION_SYSTEM_PROMPT_ZH, model=model, show_prompt=show_prompt)
    try:
        data_zh = json.loads(raw_zh)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Chinese translation failed: {exc}\nRaw output:\n{raw_zh}") from exc
    if isinstance(data_zh, dict):
        data_zh.setdefault("metadata", {}).update({"language": "zh"})
    return data_en, data_zh


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run the full Flowcode pipeline on a single file.")
    p.add_argument("filename", type=Path, help="Path to the file to include in the prompt.")
    p.add_argument("--open-ui", action="store_true", help="Launch the Stage 2 dev server after generation.")
    p.add_argument("--explanation", type=Path, default=Path("flow_explanation.txt"), help="Path for the generated explanation (default: flow_explanation.txt).")
    p.add_argument("--output-prefix", type=str, default="flowchart", help="Base name for generated flowchart JSON (default: flowchart_*.json).")
    p.add_argument("--model-stage1", type=str, default=DEFAULT_STAGE1_MODEL, help=f"Model for Stage 1 (default: {DEFAULT_STAGE1_MODEL}).")
    p.add_argument("--model-stage2", type=str, default=DEFAULT_STAGE2_MODEL, help=f"Model for Stage 2 (default: {DEFAULT_STAGE2_MODEL}).")
    p.add_argument("--show-prompts", action="store_true", help="Echo prompts sent to the model.")
    return p


def main(argv: Optional[list[str]] = None) -> None:
    args = build_parser().parse_args(argv)

    include_path = args.filename
    if not include_path.exists():
        raise SystemExit(f"Input file not found: {include_path}")

    # Stage 1 — narrative
    narrative = _stage1_generate_narrative(include_path, model=args.model_stage1, show_prompt=args.show_prompts)
    args.explanation.write_text(narrative, encoding="utf-8")
    print(f"Wrote explanation to {args.explanation}")

    # Stage 2 — bilingual graphs
    en, zh = _stage2_generate_graphs(narrative, model=args.model_stage2, show_prompt=args.show_prompts)
    en_path = Path(f"{args.output_prefix}_en.json")
    zh_path = Path(f"{args.output_prefix}_zh.json")
    en_path.write_text(json.dumps(en, ensure_ascii=False, indent=2), encoding="utf-8")
    zh_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote flowcharts: {en_path}, {zh_path}")

    # Stage 3 — Stage2 conversion
    graph_en = parse_graph(en_path)
    module_en = graph_to_stage2_module(graph_en)
    (Path(f"{args.output_prefix}_en.stage2.json")).write_text(json.dumps(module_en, indent=2), encoding="utf-8")

    graph_zh = parse_graph(zh_path)
    module_zh = graph_to_stage2_module(graph_zh)
    (Path(f"{args.output_prefix}_zh.stage2.json")).write_text(json.dumps(module_zh, indent=2), encoding="utf-8")
    print("Converted flowcharts to Stage2 JSON.")

    if args.open_ui:
        # Keep this opt-in and simple; rely on user's environment
        os.execvp("npm", ["npm", "run", "dev", "--prefix", str(Path("Archive") / "stage2")])


if __name__ == "__main__":  # pragma: no cover
    main()

