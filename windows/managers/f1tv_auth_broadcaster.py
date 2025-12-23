# -*- coding: utf-8 -*-
"""
F1tvAuthBroadcaster - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class F1tvAuthBroadcaster:
    """從 f1t_gui_main.py 提取的 _broadcast_f1tv_auth_state 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _broadcast_f1tv_auth_state(self, authenticated: bool):
        """廣播 F1TV 認證狀態到所有 Live Timing 模組"""
        # 更新 Control Dock
        if hasattr(self, '_live_timing_control_dock') and self.main_window._live_timing_control_dock:
            if hasattr(self.main_window._live_timing_control_dock, 'set_f1tv_authenticated'):
                self.main_window._live_timing_control_dock.set_f1tv_authenticated(authenticated)
        
        # 更新所有已開啟的 Live Timing 視窗
        if hasattr(self, 'mdi_area') and self.main_window.mdi_area:
            for sub_window in self.main_window.mdi_area.subWindowList():
                widget = sub_window.widget()
                if hasattr(widget, 'set_f1tv_authenticated'):
                    widget.set_f1tv_authenticated(authenticated)
    
    # ===========================================
    # Live Timing Dock Widget 設置
    # ===========================================
