# -*- coding: utf-8 -*-
"""
TabCloser - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class TabCloser:
    """從 f1t_gui_main.py 提取的 close_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def close_tab(self, index):
        """關閉指定索引的分頁 - 最後分頁關閉時顯示歡迎頁"""
        
        # [UNDO] 記錄 Tab 狀態 (用於 Ctrl+Z)
        try:
            if hasattr(self.main_window, 'get_window_state_manager'):
                manager = self.main_window.get_window_state_manager()
                if manager:
                    from windows.managers.window_state_manager import capture_tab_state
                    state = capture_tab_state(self.main_window.tab_widget, index)
                    manager.push_state(state)
                    logger.debug(f"[UNDO] 已記錄 Tab 關閉狀態: {state.tab_name}")
        except Exception as e:
            logger.warning(f"[UNDO] 記錄 Tab 關閉狀態失敗: {e}")
            
        # ✅ 最後一個分頁時，創建歡迎頁而不是退出
        if self.main_window.tab_widget.count() <= 1:
            logger.debug("[TAB] 💡 關閉最後一個分頁，創建新的歡迎頁")
            # 先關閉當前分頁
            widget = self.main_window.tab_widget.widget(index)
            self.main_window.tab_widget.removeTab(index)
            if widget:
                widget.deleteLater()
            
            # 創建新的歡迎頁
            welcome_tab = self.main_window.create_welcome_tab()
            welcome_tab.setObjectName("welcome_tab")
            self.main_window.tab_widget.addTab(welcome_tab, tr("home_page", "主頁"))
            self.main_window.tab_widget.setCurrentIndex(0)
            
            logger.debug("[TAB] ✅ 已創建新的歡迎頁")
            self.main_window.update_tab_count()
            return
        
        # 正常關閉分頁
        widget = self.main_window.tab_widget.widget(index)
        self.main_window.tab_widget.removeTab(index)
        
        if widget:
            widget.deleteLater()
        
        logger.debug(f"[TAB] ✅ 已關閉分頁 #{index}")
        self.main_window.update_tab_count()
