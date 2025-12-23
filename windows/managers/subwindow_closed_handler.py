# -*- coding: utf-8 -*-
"""
SubwindowClosedHandler - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class SubwindowClosedHandler:
    """從 f1t_gui_main.py 提取的 on_subwindow_closed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_subwindow_closed(self, subwindow):
        """處理子視窗關閉事件 - 從追蹤列表中移除"""
        try:
            window_title = subwindow.windowTitle() if subwindow else "未知視窗"
            
            # 從活動子視窗列表中移除
            if hasattr(self, 'active_subwindows') and subwindow in self.main_window.active_subwindows:
                self.main_window.active_subwindows.remove(subwindow)
            
            # 檢查是否還有分析模組在運行
            self.main_window._check_and_update_toolbar_status()
            
        except Exception as e:
            pass
