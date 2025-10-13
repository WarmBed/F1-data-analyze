#!/usr/bin/env python3
"""
api_runtime_state - shared snapshot of API health/runtime indicators.

This module provides a light-weight, thread-safe cache that lets GUI modules
query the latest API health/runtime information without having to perform
synchronous network calls on the main thread.

Author: F1T Team
Date: 2025-10-12
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Dict, Optional

from core.runtime_status_resolver import RuntimeStatusState, RuntimeStatusView


@dataclass
class ApiStatusSnapshot:
    """Thread-safe snapshot that callers can inspect without mutating state."""

    health_state: str = "unknown"
    health_message: Optional[str] = None
    health_updated_at: Optional[datetime] = None

    runtime_state: RuntimeStatusState = RuntimeStatusState.UNKNOWN
    runtime_label: Optional[str] = None
    runtime_tooltip: Optional[str] = None
    runtime_updated_at: Optional[datetime] = None

    pending_reason: Optional[str] = None
    pending_payload: Dict[str, Any] = field(default_factory=dict)
    pending_updated_at: Optional[datetime] = None


_SNAPSHOT = ApiStatusSnapshot()
_LOCK = RLock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def update_health_state(state: str, message: Optional[str] = None) -> None:
    """Record the latest health probe result (executed on the GUI thread)."""
    with _LOCK:
        _SNAPSHOT.health_state = (state or "unknown").lower()
        _SNAPSHOT.health_message = message
        _SNAPSHOT.health_updated_at = _utcnow()


def update_runtime_view(view: RuntimeStatusView) -> None:
    """Capture the most recent CLI runtime poll outcome."""
    with _LOCK:
        _SNAPSHOT.runtime_state = view.state
        _SNAPSHOT.runtime_label = view.label
        _SNAPSHOT.runtime_tooltip = view.tooltip
        _SNAPSHOT.runtime_updated_at = _utcnow()


def set_pending_update(reason: str, payload: Optional[Dict[str, Any]] = None) -> None:
    """Mark that a parameter broadcast has been scheduled."""
    with _LOCK:
        _SNAPSHOT.pending_reason = reason
        _SNAPSHOT.pending_payload = dict(payload or {})
        _SNAPSHOT.pending_updated_at = _utcnow()


def clear_pending_update() -> None:
    """Clear pending-update metadata once the batch dispatch has executed."""
    with _LOCK:
        _SNAPSHOT.pending_reason = None
        _SNAPSHOT.pending_payload = {}
        _SNAPSHOT.pending_updated_at = _utcnow()


def is_api_available(grace_period: float = 30.0) -> bool:
    """
    Determine whether the API should be considered reachable based on cached data.

    Args:
        grace_period: seconds the cached value remains authoritative before we fall
                      back to an optimistic assumption.
    """
    with _LOCK:
        snapshot = ApiStatusSnapshot(
            health_state=_SNAPSHOT.health_state,
            health_message=_SNAPSHOT.health_message,
            health_updated_at=_SNAPSHOT.health_updated_at,
            runtime_state=_SNAPSHOT.runtime_state,
            runtime_label=_SNAPSHOT.runtime_label,
            runtime_tooltip=_SNAPSHOT.runtime_tooltip,
            runtime_updated_at=_SNAPSHOT.runtime_updated_at,
            pending_reason=_SNAPSHOT.pending_reason,
            pending_payload=dict(_SNAPSHOT.pending_payload),
            pending_updated_at=_SNAPSHOT.pending_updated_at,
        )

    now = _utcnow()
    grace_delta = timedelta(seconds=max(grace_period, 0.0))

    if snapshot.health_state == "offline":
        if snapshot.health_updated_at and now - snapshot.health_updated_at <= grace_delta:
            return False
        # stale offline value -> fall back to optimistic path

    if snapshot.health_state in {"online", "degraded"}:
        if not snapshot.health_updated_at or now - snapshot.health_updated_at <= grace_delta:
            return True

    if snapshot.runtime_state and snapshot.runtime_state is not RuntimeStatusState.UNKNOWN:
        if not snapshot.runtime_updated_at or now - snapshot.runtime_updated_at <= grace_delta:
            return True

    # Default to optimistic True so GUI attempts the request and lets the worker
    # decide whether to fall back.
    return True


def get_snapshot() -> ApiStatusSnapshot:
    """Return a copy of the current snapshot for diagnostics."""
    with _LOCK:
        return ApiStatusSnapshot(
            health_state=_SNAPSHOT.health_state,
            health_message=_SNAPSHOT.health_message,
            health_updated_at=_SNAPSHOT.health_updated_at,
            runtime_state=_SNAPSHOT.runtime_state,
            runtime_label=_SNAPSHOT.runtime_label,
            runtime_tooltip=_SNAPSHOT.runtime_tooltip,
            runtime_updated_at=_SNAPSHOT.runtime_updated_at,
            pending_reason=_SNAPSHOT.pending_reason,
            pending_payload=dict(_SNAPSHOT.pending_payload),
            pending_updated_at=_SNAPSHOT.pending_updated_at,
        )


__all__ = [
    "ApiStatusSnapshot",
    "update_health_state",
    "update_runtime_view",
    "set_pending_update",
    "clear_pending_update",
    "is_api_available",
    "get_snapshot",
]
