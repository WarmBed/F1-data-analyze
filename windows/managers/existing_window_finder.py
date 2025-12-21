# -*- coding: utf-8 -*-
"""
ExistingWindowFinder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMdiSubWindow
from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class ExistingWindowFinder:
    """從 f1t_gui_main.py 提取的 _find_existing_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _find_existing_window(self, mdi_area, title_patterns):
        """
        在MDI區域中查找匹配標題模式的現有視窗
        
        參數:
            mdi_area: CustomMdiArea - MDI區域
            title_patterns: list[str] - 標題模式列表（支援萬用字元 * 和 ?）
        
        返回:
            QMdiSubWindow 或 None - 找到的第一個匹配視窗
        """
        import fnmatch
        
        # 確保 title_patterns 是列表
        if isinstance(title_patterns, str):
            title_patterns = [title_patterns]
        
        # 🔍 [DEBUG]    記錄所有現有視窗
        existing_windows = mdi_area.subWindowList()
        logger.info(f"[DUPLICATE_CHECK] 🔍 當前 MDI 區域有 {len(existing_windows)} 個視窗")
        for i, win in enumerate(existing_windows, 1):
            logger.info(f"[DUPLICATE_CHECK]   視窗{i}: '{win.windowTitle()}'")
        
        # 🔍 [DEBUG]    記錄要匹配的模式
        logger.info(f"[DUPLICATE_CHECK] 🎯 要匹配的模式共 {len(title_patterns)} 個:")
        for i, pattern in enumerate(title_patterns, 1):
            logger.info(f"[DUPLICATE_CHECK]   模式{i}: '{pattern}'")
        
        # 遍歷所有子視窗
        for sub_window in existing_windows:
            window_title = sub_window.windowTitle()
            
            # 檢查是否匹配任一模式
            for pattern in title_patterns:
                if fnmatch.fnmatch(window_title, pattern):
                    logger.info(f"[DUPLICATE_CHECK] ✅ 找到匹配視窗!")
                    logger.info(f"[DUPLICATE_CHECK]   視窗標題: '{window_title}'")
                    logger.info(f"[DUPLICATE_CHECK]   匹配模式: '{pattern}'")
                    return sub_window
        
        logger.info(f"[DUPLICATE_CHECK] ❌ 未找到匹配視窗")
        return None
