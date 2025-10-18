# Design Notes — Colorize Status Arrows

## Status data flow

- **Source**: Upstream generators (LLM or manual edits) may attach `metadata.status` to each edge before Stage 2 rendering. Status is optional and defaults to `default`.
- **Python conversion**: Extend `FlowGraph` / `GraphEdge` with an optional `status` value stored in `metadata`. `graph_to_stage2_module` copies it into the Stage 2 module’s `edges[].metadata.status`. Existing JSON parsing remains backward compatible because unknown fields are ignored.
- **React Flow transform**: `toReactFlowGraph` reads `metadata.status`, maps it to a palette token, and assigns a semantic class (e.g., `edge-status-success`). Highlight utilities append classes without stripping the status tag so selections animate correctly.

## Color palette

| Status    | Color token | Hex      | Notes                       |
|-----------|-------------|----------|-----------------------------|
| default   | slate-400   | `#94a3b8` | Matches current neutral tone |
| active    | blue-500    | `#2563eb` | Indicates primary path       |
| success   | emerald-500 | `#10b981` | Signals completion           |
| warning   | amber-500   | `#f59e0b` | Caution / branching          |
| error     | rose-500    | `#f43f5e` | Failure handling             |
| disabled  | zinc-400    | `#a1a1aa` | Muted/backpressure paths     |

All colors will be exposed as CSS variables (`--edge-status-*`) so downstream themes can override them.

## Legend placement

- Renders inside the existing toolbar on the right-hand side.
- Displays colored swatch + text label for each status present in the current graph.
- Invisible to screen readers? No — include `<ul>` with sr-friendly labels.
- Future work could add filter toggles; this iteration is static.

## Testing strategy

- **Python**: Extend `GraphProcessingTests` to ensure status metadata survives JSON → FlowGraph → Stage 2 module round trip.
- **Frontend**: Add Vitest DOM test that loads a sample graph fixture with multi-status edges, asserts class names/inline styles, and verifies legend content. Include a fixture with an unknown status to assert fallback.
