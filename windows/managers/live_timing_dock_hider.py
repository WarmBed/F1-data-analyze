# -*- coding: utf-8 -*-
"""
LiveTimingDockHider - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingDockHider:
    """從 f1t_gui_main.py 提取的 _hide_live_timing_dock 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _hide_live_timing_dock(self):
        """隱藏 Live Timing Control Dock"""
        if hasattr(self, 'live_timing_dock'):
            self.main_window.live_timing_dock.hide()
            if hasattr(self, '_action_control_panel'):
                self.main_window._action_control_panel.setChecked(False)
            logger.debug("[LIVE_TIMING] Control Dock hidden")
