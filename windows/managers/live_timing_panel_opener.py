# -*- coding: utf-8 -*-
"""
LiveTimingPanelOpener - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingPanelOpener:
    """從 f1t_gui_main.py 提取的 _open_live_timing_control_panel 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _open_live_timing_control_panel(self):
        """顯示 Live Timing 控制面板 Dock"""
        if hasattr(self, 'live_timing_dock'):
            self.main_window.live_timing_dock.show()
            if hasattr(self, '_action_control_panel'):
                self.main_window._action_control_panel.setChecked(True)
    

    # ========== 25 個 _open_live_timing_* 包裝方法已移除 ==========
    # 這些方法已由 LiveTimingManager.open_module() 取代
    # 詳見 windows/managers/live_timing_manager.py
