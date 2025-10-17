from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from .models import ModuleIR


def module_to_dict(module: ModuleIR) -> Dict[str, Any]:
    """Convert a ModuleIR instance into a JSON-serializable dictionary."""
    return module.to_dict()


def module_to_json(module: ModuleIR, *, indent: int = 2) -> str:
    """Serialize a ModuleIR to a JSON string."""
    return json.dumps(module.to_dict(), indent=indent)


def dump_module(module: ModuleIR, path: Union[str, Path], *, indent: int = 2) -> None:
    """Write the ModuleIR JSON representation to disk."""
    Path(path).write_text(module_to_json(module, indent=indent), encoding="utf-8")
