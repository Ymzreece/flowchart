from __future__ import annotations

from typing import Callable, Dict, Iterable

from .parsers.base import LanguageParser

ParserFactory = Callable[[], LanguageParser]

_REGISTRY: Dict[str, ParserFactory] = {}


def register_parser(language: str, parser_factory: ParserFactory) -> None:
    """Register a parser implementation for the given language key."""
    normalized = language.lower()
    if normalized in _REGISTRY:
        raise ValueError(f"Parser already registered for language '{language}'.")
    _REGISTRY[normalized] = parser_factory


def get_parser(language: str) -> LanguageParser:
    """Instantiate the parser associated with the language key."""
    normalized = language.lower()
    factory = _REGISTRY.get(normalized)
    if factory is None:
        available = ", ".join(sorted(_REGISTRY)) or "<none>"
        raise KeyError(f"No parser registered for '{language}'. Available: {available}")
    return factory()


def list_languages() -> Iterable[str]:
    """List languages with registered parsers."""
    return sorted(_REGISTRY.keys())
