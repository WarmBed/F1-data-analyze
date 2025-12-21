# -*- coding: utf-8 -*-
"""
MdiSubwindowSyncer - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class MdiSubwindowSyncer:
    """從 f1t_gui_main.py 提取的 sync_to_all_mdi_subwindows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def sync_to_all_mdi_subwindows(self, param_type, value):
        """同步參數到所有MDI子視窗"""
        logger.debug(f"[REFRESH] [SYNC] 開始同步 {param_type} = {value} 到所有MDI子視窗")
        logger.debug(f"[LINK] [SYNC] 已註冊的MDI區域數量: {len(self.main_window.mdi_areas)}")
        
        synced_count = 0
        for i, mdi_area in enumerate(self.main_window.mdi_areas):
            logger.debug(f"[SEARCH] [SYNC] 檢查MDI區域 {i+1}/{len(self.main_window.mdi_areas)}: {mdi_area.objectName()}")
            synced_count += self.main_window.sync_to_mdi_area(mdi_area, param_type, value)
        
        logger.debug(f"[OK] [SYNC] 完成同步，共更新 {synced_count} 個子視窗")
