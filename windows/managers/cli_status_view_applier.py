# -*- coding: utf-8 -*-
"""
CliStatusViewApplier - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class CliStatusViewApplier:
    """從 f1t_gui_main.py 提取的 _apply_cli_status_view 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _apply_cli_status_view(self, view: RuntimeStatusView) -> None:
        if not self.main_window.cli_status_label:
            return

        signature = (view.label, view.color, view.tooltip)
        if signature == self.main_window._last_cli_status_signature:
            return

        self.main_window.cli_status_label.setText(view.label)
        self.main_window.cli_status_label.setStyleSheet(f'color: {view.color}; font-weight: bold;')
        self.main_window.cli_status_label.setToolTip(view.tooltip)
        self.main_window._last_cli_status_signature = signature
