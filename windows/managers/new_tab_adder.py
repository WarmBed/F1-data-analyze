# -*- coding: utf-8 -*-
"""
NewTabAdder - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import get_gui_language, tr
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
        
        # 生成標籤名稱：根據語言選擇數字格式
        current_lang = get_gui_language()
        if current_lang == "zh":
            number_str = self.main_window._convert_to_chinese_number(tab_count)
        else:
            number_str = str(tab_count)
        tab_name = tr("tab_page", "Tab {number}").format(number=number_str)
        
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
