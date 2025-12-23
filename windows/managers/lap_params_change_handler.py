# -*- coding: utf-8 -*-
"""
LapParamsChangeHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LapParamsChangeHandler:
    """從 f1t_gui_main.py 提取的 on_lap_parameters_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_lap_parameters_changed(self):
        """
        圈速參數變更處理器（手動更新模式）
        
        ⚠️ 注意：此方法已停用自動更新功能
        現在僅用於記錄參數變更，不會觸發實際更新
        用戶必須手動點擊 "Update All Analysis" 按鈕才會更新
        """
        logger.debug("[LAP_CONTROL] [DEBUG]   � 圈速參數已變更（手動更新模式，不自動更新）")
        
        # 記錄當前參數值（僅用於調試）
        try:
            driver1 = self.main_window.driver1_combo.currentText() if hasattr(self, 'driver1_combo') else "未知"
            driver2 = self.main_window.driver2_combo.currentText() if hasattr(self, 'driver2_combo') else "未知"
            lap1 = self.main_window.lap1_spinbox.value() if hasattr(self, 'lap1_spinbox') else "未知"
            lap2 = self.main_window.lap2_spinbox.value() if hasattr(self, 'lap2_spinbox') else "未知"
            is_fastest = self.main_window.fastest_lap_checkbox.isChecked() if hasattr(self, 'fastest_lap_checkbox') else False
            
            logger.debug(f"[LAP_CONTROL] [DEBUG]   📊 當前參數值:")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     🏎️ 車手1: '{driver1}'")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     🏎️ 車手2: '{driver2}'")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     🏁 圈數1: {lap1}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     🏁 圈數2: {lap2}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     ⚡ 最速圈: {is_fastest}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]   � 提示: 請點擊 'Update All Analysis' 按鈕以應用更改")
                
        except Exception as e:
            logger.debug(f"[LAP_CONTROL] [DEBUG]   ❌ 參數記錄時發生錯誤: {e}")
        
        # ⚠️ 已移除自動更新邏輯
        # 不再啟動計時器或調用 update_all_lap_analysis()
        # 用戶必須手動點擊更新按鈕
