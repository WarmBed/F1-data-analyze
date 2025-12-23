# -*- coding: utf-8 -*-
"""
ApiRuntimeHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ApiRuntimeHandler:
    """從 f1t_gui_main.py 提取的 on_api_runtime_result 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_api_runtime_result(self, summary: dict) -> None:
        """Handle runtime status payloads and update the CLI indicator."""
        try:
            if not self.main_window.cli_status_label:
                return

            if summary.get('ok'):
                payload = summary.get('payload')
                view = self.main_window._runtime_status_resolver.resolve(payload)
            else:
                error_text = summary.get('error') or '無法取得 CLI 狀態'
                view = RuntimeStatusView(
                    state=RuntimeStatusState.UNKNOWN,
                    label='[CLI] UNKNOWN',
                    color='#c0392b',
                    tooltip=error_text,
                    active_task_count=0,
                )

            self.main_window._apply_cli_status_view(view)
            update_runtime_view(view)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error('Failed to process runtime summary: %s', exc)
            fallback = RuntimeStatusView(
                state=RuntimeStatusState.UNKNOWN,
                label='[CLI] UNKNOWN',
                color='#c0392b',
                tooltip=str(exc),
                active_task_count=0,
            )
            self.main_window._apply_cli_status_view(fallback)
            update_runtime_view(fallback)
