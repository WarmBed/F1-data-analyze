"""Synchronous local analysis client for GUI code.

GUI loaders are mostly synchronous Qt workers today. This client gives those
workers a direct local path into the existing executor without requiring an
HTTP API server.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Union

from core.local_analysis_executor import LocalAnalysisExecutor


def execute_analysis_sync(function_id: Union[str, int], **params: Any) -> Dict[str, Any]:
    """Execute one analysis request through the local executor."""

    async def _run() -> Dict[str, Any]:
        return await LocalAnalysisExecutor().execute(function_id, **params)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_run())

    # This path should not be used from an already-running event loop. Qt worker
    # code is synchronous, but keep the error explicit if future code calls it
    # from async context.
    raise RuntimeError("execute_analysis_sync cannot run inside an active asyncio loop")


__all__ = ["execute_analysis_sync"]
