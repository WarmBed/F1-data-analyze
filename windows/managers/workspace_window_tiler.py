# -*- coding: utf-8 -*-
"""
WorkspaceWindowTiler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class WorkspaceWindowTiler:
    """從 f1t_gui_main.py 提取的 _tile_all_workspace_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _tile_all_workspace_windows(self):
        """
        [已棄用] 舊版自動平鋪方法 - 使用 Qt 原生 tileSubWindows()
        
        ⚠️ 此方法已被 _tile_all_workspace_windows_delayed() 取代
        原因: Qt 原生方法在 MDI 區域尺寸未更新時會計算錯誤的視窗位置
        新方法使用智能 tile_windows() 並添加延遲處理
        """
        logger.debug(f"[WORKSPACE] ⚠️ 調用了已棄用的 _tile_all_workspace_windows()")
        logger.debug(f"[WORKSPACE] → 請改用 _tile_all_workspace_windows_delayed()")
        
        # 為了向後兼容，直接調用新方法
        self.main_window._tile_all_workspace_windows_delayed()
