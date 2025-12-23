# -*- coding: utf-8 -*-
"""
LinkageFinder - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class LinkageFinder:
    """從 f1t_gui_main.py 提取的 _find_linkage_modules_in_widget 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _find_linkage_modules_in_widget(self, widget):
        """遞歸查找 widget 中所有實現了連動功能的模組"""
        linkage_modules = []
        
        # 檢查當前 widget 是否實現了連動功能
        if hasattr(widget, 'on_x_linkage_received') or hasattr(widget, 'on_click_linkage_received'):
            linkage_modules.append(widget)
        
        # 遞歸檢查所有子 widget
        if hasattr(widget, 'children'):
            for child in widget.children():
                if hasattr(child, '__class__') and hasattr(child, 'parent'):
                    linkage_modules.extend(self.main_window._find_linkage_modules_in_widget(child))
        
        return linkage_modules
