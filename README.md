# Flowcode — Generate and View Code Flowcharts

Flowcode turns source files into bilingual flowcharts (EN/ZH) and a Stage 2 JSON that can be explored in a browser UI. It wraps a two‑stage LLM pipeline and a small React + Vite frontend.

This README explains how to install and use the Flowcode CLI on macOS and Windows (PowerShell/Cmd), via Python (pipx/pip) or a neat npm wrapper.

## Quick Start

- One-line install via npm
  - `npm install -g @reececantcode/flowcode` (use your published scope/name)
  - The installer attempts to bootstrap the Python CLI automatically using `python -m pip install --user`. If it cannot, it prints a short hint.
- Install with pipx (recommended alternative)
  - macOS/Linux
    - `pipx install "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2"`
  - Windows (PowerShell)
    - `pipx install "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2"`
  - If pipx is missing: `python -m pip install --user pipx && pipx ensurepath`, then open a new terminal.
- Set your API key
  - macOS/Linux (zsh/bash): `export OPENAI_API_KEY='sk-...'`
  - Windows PowerShell: `$env:OPENAI_API_KEY='sk-...'`
  - Windows Cmd: `set OPENAI_API_KEY=sk-...`
  - Optional: put `OPENAI_API_KEY=sk-...` in a local `.env` (the CLI also supports `api:` on one line and the key on the next).
- Generate:
  - `flowcode path/to/source.py`
- View (auto‑open UI):
  - `flowcode view path/to/source.py`
  - Or view an existing Stage 2 JSON: `flowcode view flowchart_en.stage2.json`

Note: Viewing in the browser requires Node 18+ and the `Archive/stage2` frontend (present when running inside a cloned repo).

## Install Options

- pipx (global user install; best DX)
  - `pipx install "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2"`
  - Upgrade later: `pipx install --force "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2"`
- pip inside a virtual environment
  - macOS/Linux
    - `python -m venv .venv && source .venv/bin/activate`
    - `pip install "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2"`
  - Windows PowerShell
    - `python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1`
    - `pip install "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2"`
- npm global wrapper (one-line install)
  - `npm install -g @reececantcode/flowcode` (use your published scope/name)
  - Then use `flowcode ...`
  - The npm package forwards to the Python CLI and attempts to install it during `npm install -g` using pip. If it can’t, it prints a short hint.
  - If your npm package name differs, substitute accordingly.

## Prerequisites

- Python 3.9+
- OpenAI API key in `OPENAI_API_KEY` or a local `.env`
- Node 18+ and npm (only needed for the browser UI)

## Usage

- Generate artifacts (no UI):
  - `flowcode <source-file>`
  - Defaults: Stage 1 model `gpt-5`, Stage 2 model `gpt-5-nano`.
- Auto‑open viewer after generation:
  - `flowcode view <source-file>`
  - The command generates artifacts if missing, starts Vite (`Archive/stage2`) and opens the browser with the graph preloaded.
- View an existing Stage 2 JSON:
  - `flowcode view flowchart_en.stage2.json`
- Choose language (when using `view`):
  - `flowcode view <source-file> --lang zh`
- Override models:
  - `flowcode <source-file> --model-stage1 gpt-5 --model-stage2 gpt-5-nano`
- Other flags:
  - `--output-prefix <name>`: base for generated files (default: `flowchart`)
  - `--explanation <path>`: where to write the narrative (default: `flow_explanation.txt`)
  - `--show-prompts`: echo LLM prompts for debugging

### What gets generated

- `flow_explanation.txt` — Stage 1 narrative
- `flowchart_en.json` and `flowchart_zh.json` — Stage 2 graphs (EN/ZH)
- `flowchart_en.stage2.json` and `flowchart_zh.stage2.json` — Stage 2 viewer format

### Terminal preview (no UI)

- macOS/Linux:
  - `PYTHONPATH=flowcode_2/src python -m flowcode_renderer.cli --input flowchart_en.json`
- Windows PowerShell:
  - `$env:PYTHONPATH="flowcode_2/src"; python -m flowcode_renderer.cli --input flowchart_en.json`
- Graphviz DOT export:
  - `PYTHONPATH=flowcode_2/src python -m flowcode_renderer.cli --input flowchart_en.json --format graphviz --output flowchart.dot`

## Viewing in the Browser UI

- Requirements: a clone of the repo (so `Archive/stage2` exists) and Node 18+.
- Auto‑open with the CLI:
  - `flowcode view <source-file>` or `flowcode view flowchart_en.stage2.json`
- Manual steps (fallback):
  - `mkdir -p Archive/stage2/public`
  - Copy Stage 2 JSON: `cp flowchart_en.stage2.json Archive/stage2/public/`
  - Start dev server: `npm run dev --prefix Archive/stage2`
  - Open: `http://localhost:5173/?graph=/flowchart_en.stage2.json`

## Troubleshooting

- “flowcode: command not found”
  - Run `pipx ensurepath` and open a new terminal, or use the full path reported by `pipx list`.
- The npm `flowcode` runs but can’t find Python CLI
  - Install Python CLI: `pipx install "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2"`
- Viewer does not open / port busy
  - Open the shown URL manually. If port 5173 is busy, stop other Vite servers or run the UI from `Archive/stage2` directly.
- OPENAI_API_KEY not found
  - Export it in the current shell or create a `.env` file next to where you run the command.
- Windows quoting issues
  - Use PowerShell with single quotes `'...'` or double quotes `"..."` as appropriate.

## Uninstall

- Python CLI (pipx): `pipx uninstall flowcode-renderer`
- Python CLI (venv): deactivate and remove the venv
- npm wrapper: `npm uninstall -g @reececantcode/flowcode`

## Notes

- The UI launches only when you use `flowcode view ...` (or `--open-ui` in generate mode). Pure generation works without Node.
- The npm wrapper is optional; it simply forwards to the Python CLI for a neat `npm i -g` experience.

## License

MIT
