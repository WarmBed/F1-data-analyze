"""Local analysis execution facade.

This is the migration target for both GUI and CLI paths. It deliberately
does not perform HTTP requests. For now it wraps the existing service, which
already executes analysis locally by checking cache and running CLI modules.
Future refactors should move the service out of ``api.services`` into a
neutral core package, then keep this public facade stable.
"""

from __future__ import annotations

from typing import Any, Dict, Union


class LocalAnalysisExecutor:
    """Execute analysis functions without depending on the HTTP API."""

    def __init__(self) -> None:
        # Imported lazily to avoid pulling API/FastAPI dependencies at module
        # import time. The wrapped service currently lives under api.services
        # but its execution path is local cache + CLI subprocess, not HTTP.
        from api.services.simple_analysis_service import SimpleF1AnalysisService

        self._service = SimpleF1AnalysisService()

    async def execute(self, function_id: Union[str, int], **params: Any) -> Dict[str, Any]:
        """Execute one local analysis request."""

        return await self._service.execute_analysis(function_id, **params)

    def get_runtime_state(self) -> Dict[str, Any]:
        """Return local runtime state when available."""

        return self._service.get_runtime_state()


__all__ = ["LocalAnalysisExecutor"]
