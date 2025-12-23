# -*- coding: utf-8 -*-
"""
ThirdTabChecker - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ThirdTabChecker:
    """從 f1t_gui_main.py 提取的 third_tab_check 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def third_tab_check(self):
        """第三次標籤檢查（延遲5秒後）- 簡化版本"""
        logger.debug(f"[TAB_HIDE] 最終檢查 - QTabBar 可見性: {self.main_window.tab_widget.tabBar().isVisible()}")
        logger.debug(f"[TAB_HIDE] 最終檢查 - QTabBar 高度: {self.main_window.tab_widget.tabBar().height()}")
        
        # 檢查 TabButtonsContainer 狀態
        corner_widget = self.main_window.tab_widget.cornerWidget(Qt.TopRightCorner)
        if corner_widget:
            logger.debug(f"[TAB_HIDE] TabButtonsContainer 可見性: {corner_widget.isVisible()}")
            logger.debug(f"[TAB_HIDE] TabButtonsContainer 大小: {corner_widget.size()}")
        logger.debug(f"[TAB_HIDE] 所有標籤隱藏檢查完成")
    
    # ==================== 同步功能實現 ====================
