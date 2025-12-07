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

# 🔒 EXE 模式檢測：EXE 模式下預設禁用日誌輸出
# 可以透過設定環境變數 F1T_EXE_ENABLE_LOG=1 來開啟 EXE 日誌（除錯用）
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
# EXE 模式下預設靜默，除非明確設定 F1T_EXE_ENABLE_LOG=1
FORCE_SILENT = IS_EXE_MODE and os.getenv('F1T_EXE_ENABLE_LOG') != '1'

__all__ = [
    "setup_logging",
    "get_logger",
    "restore_print",
    "logged_print",
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
    console_level: Optional[Union[str, int]] = None,
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
        console_level: Optional override for the console handler log level.
            When ``None`` the handler inherits ``level``.
        force: When ``True`` re-apply configuration even if logging is already
            initialised.
    """
    global _CONFIGURED, _ACTIVE_COMPONENT

    # � EXE 模式：只有當 FORCE_SILENT=True 時才完全禁用日誌
    if IS_EXE_MODE and FORCE_SILENT:
        with _CONFIG_LOCK:
            if not _CONFIGURED or force:
                # 配置一個完全靜默的 NullHandler
                logging.config.dictConfig({
                    "version": 1,
                    "disable_existing_loggers": False,
                    "handlers": {
                        "null": {
                            "class": "logging.NullHandler",
                        },
                    },
                    "loggers": {
                        "f1": {
                            "handlers": ["null"],
                            "level": "CRITICAL",
                            "propagate": False,
                        },
                    },
                    "root": {
                        "handlers": ["null"],
                        "level": "CRITICAL",
                    },
                })
                _CONFIGURED = True
                _ACTIVE_COMPONENT = _normalise_component(component)
                
                # EXE 模式下不 patch print（保持原生行為）
                # 這樣 print() 仍然可以輸出到終端（如果需要的話）
        return
    
    # 🔍 EXE 模式但未設置 FORCE_SILENT：正常記錄日誌到檔案
    # 這樣可以在 EXE 出問題時查看 logs/ 目錄中的日誌檔案

    with _CONFIG_LOCK:
        if _CONFIGURED and not force:
            return

        component_normalised = _normalise_component(component)
        level_normalised = _normalise_level(level)
        target_dir = _resolve_log_dir(log_dir)

        console_level_normalised = _normalise_level(console_level) if console_level is not None else None

        if config is None:
            config_dict = _build_default_config(
                component_normalised,
                level_normalised,
                target_dir,
                console_level_normalised,
            )
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


def _build_default_config(
    component: str,
    level: str,
    log_dir: Path,
    console_level: Optional[str] = None,
) -> Dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用日期式檔名：f1_gui_2025-10-06.log
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    base_filename = log_dir / f"f1_{component}_{today}.log"
    error_filename = log_dir / f"f1_{component}_error_{today}.log"

    # 🚫 停用 console handler - 不再輸出到終端機
    console_level_value = console_level or level

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
            # ⚠️ Console handler 已停用 - 不輸出到終端機
            # "console": {
            #     "class": "logging.StreamHandler",
            #     "level": console_level_value,
            #     "formatter": "console",
            #     "stream": "ext://sys.stdout",
            # },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": level,
                "formatter": "detailed",
                "filename": str(base_filename),
                "when": "midnight",  # 每天午夜自動切換新檔案
                "interval": 1,
                "backupCount": 30,  # 保留 30 天的日誌
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "WARNING",
                "formatter": "detailed",
                "filename": str(error_filename),
                "when": "midnight",
                "interval": 1,
                "backupCount": 30,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "f1": {
                "handlers": ["file", "error_file"],  # ❌ 移除 "console"
                "level": level,
                "propagate": False,
            },
            "f1.console": {
                "handlers": ["file", "error_file"],  # ❌ 移除 "console"
                "level": level,
                "propagate": False,
            },
        },
        "root": {
            "handlers": [],  # ❌ 根 logger 也不輸出到 console
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


# 模組級別的 logged_print 函數（供外部模組訪問）
def logged_print(*args: Any, **kwargs: Any) -> None:
    """
    將 print 輸出重定向到 logger。
    
    此函數在模組級別定義，以便外部模組（如 numba）可以訪問。
    """
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


def _patch_print_adapter() -> None:
    global _PRINT_PATCHED
    if _PRINT_PATCHED:
        return

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

