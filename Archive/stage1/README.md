# Stage 1 — Code Parsing and Graph Generation

This package provides the language-agnostic parsing layer for the bidirectional code–flowchart system. It converts source files into a normalized intermediate representation (IR) that downstream components can visualize and edit. The design focuses on deterministic, plugin-based parsing so that additional languages can be supported without rewriting the core pipeline.

## Project Structure

```
stage1/
├── src/
│   └── flow_ir/
│       ├── __init__.py
│       ├── models.py
│       ├── registry.py
│       ├── serializer.py
│       └── parsers/
│           ├── __init__.py
│           ├── base.py
│           ├── python_parser.py
│           └── tree_sitter_adapter.py
├── tests/
│   └── fixtures/
│       └── sample_python.py
└── README.md
```

## Getting Started

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
Optional: `pip install tree_sitter tree_sitter_languages` to enable the Tree-sitter adapter for many languages. A built-in lightweight parser for C is provided, so the C flow works even without Tree-sitter.

2. **Generate IR for a source file**
   ```bash
   python -m flow_ir.cli parse tests/fixtures/sample_python.py --language python --out flow.json
   ```

3. **Inspect the results**
   ```bash
   cat flow.json | jq
   ```

## Design Highlights

- **Language-Agnostic IR** — All parsers emit `ModuleIR`, `FunctionIR`, `NodeIR`, and `EdgeIR` objects.
- **Plugin Registry** — Parsers register themselves via `flow_ir.registry`; new languages simply implement `LanguageParser`.
- **Tree-sitter Integration** — The optional adapter loads Tree-sitter grammars dynamically for broad language coverage.
- **Traceability** — Nodes carry source locations and identifiers to support bidirectional updates in later stages.
- **Natural Language Summaries** — Each IR node includes a human-friendly `summary` describing the underlying code so Stage 2 can present accessible flowcharts.

## Registering Tree-Sitter Languages

```python
from flow_ir.parsers.tree_sitter_adapter import (
    TreeSitterLanguageConfig,
    register_tree_sitter_language,
)

register_tree_sitter_language(
    TreeSitterLanguageConfig(
        language="javascript",
        tree_sitter_language="javascript",
        function_query="""
        (function_declaration
          name: (identifier) @name
          body: (statement_block) @body)
        (method_definition
          name: (property_identifier) @name
          body: (statement_block) @body)
        """,
    )
)
```

After registration, the CLI can parse JavaScript files using `--language javascript`.

With Tree-sitter installed you can register additional languages (see example above). When the extras
are available, the CLI can parse files such as:

```bash
PYTHONPATH=stage1/src python -m flow_ir.cli parse test_code/Flash.c --language c --out flash.flow.json
```

## Next Steps

- Add additional parser plugins (e.g., TypeScript, Java, C++) via Tree-sitter or native compiler APIs.
- Expand fixtures and regression tests to cover complex control flow (loops, exceptions, comprehensions).
- Integrate with Stage 2 to feed flowchart editors with the generated JSON graph.
