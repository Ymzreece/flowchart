# AI Bidirectional Code–Flowchart System Stages

The project is organized into sequential phases, each with clear steps required to deliver the bidirectional flowchart-to-code experience described in `AI_Bidirectional_Code_Flowchart_System.md`.

## Phase 1 — Code Parsing and Graph Generation
- Confirm initial language targets (Python and TypeScript) and gather representative codebases for testing.
- Implement AST-based parsers (`ast` for Python, `ts-morph` or Babel for TypeScript/JavaScript).
- Build a canonical graph schema that captures function nodes, edges, and metadata.
- Serialize parsed graphs to JSON for downstream consumption by the frontend.
- Persist function-to-node mappings in `.flowmap.json` files for synchronization.

## Phase 2 — Interactive Flowchart Frontend
- Scaffold a React + TypeScript frontend and integrate React Flow (or similar) for graph visualization.
- Load JSON graphs and render function-level flowcharts with accurate node/edge representation.
- Enable users to add or delete nodes (conditions, loops, calls) and edit node expressions inline.
- Support reconnecting edges and updating branch conditions through the UI.
- Serialize every edit back to JSON and send it to the backend via a REST API bridge.

## Phase 3 — Code Regeneration Engine
- Diff edited flowchart JSON against the original `.flowmap.json` to detect structural and logical changes.
- Classify modifications (added/removed/reordered nodes, edited expressions) for targeted regeneration.
- Invoke an AI-assisted synthesis layer (Codex/GPT-5) to produce updated source functions that match the new logic.
- Ensure regenerated code preserves formatting, scope, imports, and naming conventions.
- Run static analysis (`flake8`, `mypy`, `eslint`) and project tests; present human-readable diffs for approval before applying changes.

## Phase 4 — Round-Trip Synchronization
- Implement background services (VS Code extension or web daemon) that monitor code saves and flowchart edits.
- On code changes, regenerate flowchart metadata to keep `.flowmap.json` in sync.
- On flowchart edits, trigger the regeneration pipeline to update code safely.
- Maintain versioned pairs of source files and flowchart JSON under `.flowmaps/`.
- Provide conflict detection and a merge/confirmation UI when simultaneous code and flowchart edits occur.

## Phase 5 — AI Enhancement (Optional)
- Add natural-language-to-flowchart generation capabilities to accelerate design tasks.
- Auto-group repeated flow patterns into reusable functions and suggest likely variable names or dependencies.
- Offer explanatory text for flowchart segments to improve developer understanding.
- Fine-tune GPT-5/Codex variants on AST→graph→code datasets to improve bidirectional fidelity.

## Supporting Workstreams
- Establish the system architecture pipeline (Parser → Graph → Editor → Synthesizer) and document integration points.
- Align the repository structure (`backend/`, `frontend/`, `.flowmaps/`, `examples/`) with implementation plans.
- Create onboarding examples (e.g., `process_order.py`) that demonstrate the end-to-end workflow.
- Define milestone tracking using the provided timeline (≈10–12 weeks) and associated deliverables.
- Plan for future extensions: additional languages, CI/CD visualization, documentation generators, collaboration, and plugin ecosystems.
