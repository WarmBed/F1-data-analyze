# -*- coding: utf-8 -*-
"""
LiveTimingClosedHandler - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingClosedHandler:
    """從 f1t_gui_main.py 提取的 _on_live_timing_module_closed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_live_timing_module_closed(self, *args, **kwargs):
        """當 Live Timing 模組關閉時調用"""
        self.main_window._live_timing_module_count = max(0, getattr(self.main_window, '_live_timing_module_count', 1) - 1)
        if self.main_window._live_timing_module_count == 0:
            self.main_window._hide_live_timing_dock()
    
    # ===========================================
    # Live Timing 模組方法（使用 LiveTimingModuleFactory）
    # ===========================================
