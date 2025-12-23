# -*- coding: utf-8 -*-
"""
SubwindowPositioner - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class SubwindowPositioner:
    """從 f1t_gui_main.py 提取的 _position_subwindow 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _position_subwindow(self, mdi_area, sub_window):
        """根據現有視窗數量調整子視窗位置，避免重疊。"""
        try:
            existing_windows = mdi_area.subWindowList()
            window_count = len(existing_windows)

            offset_x = (window_count % 4) * 30
            offset_y = (window_count // 4) * 30
            base_x = 10 + offset_x
            base_y = 10 + offset_y

            sub_window.move(base_x, base_y)
        except Exception as exc:
            logger.warning(f"[WARNING] 無法調整子視窗位置: {exc}")
