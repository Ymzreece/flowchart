# Flowcode 2 — Flowchart Renderer

This module converts the natural-language explanation produced by `flowcode_1` into a structured flowchart graph and renders it in several formats (terminal, Graphviz, Stage 2 JSON).

## Project Structure

```
flowcode_2/
├── graph_generator.py       # LLM call: explanation → flowchart.json
├── pyproject.toml
├── README.md
├── src/
│   └── flowcode_renderer/
│       ├── __init__.py
│       ├── cli.py           # Renderer CLI (terminal/graphviz/stage2)
│       ├── converter.py
│       ├── models.py
│       ├── parser.py
│       └── renderer.py
└── tests/
    └── test_graph_processing.py
```

## Workflow

1. Run `flowcode_1/flowchart_generator.py` to produce `flow_explanation.txt` (rich text narrative).
2. Convert that explanation into graph JSON:

   ```bash
   python graph_generator.py \
     --input ../flow_explanation.txt \
     --output flowchart.json
   ```

3. Render or export the graph:

   ```bash
   python -m flowcode_renderer.cli \
     --input flowchart.json \
     --output flowchart.stage2.json \
     --format stage2
   ```

   Omitting `--output` prints an ASCII flowchart directly in the terminal.

## Features

- Converts explanations to node/edge graphs using `graph_generator.py` (LLM-powered).
- Parses the JSON node/edge graph (`parse_graph`) and falls back to legacy outline if needed (`--input-format text`).
- Renders to:
  - **Terminal**: hierarchical view using `rich`.
  - **Graphviz DOT** (optional: install `graphviz` and pass `--format graphviz`).
  - **Stage 2 JSON**: `--format stage2` writes a payload compatible with the React Flow UI.
- Auto-detects the format based on file extension when possible.

## Installation

```bash
pip install -e flowcode_2
```

Graphviz export is optional; install via `pip install flowcode_2[graphviz]` if you want DOT output.

## Command Reference

Generate the explanation (Stage 1):

```bash
python ../flowcode_1/flowchart_generator.py \
  --prompt ../flowcode_1/prompt.md \
  --output flow_explanation.txt
```

Convert explanation → graph JSON:

```bash
python graph_generator.py \
  --input ../flow_explanation.txt \
  --output flowchart.json
```

Render graph (terminal / Graphviz / Stage 2):

```bash
python -m flowcode_renderer.cli \
  --input flowchart.json \
  --format terminal

python -m flowcode_renderer.cli \
  --input flowchart.json \
  --format graphviz \
  --output flowchart.dot

python -m flowcode_renderer.cli \
  --input flowchart.json \
  --format stage2 \
  --output flowchart.stage2.json
```

Renderer CLI arguments:

- `--input` / `-i`: Path to the flowchart JSON (default: `flowchart.json`).
- `--input-format`: `auto` (default), `text`, or `json`.
- `--format`: `terminal`, `graphviz`, or `stage2`.
- `--output` / `-o`: Required for `graphviz` and `stage2` modes.

## Integrations

- Pair with Stage 2 by exporting Stage 2 JSON (`--format stage2`) and importing it into the React Flow editor.
- Export Graphviz to SVG (`dot -Tsvg flowchart.dot > flowchart.svg`).
- Hook into a web frontend by reading the parsed data from `parse_graph()`.

## Tests

Run unit tests with:

```bash
python -m unittest discover -s flowcode_2/tests
```

## Next Steps

- Enhance text parser to support more output variants (e.g., nested bullets, numbered substeps).
- Add a direct React Flow exporter to integrate with the Stage 2 canvas.
- Support incremental updates when `flowchart.txt` changes (file watcher).
