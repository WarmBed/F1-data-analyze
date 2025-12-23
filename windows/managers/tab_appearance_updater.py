# -*- coding: utf-8 -*-
"""
TabAppearanceUpdater - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from PyQt5.QtGui import QColor

logger = get_logger(__name__)


class TabAppearanceUpdater:
    """從 f1t_gui_main.py 提取的 _update_tab_appearance 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _update_tab_appearance(self, tab_index, is_popped_out):
        """更新分頁標籤外觀（灰色 + 圖標）"""
        try:
            tab_name = self.main_window.tab_widget.tabText(tab_index)
            
            # 移除可能存在的 🔗 圖標
            tab_name_clean = tab_name.replace("🔗 ", "")
            
            if is_popped_out:
                # 添加 🔗 圖標並設置灰色樣式
                new_tab_text = f"🔗 {tab_name_clean}"
                self.main_window.tab_widget.setTabText(tab_index, new_tab_text)
                
                # 設置灰色樣式
                tab_bar = self.main_window.tab_widget.tabBar()
                tab_bar.setTabTextColor(tab_index, QColor(102, 102, 102))  # #666666
                
                logger.debug(f"[TAB_POPOUT] 🎨 分頁 {tab_index} 標籤已設為灰色 + 🔗")
            else:
                # 恢復正常文字和顏色
                self.main_window.tab_widget.setTabText(tab_index, tab_name_clean)
                
                # 恢復正常顏色
                tab_bar = self.main_window.tab_widget.tabBar()
                tab_bar.setTabTextColor(tab_index, QColor(0, 0, 0))  # 黑色
                
                logger.debug(f"[TAB_POPOUT] 🎨 分頁 {tab_index} 標籤已恢復正常")
                
        except Exception as e:
            logger.debug(f"[TAB_POPOUT] ❌ 更新標籤外觀失敗: {e}")
