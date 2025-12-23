# -*- coding: utf-8 -*-
"""
UniqueTabNamer - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class UniqueTabNamer:
    """從 f1t_gui_main.py 提取的 _get_unique_tab_name 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _get_unique_tab_name(self, base_name):
        """
        獲取唯一的分頁名稱，如果重複則添加 (1), (2), (3) 後綴
        
        Args:
            base_name: 基礎名稱
            
        Returns:
            唯一的分頁名稱
        """
        # 收集所有現有分頁名稱（移除 🔗 圖標）
        existing_names = []
        for i in range(self.main_window.tab_widget.count()):
            name = self.main_window.tab_widget.tabText(i).replace("🔗 ", "")
            existing_names.append(name)
        
        # 如果基礎名稱不重複，直接返回
        if base_name not in existing_names:
            return base_name
        
        # 名稱重複，添加數字後綴
        counter = 1
        while True:
            new_name = f"{base_name} ({counter})"
            if new_name not in existing_names:
                return new_name
            counter += 1
