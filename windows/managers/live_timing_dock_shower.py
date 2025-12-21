# -*- coding: utf-8 -*-
"""
LiveTimingDockShower - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingDockShower:
    """從 f1t_gui_main.py 提取的 _show_live_timing_dock 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _show_live_timing_dock(self):
        """顯示 Live Timing Control Dock"""
        if hasattr(self.main_window, 'live_timing_dock'):
            self.main_window.live_timing_dock.show()
            if hasattr(self.main_window, '_action_control_panel'):
                self.main_window._action_control_panel.setChecked(True)
            logger.debug("[LIVE_TIMING] Control Dock shown")
