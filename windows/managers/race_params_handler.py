# -*- coding: utf-8 -*-
"""
RaceParamsHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class RaceParamsHandler:
    """從 f1t_gui_main.py 提取的 on_race_parameters_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_race_parameters_changed(self):
        """
        賽事參數變更處理器（年份、賽事、賽段）- 自動更新所有視窗
        
        功能：
        - 檢測 Year/Race/Session 組合參數的變更
        - 篩選需要更新的遙測分析視窗
        - **自動更新**所有視窗（不再詢問用戶）
        - 使用 update_all_lap_analysis() 執行批次更新
        
        觸發時機：
        - Year ComboBox 改變時
        - Race ComboBox 改變時
        - Session ComboBox 改變時
        
        變更歷史：
        - v0.4.0: 移除確認對話框，改為自動更新（提升用戶體驗）
        """
        from PyQt5.QtWidgets import QMessageBox
        from core.gui_i18n import tr
        
        # 獲取當前參數值
        current_year = self.main_window.year_combo.currentText()
        current_race = self.main_window.race_combo.currentText()
        current_session = self.main_window.session_combo.currentText()
        
        logger.info("[RACE_CONTROL] 賽事參數已變更:")
        logger.info("[RACE_CONTROL]   年份: '%s'", current_year)
        logger.info("[RACE_CONTROL]   賽事: '%s'", current_race)
        logger.info("[RACE_CONTROL]   賽段: '%s'", current_session)
        
        # 檢查是否有需要更新的分析視窗
        analysis_windows = self.main_window._get_telemetry_analysis_windows()
        
        if len(analysis_windows) == 0:
            logger.info("[RACE_CONTROL] 沒有活動的分析視窗，無需更新")
            return
        
        logger.info("[RACE_CONTROL] 發現 %d 個需要更新的分析視窗", len(analysis_windows))
        
        # ✅ 自動更新所有視窗（不再詢問用戶）
        # 顯示狀態列通知
        try:
            self.main_window.statusBar().showMessage(
                tr("auto_updating_windows", "正在自動更新 {count} 個分析視窗...").format(count=len(analysis_windows)),
                2000  # 2 秒
            )
        except Exception:
            pass
        
        logger.info("[RACE_CONTROL] 開始自動更新所有視窗...")
        self.main_window.update_all_lap_analysis()
