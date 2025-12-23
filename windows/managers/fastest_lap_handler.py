# -*- coding: utf-8 -*-
"""
FastestLapHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class FastestLapHandler:
    """從 f1t_gui_main.py 提取的 _on_main_fastest_lap_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_main_fastest_lap_changed(self, checked):
        """主頁面最速圈checkbox變更時的處理 - 自動設置圈數為99"""
        logger.debug(f"[LAP_CONTROL] [DEBUG]   🏁 主頁面最速圈checkbox變更: {checked}")
        
        if checked:
            # 最速圈被勾選，自動設置圈數為99
            logger.debug("[LAP_CONTROL] [DEBUG]   🏁 最速圈被選中，自動設置圈數1和圈數2為99")
            
            if hasattr(self.main_window, 'lap1_spinbox'):
                old_value1 = self.main_window.lap1_spinbox.value()
                self.main_window.lap1_spinbox.setValue(99)
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🏁 圈數1: {old_value1} → 99")
                
            if hasattr(self.main_window, 'lap2_spinbox'):
                old_value2 = self.main_window.lap2_spinbox.value()
                self.main_window.lap2_spinbox.setValue(99)
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🏁 圈數2: {old_value2} → 99")
        else:
            # 最速圈被取消，恢復預設圈數1
            logger.debug("[LAP_CONTROL] [DEBUG]   🏁 最速圈被取消，恢復預設圈數1")
            
            if hasattr(self.main_window, 'lap1_spinbox'):
                self.main_window.lap1_spinbox.setValue(1)
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🏁 圈數1: 恢復為1")
                
            if hasattr(self.main_window, 'lap2_spinbox'):
                self.main_window.lap2_spinbox.setValue(1)
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🏁 圈數2: 恢復為1")
