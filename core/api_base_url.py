"""Utility helpers for resolving the public API base URL for GUI components.

This module enforces that GUI modules only talk to the public-facing API
endpoint, preventing accidental regressions to localhost development URLs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import urlparse
import ipaddress

PUBLIC_API_BASE_URL = "https://api.f1telemetrystationpro.org"
DEFAULT_CONFIG_PATH = Path("config/api_config.json")
EventLogger = Optional[Callable[[str], None]]


def _log(logger: EventLogger, message: str) -> None:
    if logger is None:
        return
    try:
        logger(message)
    except Exception:
        # Guard against logger implementations that may raise.
        pass


def _normalize_candidate(raw_url: str) -> Optional[str]:
    candidate = str(raw_url or "").strip()
    if not candidate:
        return None

    parsed = urlparse(candidate)
    if not parsed.scheme:
        # Assume https if no scheme is provided.
        candidate = f"https://{candidate}"
        parsed = urlparse(candidate)

    if parsed.scheme not in {"https", "http"}:
        return None

    netloc = parsed.netloc or ""
    if not netloc:
        return None

    # Force https for any valid host.
    candidate = f"https://{netloc}"
    return candidate.rstrip("/")


def _is_internal_host(hostname: str) -> bool:
    host = (hostname or "").strip().lower()
    if not host:
        return True
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return True
    if host.endswith(".local"):
        return True
    try:
        ip_obj = ipaddress.ip_address(host)
        if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_reserved:
            return True
    except ValueError:
        # Not an IP address; continue with hostname rules.
        pass
    return False


def _iter_candidates(
    config_path: Path,
    event_logger: EventLogger,
) -> Iterable[tuple[str, str]]:
    env_url = os.getenv("F1_API_BASE_URL")
    if env_url:
        yield ("環境變數 F1_API_BASE_URL", env_url)

    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            api_url = data.get("api_base_url")
            if api_url:
                yield (f"設定檔 {config_path}", api_url)
        except Exception:
            _log(event_logger, f"讀取 {config_path} 失敗，忽略設定檔 API URL")


def resolve_api_base_url(
    *,
    config_path: Path | None = None,
    event_logger: EventLogger = None,
    preferred_urls: Iterable[tuple[str, str]] | None = None,
) -> str:
    """Resolve the API base URL while filtering out localhost/internal targets.

    The resolution order respects the environment variable ``F1_API_BASE_URL``
    followed by the optional JSON config file. Any URLs that point to local or
    internal hosts are ignored so the GUI always targets the public endpoint.
    """

    effective_config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    combined_candidates: list[tuple[str, str]] = []
    if preferred_urls:
        combined_candidates.extend(list(preferred_urls))
    combined_candidates.extend(list(_iter_candidates(effective_config_path, event_logger)))

    for source, raw_url in combined_candidates:
        normalized = _normalize_candidate(raw_url)
        if not normalized:
            _log(event_logger, f"忽略 {source}: 無法解析的 URL 值 `{raw_url}`")
            continue

        parsed = urlparse(normalized)
        if _is_internal_host(parsed.hostname or ""):
            _log(event_logger, f"忽略 {source}: {normalized} 屬於本地/內部位址，改用公開 API")
            continue

        _log(event_logger, f"採用 API 基底網址 {normalized} (來源: {source})")
        return normalized

    _log(event_logger, f"使用預設公開 API 網域 {PUBLIC_API_BASE_URL}")
    return PUBLIC_API_BASE_URL


__all__ = ["PUBLIC_API_BASE_URL", "resolve_api_base_url"]
