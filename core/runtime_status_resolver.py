#!/usr/bin/env python3
"""Utility helpers for mapping API runtime telemetry into GUI-friendly CLI status states."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Sequence


class RuntimeStatusState(str, Enum):
    """Possible UI states for the CLI status indicator."""

    IDLE = "idle"
    CLI_LOADING = "cli_loading"
    DATA_DOWNLOADING = "data_downloading"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RuntimeStatusView:
    """Resolved view properties for the CLI status label."""

    state: RuntimeStatusState
    label: str
    color: str
    tooltip: str
    active_task_count: int


class RuntimeStatusResolver:
    """Analyse the API runtime payload and produce GUI-friendly status metadata."""

    _DEFAULT_DOWNLOAD_KEYWORDS: Sequence[str] = (
        "download",
        "downloading",
        "fetch",
        "fetching",
        "fastf1",
        "openf1",
        "http",
        "requesting",
    )

    _DEFAULT_LOADING_KEYWORDS: Sequence[str] = (
        "cli",
        "launch",
        "running",
        "queued",
        "starting",
        "process",
        "loading",
    )

    def __init__(
        self,
        *,
        download_keywords: Iterable[str] | None = None,
        loading_keywords: Iterable[str] | None = None,
    ) -> None:
        self._download_keywords = tuple(
            kw.lower() for kw in (download_keywords or self._DEFAULT_DOWNLOAD_KEYWORDS)
        )
        self._loading_keywords = tuple(
            kw.lower() for kw in (loading_keywords or self._DEFAULT_LOADING_KEYWORDS)
        )

    # ------------------------------------------------------------------
    def resolve(self, payload: Dict[str, Any] | None) -> RuntimeStatusView:
        """Resolve the status view from an analysis/status payload."""

        if not isinstance(payload, dict):
            return self._build_unknown("無法取得分析狀態 (payload missing)")

        runtime = payload.get("runtime") or {}
        if not isinstance(runtime, dict):
            return self._build_unknown("無效的 runtime 結構")

        active_tasks = runtime.get("active_tasks") or []
        if not active_tasks:
            return RuntimeStatusView(
                state=RuntimeStatusState.IDLE,
                label="[CLI] IDLE",
                color="#95a5a6",
                tooltip="CLI 閒置，沒有正在執行的分析任務",
                active_task_count=0,
            )

        state = self._classify_tasks(active_tasks)
        tooltip = self._build_tooltip(active_tasks)

        if state is RuntimeStatusState.DATA_DOWNLOADING:
            return RuntimeStatusView(
                state=state,
                label="[CLI] DOWNLOADING",
                color="#e67e22",
                tooltip=tooltip,
                active_task_count=len(active_tasks),
            )

        if state is RuntimeStatusState.CLI_LOADING:
            return RuntimeStatusView(
                state=state,
                label="[CLI] LOADING",
                color="#3498db",
                tooltip=tooltip,
                active_task_count=len(active_tasks),
            )

        return self._build_unknown(tooltip or "分析狀態未知")

    # ------------------------------------------------------------------
    def _classify_tasks(self, tasks: Sequence[Dict[str, Any]]) -> RuntimeStatusState:
        """Inspect active tasks and determine the most descriptive state."""

        download_hit = False
        loading_hit = False

        for task in tasks:
            text_blob = self._merge_task_text(task).lower()
            if any(keyword in text_blob for keyword in self._download_keywords):
                download_hit = True
                break
            if any(keyword in text_blob for keyword in self._loading_keywords):
                loading_hit = True

        if download_hit:
            return RuntimeStatusState.DATA_DOWNLOADING
        if loading_hit:
            return RuntimeStatusState.CLI_LOADING
        return RuntimeStatusState.CLI_LOADING

    def _merge_task_text(self, task: Dict[str, Any]) -> str:
        message = str(task.get("message") or "")
        last_log = str(task.get("last_log") or "")
        status = str(task.get("status") or "")
        return " | ".join(filter(None, (message, last_log, status)))

    def _build_tooltip(self, tasks: Sequence[Dict[str, Any]]) -> str:
        lines = []
        for task in tasks:
            function_id = task.get("function_id", "?")
            status = task.get("status", "unknown")
            message = task.get("message") or "--"
            last_log = task.get("last_log")
            base = f"功能 {function_id} - 狀態: {status}"
            lines.append(base)
            lines.append(f"  ↳ {message}")
            if last_log:
                lines.append(f"  ↳ 日誌: {last_log}")
        return "\n".join(lines) or "目前正在處理 CLI 任務"

    def _build_unknown(self, reason: str) -> RuntimeStatusView:
        return RuntimeStatusView(
            state=RuntimeStatusState.UNKNOWN,
            label="[CLI] UNKNOWN",
            color="#c0392b",
            tooltip=reason,
            active_task_count=0,
        )


__all__ = [
    "RuntimeStatusState",
    "RuntimeStatusView",
    "RuntimeStatusResolver",
]
