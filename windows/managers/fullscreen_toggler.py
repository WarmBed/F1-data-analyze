# -*- coding: utf-8 -*-
"""
FullscreenToggler - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class FullscreenToggler:
    """從 f1t_gui_main.py 提取的 toggle_fullscreen 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def toggle_fullscreen(self):
        """切換全螢幕模式"""
        #print("[檢視] 全螢幕切換")
        
        if self.main_window.isFullScreen():
            # 退出全螢幕
            self.main_window.showNormal()
            #print("🔲 退出全螢幕模式")
        else:
            # 進入全螢幕
            self.main_window.showFullScreen()
            #print("🔳 進入全螢幕模式")
            
        # 強制刷新界面
        self.main_window.update()
