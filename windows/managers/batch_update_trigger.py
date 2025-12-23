# -*- coding: utf-8 -*-
"""
BatchUpdateTrigger - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class BatchUpdateTrigger:
    """從 f1t_gui_main.py 提取的 _check_and_trigger_batch_update 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _check_and_trigger_batch_update(self):
        """
        檢查並觸發批次更新
        
        當 year/race/session 參數變更時調用，
        檢測是否有活動的分析視窗需要更新，如果有則詢問用戶是否批次更新
        """
        # ✅ 調試點 1: 方法入口
        logger.info("🔵 [DEBUG]    ========== _check_and_trigger_batch_update 開始 ==========")
        logger.debug("🔵 [DEBUG]    ========== _check_and_trigger_batch_update 開始 ==========")
        
        from PyQt5.QtWidgets import QMessageBox
        
        # ✅ 調試點 2: 檢查視窗前
        logger.info("🔵 [DEBUG]    準備調用 _get_telemetry_analysis_windows()")
        logger.debug("🔵 [DEBUG]    準備調用 _get_telemetry_analysis_windows()")
        
        # 檢查是否有需要更新的視窗
        try:
            analysis_windows = self.main_window._get_telemetry_analysis_windows()
            logger.info(f"🔵 [DEBUG]    _get_telemetry_analysis_windows() 返回: {len(analysis_windows)} 個視窗")
            logger.debug(f"🔵 [DEBUG]    _get_telemetry_analysis_windows() 返回: {len(analysis_windows)} 個視窗")
            
            # ✅ 調試點 3: 顯示視窗詳情
            if analysis_windows:
                for i, win in enumerate(analysis_windows, 1):
                    win_type = getattr(win, 'analysis_type', 'unknown')
                    win_title = getattr(win, 'windowTitle', lambda: 'unknown')()
                    logger.info(f"🔵 [DEBUG]      視窗 {i}: type={win_type}, title={win_title}")
                    logger.debug(f"🔵 [DEBUG]      視窗 {i}: type={win_type}, title={win_title}")
        except Exception as e:
            # 🔴 關鍵修復：移除 exc_info=True 避免 logging 持有 frame chain
            logger.error(f"🔴 [ERROR] 獲取分析視窗失敗: {e}")
            logger.error(f"🔴 [ERROR] 獲取分析視窗失敗: {e}")
            e = None  # 🔴 立即釋放異常對象
            return
        
        if not analysis_windows:
            logger.info("🔵 [DEBUG]    無活動分析視窗，跳過批次更新")
            logger.debug("[RACE_CONTROL] 📭 無活動分析視窗，跳過批次更新")
            return
        
        # 獲取當前參數
        current_year = self.main_window.year_combo.currentText()
        current_race = self.main_window.get_selected_race_key()
        current_session = self.main_window.get_selected_session_code()
        
        logger.info(f"🔵 [DEBUG]    當前參數: year={current_year}, race={current_race}, session={current_session}")
        logger.debug(f"🔵 [DEBUG]    當前參數: year={current_year}, race={current_race}, session={current_session}")
        logger.debug(f"[RACE_CONTROL] 🔍 發現 {len(analysis_windows)} 個需要更新的分析視窗")
        logger.info(f"[RACE_CONTROL] 發現 {len(analysis_windows)} 個需要更新的分析視窗")
        
        # ✅ 調試點 4: 準備顯示對話框
        logger.info("🔵 [DEBUG]    準備顯示確認對話框")
        logger.debug("🔵 [DEBUG]    準備顯示確認對話框")
        
        # 詢問用戶是否更新所有視窗
        reply = QMessageBox.question(
            self,
            tr("update", "更新確認"),
            tr("update_race_params_confirm", 
               "檢測到賽事參數變更：\n年份: {year}\n賽事: {race}\n賽段: {session}\n\n"
               "共有 {count} 個分析視窗需要更新。\n是否立即更新所有視窗？").format(
                   year=current_year, 
                   race=current_race, 
                   session=current_session, 
                   count=len(analysis_windows)
               ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 預設為 No，避免誤觸
        )
        
        # ✅ 調試點 5: 對話框結果
        logger.info(f"🔵 [DEBUG]    對話框返回: reply={reply} (Yes={QMessageBox.Yes}, No={QMessageBox.No})")
        logger.debug(f"🔵 [DEBUG]    對話框返回: reply={reply} (Yes={QMessageBox.Yes}, No={QMessageBox.No})")
        
        if reply == QMessageBox.Yes:
            logger.info("🔵 [DEBUG]    用戶點擊「是」，準備調用 update_all_lap_analysis()")
            logger.debug("[RACE_CONTROL] ✅ 用戶確認更新，開始批次更新所有視窗...")
            
            # ✅ 調試點 6: 調用批次更新前
            logger.info("🔵 [DEBUG]    調用 update_all_lap_analysis()")
            logger.debug("🔵 [DEBUG]    調用 update_all_lap_analysis()")
            
            self.main_window.update_all_lap_analysis()
            
            # ✅ 調試點 7: 批次更新完成
            logger.info("🔵 [DEBUG]    update_all_lap_analysis() 已完成")
            logger.debug("🔵 [DEBUG]    update_all_lap_analysis() 已完成")
        else:
            logger.info("🔵 [DEBUG]    用戶點擊「否」，取消更新")
            logger.debug("[RACE_CONTROL] ❌ 用戶取消更新")
        
        logger.info("🔵 [DEBUG]    ========== _check_and_trigger_batch_update 結束 ==========")
        logger.debug("🔵 [DEBUG]    ========== _check_and_trigger_batch_update 結束 ==========")
