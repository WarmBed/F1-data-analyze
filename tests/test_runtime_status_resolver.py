#!/usr/bin/env python3
"""Tests for CLI runtime status resolver."""

from core.runtime_status_resolver import (
    RuntimeStatusResolver,
    RuntimeStatusState,
)


def _wrap_tasks(tasks):
    return {"runtime": {"active_tasks": tasks}}


def test_resolver_idle_when_no_tasks():
    resolver = RuntimeStatusResolver()
    view = resolver.resolve({"runtime": {"active_tasks": []}})

    assert view.state is RuntimeStatusState.IDLE
    assert view.label == "[CLI] IDLE"
    assert view.active_task_count == 0
    assert "閒置" in view.tooltip


def test_resolver_cli_loading_default_state():
    resolver = RuntimeStatusResolver()
    payload = _wrap_tasks([
        {
            "function_id": "12",
            "status": "running",
            "message": "CLI 進程啟動",
            "last_log": "Processing telemetry",
        }
    ])

    view = resolver.resolve(payload)

    assert view.state is RuntimeStatusState.CLI_LOADING
    assert view.label == "[CLI] LOADING"
    assert view.color == "#3498db"
    assert view.active_task_count == 1
    assert "功能 12" in view.tooltip


def test_resolver_detects_data_downloading_keywords():
    resolver = RuntimeStatusResolver()
    payload = _wrap_tasks([
        {
            "function_id": "21",
            "status": "running",
            "message": "Downloading FastF1 session",
            "last_log": "Fetching lap data",
        }
    ])

    view = resolver.resolve(payload)

    assert view.state is RuntimeStatusState.DATA_DOWNLOADING
    assert view.label == "[CLI] DOWNLOADING"
    assert view.color == "#e67e22"
    assert view.active_task_count == 1
    assert "FastF1" in view.tooltip


def test_resolver_handles_invalid_payload():
    resolver = RuntimeStatusResolver()
    view = resolver.resolve(None)

    assert view.state is RuntimeStatusState.UNKNOWN
    assert view.label == "[CLI] UNKNOWN"
    assert "payload" in view.tooltip.lower()
