from __future__ import annotations

import abc
from pathlib import Path
from typing import Iterable, Optional

from ..models import ModuleIR


class LanguageParser(abc.ABC):
    """Abstract base class for language-specific parsers."""

    language: str

    def __init__(self) -> None:
        if not getattr(self, "language", None):
            raise ValueError(f"{self.__class__.__name__} must define a language attribute.")

    @abc.abstractmethod
    def parse_code(self, code: str, *, file_path: Optional[str] = None) -> ModuleIR:
        """Parse a snippet or file contents into a ModuleIR."""

    def parse_file(self, path: str | Path) -> ModuleIR:
        """Convenience helper to parse from a file path."""
        path_obj = Path(path)
        code = path_obj.read_text(encoding="utf-8")
        return self.parse_code(code, file_path=str(path_obj))

    def parse_files(self, paths: Iterable[str | Path]) -> Iterable[ModuleIR]:
        """Parse multiple files, yielding ModuleIR objects."""
        for path in paths:
            yield self.parse_file(path)
