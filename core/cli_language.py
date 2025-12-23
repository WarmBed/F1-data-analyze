"""CLI language utilities for the F1T toolchain.

This module centralises lookup and normalisation of the language used for
command-line help output.  It prefers caller-specified values, then honours the
``F1T_CLI_LANGUAGE`` environment variable, and finally falls back to the project
default (Traditional Chinese).
"""

from __future__ import annotations

import os
from typing import Final

DEFAULT_LANGUAGE: Final[str] = "zh-TW"

_LANGUAGE_ALIASES = {
    "zh-TW": {"zh", "zh-tw", "zh_tw", "zh-hant", "zh-hant-tw"},
    "en-US": {"en", "en-us", "en_us", "en-gb", "en-ca"},
}

SUPPORTED_LANGUAGES: Final[set[str]] = set(_LANGUAGE_ALIASES.keys())


def normalize_cli_language(language: str | None) -> str:
    """Normalise an arbitrary language token to a supported code."""
    if not language:
        return DEFAULT_LANGUAGE

    token = language.strip().lower()
    if not token:
        return DEFAULT_LANGUAGE

    for canonical, aliases in _LANGUAGE_ALIASES.items():
        if token == canonical.lower() or token in aliases:
            return canonical

    return DEFAULT_LANGUAGE


def resolve_cli_language(preferred: str | None = None) -> str:
    """Resolve the CLI language using preference, env var, and default."""
    candidates = [preferred, os.getenv("F1T_CLI_LANGUAGE"), DEFAULT_LANGUAGE]
    for candidate in candidates:
        lang = normalize_cli_language(candidate)
        if lang in SUPPORTED_LANGUAGES:
            return lang
    return DEFAULT_LANGUAGE


def list_supported_cli_languages() -> list[str]:
    """Return the list of supported CLI language codes."""
    return sorted(SUPPORTED_LANGUAGES)
