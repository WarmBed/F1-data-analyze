# -*- coding: utf-8 -*-
"""
LapAnalysisLauncher - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox, QDialog
from core.gui_i18n import tr
from core.logger import get_logger
from windows.dialogs.lap_analysis_options_dialog import LapAnalysisOptionsDialog

logger = get_logger(__name__)


class LapAnalysisLauncher:
    """從 f1t_gui_main.py 提取的 lap_analysis 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def lap_analysis(self): 
        """圈速分析 - 彈出選項對話框讓使用者選擇要顯示的遙測圖表和車手"""
        params = self.main_window.get_current_parameters()
        logger.debug(f"[分析] 圈速分析 - {params['year']} {params['race']} {params['session']}")
        
        try:
            # 移除歡迎頁面（如果存在）
            self.main_window.remove_welcome_tab()
            
            # 彈出選項對話框
            dialog = LapAnalysisOptionsDialog(self.main_window)
            
            if dialog.exec_() == QDialog.Accepted:
                selected_charts = dialog.get_selected_charts()
                driver_info = dialog.get_selected_drivers()
                
                driver1 = driver_info['driver1']
                driver2 = driver_info['driver2']
                lap1_number = driver_info['lap1_number']
                lap2_number = driver_info['lap2_number']
                lap_type = driver_info['lap_type']
                is_fastest_lap = driver_info['is_fastest_lap']
                
                if not selected_charts:
                    QMessageBox.information(self.main_window, tr('info', 'Information'), tr('no_chart_selected', 'No chart selected. Window will not be opened.'))
                    return
                
                if not driver1:
                    QMessageBox.information(self.main_window, tr('info', 'Information'), tr('select_driver', 'Please select at least one driver.'))
                    return
                
                none_display = tr("none_option", "None")
                lap_word = tr("lap", "Lap")
                fastest_label = tr("fastest_lap_type", "Fastest Lap")

                logger.debug(f"[圈速分析] 使用者選擇的圖表: {selected_charts}")
                logger.debug(f"[圈速分析] 選擇的車手: 車手1={driver1}, 車手2={driver2 if driver2 else none_display}")
                if is_fastest_lap:
                    logger.debug(f"[圈速分析] 圈數設定: {fastest_label}")
                else:
                    if driver2:
                        logger.debug(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}, 車手2第{lap2_number}{lap_word}")
                    else:
                        logger.debug(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}")
                
                # 🆕 將對話框的選擇同步到主視窗參數欄
                try:
                    # 同步 Driver 1
                    if driver1 and hasattr(self, 'driver1_combo'):
                        index = self.main_window.driver1_combo.findText(driver1)
                        if index >= 0:
                            self.main_window.driver1_combo.setCurrentIndex(index)
                            logger.debug(f"[同步] Driver 1 → {driver1}")
                    
                    # 同步 Driver 2
                    if hasattr(self, 'driver2_combo'):
                        if driver2:
                            index = self.main_window.driver2_combo.findText(driver2)
                            if index >= 0:
                                self.main_window.driver2_combo.setCurrentIndex(index)
                                logger.debug(f"[同步] Driver 2 → {driver2}")
                        else:
                            # Driver 2 為 None，設定為第一個選項（通常是空或 None）
                            self.main_window.driver2_combo.setCurrentIndex(0)
                            logger.debug(f"[同步] Driver 2 → None")
                    
                    # 同步 Lap 1
                    if lap1_number and hasattr(self, 'lap1_spinbox'):
                        self.main_window.lap1_spinbox.setValue(lap1_number)
                        logger.debug(f"[同步] Lap 1 → {lap1_number}")
                    
                    # 同步 Lap 2
                    if lap2_number and hasattr(self, 'lap2_spinbox'):
                        self.main_window.lap2_spinbox.setValue(lap2_number)
                        logger.debug(f"[同步] Lap 2 → {lap2_number}")
                    
                    # 同步 Fastest Lap 選項
                    if hasattr(self, 'fastest_lap_checkbox'):
                        self.main_window.fastest_lap_checkbox.setChecked(is_fastest_lap)
                        logger.debug(f"[同步] Fastest Lap → {is_fastest_lap}")
                    
                    logger.debug(f"[同步] ✅ 主視窗參數已同步")
                except Exception as sync_error:
                    logger.debug(f"[同步] ⚠️ 參數同步失敗: {sync_error}")
                
                # 為每個選擇的圖表類型創建視窗
                for chart_type in selected_charts:
                    # 特殊處理：將速度圖表映射到速度分析
                    if chart_type == 'speed':
                        chart_type = 'speed_analysis'
                        logger.debug(f"[圈速分析] 映射 'speed' -> 'speed_analysis'")
                    
                    self.main_window.create_telemetry_window(chart_type, params, driver1, driver2, lap1_number, lap2_number, lap_type, is_fastest_lap)
                
                driver_summary = f"車手: {driver1}" + (f" vs {driver2}" if driver2 else "")
                if is_fastest_lap:
                    lap_summary = fastest_label
                else:
                    if driver2:
                        lap_summary = f"車手1第{lap1_number}{lap_word}, 車手2第{lap2_number}{lap_word}"
                    else:
                        lap_summary = f"第{lap1_number}{lap_word}"
                logger.debug(f"[OK] 圈速分析完成，已開啟 {len(selected_charts)} 個遙測圖表視窗 ({driver_summary}, {lap_summary})")
            else:
                logger.debug(f"[圈速分析] 使用者取消了分析")
                
        except Exception as e:
            logger.error(f"[ERROR] 圈速分析失敗: {e}")
            import traceback
            traceback.print_exc()
            self.main_window.show_error_message("圈速分析錯誤", f"開啟圈速分析時發生錯誤: {e}")
