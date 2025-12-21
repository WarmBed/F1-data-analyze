# -*- coding: utf-8 -*-
"""
WelcomePageRemover - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class WelcomePageRemover:
    """從 f1t_gui_main.py 提取的 check_and_remove_welcome_page 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def check_and_remove_welcome_page(self):
        """
        檢查並處理歡迎頁面
        
        ⚠️ 分頁架構改進：
        - 只有當前在主頁時才創建 "分頁一"
        - 如果已在其他分頁，不做任何操作（允許添加到當前分頁）
        """
        # 獲取當前分頁
        current_tab = self.main_window.tab_widget.currentWidget()
        
        # ✅ 只有當前在主頁時才創建新分頁
        if current_tab and current_tab.objectName() == "welcome_tab":
            logger.debug("[TAB] 💡 檢測到在主頁，自動創建 '分頁一'")
            
            # 檢查是否已經有非主頁的分頁存在
            has_non_welcome_tab = False
            for i in range(self.main_window.tab_widget.count()):
                tab = self.main_window.tab_widget.widget(i)
                if tab.objectName() != "welcome_tab":
                    has_non_welcome_tab = True
                    logger.debug(f"[TAB] 💡 發現已存在的分頁，切換到該分頁而不創建新分頁")
                    self.main_window.tab_widget.setCurrentIndex(i)
                    break
            
            # 如果沒有其他分頁，才創建新分頁
            if not has_non_welcome_tab:
                self.main_window.add_new_tab()  # 創建 "分頁一" 並自動切換
                logger.debug("[TAB] ✅ 已創建 '分頁一' 並切換過去")
        else:
            # 當前不在主頁，不做任何操作（模組會添加到當前分頁）
            if current_tab:
                logger.debug(f"[TAB] 💡 當前在分頁 '{self.main_window.tab_widget.tabText(self.main_window.tab_widget.currentIndex())}'，模組將添加到此分頁")
            else:
                logger.debug("[TAB] ⚠️ 無法獲取當前分頁")
