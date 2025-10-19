# Change Proposal — Add End-to-End `flowcode` CLI

## Problem

Running the end-to-end flow requires several manual commands (Stage 1 generation, Stage 2 graph extraction/translation, and Stage 2 JSON export), plus an optional frontend preview. The multi-step workflow is error-prone and increases onboarding friction.

## Proposal

Introduce a minimal, verb-first `flowcode` CLI at the repo root that orchestrates Steps 1–3 from `flow.md` and optionally launches the Stage 2 dev server. The command accepts a target filename to include in the prompt and produces the same canonical outputs (`flow_explanation.txt`, `flowchart_en.json`, `flowchart_zh.json`, and `*.stage2.json`).

## Scope

- Provide a root-level executable `flowcode` script (Python) that:
  - Loads the prompt from `flowcode_1/prompt.md` and includes the user-provided file.
  - Calls Stage 1 to produce `flow_explanation.txt`.
  - Calls Stage 2 to generate bilingual `flowchart_*.json`.
  - Converts both graphs to Stage 2 JSON (`*.stage2.json`).
  - Optionally launches the frontend via `npm run dev --prefix Archive/stage2` when `--open-ui` is used.
- Handle environment key discovery in a friendly way: if `OPENAI_API_KEY` is unset, attempt to read `.env` (supports either `OPENAI_API_KEY=...` or an `api:` style followed by the key).
- Keep implementation minimal and dependency-free beyond existing packages.

## Out of Scope

- Packaging a global installer or publishing to PyPI/npm.
- Advanced flags for model selection, parallelisation, or caching.
- Prompt templating or multi-file include globs beyond a single filename argument.

## Risks & Mitigations

- Missing dependencies (`openai`, `rich`, Node) — print clear, actionable errors; make Step 4 optional.
- Environment key format variance — fall back to `.env` parsing heuristics if `OPENAI_API_KEY` is not exported.
- Path assumptions — resolve paths relative to repo root and validate inputs early.

## Open Questions

1. Should the CLI default to launching the UI automatically, or keep it opt-in? (Current proposal: opt-in via `--open-ui`).
2. Do we want flags for choosing Stage 1/Stage 2 models? (Not included for now; easy to extend.)

## Dependencies

- Stage 1: `flowcode_1/flowchart_generator.py`
- Stage 2: `flowcode_2/graph_generator.py`, `flowcode_2/src/flowcode_renderer/{parser,converter}.py`
- Frontend: `Archive/stage2`
