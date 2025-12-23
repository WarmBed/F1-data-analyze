# -*- coding: utf-8 -*-
"""
WelcomeTabRemover - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class WelcomeTabRemover:
    """從 f1t_gui_main.py 提取的 remove_welcome_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def remove_welcome_tab(self):
        """移除歡迎頁面 - 當使用者開始分析時"""
        try:
            for i in range(self.main_window.tab_widget.tabCount()):
                tab_text = self.main_window.tab_widget.tabText(i)
                if "歡迎" in tab_text or "Welcome" in tab_text:
                    self.main_window.tab_widget.removeTab(i)
                    #print(f"[OK] 已移除歡迎頁面: {tab_text}")
                    break
        except Exception as e:
            #print(f"[WARNING] 移除歡迎頁面時發生錯誤: {e}")
            pass
