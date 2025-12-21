# -*- coding: utf-8 -*-
"""
TelemetryAnalysisOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMdiSubWindow, QDialog, QMessageBox
from core.logger import get_logger
from core.gui_i18n import tr
from windows.workers.cli_workers import MainWindowParameterProvider
from windows.dialogs.lap_analysis_options_dialog import LapAnalysisOptionsDialog

logger = get_logger(__name__)


class TelemetryAnalysisOpener:
    """從 f1t_gui_main.py 提取的 open_telemetry_analysis 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def open_telemetry_analysis(self):
        """開啟單場賽事總攬模組 - 🔧 修復：加入車手選擇對話框"""
        try:
            # 移除歡迎頁面（如果存在）
            self.main_window.remove_welcome_tab()
            
            params = self.main_window.get_current_parameters()
            logger.debug(f"[分析] [TELEMETRY] 單場賽事總攬 - {params['year']} {params['race']} {params['session']}")
            
            # 🔧 修復：彈出車手選擇對話框
            dialog = LapAnalysisOptionsDialog(self.main_window)
            dialog.setWindowTitle(tr("lap_analysis_options", "Telemetry Analysis - Select Drivers"))
            
            if dialog.exec_() != QDialog.Accepted:
                logger.debug(f"[TELEMETRY] 使用者取消了車手選擇")
                return
            
            # 獲取用戶選擇的車手和圈數
            driver_info = dialog.get_selected_drivers()
            driver1 = driver_info['driver1']
            driver2 = driver_info['driver2']
            lap1_number = driver_info['lap1_number']
            lap2_number = driver_info['lap2_number']
            lap_type = driver_info['lap_type']
            is_fastest_lap = driver_info['is_fastest_lap']
            
            # 至少需要選擇一個車手
            if not driver1:
                QMessageBox.information(
                    self.main_window, 
                    tr('info', 'Information'), 
                    tr('select_driver', 'Please select at least one driver.')
                )
                return
            
            logger.debug(f"[TELEMETRY] 選擇的車手: Driver1={driver1}, Driver2={driver2}")
            logger.debug(f"[TELEMETRY] 圈數: Lap1={lap1_number}, Lap2={lap2_number}, Fastest={is_fastest_lap}")
            
            # 導入單場賽事總攬模組
            from modules.gui.telemetry_analysis_mdi import TelemetryAnalysisModule
            
            # 創建模組實例
            telemetry_module = TelemetryAnalysisModule()
            
            # 設置參數提供者
            parameter_provider = MainWindowParameterProvider(self.main_window)
            telemetry_module.parameter_provider = parameter_provider
            
            # 設置當前參數
            telemetry_module.current_year = str(params['year'])
            telemetry_module.current_race = params['race']
            telemetry_module.current_session = params['session']
            
            # 🔧 修復：設置車手和圈數參數
            telemetry_module.driver1 = driver1
            telemetry_module.driver2 = driver2
            telemetry_module.lap1 = lap1_number
            telemetry_module.lap2 = lap2_number
            telemetry_module.is_fastest_lap = is_fastest_lap
            logger.debug(f"[TELEMETRY] 已設置模組車手參數: {driver1} vs {driver2}, Lap {lap1_number} vs {lap2_number}")
            
            # 初始化模組
            if telemetry_module.initialize_module():
                logger.debug(f"[OK] 單場賽事總攬模組初始化成功")
                
                # 創建子視窗
                subwindow = QMdiSubWindow()
                subwindow.setWidget(telemetry_module.get_widget())
                
                # 設置視窗標題
                window_title = telemetry_module.get_window_title(params['year'], params['race'], params['session'])
                subwindow.setWindowTitle(window_title)
                
                # 設置視窗大小
                default_size = telemetry_module.get_default_size()
                subwindow.resize(default_size[0], default_size[1])
                
                # 添加到MDI區域 - 獲取當前活動的 MDI 區域
                current_mdi = self.main_window.get_current_mdi_area()
                if current_mdi:
                    current_mdi.addSubWindow(subwindow)
                    subwindow.show()
                    
                    # 觸發參數更新以載入數據
                    telemetry_module.update_parameters(params['year'], params['race'], params['session'])
                    
                    logger.debug(f"[OK] 單場賽事總攬視窗已開啟: {window_title}")
                else:
                    logger.error("[ERROR] 無法獲取當前 MDI 區域")
                    self.main_window.show_error_message("錯誤", "無法獲取當前 MDI 區域")
                    return
                
            else:
                logger.error(f"[ERROR] 單場賽事總攬模組初始化失敗")
                self.main_window.show_error_message("模組錯誤", "單場賽事總攬模組初始化失敗")
            
        except ImportError as e:
            logger.error(f"[ERROR] 單場賽事總攬模組導入失敗: {e}")
            self.main_window.show_error_message("模組錯誤", f"無法載入單場賽事總覽模組: {e}")
        except Exception as e:
            logger.error(f"[ERROR] 單場賽事總覽開啟失敗: {e}")
            import traceback
            traceback.print_exc()
            self.main_window.show_error_message("單場賽事總覽錯誤", f"開啟單場賽事總覽時發生錯誤: {e}")
