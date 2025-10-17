# AI-Driven Bidirectional Code–Flowchart System

## 1. Objective

Build a system that:
1. **Reads existing project codebases.**
2. **Generates visual flowcharts** (global and function-level).
3. Allows users to **edit or rearrange nodes/steps** on the flowchart.
4. **Automatically updates the code** to match the new logic reflected in the edited flowchart.

In short: a **round-trip engineering system** for *logic flow*, not just structure — enabling users to modify business logic visually.

---

## 2. Core Concept

### Flow
```
Existing Code → Parser/Analyzer → Graph Representation → Flowchart UI → User Edits →
Updated Graph → Code Synthesizer → Updated Codebase
```

### Requirements
- Multi-language support (start with Python + TypeScript)
- Accurate mapping between flow nodes and code blocks
- Safe bidirectional sync (human-readable diffs + commit hooks)
- Extensible plugin architecture (VS Code / web app)

---

## 3. Development Phases

### Phase 1 — Code Parsing and Graph Generation
**Goal:** Convert source code into an intermediate representation (IR) suitable for graph visualization.

#### Tasks
- Implement **AST-based parsers**:
  - Use `ast` for Python, `ts-morph` or Babel for JavaScript/TypeScript.
- Build a **Graph Schema**:
  ```json
  {
    "functions": [
      {
        "name": "process_order",
        "nodes": [
          {"id": "start", "type": "start"},
          {"id": "cond1", "type": "if", "expr": "if order.total > 100"},
          {"id": "discount", "type": "call", "expr": "apply_discount()"},
          {"id": "ship", "type": "call", "expr": "ship_order()"},
          {"id": "end", "type": "end"}
        ],
        "edges": [
          {"from": "start", "to": "cond1"},
          {"from": "cond1", "to": "discount", "cond": "True"},
          {"from": "cond1", "to": "ship", "cond": "False"},
          {"from": "discount", "to": "ship"},
          {"from": "ship", "to": "end"}
        ]
      }
    ]
  }
  ```
- Serialize to JSON for use in frontend flowchart tools.
- Store function↔node mappings in a metadata file (`.flowmap.json`).

#### Key Tech
- `ast`, `asttokens`, `networkx` (Python)
- `esprima`, `babel-parser`, `ts-morph` (JS/TS)

---

### Phase 2 — Interactive Flowchart Frontend
**Goal:** Provide a visual editor where users can explore and modify logic flows.

#### Tasks
- Use a **React + TypeScript** frontend.
- Integrate with a node-based flow editor (e.g., [React Flow](https://reactflow.dev/)).
- Import JSON graph and render function-level flowcharts.
- Allow:
  - Add/Delete nodes (conditions, loops, function calls)
  - Edit conditions and function names
  - Reconnect flow edges
- On each edit, serialize modified graph to JSON → send back to backend.

#### Key Tech
- React Flow
- TailwindCSS + Shadcn/UI
- Monaco Editor (inline code editing)
- REST API bridge with backend

---

### Phase 3 — Code Regeneration Engine
**Goal:** Reflect edited flowcharts back into real code.

#### Strategy
1. Compare modified JSON with original `.flowmap.json`.
2. Identify:
   - Added / removed / reordered nodes
   - Edited expressions or conditions
3. Use an **AI-assisted synthesis layer** (Codex or local LLM):
   - Generate updated source functions.
   - Ensure indentation, variable scope, and imports are consistent.
4. Validate regenerated code:
   - Static analysis (`flake8`, `mypy`, `eslint`)
   - Run tests automatically
   - Present unified diff preview to user before applying

#### Key Tech
- OpenAI Codex / GPT-5 API
- `difflib` or `git diff` integration
- `black` / `prettier` for code formatting

---

### Phase 4 — Round-Trip Synchronization
**Goal:** Keep code and flowchart always in sync.

#### Mechanism
- A VS Code extension or web daemon runs:
  - `onSave`: update flowchart metadata when code changes
  - `onEditFlowchart`: trigger regeneration pipeline
- Maintain versioned JSON and code pairs:
  ```
  src/
    process_order.py
  .flowmaps/
    process_order.flow.json
  ```

#### Conflict Handling
- If user edits both code and flowchart simultaneously:
  - Diff detection → human confirmation layer.
  - Conflict resolution via merge interface.

---

### Phase 5 — AI Enhancement (Optional)
**Goal:** Introduce intelligent refactoring & intent recognition.

#### Features
- Natural language prompt → auto-generate flowchart sections
- Auto-group repeated patterns into reusable functions
- Predict likely variable names and dependencies
- Explain flowchart segments in plain English

#### Models
- Use fine-tuned GPT-5/Codex variants on AST→graph→code datasets.

---

## 4. System Architecture Overview

```
┌────────────────────┐
│   Source Code      │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Code Parser (AST) │
└────────┬───────────┘
         │ JSON Graph
         ▼
┌────────────────────┐
│ Flowchart Editor   │ (React Flow)
└────────┬───────────┘
         │ Edits
         ▼
┌────────────────────┐
│ Code Synthesizer   │ (Codex-based)
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Updated Codebase  │
└────────────────────┘
```

---

## 5. Key Milestones

| Phase | Deliverable | Target Duration | Notes |
|-------|--------------|----------------|-------|
| 1 | Parser + JSON graph generator | 2 weeks | Works for Python |
| 2 | Flowchart UI + basic editing | 3 weeks | React Flow MVP |
| 3 | Code regeneration prototype | 3 weeks | Codex in backend |
| 4 | Bidirectional sync | 2 weeks | VS Code plugin |
| 5 | AI enhancement | 4 weeks | Optional fine-tuning |

Total: **≈10–12 weeks** for v1 MVP.

---

## 6. Future Directions

- Multi-language support (C++, Java)
- Integration with CI/CD to visualize code changes
- Auto documentation generator (`README` + sequence diagrams)
- Collaboration mode (multi-user editing)
- Plugin marketplace (custom node templates)

---

## 7. Example Workflow (Python)

1. User selects `process_order.py`
2. System generates flowchart.
3. User edits:
   - Adds new condition “if customer.is_vip”.
4. Flowchart saved → JSON updated.
5. Backend regenerates code:
   ```python
   def process_order(order, customer):
       if customer.is_vip:
           apply_vip_discount(order)
       elif order.total > 100:
           apply_discount(order)
       ship_order(order)
   ```
6. Tests auto-run, diffs confirmed → committed.

---

## 8. Repository Structure

```
root/
├── backend/
│   ├── parser/
│   │   └── python_parser.py
│   ├── synthesizer/
│   │   └── codex_synthesizer.py
│   └── api/
│       └── server.py
├── frontend/
│   ├── src/
│   │   ├── components/FlowEditor.tsx
│   │   └── utils/api.ts
├── examples/
│   └── process_order.py
└── .flowmaps/
    └── process_order.flow.json
```

---

## 9. Deliverables

- **Flowchart Generation Engine** — from code → JSON graph  
- **Visual Flowchart Editor** — edit/add/delete nodes  
- **Code Synthesizer** — JSON → updated code  
- **VS Code Plugin / Web IDE Integration** — optional  
- **AI Enhancement Module** — NLP → flow modifications  

---

## 10. Conclusion

This project defines an **end-to-end closed loop** between human-intuitive visual editing and machine-generated code, bridging the gap between **design thinking and code implementation**.

The MVP can start as:
- Python backend (`FastAPI` + `ast` + Codex)
- React frontend (`React Flow`)
- Simple CLI or VS Code extension for sync

Once stable, extend to other languages and integrate continuous learning loops from user edits.
