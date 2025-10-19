# Tasks — Colorize Status Arrows

- [x] Update Stage 2 graph schema types and fixtures to accept `EdgeIR.metadata.status`, documenting supported values.
- [x] Extend `flowcode_renderer` models/converter to carry optional edge status metadata through Stage 1 → Stage 2 exports.
- [x] Enhance React Flow transformer/highlight utilities to compute status-specific class names and ensure selection logic coexists with status styling.
- [x] Add CSS tokens and a persistent legend component that explains color ↔ status mappings, covering hover/focus/contrast behaviour.
- [x] Expand automated coverage (Python unit test + Vitest snapshot/DOM assertions) to verify both status-aware rendering and graceful fallbacks.
