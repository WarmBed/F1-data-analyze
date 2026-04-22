# -*- coding: utf-8 -*-
"""Local GUI task workers.

Use this worker as the migration target for GUI modules that currently create
their own QThread plus requests.post implementation. It keeps the UI thread
free and routes analysis through the local executor instead of HTTP.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, Union

from PyQt5.QtCore import QThread, pyqtSignal

from core.local_analysis_executor import LocalAnalysisExecutor


class LocalAnalysisWorker(QThread):
    """Run one local analysis request on a background Qt thread."""

    started_with_id = pyqtSignal(str)
    progress_updated = pyqtSignal(str, str)
    result_ready = pyqtSignal(str, dict)
    error_ready = pyqtSignal(str, str)
    cancelled = pyqtSignal(str)
    finished_with_id = pyqtSignal(str)

    def __init__(
        self,
        function_id: Union[str, int],
        params: Dict[str, Any] | None = None,
        request_id: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.function_id = function_id
        self.params = dict(params or {})
        self.request_id = request_id or str(uuid.uuid4())
        self._should_stop = False

    def stop_worker(self) -> None:
        """Request cancellation at the worker boundary.

        Existing CLI subprocess execution cannot yet be interrupted from here.
        The next refactor should pass cancellation into LocalAnalysisExecutor.
        """

        self._should_stop = True

    def run(self) -> None:
        self.started_with_id.emit(self.request_id)
        start = time.perf_counter()

        if self._should_stop:
            self.cancelled.emit(self.request_id)
            self.finished_with_id.emit(self.request_id)
            return

        try:
            self.progress_updated.emit(self.request_id, "local analysis starting")
            result = asyncio.run(self._execute())
            if self._should_stop:
                self.progress_updated.emit(self.request_id, "local analysis cancelled")
                self.cancelled.emit(self.request_id)
                return

            result.setdefault("request_id", self.request_id)
            result.setdefault("worker_elapsed_seconds", round(time.perf_counter() - start, 3))
            self.result_ready.emit(self.request_id, result)
        except Exception as exc:
            self.error_ready.emit(self.request_id, f"{type(exc).__name__}: {exc}")
        finally:
            self.finished_with_id.emit(self.request_id)

    async def _execute(self) -> Dict[str, Any]:
        executor = LocalAnalysisExecutor()
        return await executor.execute(self.function_id, **self.params)


__all__ = ["LocalAnalysisWorker"]
