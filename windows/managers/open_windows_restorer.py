# -*- coding: utf-8 -*-
"""
OpenWindowsRestorer - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from typing import Dict
from typing import List
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)


class OpenWindowsRestorer:
    """從 f1t_gui_main.py 提取的 _restore_open_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _restore_open_windows(self, windows_state: Optional[List[Dict[str, Any]]]) -> None:
        """依據快照資料還原目前工作區的分析視窗"""
        # 關閉現有活動視窗，避免與快照資料衝突
        for subwindow in list(getattr(self, "active_subwindows", []) or []):
            try:
                subwindow.close()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to close subwindow during restore: %s", exc)

        if hasattr(self, "active_subwindows"):
            self.main_window.active_subwindows.clear()

        if not windows_state:
            return

        for window_state in windows_state:
            try:
                self.main_window._restore_single_window(window_state)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to restore window state", exc_info=exc)
