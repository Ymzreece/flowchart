# Flowcode Project Profile

## Overview

Flowcode is a multi-stage toolchain for turning source code or textual briefs into interactive control-flow visualisations. The workflow combines two Python stages (LLM-backed content generation and graph conversion) with a React + TypeScript editor that renders and edits the resulting graphs.

## End-to-End Flow

1. **Narrative generation (`flowcode_1/`)**  
   `flowchart_generator.py` sends the prompt in `prompt.md` to OpenAI (`OPENAI_API_KEY` must be set) and writes a rich natural-language walkthrough to `flow_explanation.txt` or a user-specified path.
2. **Graph extraction + localisation (`flowcode_2/graph_generator.py`)**  
   Converts the narrative into structured flowchart JSON, emitting `*_en.json` and `*_zh.json`. The same model call is used for the English graph, followed by a second call that translates human-readable strings to Simplified Chinese while preserving structure.
3. **Rendering utilities (`flowcode_2/src/flowcode_renderer/`)**  
   `parse_graph` understands both JSON and outline text. `cli.py` renders to the terminal (`rich` tables), Graphviz DOT, or Stage 2 JSON via `converter.py`.
4. **Interactive editor (`Archive/stage2/`)**  
   React Flow canvas that loads Stage 2 JSON modules, highlights control-flow, supports bilingual display, and prepares edited graphs for export.

**Key Artifacts**

- `flow_explanation*.txt` — freeform narrative produced by Stage 1.  
- `flowchart_{en,zh}.json` — bilingual graph representation with `metadata`, `nodes`, `edges`, and optional `stages` fallback.  
- `flowchart*.stage2.json` — Stage 2-compatible module schema for the React editor.  
- `Archive/stage2/tests/FlowEditor.test.tsx` / `flowcode_2/tests/test_graph_processing.py` — regression tests around parsing and rendering.

## Repository Layout

- `flowcode_1/` — Stage 1 CLI (OpenAI -> narrative).  
- `flowcode_2/` — Stage 2 conversion + renderer package (`pyproject.toml`, unit tests).  
- `Archive/stage2/` — React + TypeScript front-end editor scaffolded with Vite.  
- `Archive/stage1/` — earlier prototype of the Stage 1 pipeline (kept for reference).  
- Root assets (`flow.md`, `flowchart*.json`, etc.) record sample runs and outputs.  
- `AGENTS.md`, `openspec/` — OpenSpec metadata and change tracking.

## Tech Stack

### Python stages

- **Runtime**: Python 3.9+. Code relies on `from __future__ import annotations`, dataclasses, and rich type hints.  
- **Dependencies**:
  - `openai` SDK for both Stage 1 and Stage 2 LLM calls.
  - `rich` for terminal rendering (`flowcode_renderer.renderer.render_terminal`).
  - Optional `graphviz` extra for DOT export (`pip install flowcode_2[graphviz]`).  
- **Packaging**: `flowcode_2` is an editable package (`pip install -e flowcode_2`) exposing `flowcode_renderer` modules.  
- **Testing**: `unittest` suite (`flowcode_2/tests/test_graph_processing.py`) validates JSON parsing and Stage 2 conversion.

### Frontend stage (`Archive/stage2`)

- **Tooling**: Vite + TypeScript + React 18.  
- **Graph canvas**: `reactflow` for node/edge visualisation and editing.  
- **State**: `zustand` store (`useFlowStore.ts`) orchestrates current module/function, selection, and language.  
- **Styling**: Hand-authored CSS (`src/styles/index.css`) with utility classes; `clsx` assists conditional class building.  
- **Internationalisation**: Lightweight localisation (`src/i18n`) toggles between English and Chinese labels supplied by Stage 2 JSON.  
- **Testing**: Vitest + Testing Library (`npm test` / `npm run test`).

## Data Contracts & Conversions

- **Stage 1 output**: freeform prose.
- **Stage 2 graph JSON**:  
  ```json
  {
    "metadata": {"title": "", "summary": "", "language": "en|zh"},
    "entry_node": "node-id",
    "nodes": [{"id": "", "title": "", "summary": "", "detail": null, "type": "start|process|decision|loop|end|io|call"}],
    "edges": [{"source": "", "target": "", "label": ""}],
    "stages": [...]
  }
  ```
- `stages` is an optional array used when the LLM falls back to outline text.
- **Renderer IR (`FlowGraph`)**: Dataclasses defined in `flowcode_renderer.models` power CLI rendering, preserve metadata, and expose `adjacency()` for traversals.
- **Stage 2 module schema**: `graph_to_stage2_module` maps `FlowGraph` to the React Flow-compatible format (`language`, `functions[]`, `nodes[]`, `edges[]`, optional `docstring`). The front-end mirrors this contract in `Archive/stage2/src/lib/graphSchema.ts`.

## Conventions & Practices

- **Environment**: Require `OPENAI_API_KEY`; CLI scripts exit via `SystemExit` with descriptive error messages when preconditions fail (missing files, empty prompts, missing keys).  
- **File naming**:
  - Input prompts in `prompt.md`.
  - Outputs default to `flow_explanation.txt`, `flowchart_en.json`, `flowchart_zh.json`; overrides use `--output`/`--output-prefix`.
  - Stage 2 exports expect `.stage2.json` suffix when targeting the React UI.
- **Encoding**: All disk writes use UTF-8 (`ensure_ascii=False` for Chinese JSON).  
- **Type hints**: Consistent use of explicit typing, dataclasses, and `Optional[...]` to keep the LLM-assisted pipeline self-documenting.  
- **CLI ergonomics**: All scripts build argument parsers (`argparse`), validate inputs early, and print canonical success messages (“Wrote …”).  
- **Testing placement**: Python tests live under `flowcode_2/tests/`; frontend tests under `Archive/stage2/tests/`.  
- **Frontend structure**: Path aliases (`@hooks`, `@lib`, `@i18n`) configured via `tsconfig*.json`; components split into `components/`, `pages/`, `hooks/`, `services/`, `styles/`. React Flow is wrapped in `ReactFlowProvider` and enhanced with custom highlighting utilities.  
- **Localization workflow**: Stage 2 JSON carries a `metadata.language` flag; the front-end store auto-detects language and allows switching (`setLanguage`). When Stage 1 outputs English-only, the UI keeps the previous selection.

## Setup & Commands

- Generate narrative: `python flowcode_1/flowchart_generator.py --prompt flowcode_1/prompt.md --output flow_explanation.txt`
- Produce bilingual graphs: `python flowcode_2/graph_generator.py --input flow_explanation.txt --output-prefix flowchart`
- Render terminal view: `PYTHONPATH=flowcode_2/src python -m flowcode_renderer.cli --input flowchart_en.json --format terminal`
- Export Stage 2 JSON: `python -m flowcode_renderer.cli --input flowchart_en.json --format stage2 --output flowchart.stage2.json`
- Run interactive editor: `npm install --prefix Archive/stage2 && npm run dev --prefix Archive/stage2`
- Test suites:
  - Python: `python -m unittest discover -s flowcode_2/tests`
  - Frontend: `npm run test --prefix Archive/stage2`

## Known Gaps / Future Directions

- Stage 1/2 rely on OpenAI APIs; add adapters or mock layers for offline testing.  
- Expand Python test coverage to include outline parsing and Graphviz rendering.  
- Stage 2 React app currently lives under `Archive/`; plan to surface it as an active package once editing workflows stabilise.  
- Introduce automated linting (`ruff`, `prettier`, `eslint`) to codify style conventions referenced informally above.
