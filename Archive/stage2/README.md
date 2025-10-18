# Stage 2 — Interactive Flowchart Frontend

This stage delivers the visual editor that allows developers to explore, edit, and export control-flow graphs generated in Stage 1. The frontend is built with React + TypeScript, leveraging a canvas library (React Flow) to render nodes/edges and synchronize changes back to the backend.

## Objectives

- Load JSON graphs (produced by Stage 1) and render function-level flowcharts.
- Provide intuitive editing capabilities: add/remove nodes, edit labels/conditions, reconnect edges, reorder paths.
- Track edits and serialize the modified graph to JSON, ready to be sent to the backend regeneration pipeline.
- Offer context-aware inspectors (e.g., code preview, metadata pane) to show source snippets and node details.
- Support multi-function navigation, zooming/panning, and basic theming for readability.

## Planned Architecture

```
stage2/
├── package.json
├── src/
│   ├── App.tsx              # Root layout, router, providers
│   ├── components/
│   │   ├── FlowEditor.tsx   # Main React Flow canvas and interaction logic
│   │   ├── NodeSidebar.tsx  # Inspector for selected node metadata and edits
│   │   └── Toolbar.tsx      # Import/export, undo/redo, layout controls
│   ├── hooks/
│   │   └── useFlowStore.ts  # Zustand store for graph state & change tracking
│   ├── lib/
│   │   ├── graphSchema.ts   # Types shared with Stage 1 (FunctionIR, NodeIR, EdgeIR)
│   │   └── transformer.ts   # Helpers to convert IR JSON ↔ React Flow elements
│   ├── pages/
│   │   └── FunctionView.tsx # Page shell for viewing/editing a single function graph
│   ├── services/
│   │   └── api.ts           # REST bridge (load/save graphs)
│   ├── styles/
│   │   └── index.css        # Tailwind + custom styling
│   └── main.tsx             # React entry point
└── tests/
    └── FlowEditor.test.tsx  # Interaction tests (Vitest/React Testing Library)
```

## Key Libraries

- **React 18 + TypeScript** — component framework.
- **Vite** — fast dev server & build tooling.
- **React Flow** — graph visualization and editing canvas.
- **Zustand** — lightweight state management for graph edits and undo history.
- **TailwindCSS + Shadcn/UI** — rapid UI styling.
- **React Query** (optional) — manage async fetching of graphs and save operations.

## Feature Roadmap

1. **MVP Viewer**  
   - Load IR JSON from local file (drag/drop) and display nodes/edges.
   - Highlight selected node with metadata (location, label, type).

2. **Editing Controls**  
   - Add/delete nodes (condition, loop, statement, return) via context menu.
   - Connect/disconnect edges with guard labels.
   - Inline editing of labels/conditions with Monaco editor.
   - Track dirty state and provide JSON export.

3. **Advanced UX**  
   - Multi-function navigation, breadcrumbs, minimap.
   - Undo/redo, auto-layout options.
   - Validation warnings (e.g., dangling edges).

4. **Backend Integration**  
   - Hook up REST API to retrieve Stage 1 outputs and post edited graphs.
   - Auth/session handling if needed (later phases).

## Environment Setup (planned)

```bash
cd stage2
pnpm install        # or npm/yarn
pnpm run dev        # Launch Vite dev server
pnpm run build      # Production build
pnpm run test       # Vitest suite
```

## Next Actions

1. Scaffold the Vite + React + TS project (`pnpm create vite stage2 --template react-ts` or equivalent).
2. Implement shared schema/types aligning with Stage 1 JSON output.
3. Integrate React Flow and render a static function graph.
4. Flesh out editing features and persistence.

This README will evolve as implementation progresses; the initial focus is laying down the scaffold and ensuring JSON interchange with Stage 1 is seamless.
