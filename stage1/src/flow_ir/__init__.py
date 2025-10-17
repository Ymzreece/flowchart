"""Flow IR generation toolkit for Stage 1 of the bidirectional code–flowchart system."""

from .models import EdgeIR, FunctionIR, ModuleIR, NodeIR
from .registry import get_parser, list_languages, register_parser

# Ensure default parser plugins are registered on import.
from .parsers import python_parser as _python_parser  # noqa: F401
from .parsers import c_simple_parser as _c_simple_parser  # noqa: F401

__all__ = [
    "ModuleIR",
    "FunctionIR",
    "NodeIR",
    "EdgeIR",
    "register_parser",
    "get_parser",
    "list_languages",
]
