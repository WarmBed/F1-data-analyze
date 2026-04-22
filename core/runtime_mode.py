"""Runtime mode helpers for the local-first desktop application.

The project is being moved away from an always-on HTTP API dependency.
Keep this module small and dependency-free so GUI, CLI, and future shared
executors can check the intended runtime without importing FastAPI or Qt.
"""

from __future__ import annotations

import os
from typing import Literal


RuntimeMode = Literal["local", "hybrid", "api"]

DEFAULT_RUNTIME_MODE: RuntimeMode = "local"
_VALID_MODES = {"local", "hybrid", "api"}


def get_runtime_mode() -> RuntimeMode:
    """Return the configured runtime mode."""

    raw_mode = os.getenv("F1T_RUNTIME_MODE", DEFAULT_RUNTIME_MODE).strip().lower()
    if raw_mode not in _VALID_MODES:
        return DEFAULT_RUNTIME_MODE
    return raw_mode  # type: ignore[return-value]


def is_local_first() -> bool:
    """Return True when local execution should be preferred."""

    return get_runtime_mode() in {"local", "hybrid"}


def is_api_enabled() -> bool:
    """Return True when legacy API workers/routes should be active."""

    return get_runtime_mode() in {"hybrid", "api"}


__all__ = [
    "DEFAULT_RUNTIME_MODE",
    "RuntimeMode",
    "get_runtime_mode",
    "is_api_enabled",
    "is_local_first",
]
