# -*- coding: utf-8 -*-
"""
MdiScrollUpdater - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class MdiScrollUpdater:
    """從 f1t_gui_main.py 提取的 _update_all_mdi_scroll_areas 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _update_all_mdi_scroll_areas(self):
        """
        更新所有分頁的 MDI 滾動範圍
        
        用於 Workspace 載入後，確保所有超出範圍的視窗都能透過滾動條訪問
        """
        logger.debug(f"[WORKSPACE] 🔄 更新所有 MDI 區域的滾動範圍...")
        
        updated_tabs = 0
        for tab_index in range(1, self.main_window.tab_widget.count()):  # 跳過 HOME
            tab_widget = self.main_window.tab_widget.widget(tab_index)
            
            # 檢查是否為 CustomMdiArea
            if hasattr(tab_widget, '_update_scroll_area'):
                tab_name = self.main_window.tab_widget.tabText(tab_index)
                logger.debug(f"[WORKSPACE] 📏 更新分頁 '{tab_name}' 的滾動範圍")
                tab_widget._update_scroll_area()
                updated_tabs += 1
        
        logger.debug(f"[WORKSPACE] ✅ 已更新 {updated_tabs} 個分頁的滾動範圍")
