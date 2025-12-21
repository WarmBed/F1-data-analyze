# -*- coding: utf-8 -*-
"""
SplitterAdjuster - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class SplitterAdjuster:
    """從 f1t_gui_main.py 提取的 _adjust_splitter_for_tree 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _adjust_splitter_for_tree(self, tree_width):
        """根據樹狀圖寬度調整 Splitter"""
        if hasattr(self, 'analysis_splitter'):
            # 加上一些邊距（20px）以避免文字緊貼邊緣
            desired_width = tree_width + 20
            
            # 獲取當前 Splitter 的總寬度
            total_width = self.main_window.analysis_splitter.width()
            
            # 計算右側面板的寬度
            right_width = total_width - desired_width
            
            # 確保右側面板至少保留 800px
            if right_width < 800:
                desired_width = total_width - 800
            
            # 設置新的 Splitter 大小
            self.main_window.analysis_splitter.setSizes([desired_width, right_width])
