# Stage 1 Tutorial — Building the Code Parsing & Graph Generation Layer

This guide walks through the design and implementation of the Stage 1 milestone: transforming source code into a language‑agnostic intermediate representation (IR) suitable for flowchart visualization and downstream round-trip editing.

## 1. Project Goal

Create a deterministic pipeline that:
- Parses source files (initially Python and C) and extracts function-level control flow.
- Normalizes logic into a common IR (`ModuleIR`, `FunctionIR`, `NodeIR`, `EdgeIR`) with traceable source locations.
- Emits JSON artifacts that Stage 2 can render as interactive flowcharts.
- Supports additional languages via a pluggable parser interface.

## 2. Directory Layout

```
stage1/
├── pyproject.toml              # Packaging metadata and dependencies
├── README.md                   # High-level overview and quickstart
├── tutorial.md                 # This step-by-step guide
├── src/
│   └── flow_ir/
│       ├── __init__.py         # Package entry point, registers default parsers
│       ├── cli.py              # CLI for parsing files into JSON
│       ├── models.py           # IR data classes (ModuleIR, FunctionIR, NodeIR, EdgeIR)
│       ├── registry.py         # Parser registry (language → parser factory)
│       ├── serializer.py       # Helpers to convert IR into JSON
│       └── parsers/
│           ├── __init__.py
│           ├── base.py         # Abstract LanguageParser definition
│           ├── python_parser.py
│           ├── c_simple_parser.py
│           └── tree_sitter_adapter.py (optional for expanded coverage)
├── test_code/
│   └── Flash.c                 # Example C source file
└── tests/
    ├── fixtures/
    │   ├── sample_python.py
    │   └── sample_c.c
    ├── test_python_parser.py
    └── test_c_parser.py
```

## 3. Core Components

### 3.1 Models (`src/flow_ir/models.py`)
Defines the IR schema:
- `ModuleIR`: aggregates functions parsed from a file.
- `FunctionIR`: holds nodes (`NodeIR`) and edges (`EdgeIR`) plus metadata (parameters, docstring, async flag).
- `NodeIR`: typed control-flow node (`NodeKind` enum covers start, end, conditional, loop, call, return, etc.).
- `EdgeIR`: directed connection with optional labels (e.g., `True/False` for branches).
- `SourceLocation`: pinpoints the originating file, line, and column for traceability.

### 3.2 Parser Base & Registry
- `LanguageParser` (`parsers/base.py`): abstract class with `parse_code`/`parse_file` methods. Each language-specific parser extends this base.
- `registry.py`: keeps a global mapping from language keys (`"python"`, `"c"`, …) to parser factories. New parsers register via `register_parser`.
- `serializer.py`: turns `ModuleIR` instances into JSON strings or writes them to disk.

### 3.3 Parser Implementations
- `python_parser.py`: uses Python’s `ast` module to walk function bodies, building control-flow graphs (handles `if`, `for`, `while`, `try`, `with`, returns, raises).
- `c_simple_parser.py`: lightweight C parser that strips comments, heuristically extracts function signatures, and sketches control flow (branching, loops, returns). Designed to work without external dependencies.
- `tree_sitter_adapter.py`: optional generic adapter powered by Tree-sitter grammars for broader language support once dependencies are available.
- `__init__.py`: imports parser modules to ensure registration happens on package import.

### 3.4 CLI Interface (`src/flow_ir/cli.py`)
Exposes two commands:
- `list-languages`: prints registered languages.
- `parse`: produces JSON flow data for a given file and language. Example:
  ```bash
  PYTHONPATH=stage1/src python -m flow_ir.cli parse tests/fixtures/sample_python.py --language python --out flow.json
  ```

## 4. Building the IR Pipeline

1. **Define the IR schema** (`models.py`) to express flow nodes, edges, metadata, and natural-language summaries consistently across languages.
2. **Implement the parser registry** (`registry.py`) so languages can be added modularly.
3. **Create language parsers**:
   - Start with deterministic AST utilities (`python_parser.py`).
   - Add `c_simple_parser.py` for immediate C support.
   - Generate readable summaries for each node using helpers in `text_utils.py`.
   - Offer Tree-sitter integration as an optional extension for richer coverage.
4. **Wire up the CLI** (`cli.py`) to invoke parsers and emit JSON.
5. **Add fixtures and tests** (`tests/`) to validate that the parser outputs sensible nodes/edges.

## 5. Running Tests

Either install the package in editable mode or set `PYTHONPATH` when invoking commands:

```bash
PYTHONPATH=stage1/src python -m unittest stage1/tests/test_python_parser.py stage1/tests/test_c_parser.py
```

## 6. Generating Flow JSON

Parse a Python file:
```bash
PYTHONPATH=stage1/src python -m flow_ir.cli parse stage1/tests/fixtures/sample_python.py --language python --out sample_python.flow.json
```

Parse the provided C example:
```bash
PYTHONPATH=stage1/src python -m flow_ir.cli parse stage1/test_code/Flash.c --language c --out Flash.flow.json
```

The resulting JSON contains a `functions` list; each function has `nodes` and `edges` suitable for Stage 2 visualization.

## 7. Extending to New Languages

1. **Implement a parser** that extends `LanguageParser` and emits `ModuleIR`.
2. **Register the parser** in its module (call `register_parser("language_key", ParserClass)`).
3. Optionally add fixtures/tests similar to the Python and C examples.
4. Update documentation if the language requires additional dependencies or instructions.

## 8. Next Milestones

- Expand language support (TypeScript via Tree-sitter or `ts-morph`, Java via `javalang`, etc.).
- Improve loop and branch fidelity for complex constructs (e.g., break/continue, switch cases).
- Store `.flowmap.json` metadata to align with Stage 4 synchronization requirements.
- Provide richer node metadata for Stage 3 (code regeneration) to correlate graph edits back to source patches.

## 9. Troubleshooting

- **Import errors**: ensure `PYTHONPATH` includes `stage1/src` or install via `pip install -e stage1`.
- **Missing languages**: run `python -m flow_ir.cli list-languages` to confirm registration.
- **Complex C code not parsed**: the simple parser skips unsupported constructs; consider enabling Tree-sitter or enhancing the heuristics.

With this foundation, Stage 1 delivers the required IR artifacts for the round-trip engineering workflow and sets the stage for interactive flowchart editing and code regeneration in subsequent phases.
