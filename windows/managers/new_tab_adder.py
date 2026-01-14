# -*- coding: utf-8 -*-
"""
NewTabAdder - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class NewTabAdder:
    """從 f1t_gui_main.py 提取的 add_new_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def add_new_tab(self, *args, **kwargs):
        """新增分頁 - 簡化版，直接創建空白工作區"""
        # 計算分頁編號（排除歡迎頁）
        tab_count = self.main_window.tab_widget.count()
        
        # 生成標籤名稱：統一使用英文 "Tab X"
        tab_name = f"Tab {tab_count}"
        
        # 創建空白 MDI 工作區
        new_mdi_area = CustomMdiArea()
        new_mdi_area.setObjectName(f"MdiArea_{tab_count}")
        
        # 添加到標籤列
        index = self.main_window.tab_widget.addTab(new_mdi_area, tab_name)
        self.main_window.tab_widget.setCurrentIndex(index)
        
        # 追蹤 MDI 區域
        self.main_window.mdi_areas.append(new_mdi_area)
        
        logger.debug(f"[TAB] ✅ 已創建新分頁: {tab_name}")
        self.main_window.update_tab_count()
