# Change Proposal — Colorize Status Arrows

## Problem

Flow editors currently render every connection with the same neutral stroke (aside from temporary highlight effects). When teams review complex control flow, they need a quick way to spot which transitions are “happy path”, “error handling”, “background work”, or other lifecycle states. Without a visual distinction, reviewers must read each edge label or inspect metadata manually, slowing code reviews and design discussions.

## Proposal

Introduce status-aware arrow styling in the Stage 2 React Flow editor so edges can communicate their lifecycle at a glance. The proposal adds a lightweight status taxonomy to the Stage 2 module schema, teaches the Python renderer to preserve it, and updates the web UI to render a consistent color palette with an always-visible legend. Unknown or missing statuses continue to render with today’s neutral styling.

## Scope

- Extend the Stage 2 module schema (and TypeScript types) to accept an optional `metadata.status` string on edges.
- Update the Python `graph_to_stage2_module` converter to pass through status hints when present on a `GraphEdge`.
- Render colored strokes, arrowheads, and labels in the React Flow canvas based on the status value, including accessible contrast and hover/focus handling.
- Surface a legend / filter helper in the Stage 2 UI so viewers understand the mapping.
- Provide sensible defaults and fallbacks for graphs without status metadata.

## Out of Scope

- Automatically inferring status from labels or node types (remains manual / upstream for now).
- Editing workflows to change an edge’s status in the UI (view-only for this iteration).
- Persisting status back to Stage 1 text generation; upstream prompts remain unchanged aside from optional metadata injection.

## Risks & Mitigations

- **Color accessibility**: choose palette that maintains AA contrast; include legend and retain existing highlight animation for selected paths.
- **Schema drift**: keep status optional and backward compatible; fallback rendering ensures existing specs/tests continue to pass.
- **Data availability**: document how status metadata should be supplied (e.g., via `graph_generator` post-processing) and expose unit tests that cover presence/absence cases.

## Open Questions

1. Which status labels should we support out of the box? (Proposal assumes `default`, `active`, `success`, `warning`, `error`, `disabled`.)
2. Should the CLI expose a switch to apply default statuses (e.g., mark terminal edges as `success`)? For now, spec keeps this manual.
3. Would users benefit from a filter/toggle beyond the legend to isolate specific statuses?

## Dependencies

- Stage 2 Graph schema (`Archive/stage2/src/lib/graphSchema.ts`) and supporting transformer utilities.
- Python renderer (`flowcode_2/src/flowcode_renderer/converter.py`, `models.py`) for Stage 1+2 integration tests.
- Stage 2 UI styling (`Archive/stage2/src/styles/index.css`) and highlight utilities.
