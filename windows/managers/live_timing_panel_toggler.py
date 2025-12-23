# -*- coding: utf-8 -*-
"""
LiveTimingPanelToggler - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingPanelToggler:
    """從 f1t_gui_main.py 提取的 _toggle_live_timing_control_panel 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _toggle_live_timing_control_panel(self, checked: bool):
        """切換 Live Timing 控制面板 Dock 的顯示狀態"""
        if hasattr(self, 'live_timing_dock'):
            if checked:
                self.main_window.live_timing_dock.show()
            else:
                self.main_window.live_timing_dock.hide()
