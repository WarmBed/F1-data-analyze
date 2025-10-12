#!/usr/bin/env python3
"""
F1T 油門分析 MDI 模組
基於進站分析模組的成功架構設計
支援雙車手油門對比的 GUI 模組，使用新版模組更新機制
"""

import sys
import os
import json
import datetime
import traceback
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QStatusBar, QToolBar, QAction,
    QHeaderView, QDialog, QDialogButtonBox, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QTextEdit, QMessageBox, QFrame, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 導入國際化模組
from core.gui_i18n import tr

# 導入分析模組介面
from modules.gui.interfaces.analysis_module import IAnalysisModule

class ThrottleDataManager(QObject):
    """油門數據管理器 - 負責JSON緩存和CLI備援"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    loading_progress = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = None
        self.current_race = None
        self.current_session = None
        self.loading = False
        self._is_loading = False
        
    def load_throttle_data(self, year: str, race: str, session: str, 
                       driver1: str = "VER", driver2: str = "VER",
                       lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:
        """載入油門對比數據"""
        try:
            print(f"[THROTTLE_MDI_DATA] ========== 載入油門數據 ==========")
            print(f"[THROTTLE_MDI_DATA] 參數: {year} {race} {session}")
            print(f"[THROTTLE_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            if self._is_loading:
                print(f"[THROTTLE_MDI_DATA] ⚠️ 數據載入中，忽略新請求")
                self.error_occurred.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.loading_progress.emit(0)
            self.status_changed.emit("開始載入油門數據...")

            # 儲存最新賽事上下文，以支援遙測檢查
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # 檢查最速圈選項並自動載入遙測分析
            if is_fastest or lap1 == "fastest" or lap2 == "fastest":
                print(f"🔄 [THROTTLE_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")
                self._check_and_load_telemetry_if_needed()
                
                # 解析最速圈參數為實際圈數
                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)
                print(f"🔢 [THROTTLE_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")
            
            print(f"[THROTTLE_MDI_DATA] 🔗 創建 ThrottleAnalysisDataLoader...")
            
            # 使用現有的油門分析數據載入器
            from .throttle_analysis_data_loader import ThrottleAnalysisDataLoader
            
            print(f"[THROTTLE_MDI_DATA] 🚀 調用 load_throttle_data...")
            
            # 創建數據載入器
            throttle_loader = ThrottleAnalysisDataLoader()
            throttle_loader.data_loaded.connect(self._on_data_loaded)
            throttle_loader.load_error.connect(self._on_load_error)
            throttle_loader.status_changed.connect(self.status_changed.emit)
            throttle_loader.load_progress.connect(self.loading_progress.emit)
            
            # 開始載入數據
            success = throttle_loader.load_throttle_data(
                year=int(year),
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest_lap=is_fastest  # 修正：使用傳入的is_fastest參數
            )
            
            # 保存載入器引用避免被回收
            self._throttle_loader = throttle_loader
            
            # 將loader設置給chart widget以供直接更新
            if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
                self.throttle_chart_widget.throttle_loader = throttle_loader
                print(f"[THROTTLE_MDI] ✅ 已將loader設置給chart widget")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 油門數據載入失敗: {e}")
            self.error_occurred.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False

    def _check_and_load_telemetry_if_needed(self):
        """檢查本地遙測分析數據（API-ONLY 模式：不自動創建視窗）"""
        try:
            print(f"� [THROTTLE_MDI] [API-ONLY] 檢查本地遙測分析數據...")
            
            # API-ONLY 模式：僅檢查本地數據，不自動創建視窗
            print(f"💡 [THROTTLE_MDI] 提示：如需遙測分析，請手動開啟遙測分析模組")
            print(f"💡 [THROTTLE_MDI] 或使用 API 獲取遙測數據")
            return False
                
        except Exception as e:
            print(f"❌ [THROTTLE_MDI] 檢查遙測數據時發生錯誤: {e}")
            return False

    def _get_fastest_lap_number(self, driver: str) -> int:
        """從遙測分析數據獲取指定車手的最速圈數"""
        try:
            print(f"🔍 [THROTTLE_MDI] 開始搜尋 {driver} 的最速圈數據...")
            
            # 搜尋遙測分析JSON檔案
            telemetry_patterns = [
                f"all_drivers_telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"all_drivers_telemetry_analysis_{self.current_year}_{self.current_race}.json"
            ]
            
            search_dirs = ["json", "json_exports", "cache"]
            telemetry_file = None
            
            for directory in search_dirs:
                if os.path.exists(directory):
                    for pattern in telemetry_patterns:
                        file_path = os.path.join(directory, pattern)
                        if os.path.exists(file_path):
                            telemetry_file = file_path
                            print(f"📁 [THROTTLE_MDI] 找到遙測檔案: {telemetry_file}")
                            break
                    if telemetry_file:
                        break
            
            if not telemetry_file:
                print(f"❌ [THROTTLE_MDI] 找不到遙測分析檔案，使用預設圈數 1")
                return 1
                
            # 讀取並解析遙測分析數據
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            print(f"📊 [THROTTLE_MDI] 遙測檔案讀取成功，開始解析最速圈數據...")
            
            # 嘗試多種數據結構格式
            fastest_lap_num = None
            
            # 格式1: data.all_drivers_telemetry[driver].fastest_lap
            if 'data' in telemetry_data and 'all_drivers_telemetry' in telemetry_data['data']:
                driver_data = telemetry_data['data']['all_drivers_telemetry'].get(driver)
                if driver_data and 'fastest_lap' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap'].get('lap_number')
                    if fastest_lap_num:
                        print(f"✅ [THROTTLE_MDI] 從格式1找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                        return int(fastest_lap_num)
            
            # 格式2: data.fastest_laps中的列表
            if 'data' in telemetry_data and 'fastest_laps' in telemetry_data['data']:
                for fastest_data in telemetry_data['data']['fastest_laps']:
                    if fastest_data.get('driver') == driver:
                        fastest_lap_num = fastest_data.get('lap_number')
                        if fastest_lap_num:
                            print(f"✅ [THROTTLE_MDI] 從格式2找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                            return int(fastest_lap_num)
            
            # 格式3: 直接在data下按車手分組
            if 'data' in telemetry_data:
                driver_data = telemetry_data['data'].get(driver)
                if driver_data and 'fastest_lap_number' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap_number']
                    print(f"✅ [THROTTLE_MDI] 從格式3找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                    return int(fastest_lap_num)
            
            print(f"⚠️ [THROTTLE_MDI] 無法找到 {driver} 的最速圈數據，使用預設圈數 1")
            return 1
            
        except Exception as e:
            print(f"❌ [THROTTLE_MDI] 解析最速圈數據時發生錯誤: {e}")
            return 1

    def _resolve_lap_numbers(self, lap1, lap2, driver1, driver2, is_fastest):
        """解析圈數參數，將'fastest'轉換為實際圈數"""
        try:
            resolved_lap1 = lap1
            resolved_lap2 = lap2
            
            # 處理lap1
            if lap1 == "fastest" or is_fastest:
                print(f"🔄 [THROTTLE_MDI] 解析 {driver1} 的最速圈...")
                resolved_lap1 = self._get_fastest_lap_number(driver1)
                
            # 處理lap2
            if lap2 == "fastest" or is_fastest:
                print(f"🔄 [THROTTLE_MDI] 解析 {driver2} 的最速圈...")
                resolved_lap2 = self._get_fastest_lap_number(driver2)
            
            print(f"📊 [THROTTLE_MDI] 圈數解析結果: {driver1}=第{resolved_lap1}圈, {driver2}=第{resolved_lap2}圈")
            
            return int(resolved_lap1), int(resolved_lap2)
            
        except Exception as e:
            print(f"❌ [THROTTLE_MDI] 解析圈數時發生錯誤: {e}")
            return 1, 1
    
    def _on_data_loaded(self, data: dict):
        """處理數據載入完成"""
        try:
            print(f"[THROTTLE_MDI] 數據載入完成")
            self._is_loading = False
            self.data_loaded.emit(data)
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 數據處理失敗: {e}")
            self.error_occurred.emit(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_message: str):
        """處理載入錯誤"""
        print(f"[ERROR] [THROTTLE_MDI] 載入錯誤: {error_message}")
        self._is_loading = False
        self.error_occurred.emit(error_message)

class ThrottleAnalysisModule(IAnalysisModule):
    """油門分析主模組"""
    
    # 信號定義
    module_error = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 設置分析類型（用於批次更新識別）
        self.analysis_type = 'throttle'
        
        # 參數狀態
        self.current_year = "2025"
        self.current_race = "Japan"
        self.current_session = "R"
        self.parameter_provider = None
        
        # 車手和圈數參數
        self.driver1 = "VER"
        self.driver2 = "VER" 
        self.lap1 = 1
        self.lap2 = 1
        
        # 組件
        self.data_manager = None
        self.throttle_chart_widget = None
        self.main_widget = None  # 主容器 widget
        self.parent_window = None  # MDI 子視窗引用
        
        # 初始化狀態
        self._initialized = False
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 實現抽象方法"""
        try:
            print(f"[THROTTLE_MDI] 初始化油門分析模組")
            
            # 創建數據管理器
            self.data_manager = ThrottleDataManager()
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            
            # 創建油門圖表組件
            from .throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
            self.throttle_chart_widget = ThrottleAnalysisChartWidget()
            
            # 連接圈數變更信號
            self.throttle_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
            
            # 設置初始圈數
            self.throttle_chart_widget.set_lap_numbers(self.lap1, self.lap2)
            
            # 設置主界面
            self._setup_ui()
            
            # 註冊到分析模組管理器
            try:
                from ..analysis_module_manager import get_analysis_module_manager
                manager = get_analysis_module_manager()
                
                # 註冊模組
                module_id = f"throttle_analysis_{id(self)}"
                manager.register_module(module_id, self, "throttle_analysis")
                
                # 註冊圖表組件
                if self.throttle_chart_widget:
                    manager.register_chart_widget(self.throttle_chart_widget)
                
                # 保存管理器引用和模組ID
                self._analysis_manager = manager
                self._module_id = module_id
                
                print(f"[THROTTLE_MDI] ✅ 已註冊到分析模組管理器: {module_id}")
                
            except ImportError as e:
                print(f"[WARNING] [THROTTLE_MDI] 無法導入分析模組管理器: {e}")
                self._analysis_manager = None
                self._module_id = None
            except Exception as e:
                print(f"[ERROR] [THROTTLE_MDI] 註冊到分析模組管理器失敗: {e}")
                self._analysis_manager = None
                self._module_id = None
            
            self._initialized = True
            print(f"[OK] [THROTTLE_MDI] 油門分析模組初始化完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用（MDI 子視窗）"""
        self.parent_window = parent_window
        
        if parent_window:
            # 立即設置正確的標題
            self.update_window_title()
    
    def _setup_ui(self):
        """設置用戶界面"""
        # 創建主容器 widget
        self.main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加油門圖表
        if self.throttle_chart_widget:
            layout.addWidget(self.throttle_chart_widget)
        
        # 設置佈局到主 widget
        self.main_widget.setLayout(layout)
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            print(f"[THROTTLE_MDI] 更新油門圖表")
            if self.throttle_chart_widget:
                self.throttle_chart_widget.update_throttle_data(data)
                
                # 更新工具欄狀態信息
                self._update_toolbar_status(data)
                
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 圖表更新失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def _update_toolbar_status(self, data: dict):
        """更新工具欄狀態信息"""
        try:
            # 獲取主視窗引用
            main_window = self._get_main_window()
            if not main_window or not hasattr(main_window, 'update_toolbar_status'):
                return
            
            # 提取狀態信息
            metadata = data.get('metadata', {})
            drivers = metadata.get('drivers', [])
            
            module_name = "油門分析"
            lap_time = ""
            tyre_compound = ""
            lap_numbers = ""
            
            if drivers:
                if len(drivers) >= 2:
                    # 雙車手模式
                    driver1 = drivers[0]
                    driver2 = drivers[1]
                    
                    lap_time1 = driver1.get('lap_time', 'N/A')
                    lap_time2 = driver2.get('lap_time', 'N/A')
                    lap_time = f"{lap_time1} | {lap_time2}"
                    
                    compound1 = driver1.get('compound', 'N/A')
                    compound2 = driver2.get('compound', 'N/A')
                    tyre_compound = f"{compound1} | {compound2}"
                    
                    driver1_code = driver1.get('code', self.driver1)
                    driver2_code = driver2.get('code', self.driver2)
                    lap_numbers = f"{driver1_code} 第{self.lap1}圈 vs {driver2_code} 第{self.lap2}圈"
                    
                elif len(drivers) >= 1:
                    # 單車手模式
                    driver1 = drivers[0]
                    lap_time = driver1.get('lap_time', 'N/A')
                    tyre_compound = driver1.get('compound', 'N/A')
                    
                    driver1_code = driver1.get('code', self.driver1)
                    lap_numbers = f"{driver1_code} 第{self.lap1}圈"
            else:
                # 無車手數據時顯示基本信息
                lap_numbers = f"第{self.lap1}圈 vs 第{self.lap2}圈"
            
            # 更新工具欄狀態
            main_window.update_toolbar_status(
                module_name=module_name,
                lap_time=lap_time,
                tyre_compound=tyre_compound,
                lap_numbers=lap_numbers
            )
            
            print(f"[THROTTLE_MDI] 已更新工具欄狀態: {module_name}")
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 更新工具欄狀態失敗: {e}")
    
    def _get_main_window(self):
        """獲取主視窗引用"""
        try:
            # 通過MDI子視窗獲取主視窗
            if self.parent_window:
                mdi_area = self.parent_window.parent()
                if mdi_area:
                    # 查找主視窗
                    widget = mdi_area
                    while widget and not hasattr(widget, 'update_toolbar_status'):
                        widget = widget.parent()
                    return widget
            return None
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 獲取主視窗失敗: {e}")
            return None
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] [THROTTLE_MDI] {error_message}")
        self.module_error.emit(error_message)
    
    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更"""
        try:
            print(f"[THROTTLE_MDI] ========== 圈數變更處理 ==========")
            print(f"[THROTTLE_MDI] 新圈數: 第{lap1}圈 vs 第{lap2}圈")
            
            # 更新模組的圈數參數
            old_lap1, old_lap2 = self.lap1, self.lap2
            self.lap1 = lap1
            self.lap2 = lap2
            
            print(f"[THROTTLE_MDI] 圈數變更: 第{old_lap1}圈 vs 第{old_lap2}圈 → 第{lap1}圈 vs 第{lap2}圈")
            
            # 重新載入數據
            if self.data_manager:
                print(f"[THROTTLE_MDI] 🔄 因圈數變更重新載入數據...")
                success = self.data_manager.load_throttle_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                
                if success:
                    print(f"[THROTTLE_MDI] ✅ 圈數變更後數據重載成功")
                else:
                    print(f"[THROTTLE_MDI] ❌ 圈數變更後數據重載失敗")
            else:
                print(f"[THROTTLE_MDI] ❌ 數據管理器未初始化，無法重載數據")
                
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 處理圈數變更失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"處理圈數變更失敗: {str(e)}")
    
    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """更新參數 - 實現抽象方法"""
        try:
            # 準備更新的參數
            new_year = str(year) if year is not None else self.current_year
            new_race = race if race is not None else self.current_race
            new_session = session if session is not None else self.current_session
            
            # 檢查參數是否有變化（基於當前的模組參數）
            params_changed = (
                self.current_year != new_year or 
                self.current_race != new_race or 
                self.current_session != new_session
            )
            
            # 更新本地參數（如果調用者沒有提前更新的話）
            self.current_year = new_year
            self.current_race = new_race
            self.current_session = new_session
            
            # 確保視窗標題是最新的
            self.update_window_title()
            
            if params_changed:
                # 載入新數據
                if self.data_manager:
                    success = self.data_manager.load_throttle_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        # 數據載入成功後再次確保標題正確
                        self.update_window_title()
                        self.parameters_updated.emit({
                            'year': int(new_year),
                            'race': new_race,
                            'session': new_session
                        })
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                # 如果是首次載入或沒有數據，仍然需要載入
                if self.data_manager and not hasattr(self, '_data_loaded'):
                    success = self.data_manager.load_throttle_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    if success:
                        self._data_loaded = True
                        return True
                    else:
                        return False
                else:
                    return True
                
        except Exception as e:
            print(f"[ERROR] [SPEED_PARAMS_DEBUG] 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
            traceback.print_exc()
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False,
                            use_time_axis: bool = False) -> bool:
        """更新圈速油門油門分析參數（包含車手和圈數）"""
        try:
            print(f"[THROTTLE_MDI] ========== 圈速油門油門參數更新 ==========")
            print(f"[THROTTLE_MDI] 收到參數: {year} {race} {session}")
            print(f"[THROTTLE_MDI] 車手: {driver1} vs {driver2}")
            print(f"[THROTTLE_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
            print(f"[THROTTLE_MDI] 最速圈: {is_fastest}")
            print(f"[THROTTLE_MDI] 🕒 時間軸模式: {use_time_axis}")
            
            # 檢查是否需要最速圈數據
            if is_fastest:
                print(f"[THROTTLE_MDI] 🏁 用戶選擇了最速圈選項，檢查遙測分析數據...")
                fastest_laps = self._ensure_telemetry_data_for_fastest_laps()
                if fastest_laps:
                    # 使用最速圈數據更新圈數
                    if driver1 in fastest_laps:
                        lap1 = fastest_laps[driver1]
                        print(f"[THROTTLE_MDI] 🏁 車手 {driver1} 最速圈: 第{lap1}圈")
                    if driver2 and driver2 in fastest_laps:
                        lap2 = fastest_laps[driver2]
                        print(f"[THROTTLE_MDI] 🏁 車手 {driver2} 最速圈: 第{lap2}圈")
                else:
                    print(f"[THROTTLE_MDI] ⚠️ 無法獲取最速圈數據，使用預設圈數")
            
            # 檢查參數是否有變化
            params_changed = (
                self.current_year != str(year) or 
                self.current_race != race or 
                self.current_session != session or
                self.driver1 != driver1 or
                self.driver2 != driver2 or  # 正確處理 None 值比較
                self.lap1 != lap1 or
                self.lap2 != lap2
            )
            
            print(f"[THROTTLE_MDI] 參數是否變化: {params_changed}")
            
            # 更新所有參數 - 保持 driver2 的原始值（包括 None）
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.driver1 = driver1
            self.driver2 = driver2  # 保持原始值，支援單場賽事車手分析
            self.lap1 = lap1
            self.lap2 = lap2
            self.lap1 = lap1
            self.lap2 = lap2
            
            # 更新圖表組件的圈數顯示
            if self.throttle_chart_widget:
                self.throttle_chart_widget.set_lap_numbers(lap1, lap2)
                print(f"[THROTTLE_MDI] ✅ 已更新圖表組件的圈數顯示")
                
                # 🆕 設置時間軸模式
                self.throttle_chart_widget.set_time_axis_mode(use_time_axis)
                print(f"[THROTTLE_MDI] ✅ 已設置時間軸模式: {use_time_axis}")
            
            if params_changed:
                print(f"[THROTTLE_MDI] 🔄 參數已變化，開始重載數據...")
                
                # 載入新數據
                if self.data_manager:
                    print(f"[THROTTLE_MDI] 📡 調用數據管理器載入新數據...")
                    success = self.data_manager.load_throttle_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        print(f"[THROTTLE_MDI] ✅ 圈速油門油門參數更新後數據重載成功")
                        # 發送參數更新信號
                        self.parameters_updated.emit({
                            'year': self.current_year,
                            'race': self.current_race,
                            'session': self.current_session,
                            'driver1': self.driver1,
                            'driver2': self.driver2,
                            'lap1': self.lap1,
                            'lap2': self.lap2
                        })
                        
                        # 更新視窗標題以反映新的參數 - 使用統一的 get_window_title
                        parent = getattr(self, 'parent_window', None)
                        if parent and hasattr(parent, 'setWindowTitle'):
                            new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                            parent.setWindowTitle(new_title)
                            print(f"[THROTTLE_MDI] 🏷️ 視窗標題已更新為: {new_title}")
                        else:
                            print(f"[THROTTLE_MDI] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
                        
                        return True
                    else:
                        print(f"[THROTTLE_MDI] ❌ 圈速油門油門參數更新後數據重載失敗")
                        return False
                else:
                    print(f"[THROTTLE_MDI] ❌ 數據管理器未初始化")
                    return False
            else:
                print(f"[THROTTLE_MDI] ℹ️ 圈速油門油門參數未變化，保持現有數據")
                
                # 即使參數未變化，也確保視窗標題是正確的 - 使用統一的 get_window_title
                parent = getattr(self, 'parent_window', None)
                if parent and hasattr(parent, 'setWindowTitle'):
                    current_title = parent.windowTitle()
                    expected_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                    if current_title != expected_title:
                        parent.setWindowTitle(expected_title)
                        print(f"[THROTTLE_MDI] 🏷️ 同步視窗標題: {expected_title}")
                else:
                    print(f"[THROTTLE_MDI] ⚠️ 無法同步視窗標題 - 父視窗引用未設置")
                
                return True
                
        except Exception as e:
            print(f"[THROTTLE_MDI] ❌ 圈速油門油門參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"圈速油門油門參數更新失敗: {str(e)}")
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 統一格式，不包含車手資訊以保持模組兼容性"""
        # 如果提供了參數，使用傳入的參數；否則使用內部狀態
        use_year = year if year is not None else self.current_year
        use_race = race if race is not None else self.current_race
        use_session = session if session is not None else self.current_session
        
        # 使用統一的簡潔標題格式，與其他模組保持一致
        title = f"{tr('throttle_analysis', '油門分析')}_{use_year}_{use_race}_{use_session}"
        return title
    
    def update_window_title(self) -> None:
        """更新視窗標題"""
        try:
            # 檢查 parent_window 屬性（MDI 子視窗引用）
            parent = getattr(self, 'parent_window', None)
            
            if parent and hasattr(parent, 'setWindowTitle'):
                new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                parent.setWindowTitle(new_title)
                
                # 強制刷新視窗顯示
                parent.update()
                parent.repaint()
        except Exception as e:
            print(f"[ERROR] [SPEED_TITLE_DEBUG] 更新視窗標題失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _delayed_title_update(self, title: str) -> None:
        """延遲標題更新 - 採用進站分析模式"""
        try:
            # 使用 parent_window 屬性而不是 parent() 方法
            parent = getattr(self, 'parent_window', None)
            if parent and hasattr(parent, 'setWindowTitle'):
                print(f"[SPEED_TITLE_DEBUG] 🔄 延遲標題更新: '{title}'")
                parent.setWindowTitle(title)
                parent.update()
                parent.repaint()
                
                # 再次驗證
                actual_title = parent.windowTitle()
                success = (actual_title == title)
                print(f"[SPEED_TITLE_DEBUG] 延遲更新結果: {success}, 實際標題: '{actual_title}'")
                
                if not success:
                    print(f"[ERROR] [SPEED_TITLE_DEBUG] ❌ 延遲更新也失敗了！可能是視窗引用問題")
                    print(f"[SPEED_TITLE_DEBUG] 視窗類型: {type(parent)}")
                    print(f"[SPEED_TITLE_DEBUG] 視窗是否可見: {parent.isVisible()}")
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] 延遲標題更新失敗: {e}")
    
    # 實現 IAnalysisModule 抽象方法
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return "throttle_analysis"
    
    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return tr("throttle_analysis", "油門分析")
    
    @property
    def description(self) -> str:
        """模組描述"""
        return tr("throttle_analysis_description", "F1賽車油門分析模組，支援雙車手油門對比")
    
    @property
    def version(self) -> str:
        """模組版本"""
        return "1.0.0"
    
    def get_widget(self):
        """獲取主要組件"""
        if hasattr(self, 'main_widget'):
            return self.main_widget
        else:
            # 如果主 widget 還沒創建，返回圖表組件作為後備
            return self.throttle_chart_widget
    
    def get_default_size(self):
        """獲取預設尺寸"""
        return (900, 600)
    
    def get_title(self) -> str:
        """返回模組標題 - 實現拽象方法"""
        return f"{tr('throttle_analysis', '油門分析')} - {self.current_year} {self.current_race} {self.current_session}"
    
    def supports_sync(self) -> bool:
        """是否支援主程式同步 - 實現抽象方法"""
        return True
    
    def get_parameter_interface(self) -> Optional[QWidget]:
        """返回參數設定介面 - 實現抽象方法"""
        # 油門分析模組暫時不提供參數設定介面
        return None
    
    def reset_chart_view(self):
        """重置圖表視圖 - 與 Show All Data 按鈕整合"""
        print(f"[THROTTLE_MDI] 🔄 reset_chart_view() 被調用")
        if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
            print(f"[THROTTLE_MDI] ✅ 找到 throttle_chart_widget，調用 reset_chart_view()")
            self.throttle_chart_widget.reset_chart_view()
        else:
            print(f"[THROTTLE_MDI] ❌ 未找到 throttle_chart_widget 屬性")
    
    def cleanup(self):
        """清理資源 - 實現抽象方法"""
        try:
            # 從分析模組管理器解除註冊
            if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
                try:
                    # 解除註冊圖表組件
                    if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
                        self._analysis_manager.unregister_chart_widget(self.throttle_chart_widget)
                    
                    # 解除註冊模組
                    self._analysis_manager.unregister_module(self._module_id)
                    print(f"[THROTTLE_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                    
                except Exception as e:
                    print(f"[ERROR] [THROTTLE_MDI] 從分析模組管理器解除註冊失敗: {e}")
            
            if hasattr(self, 'data_manager') and self.data_manager:
                # 清理數據管理器
                if hasattr(self.data_manager, 'cleanup'):
                    self.data_manager.cleanup()
                    
            if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
                # 🔧 修復：從連動管理器中取消註冊圖表組件
                try:
                    from modules.gui.lap_analysis.linkage import linkage_manager
                    if linkage_manager:
                        linkage_manager.unregister_module(self.throttle_chart_widget)
                        print(f"[THROTTLE_MDI] ✅ 已從連動管理器解除註冊圖表組件")
                except Exception as e:
                    print(f"[ERROR] [THROTTLE_MDI] 從連動管理器解除註冊失敗: {e}")
                
                # 清理圖表組件
                if hasattr(self.throttle_chart_widget, 'cleanup'):
                    self.throttle_chart_widget.cleanup()
                self.throttle_chart_widget.deleteLater()
                
            if hasattr(self, 'main_widget') and self.main_widget:
                # 清理主要組件
                self.main_widget.deleteLater()
                
            print(f"[CLEANUP] 油門分析模組資源清理完成")
        except Exception as e:
            print(f"[ERROR] 油門分析模組清理失敗: {e}")
    
    def load_data(self, **kwargs) -> bool:
        """載入數據 - 實現抽象方法"""
        try:
            year = str(kwargs.get('year', self.current_year))
            race = kwargs.get('race', self.current_race)
            session = kwargs.get('session', self.current_session)
            
            return self.data_manager.load_throttle_data(
                year=year,
                race=race,
                session=session,
                driver1=kwargs.get('driver1', 'VER'),
                driver2=kwargs.get('driver2', 'VER'),
                lap1=kwargs.get('lap1', 1),
                lap2=kwargs.get('lap2', 1)
            )
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] load_data 失敗: {e}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str,
                            driver1: str, driver2: str = None,
                            lap1: int = 1, lap2: int = None,
                            is_fastest: bool = False,
                            use_time_axis: bool = False) -> bool:
        """更新圈速油門油門參數並重新載入數據 - 供統一更新介面使用"""
        try:
            print(f"[THROTTLE_MDI] 🔄 更新圈速油門油門參數...")
            print(f"[THROTTLE_MDI]   📊 基本參數: {year} {race} {session}")
            print(f"[THROTTLE_MDI]   🏎️ 車手參數: {driver1} vs {driver2}")
            print(f"[THROTTLE_MDI]   🏁 圈數參數: 第{lap1}圈 vs 第{lap2}圈")
            print(f"[THROTTLE_MDI]   ⚡ 最速圈: {is_fastest}")
            print(f"[THROTTLE_MDI]   🕒 時間軸模式: {use_time_axis}")
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.driver1 = driver1
            self.driver2 = driver2 if driver2 else driver1
            self.lap1 = lap1
            self.lap2 = lap2 if lap2 else lap1
            
            # 更新視窗標題
            self.update_window_title()
            
            # 🆕 設置時間軸模式
            if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
                if hasattr(self.throttle_chart_widget, 'set_time_axis_mode'):
                    self.throttle_chart_widget.set_time_axis_mode(use_time_axis)
                    print(f"[THROTTLE_MDI] ✅ 已設置時間軸模式: {use_time_axis}")
            
            # 重新載入數據
            print(f"[THROTTLE_MDI] 🚀 重新載入數據...")
            success = self.load_data(
                year=year,
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest=is_fastest
            )
            
            if success:
                print(f"[THROTTLE_MDI] ✅ 圈速油門油門參數更新成功")
            else:
                print(f"[THROTTLE_MDI] ❌ 數據載入失敗")
                
            return success
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] update_lap_parameters 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def refresh_analysis(self) -> None:
        """刷新分析 - 實現抽象方法"""
        try:
            self.data_manager.load_throttle_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver1="VER",
                driver2="VER",
                lap1=1,
                lap2=1
            )
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] refresh_analysis 失敗: {e}")
    
    def clear_data(self):
        """清除數據 - 實現抽象方法"""
        try:
            if self.throttle_chart_widget:
                # 清除油門圖表數據
                self.throttle_chart_widget.reset_data()
            print(f"[THROTTLE_MDI] 數據已清除")
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] clear_data 失敗: {e}")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據 - 實建抽象方法"""
        try:
            return {
                'module': 'throttle_analysis',
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session,
                'initialized': self._initialized,
                'data_loaded': self.data_manager is not None
            }
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] get_current_data 失敗: {e}")
            return None

    
    def _check_and_load_telemetry_if_needed(self, year: Optional[str] = None,
                                            race: Optional[str] = None,
                                            session: Optional[str] = None) -> bool:
        """確保遙測分析資料可用，遵循 API-ONLY 模式
        
        ⚠️ API-ONLY 模式：此方法只檢查本地 JSON 緩存，不自動創建視窗
        若數據不存在，應通過 API 或提示用戶手動操作
        """
        try:
            target_year = str(year or self.current_year or "").strip()
            target_race = (race or self.current_race or "").strip()
            target_session = str(session or self.current_session or "").strip()

            print(f"[throttle_MDI] 🔍 [API-ONLY] 檢查遙測分析本地緩存: {{target_year}} {{target_race}} {{target_session}}")

            # ✅ 允許：檢查本地 JSON 緩存
            telemetry_file = self._find_telemetry_analysis_file(
                year=target_year,
                race=target_race,
                session=target_session
            )
            if telemetry_file:
                print(f"[throttle_MDI] 📂 [API-ONLY] 找到本地遙測分析緩存: {{telemetry_file}}")
                return True

            # ❌ 禁止：自動創建視窗或啟動 CLI
            # 改為僅提示用戶通過 API 或主視窗遙測模組獲取數據
            print("⚠️ [throttle_MDI] [API-ONLY] 遙測分析數據不存在於本地緩存")
            print("💡 [throttle_MDI] [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據")
            print("💡 [throttle_MDI] [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8")
            return False

        except Exception as e:
            print(f"[ERROR] [throttle_MDI] _check_and_load_telemetry_if_needed 失敗: {{e}}")
            return False

    def _ensure_telemetry_data_for_fastest_laps(self) -> Optional[Dict[str, int]]:
        """確保遙測分析數據存在，並獲取最速圈數據
        
        Returns:
            Dict[str, int]: 車手代碼到最速圈數的映射，例如 {'VER': 15, 'LEC': 23}
        """
        try:
            print(f"[THROTTLE_MDI] 🔍 檢查遙測分析數據: {self.current_year} {self.current_race} {self.current_session}")
            
            # 檢查遙測分析JSON檔案是否存在
            telemetry_file = self._find_telemetry_analysis_file()
            
            if not telemetry_file:
                print(f"[THROTTLE_MDI] 📡 遙測分析數據不存在，開始自動載入...")
                success = self._trigger_telemetry_analysis()
                if success:
                    # 重新檢查檔案
                    telemetry_file = self._find_telemetry_analysis_file()
                else:
                    print(f"[THROTTLE_MDI] ❌ 遙測分析載入失敗")
                    return None
            
            if telemetry_file:
                print(f"[THROTTLE_MDI] 📂 找到遙測分析檔案: {telemetry_file}")
                return self._extract_fastest_laps_from_telemetry(telemetry_file)
            else:
                print(f"[THROTTLE_MDI] ❌ 無法獲取遙測分析數據")
                return None
                
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] _ensure_telemetry_data_for_fastest_laps 失敗: {e}")
            return None

    def _find_telemetry_analysis_file(self) -> Optional[str]:
        """尋找遙測分析JSON檔案"""
        try:
            import glob
            
            # 搜尋可能的檔案位置
            search_patterns = [
                f"json/telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"json/telemetry_analysis_{self.current_year}_{self.current_race}.json",
                f"json_exports/telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"json_exports/telemetry_analysis_{self.current_year}_{self.current_race}.json"
            ]
            
            for pattern in search_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    print(f"[THROTTLE_MDI] 🎯 找到遙測分析檔案: {matching_files[0]}")
                    return matching_files[0]
            
            # 如果沒找到精確匹配，嘗試模糊搜尋
            fuzzy_pattern = f"json*/telemetry_analysis*{self.current_year}*{self.current_race}*.json"
            matching_files = glob.glob(fuzzy_pattern)
            if matching_files:
                print(f"[THROTTLE_MDI] 🔍 模糊搜尋找到遙測分析檔案: {matching_files[0]}")
                return matching_files[0]
            
            print(f"[THROTTLE_MDI] ❌ 未找到遙測分析檔案")
            return None
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] _find_telemetry_analysis_file 失敗: {e}")
            return None

    def _trigger_telemetry_analysis(self) -> bool:
        """觸發遙測分析載入/生成"""
        try:
            print(f"[THROTTLE_MDI] 🚀 觸發遙測分析載入: {self.current_year} {self.current_race} {self.current_session}")
            
            # 方法1: 嘗試通過主視窗找到遙測分析模組
            if hasattr(self, 'parent_window') and self.parent_window:
                main_window = self.parent_window
                # 尋找主視窗的父級(可能是F1T主視窗)
                while main_window.parent():
                    main_window = main_window.parent()
                
                # 檢查是否有MDI區域
                if hasattr(main_window, 'mdi_area'):
                    # 檢查是否已有遙測分析視窗
                    for sub_window in main_window.mdi_area.subWindowList():
                        window_title = sub_window.windowTitle()
                        if "遙測分析" in window_title:
                            print(f"[THROTTLE_MDI] 🎯 找到現有遙測分析視窗: {window_title}")
                            # 激活並刷新遙測分析視窗
                            main_window.mdi_area.setActiveSubWindow(sub_window)
                            return True
                    
                    # API-ONLY 模式：不自動創建視窗
                    print(f"[THROTTLE_MDI] � [API-ONLY] 未找到現有遙測分析視窗")
                    print(f"[THROTTLE_MDI] 💡 提示：請手動開啟遙測分析模組或通過 API 獲取數據")
                    return False
            
            # 方法2: 通過CLI生成遙測分析數據（Function 12）
            print(f"[THROTTLE_MDI] 🔧 通過CLI生成遙測分析數據（Function 12）...")
            return self._generate_telemetry_via_cli()
            
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] _trigger_telemetry_analysis 失敗: {e}")
            return False

    def _generate_telemetry_via_cli(self) -> bool:
        """通過CLI生成遙測分析數據（Function 12）"""
        try:
            import subprocess
            import threading
            import time
            
            # 構建CLI命令 - 功能12是車手詳細遙測分析（正確的遙測數據來源）
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "12",  # 功能12: 車手詳細遙測分析
                "-y", str(self.current_year),
                "-r", self.current_race,
                "-s", self.current_session
            ]
            
            print(f"[THROTTLE_MDI] 🔧 執行CLI命令: {' '.join(command)}")
            
            # 同步執行CLI命令（因為油門分析需要立即使用結果）
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                cwd=os.getcwd()
            )
            
            stdout, stderr = process.communicate(timeout=120)  # 2分鐘超時
            
            if process.returncode == 0:
                print(f"[THROTTLE_MDI] ✅ 遙測分析CLI執行成功")
                # 等待檔案寫入完成
                time.sleep(2)
                return True
            else:
                print(f"[THROTTLE_MDI] ❌ 遙測分析CLI執行失敗: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[THROTTLE_MDI] ⏰ 遙測分析CLI執行超時")
            process.kill()
            return False
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] _generate_telemetry_via_cli 失敗: {e}")
            return False

    def _extract_fastest_laps_from_telemetry(self, telemetry_file: str) -> Optional[Dict[str, int]]:
        """從遙測分析JSON檔案中提取最速圈數據"""
        try:
            import json
            
            print(f"[THROTTLE_MDI] 📊 讀取遙測分析檔案: {telemetry_file}")
            
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            fastest_laps = {}
            
            # 檢查數據結構
            if 'data' in telemetry_data:
                driver_data = telemetry_data['data']
            else:
                driver_data = telemetry_data
            
            # 提取每個車手的最速圈數
            for driver_code, driver_info in driver_data.items():
                if isinstance(driver_info, dict):
                    lap_analysis = driver_info.get('lap_time_analysis', {})
                    fastest_lap = lap_analysis.get('fastest_lap', {})
                    lap_number = fastest_lap.get('lap_number')
                    
                    if lap_number and lap_number != 'N/A':
                        try:
                            fastest_laps[driver_code] = int(lap_number)
                            print(f"[THROTTLE_MDI] 🏁 {driver_code} 最速圈: 第{lap_number}圈")
                        except (ValueError, TypeError):
                            print(f"[THROTTLE_MDI] ⚠️ {driver_code} 最速圈數無效: {lap_number}")
            
            if fastest_laps:
                print(f"[THROTTLE_MDI] ✅ 成功提取 {len(fastest_laps)} 個車手的最速圈數據")
                return fastest_laps
            else:
                print(f"[THROTTLE_MDI] ❌ 未找到有效的最速圈數據")
                return None
                
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] _extract_fastest_laps_from_telemetry 失敗: {e}")
            return None

    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數更新通知
        
        支援兩種調用方式：
        1. 主視窗格式: receive_main_window_update_notification(param_type, value)
        2. 直接參數格式: receive_main_window_update_notification(year=xxx, race=xxx, session=xxx)
        
        Args:
            param_type_or_year: 參數類型('year'/'race'/'session') 或直接的年份值
            value_or_race: 參數值 或直接的賽事名稱
            session: 賽段 (當使用直接參數格式時)
            **kwargs: 其他可能的參數
        """
        try:
            print(f"[SPEED_NOTIFICATION_DEBUG] ========== 收到主視窗更新通知 ==========")
            print(f"[SPEED_NOTIFICATION_DEBUG] � 原始參數:")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - param_type: {param_type}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - value: {value}")
            
            # 簡化的參數處理
            # 直接處理參數更新
            if param_type == 'year':
                self.current_year = str(value)
                print(f"[UPDATE] 年份更新為: {self.current_year}")
            elif param_type == 'race':
                self.current_race = str(value)
                print(f"[UPDATE] 賽事更新為: {self.current_race}")
            elif param_type == 'session':
                self.current_session = str(value)
                print(f"[UPDATE] 場次更新為: {self.current_session}")
            
            print(f"[SPEED_NOTIFICATION_DEBUG] 📊 當前模組狀態:")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前年份: {self.current_year}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前賽事: {self.current_race}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前賽段: {self.current_session}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前車手: {self.driver1} vs {self.driver2}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前圈數: 第{self.lap1}圈 vs 第{self.lap2}圈")
            
            # [TOOL] 更新窗口標題（如果有父窗口）- 使用統一的 get_window_title
            parent = getattr(self, 'parent_window', None)
            if parent and hasattr(parent, 'setWindowTitle'):
                title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                parent.setWindowTitle(title)
                print(f"[TITLE] 窗口標題更新為: {title}")
            else:
                print(f"[WARNING] 無法更新視窗標題 - 父視窗引用未設置")
            
            # 重新載入數據
            if self.data_manager:
                print(f"[REFRESH] 重新載入油門數據...")
                self.data_manager.load_throttle_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
            print(f"[OK] [NOTIFICATION] ⚡ 油門分析模組內容更新成功")
                
        except Exception as e:
            print(f"[ERROR] [NOTIFICATION] ⚡ 油門分析模組內容更新失敗: {e}")
            import traceback
            traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據 - 實現抽象方法"""
        try:
            print(f"[THROTTLE_MDI] 匯出數據功能尚未實現 (路徑: {export_path}, 格式: {export_format})")
            return False
        except Exception as e:
            print(f"[ERROR] [THROTTLE_MDI] export_data 失敗: {e}")
            return False

# 註冊油門分析模組到工廠
try:
    from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
    ModuleFactory.register_module(ModuleTypes.TELEMETRY_THROTTLE, ThrottleAnalysisModule)
    print(f"[OK] [MODULE_FACTORY] Throttle analysis module registered")
except ImportError as e:
    print(f"[WARNING] [MODULE_FACTORY] 油門分析模組註冊失敗: {e}")
