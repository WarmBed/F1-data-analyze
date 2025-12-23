# -*- coding: utf-8 -*-
"""
MdiAreaRegistrar - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class MdiAreaRegistrar:
    """從 f1t_gui_main.py 提取的 register_mdi_area 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def register_mdi_area(self, mdi_area):
        """註冊MDI區域到主視窗（用於同步功能）"""
        logger.debug(f"[LINK] [DEBUG]    嘗試註冊MDI區域: {mdi_area.objectName() if mdi_area else 'None'}")
        logger.debug(f"[LINK] [DEBUG]    當前已註冊的MDI區域數量: {len(self.main_window.mdi_areas)}")
        logger.debug(f"[LINK] [DEBUG]    主視窗類型: {type(self).__name__}")
        
        if mdi_area not in self.main_window.mdi_areas:
            self.main_window.mdi_areas.append(mdi_area)
            logger.debug(f"[OK] [MDI] MDI區域已註冊: {mdi_area.objectName()}")
            logger.debug(f"[OK] [MDI] 註冊後MDI區域總數: {len(self.main_window.mdi_areas)}")
        else:
            logger.warning(f"[WARNING] [MDI] MDI區域已存在，跳過註冊: {mdi_area.objectName()}")
