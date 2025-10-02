#!/usr/bin/env python3
"""Centralised logging utilities for the F1 analysis platform."""

from __future__ import annotations

import builtins
import logging
import logging.config
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

__all__ = [
    "setup_logging",
    "get_logger",
    "restore_print",
]

_DEFAULT_COMPONENT = "app"
_ACTIVE_COMPONENT = _DEFAULT_COMPONENT
_CONFIGURED = False
_PRINT_PATCHED = False
_CONFIG_LOCK = threading.Lock()
_ORIGINAL_PRINT = builtins.print

PathLike = Union[str, os.PathLike]

_ERROR_PREFIXES = (
    "[ERROR",
    "ERROR:",
    "ERROR ",
    "CRITICAL",
    "FATAL",
    "EXCEPTION",
    "TRACEBACK",
)
_ERROR_KEYWORDS = (
    "錯誤",  # 錯誤
    "失敗",  # 失敗
    "災難",  # 災難
)
_ERROR_SYMBOLS = (
    "❌",      # ❌
    "🔴",  # 🔴
    "🚫",  # 🚫
)

_WARNING_PREFIXES = (
    "[WARN",
    "WARN:",
    "WARNING",
    "CAUTION",
    "ATTENTION",
)
_WARNING_KEYWORDS = (
    "警告",  # 警告
    "注意",  # 注意
)
_WARNING_SYMBOLS = (
    "⚠",
    "⚠️",  # ⚠️
    "🟡",    # 🟡
)

_DEBUG_PREFIXES = (
    "[DEBUG",
    "DEBUG:",
    "TRACE",
    "VERBOSE",
)
_DEBUG_KEYWORDS = (
    "調試",  # 調試
    "除錯",  # 除錯
    "偵錯",  # 偵錯
)
_DEBUG_SYMBOLS = (
    "🔍",  # 🔍
    "🧪",  # 🧪
    "🧾",  # 🧾
)


def setup_logging(
    component: str = _DEFAULT_COMPONENT,
    level: Optional[Union[str, int]] = None,
    config: Optional[Dict[str, Any]] = None,
    log_dir: Optional[PathLike] = None,
    patch_print: bool = True,
    force: bool = False,
) -> None:
    """Configure the global logging behaviour.

    Args:
        component: Logical component name (e.g. "cli", "gui", "api").
        level: Desired minimum log level (string or numeric). Defaults to
            ``F1_LOG_LEVEL`` env var or INFO.
        config: Optional ``logging.config.dictConfig`` payload. When provided it
            overrides the default layout.
        log_dir: Directory for log files. Defaults to ``F1_LOG_DIR`` env var or
            ``./logs``.
        patch_print: When ``True`` (default) replace :func:`print` with an
            adapter that routes messages through the logging system.
        force: When ``True`` re-apply configuration even if logging is already
            initialised.
    """
    global _CONFIGURED, _ACTIVE_COMPONENT

    with _CONFIG_LOCK:
        if _CONFIGURED and not force:
            return

        component_normalised = _normalise_component(component)
        level_normalised = _normalise_level(level)
        target_dir = _resolve_log_dir(log_dir)

        if config is None:
            config_dict = _build_default_config(component_normalised, level_normalised, target_dir)
        else:
            config_dict = config

        logging.config.dictConfig(config_dict)
        _CONFIGURED = True
        _ACTIVE_COMPONENT = component_normalised

        if patch_print:
            _patch_print_adapter()


def get_logger(name: Optional[str] = None, component: Optional[str] = None) -> logging.Logger:
    """Return a namespaced logger for the requested component."""
    if not _CONFIGURED:
        setup_logging(component=component or _ACTIVE_COMPONENT)

    component_normalised = _normalise_component(component or _ACTIVE_COMPONENT)
    if name:
        logger_name = f"f1.{component_normalised}.{name}"
    else:
        logger_name = f"f1.{component_normalised}"

    return logging.getLogger(logger_name)


def restore_print() -> None:
    """Restore the original built-in print function."""
    global _PRINT_PATCHED
    with _CONFIG_LOCK:
        if not _PRINT_PATCHED:
            return
        builtins.print = _ORIGINAL_PRINT
        _PRINT_PATCHED = False


def _build_default_config(component: str, level: str, log_dir: Path) -> Dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    base_filename = log_dir / f"f1_{component}.log"
    error_filename = log_dir / f"f1_{component}_error.log"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {"format": "%(message)s"},
            "detailed": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "console",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "detailed",
                "filename": str(base_filename),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "detailed",
                "filename": str(error_filename),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "f1": {
                "handlers": ["console", "file", "error_file"],
                "level": level,
                "propagate": False,
            },
            "f1.console": {
                "handlers": ["console", "file", "error_file"],
                "level": level,
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }


def _normalise_component(component: Optional[str]) -> str:
    text = (component or _DEFAULT_COMPONENT).strip().lower()
    safe = [ch if ch.isalnum() or ch in {"_", "."} else "_" for ch in text]
    value = "".join(safe).strip("._")
    return value or _DEFAULT_COMPONENT


def _normalise_level(level: Optional[Union[str, int]]) -> str:
    if isinstance(level, int):
        name = logging.getLevelName(level)
        return name if isinstance(name, str) and name.isupper() else "INFO"

    env_level = os.getenv("F1_LOG_LEVEL")
    raw = level or env_level or "INFO"
    upper = str(raw).strip().upper()
    return upper if upper in logging._nameToLevel else "INFO"


def _resolve_log_dir(log_dir: Optional[PathLike]) -> Path:
    if log_dir is not None:
        return Path(log_dir)
    env_dir = os.getenv("F1_LOG_DIR")
    if env_dir:
        return Path(env_dir)
    return Path("logs")




def _patch_print_adapter() -> None:
    global _PRINT_PATCHED
    if _PRINT_PATCHED:
        return

    def logged_print(*args: Any, **kwargs: Any) -> None:
        file_arg = kwargs.get("file", sys.stdout)
        end_arg = kwargs.get("end", "\n")

        if file_arg is not None and file_arg is not sys.stdout:
            _ORIGINAL_PRINT(*args, **kwargs)
            return
        if end_arg != "\n":
            _ORIGINAL_PRINT(*args, **kwargs)
            return

        sep = kwargs.get("sep", " ")
        message = sep.join(str(arg) for arg in args)
        level = _infer_log_level(message)
        logger = logging.getLogger("f1.console")
        logger.log(level, message)

    builtins.print = logged_print
    _PRINT_PATCHED = True

def _infer_log_level(message: str) -> int:
    stripped = message.lstrip()
    if not stripped:
        return logging.INFO

    upper = stripped.upper()
    for prefix in _ERROR_PREFIXES:
        if upper.startswith(prefix):
            return logging.ERROR
    if any(symbol in stripped for symbol in _ERROR_SYMBOLS):
        return logging.ERROR
    lower = stripped.lower()
    if any(keyword in lower for keyword in _ERROR_KEYWORDS):
        return logging.ERROR

    for prefix in _WARNING_PREFIXES:
        if upper.startswith(prefix):
            return logging.WARNING
    if any(symbol in stripped for symbol in _WARNING_SYMBOLS):
        return logging.WARNING
    if any(keyword in lower for keyword in _WARNING_KEYWORDS):
        return logging.WARNING

    for prefix in _DEBUG_PREFIXES:
        if upper.startswith(prefix):
            return logging.DEBUG
    if any(symbol in stripped for symbol in _DEBUG_SYMBOLS):
        return logging.DEBUG
    if any(keyword in lower for keyword in _DEBUG_KEYWORDS):
        return logging.DEBUG

    return logging.INFO

