#!/usr/bin/env python3
"""
Telemetry generation helper utilities for Lap Analysis modules.

Provides a blocking helper that triggers the telemetry comparison API
(Function 13) via the SpeedAnalysisDataLoader and waits for completion.
This replaces the legacy CLI invocation that is disallowed under the
2025-10-03 API-ONLY policy.
"""

from __future__ import annotations

from typing import Optional, Tuple

from PyQt5.QtCore import QEventLoop, QTimer


def ensure_telemetry_analysis_via_api(
    year: int,
    race: str,
    session: str,
    driver1: str,
    driver2: Optional[str] = None,
    *,
    parent=None,
    timeout_ms: int = 60000,
    is_fastest_lap: bool = True,
) -> Tuple[bool, Optional[str]]:
    """Generate telemetry comparison data via the REST API.

    This helper instantiates ``SpeedAnalysisDataLoader`` (which is backed by
    ``TelemetryDataLoader``) and waits synchronously for the ``data_loaded`` or
    ``load_error`` signal. The function returns once a response is received or
    the timeout elapses.

    Args:
        year: Race year.
        race: Grand Prix name.
        session: Session code (R/Q/FP1/... ).
        driver1: Primary driver code.
        driver2: Second driver code; falls back to driver1 when ``None``.
        parent: Optional QObject parent passed to the loader.
        timeout_ms: Milliseconds to wait before aborting.
        is_fastest_lap: Whether to request fastest-lap telemetry data.

    Returns:
        A tuple ``(success, message)`` where ``success`` indicates whether
        telemetry data was produced and ``message`` contains an optional error
        description when ``success`` is ``False``.
    """

    try:
        from modules.gui.lap_analysis.speed_analysis.speed_analysis_data_loader import (
            SpeedAnalysisDataLoader,
        )
    except Exception as exc:  # pragma: no cover - import failure is exceptional
        return False, f"Failed to import SpeedAnalysisDataLoader: {exc}"

    loader = SpeedAnalysisDataLoader(parent)
    try:
        loader.set_local_fallback_allowed(False, "[API-ONLY] 禁用 CLI 後備流程")
    except AttributeError:
        # Older loaders might not expose this API; fail fast to avoid CLI usage.
        loader.deleteLater()
        return False, "Telemetry loader does not support API-only mode"

    loop = QEventLoop()
    result = {"success": False, "message": None}

    def _cleanup():
        try:
            loader.data_loaded.disconnect(on_loaded)
        except Exception:
            pass
        try:
            loader.load_error.disconnect(on_error)
        except Exception:
            pass
        loader.deleteLater()

    def on_loaded(_: dict) -> None:
        result["success"] = True
        result["message"] = None
        if loop.isRunning():
            loop.quit()

    def on_error(message: str) -> None:
        result["success"] = False
        result["message"] = message
        if loop.isRunning():
            loop.quit()

    loader.data_loaded.connect(on_loaded)
    loader.load_error.connect(on_error)

    primary = (driver1 or "VER").upper()
    secondary = (driver2 or primary or "VER").upper()

    started = loader.load_speed_data(
        year=int(year),
        race=race,
        session=session,
        driver1=primary,
        driver2=secondary,
        lap1=1,
        lap2=1,
        is_fastest_lap=is_fastest_lap,
    )

    if not started:
        _cleanup()
        return False, "Telemetry API request could not be started"

    timer = QTimer()
    timer.setSingleShot(True)

    def on_timeout() -> None:
        result["success"] = False
        result["message"] = "Telemetry API request timed out"
        if loop.isRunning():
            loop.quit()

    timer.timeout.connect(on_timeout)
    timer.start(max(1000, int(timeout_ms)))

    loop.exec_()

    if timer.isActive():
        timer.stop()
    try:
        timer.timeout.disconnect(on_timeout)
    except Exception:
        pass

    _cleanup()

    return result["success"], result["message"]
