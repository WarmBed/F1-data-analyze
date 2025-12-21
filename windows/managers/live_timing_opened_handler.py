# -*- coding: utf-8 -*-
"""
LiveTimingOpenedHandler - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingOpenedHandler:
    """從 f1t_gui_main.py 提取的 _on_live_timing_module_opened 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_live_timing_module_opened(self):
        """當 Live Timing 模組開啟時調用"""
        self.main_window._live_timing_module_count = getattr(self, '_live_timing_module_count', 0) + 1
        if self.main_window._live_timing_module_count == 1:
            self.main_window._show_live_timing_dock()
