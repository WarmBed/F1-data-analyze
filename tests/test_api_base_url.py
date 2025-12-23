#!/usr/bin/env python3
"""Unit tests for the API base URL resolver helper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.api_base_url import PUBLIC_API_BASE_URL, resolve_api_base_url


@pytest.mark.parametrize(
    "env_value",
    [
        "http://127.0.0.1:8000",
        "http://localhost:9000",
        "https://192.168.1.10:5000",
    ],
)
def test_env_localhost_candidates_are_rejected(monkeypatch: pytest.MonkeyPatch, env_value: str) -> None:
    """Local or private hosts in the environment must be ignored."""
    monkeypatch.setenv("F1_API_BASE_URL", env_value)

    resolved = resolve_api_base_url()

    assert resolved == PUBLIC_API_BASE_URL


def test_env_remote_domain_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    """A remote domain in the environment should be used as-is."""
    monkeypatch.setenv("F1_API_BASE_URL", "http://api.example.com")

    resolved = resolve_api_base_url()

    assert resolved == "https://api.example.com"


def test_preferred_url_is_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Preferred URLs passed by the caller take precedence."""
    monkeypatch.delenv("F1_API_BASE_URL", raising=False)
    preferred = [("自訂覆寫", "staging.localhost")]

    resolved = resolve_api_base_url(preferred_urls=preferred)

    assert resolved == "https://staging.localhost"


def test_config_localhost_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A config file that points to localhost must be ignored."""
    monkeypatch.delenv("F1_API_BASE_URL", raising=False)
    config_path = tmp_path / "api_config.json"
    config_path.write_text(json.dumps({"api_base_url": "http://localhost:8000"}), encoding="utf-8")

    resolved = resolve_api_base_url(config_path=config_path)

    assert resolved == PUBLIC_API_BASE_URL
