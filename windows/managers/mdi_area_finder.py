# -*- coding: utf-8 -*-
"""
MdiAreaFinder - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class MdiAreaFinder:
    """從 f1t_gui_main.py 提取的 _find_mdi_area 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _find_mdi_area(self, widget):
        """遞迴尋找 CustomMdiArea"""
        if isinstance(widget, CustomMdiArea):
            return widget
        
        # 檢查子組件
        if hasattr(widget, 'children'):
            for child in widget.children():
                if isinstance(child, CustomMdiArea):
                    return child
                # 遞迴搜尋
                result = self.main_window._find_mdi_area(child)
                if result:
                    return result
        return None
