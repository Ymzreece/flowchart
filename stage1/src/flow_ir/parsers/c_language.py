"""Tree-sitter powered parser registration for C."""

from __future__ import annotations

from .tree_sitter_adapter import (
    TreeSitterLanguageConfig,
    register_tree_sitter_language,
)

try:
    register_tree_sitter_language(
        TreeSitterLanguageConfig(
            language="c",
            tree_sitter_language="c",
            function_query="""
            (function_definition
              declarator: (function_declarator
                declarator: (identifier) @name)
              body: (compound_statement) @body)
            """,
        )
    )
except RuntimeError:
    # tree_sitter optional dependency missing; user can install flow-ir[treesitter] to enable.
    pass
