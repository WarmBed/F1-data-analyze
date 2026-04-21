#!/usr/bin/env python3
"""Centralised logging utilities for the F1 analysis platform."""

from __future__ import annotations

import builtins
import json
import logging
import logging.config
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

# 🔒 EXE 模式檢測：EXE 模式下可選擇性禁用日誌輸出
# 可以透過設定環境變數 F1T_EXE_DISABLE_LOG=1 來禁用 EXE 日誌（節省效能）
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
# EXE 模式下預設啟用日誌（方便除錯），除非明確設定 F1T_EXE_DISABLE_LOG=1
FORCE_SILENT = IS_EXE_MODE and os.getenv('F1T_EXE_DISABLE_LOG') == '1'


def _load_logging_config() -> Dict[str, Any]:
    """載入 logging 設定檔（如果存在）"""
    try:
        # 嘗試找到專案根目錄
        if IS_EXE_MODE:
            # EXE 模式：從執行檔目錄尋找
            base_path = Path(sys.executable).parent
        else:
            # 開發模式：從此檔案往上兩層
            base_path = Path(__file__).parent.parent
        
        config_file = base_path / "config" / "logging_config.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        # 如果讀取失敗，使用預設值（不影響程式運行）
        print(f"[LOGGER] Warning: Could not load logging config: {e}")
    
    # 預設設定：啟用 logging
    return {
        "enabled": True,
        "level": "INFO",
        "console_level": None,
        "patch_print": True
    }


class SafeStreamHandler(logging.StreamHandler):
    """
    安全的 StreamHandler，忽略 Windows 下 flush 時的 OSError。
    
    這個問題通常發生在 debugpy + PyQt5 環境下，
    當 QApplication.processEvents() 被嵌套調用時，
    stdout/stderr 可能暫時變得無效。
    """
    
    def flush(self):
        try:
            super().flush()
        except OSError:
            # 忽略 Windows flush 錯誤（通常是 Errno 22: Invalid argument）
            pass
    
    def emit(self, record):
        try:
            super().emit(record)
        except OSError:
            # 忽略 emit 時的 OSError
            pass


__all__ = [
    "setup_logging",
    "get_logger",
    "restore_print",
    "logged_print",
    "SafeStreamHandler",
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

    # 📁 載入設定檔（優先）
    logging_config = _load_logging_config()
    
    # ⚠️ 如果設定檔明確禁用 logger，則配置為靜默模式
    if not logging_config.get("enabled", True):
        with _CONFIG_LOCK:
            if not _CONFIGURED or force:
                # 配置一個完全靜默的 NullHandler（但不關閉 stdout）
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
                
                # ✅ 重要：即使 Logger 禁用，也要 patch print，讓它靜默處理
                # 這樣可以避免 "I/O operation on closed file" 錯誤
                if logging_config.get("patch_print", True):
                    _patch_print_adapter()
                
                # 使用原始 print 輸出此訊息（因為 logger 已禁用）
                try:
                    _ORIGINAL_PRINT("[LOGGER] ⚠️  Logger is DISABLED via config/logging_config.json")
                except:
                    pass  # 如果連原始 print 都失敗，完全靜默
        return
    
    # 從設定檔讀取參數（如果沒有明確指定）
    if level is None:
        level = logging_config.get("level", "INFO")
    if console_level is None and "console_level" in logging_config:
        console_level = logging_config["console_level"]
    if "patch_print" in logging_config:
        patch_print = logging_config["patch_print"]

    # 🔒 EXE 模式：只有當明確設置 F1T_EXE_DISABLE_LOG=1 時才完全禁用日誌
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

    # ✅ EXE 模式預設啟用日誌：正常記錄日誌到檔案
    # 這樣可以在 EXE 出問題時查看 logs/ 目錄中的日誌檔案，方便除錯

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
        
        # 🔧 禁用 Python 的 lastResort handler，避免 debugpy + PyQt5 環境下的 flush 錯誤
        # logging.lastResort 是一個 _StderrHandler，當沒有配置 handler 時會寫入 stderr
        # 在 debugpy 環境下 stderr.flush() 可能導致 OSError: [Errno 22] Invalid argument
        logging.lastResort = None
        
        # 🔧 清除 root logger 的所有 StreamHandler，避免 debugpy 環境下的 flush 錯誤
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                root_logger.removeHandler(handler)
        
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

    result = {
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
    return result


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
    
    ⚠️ 安全機制：
    - 檢查 sys.stdout 是否已關閉或不可用
    - 在異常情況下靜默處理，避免程式崩潰
    """
    # ✅ 安全檢查 1：確保 sys.stdout 存在且未關閉
    try:
        if not hasattr(sys, 'stdout') or sys.stdout is None:
            # stdout 不存在，靜默返回
            return
        if hasattr(sys.stdout, 'closed') and sys.stdout.closed:
            # stdout 已關閉，靜默返回
            return
    except (AttributeError, ValueError):
        # 任何訪問 stdout 時的異常都靜默處理
        return
    
    # ✅ 安全檢查 2：獲取 file 參數時捕獲異常
    try:
        file_arg = kwargs.get("file", sys.stdout)
    except (ValueError, AttributeError):
        # 如果連獲取預設值都失敗，使用 None
        file_arg = None
    
    end_arg = kwargs.get("end", "\n")

    # 如果指定了其他輸出目標，嘗試使用原始 print
    if file_arg is not None and file_arg is not sys.stdout:
        try:
            _ORIGINAL_PRINT(*args, **kwargs)
        except (ValueError, AttributeError, OSError):
            # 即使原始 print 也失敗，也不要崩潰
            pass
        return
    
    if end_arg != "\n":
        try:
            _ORIGINAL_PRINT(*args, **kwargs)
        except (ValueError, AttributeError, OSError):
            pass
        return

    # ✅ 安全檢查 3：記錄到 logger 時捕獲異常
    try:
        sep = kwargs.get("sep", " ")
        message = sep.join(str(arg) for arg in args)
        level = _infer_log_level(message)
        logger = logging.getLogger("f1.console")
        logger.log(level, message)
    except Exception:
        # 如果 logger 也失敗，完全靜默（避免無限遞迴或其他問題）
        pass


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

