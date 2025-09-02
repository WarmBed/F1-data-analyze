#!/usr/bin/env python3
"""
F1T RPM分析 MDI 模組
基於速度分析模組的成功架構設計
支援雙車手RPM對比的 GUI 模組，使用新版模組更新機制
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

# 導入分析模組介面
try:
    from .interfaces.analysis_module import IAnalysisModule
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    try:
        from modules.interfaces.analysis_module import IAnalysisModule
    except ImportError:
        # 如果都失敗，定義一個基本的接口
        from PyQt5.QtCore import QObject
        class IAnalysisModule(QObject):
            def __init__(self, parent=None):
                super().__init__(parent)

class RPMDataManager(QObject):
    """RPM數據管理器 - 負責JSON緩存和CLI備援"""
    
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
        
    def load_rpm_data(self, year: str, race: str, session: str, 
                      driver1: str = "VER", driver2: str = "VER",
                      lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:
        """載入RPM對比數據"""
        try:
            print(f"[RPM_MDI_DATA] ========== 載入RPM數據 ==========")
            print(f"[RPM_MDI_DATA] 參數: {year} {race} {session}")
            print(f"[RPM_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            if self._is_loading:
                print(f"[RPM_MDI_DATA] ⚠️ 數據載入中，忽略新請求")
                self.error_occurred.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.loading_progress.emit(0)
            self.status_changed.emit("開始載入RPM數據...")
            
            # 檢查最速圈選項並自動載入遙測分析
            if is_fastest or lap1 == "fastest" or lap2 == "fastest":
                print(f"🔄 [RPM_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")
                self._check_and_load_telemetry_if_needed()
                
                # 解析最速圈參數為實際圈數
                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)
                print(f"🔢 [RPM_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")
            
            print(f"[RPM_MDI_DATA] 🔗 創建 RPMAnalysisDataLoader...")
            
            # 使用現有的RPM分析數據載入器
            from modules.rpm_analysis_data_loader import RPMAnalysisDataLoader
            
            print(f"[RPM_MDI_DATA] 🚀 調用 load_rpm_analysis_data...")
            
            # 創建數據載入器
            rpm_loader = RPMAnalysisDataLoader()
            rpm_loader.data_loaded.connect(self._on_data_loaded)
            rpm_loader.loading_error.connect(self._on_load_error)
            rpm_loader.status_changed.connect(self.status_changed.emit)
            
            # 開始載入數據
            session_info = {
                'year': int(year),
                'race': race,
                'session': session,
                'driver1': driver1,
                'driver2': driver2,
                'lap1': lap1,
                'lap2': lap2,
                'is_fastest_lap': is_fastest
            }
            
            success = rpm_loader.load_rpm_analysis_data(session_info)
            
            # 保存載入器引用避免被回收
            self._rpm_loader = rpm_loader
            
            return success
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] RPM數據載入失敗: {e}")
            self.error_occurred.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False

    def _check_and_load_telemetry_if_needed(self):
        """檢查並在需要時載入遙測分析"""
        try:
            print(f"📞 [RPM_MDI] 調用主視窗開啟遙測分析...")
            
            # 通過主視窗調用遙測分析
            if hasattr(self, 'parent_window') and self.parent_window:
                if hasattr(self.parent_window, 'open_telemetry_analysis'):
                    self.parent_window.open_telemetry_analysis()
                    print(f"✅ [RPM_MDI] 遙測分析已觸發")
                    return True
                elif hasattr(self.parent_window, 'create_telemetry_analysis_tab'):
                    self.parent_window.create_telemetry_analysis_tab()
                    print(f"✅ [RPM_MDI] 遙測分析已觸發")
                    return True
                else:
                    print(f"❌ [RPM_MDI] 主視窗沒有遙測分析方法")
                    return False
            else:
                print(f"❌ [RPM_MDI] 找不到主視窗引用")
                return False
                
        except Exception as e:
            print(f"❌ [RPM_MDI] 觸發遙測分析時發生錯誤: {e}")
            return False

    def _get_fastest_lap_number(self, driver: str) -> int:
        """從遙測分析數據獲取指定車手的最速圈數"""
        try:
            print(f"🔍 [RPM_MDI] 開始搜尋 {driver} 的最速圈數據...")
            
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
                            print(f"📁 [RPM_MDI] 找到遙測檔案: {telemetry_file}")
                            break
                    if telemetry_file:
                        break
            
            if not telemetry_file:
                print(f"❌ [RPM_MDI] 找不到遙測分析檔案，使用預設圈數 1")
                return 1
                
            # 讀取並解析遙測分析數據
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            print(f"📊 [RPM_MDI] 遙測檔案讀取成功，開始解析最速圈數據...")
            
            # 嘗試多種數據結構格式
            fastest_lap_num = None
            
            # 格式1: data.all_drivers_telemetry[driver].fastest_lap
            if 'data' in telemetry_data and 'all_drivers_telemetry' in telemetry_data['data']:
                driver_data = telemetry_data['data']['all_drivers_telemetry'].get(driver)
                if driver_data and 'fastest_lap' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap'].get('lap_number')
                    if fastest_lap_num:
                        print(f"✅ [RPM_MDI] 從格式1找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                        return int(fastest_lap_num)
            
            # 格式2: data.fastest_laps中的列表
            if 'data' in telemetry_data and 'fastest_laps' in telemetry_data['data']:
                for fastest_data in telemetry_data['data']['fastest_laps']:
                    if fastest_data.get('driver') == driver:
                        fastest_lap_num = fastest_data.get('lap_number')
                        if fastest_lap_num:
                            print(f"✅ [RPM_MDI] 從格式2找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                            return int(fastest_lap_num)
            
            # 格式3: 直接在data下按車手分組
            if 'data' in telemetry_data:
                driver_data = telemetry_data['data'].get(driver)
                if driver_data and 'fastest_lap_number' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap_number']
                    print(f"✅ [RPM_MDI] 從格式3找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                    return int(fastest_lap_num)
            
            print(f"⚠️ [RPM_MDI] 無法找到 {driver} 的最速圈數據，使用預設圈數 1")
            return 1
            
        except Exception as e:
            print(f"❌ [RPM_MDI] 解析最速圈數據時發生錯誤: {e}")
            return 1

    def _resolve_lap_numbers(self, lap1, lap2, driver1, driver2, is_fastest):
        """解析圈數參數，將'fastest'轉換為實際圈數"""
        try:
            resolved_lap1 = lap1
            resolved_lap2 = lap2
            
            # 處理lap1
            if lap1 == "fastest" or is_fastest:
                print(f"🔄 [RPM_MDI] 解析 {driver1} 的最速圈...")
                resolved_lap1 = self._get_fastest_lap_number(driver1)
                
            # 處理lap2
            if lap2 == "fastest" or is_fastest:
                print(f"🔄 [RPM_MDI] 解析 {driver2} 的最速圈...")
                resolved_lap2 = self._get_fastest_lap_number(driver2)
            
            print(f"📊 [RPM_MDI] 圈數解析結果: {driver1}=第{resolved_lap1}圈, {driver2}=第{resolved_lap2}圈")
            
            return int(resolved_lap1), int(resolved_lap2)
            
        except Exception as e:
            print(f"❌ [RPM_MDI] 解析圈數時發生錯誤: {e}")
            return 1, 1
    
    def _on_data_loaded(self, data: dict):
        """處理數據載入完成"""
        try:
            print(f"[RPM_MDI] 數據載入完成")
            self._is_loading = False
            self.data_loaded.emit(data)
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 數據處理失敗: {e}")
            self.error_occurred.emit(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_message: str):
        """處理載入錯誤"""
        print(f"[ERROR] [RPM_MDI] 載入錯誤: {error_message}")
        self._is_loading = False
        self.error_occurred.emit(error_message)

class RPMAnalysisModule(IAnalysisModule):
    """RPM分析主模組"""
    
    # 信號定義
    module_error = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
        self.rpm_chart_widget = None
        self.main_widget = None  # 主容器 widget
        self.parent_window = None  # MDI 子視窗引用
        
        # 初始化狀態
        self._initialized = False
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 實現抽象方法"""
        try:
            print(f"[RPM_MDI] ========== 初始化RPM分析模組 ==========")
            print(f"[RPM_MDI] 傳入參數: {kwargs}")
            
            # 創建數據管理器
            print(f"[RPM_MDI] 🔧 創建 RPMDataManager...")
            self.data_manager = RPMDataManager()
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            
            # 設置數據管理器的父視窗引用
            self.data_manager.parent_window = self.parent_window
            
            # 創建RPM圖表組件
            print(f"[RPM_MDI] 🔧 創建 RPMAnalysisChartWidget...")
            try:
                from modules.rpm_analysis_chart_widget import RPMAnalysisChartWidget
                self.rpm_chart_widget = RPMAnalysisChartWidget()
                print(f"[RPM_MDI] ✅ RPM圖表組件創建成功")
            except ImportError as e:
                print(f"[ERROR] [RPM_MDI] RPM圖表組件導入失敗: {e}")
                self.module_error.emit(f"RPM圖表組件導入失敗: {str(e)}")
                return False
            
            # 連接圈數變更信號
            print(f"[RPM_MDI] 🔗 連接信號...")
            if hasattr(self.rpm_chart_widget, 'lap_numbers_changed'):
                self.rpm_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
                print(f"[RPM_MDI] ✅ lap_numbers_changed 信號連接成功")
            else:
                print(f"[ERROR] [RPM_MDI] RPM圖表組件缺少 lap_numbers_changed 信號")
            
            # 設置初始圈數
            print(f"[RPM_MDI] 🔢 設置初始圈數: {self.lap1}, {self.lap2}")
            if hasattr(self.rpm_chart_widget, 'set_lap_numbers'):
                self.rpm_chart_widget.set_lap_numbers(self.lap1, self.lap2)
                print(f"[RPM_MDI] ✅ 圈數設置成功")
            else:
                print(f"[ERROR] [RPM_MDI] RPM圖表組件缺少 set_lap_numbers 方法")
            
            # 設置主界面
            print(f"[RPM_MDI] 🎨 設置UI...")
            self._setup_ui()
            
            self._initialized = True
            print(f"[OK] [RPM_MDI] RPM分析模組初始化完成")
            
            # 檢查初始參數狀態
            print(f"[RPM_MDI] 🔍 檢查初始參數:")
            print(f"[RPM_MDI]   - current_year: {self.current_year}")
            print(f"[RPM_MDI]   - current_race: {self.current_race}")
            print(f"[RPM_MDI]   - current_session: {self.current_session}")
            print(f"[RPM_MDI]   - driver1: {self.driver1}")
            print(f"[RPM_MDI]   - driver2: {self.driver2}")
            print(f"[RPM_MDI]   - data_manager: {self.data_manager is not None}")
            
            # 立即載入初始數據（如果有參數）
            if self.current_year and self.current_race and self.current_session:
                print(f"[RPM_MDI] 🚀 參數完整，開始載入初始數據...")
                self._load_initial_data()
            else:
                print(f"[RPM_MDI] ⚠️ 參數不完整，跳過初始數據載入")
                print(f"[RPM_MDI]   - 缺少年份: {not self.current_year}")
                print(f"[RPM_MDI]   - 缺少賽事: {not self.current_race}")
                print(f"[RPM_MDI]   - 缺少賽段: {not self.current_session}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用（MDI 子視窗）"""
        self.parent_window = parent_window
        
        # 如果數據管理器已存在，同時更新其父視窗引用
        if self.data_manager:
            self.data_manager.parent_window = parent_window
        
        if parent_window:
            # 立即設置正確的標題
            self.update_window_title()
            
            # 如果模組已初始化且有參數，嘗試載入數據
            if (self._initialized and self.current_year and 
                self.current_race and self.current_session):
                print(f"[RPM_MDI] 🔄 父視窗設置後觸發數據載入...")
                self._load_initial_data()
    
    def _setup_ui(self):
        """設置用戶界面"""
        print(f"[RPM_MDI] 🎨 設置UI界面...")
        # 創建主容器 widget
        self.main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加RPM圖表
        if self.rpm_chart_widget:
            print(f"[RPM_MDI] ➕ 添加RPM圖表到佈局")
            layout.addWidget(self.rpm_chart_widget)
        else:
            print(f"[ERROR] [RPM_MDI] RPM圖表組件為 None")
        
        # 設置佈局到主 widget
        self.main_widget.setLayout(layout)
        print(f"[RPM_MDI] ✅ UI界面設置完成")
    
    def _load_initial_data(self):
        """載入初始數據"""
        try:
            print(f"[RPM_MDI] 🚀 載入初始數據...")
            print(f"[RPM_MDI] 參數: {self.current_year} {self.current_race} {self.current_session}")
            print(f"[RPM_MDI] 車手: {self.driver1} vs {self.driver2}, 圈數: {self.lap1} vs {self.lap2}")
            
            if self.data_manager:
                success = self.data_manager.load_rpm_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                print(f"[RPM_MDI] 數據載入結果: {success}")
            else:
                print(f"[ERROR] [RPM_MDI] 數據管理器為 None")
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 載入初始數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] [RPM_MDI] 收到錯誤: {error_message}")
        self.module_error.emit(error_message)
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            print(f"[RPM_MDI] ========== 更新RPM圖表 ==========")
            print(f"[RPM_MDI] 收到數據鍵: {list(data.keys()) if data else 'None'}")
            
            if not data:
                print(f"[ERROR] [RPM_MDI] 收到空數據")
                return
                
            if self.rpm_chart_widget:
                print(f"[RPM_MDI] 📊 調用圖表更新...")
                self.rpm_chart_widget.update_rpm_data(data)
                print(f"[RPM_MDI] ✅ 圖表更新完成")
                
                # 更新工具欄狀態信息
                print(f"[RPM_MDI] 📋 更新工具欄狀態...")
                self._update_toolbar_status(data)
            else:
                print(f"[ERROR] [RPM_MDI] RPM圖表組件為 None")
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
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
            
            module_name = "RPM分析"
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
            
            print(f"[RPM_MDI] 已更新工具欄狀態: {module_name}")
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 更新工具欄狀態失敗: {e}")
    
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
            print(f"[ERROR] [RPM_MDI] 獲取主視窗失敗: {e}")
            return None
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] [RPM_MDI] {error_message}")
        self.module_error.emit(error_message)
    
    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更"""
        try:
            print(f"[RPM_MDI] ========== 圈數變更處理 ==========")
            print(f"[RPM_MDI] 新圈數: 第{lap1}圈 vs 第{lap2}圈")
            
            # 更新模組的圈數參數
            old_lap1, old_lap2 = self.lap1, self.lap2
            self.lap1 = lap1
            self.lap2 = lap2
            
            print(f"[RPM_MDI] 圈數變更: 第{old_lap1}圈 vs 第{old_lap2}圈 → 第{lap1}圈 vs 第{lap2}圈")
            
            # 重新載入數據
            if self.data_manager:
                print(f"[RPM_MDI] 🔄 因圈數變更重新載入數據...")
                success = self.data_manager.load_rpm_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                
                if success:
                    print(f"[RPM_MDI] ✅ 圈數變更後數據重載成功")
                else:
                    print(f"[RPM_MDI] ❌ 圈數變更後數據重載失敗")
            else:
                print(f"[RPM_MDI] ❌ 數據管理器未初始化，無法重載數據")
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 處理圈數變更失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"處理圈數變更失敗: {str(e)}")
    
    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """更新參數 - 實現抽象方法"""
        try:
            print(f"[RPM_PARAMS_DEBUG] ========== RPM參數更新開始 ==========")
            print(f"[RPM_PARAMS_DEBUG] 收到參數: year={year}, race={race}, session={session}")
            print(f"[RPM_PARAMS_DEBUG] 當前參數: year={self.current_year}, race={self.current_race}, session={self.current_session}")
            print(f"[RPM_PARAMS_DEBUG] 額外參數: {kwargs}")
            
            # 準備更新的參數
            new_year = str(year) if year is not None else self.current_year
            new_race = race if race is not None else self.current_race
            new_session = session if session is not None else self.current_session
            
            print(f"[RPM_PARAMS_DEBUG] 新參數: new_year={new_year}, new_race={new_race}, new_session={new_session}")
            
            # 檢查參數是否有變化（基於當前的模組參數）
            params_changed = (
                self.current_year != new_year or 
                self.current_race != new_race or 
                self.current_session != new_session
            )
            
            print(f"[RPM_PARAMS_DEBUG] 參數是否有變化: {params_changed}")
            
            # 更新本地參數（如果調用者沒有提前更新的話）
            self.current_year = new_year
            self.current_race = new_race
            self.current_session = new_session
            
            print(f"[RPM_PARAMS_DEBUG] 更新後的參數: year={self.current_year}, race={self.current_race}, session={self.current_session}")
            
            # 確保視窗標題是最新的
            self.update_window_title()
            
            print(f"[RPM_PARAMS_DEBUG] 數據管理器狀態: {self.data_manager is not None}")
            
            if params_changed:
                print(f"[RPM_PARAMS_DEBUG] 🔄 參數有變化，載入新數據...")
                # 載入新數據
                if self.data_manager:
                    print(f"[RPM_PARAMS_DEBUG] 📊 呼叫 data_manager.load_rpm_data...")
                    success = self.data_manager.load_rpm_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    print(f"[RPM_PARAMS_DEBUG] 📊 數據載入結果: {success}")
                    
                    if success:
                        # 數據載入成功後再次確保標題正確
                        self.update_window_title()
                        self.parameters_updated.emit({
                            'year': int(new_year),
                            'race': new_race,
                            'session': new_session
                        })
                        print(f"[RPM_PARAMS_DEBUG] ✅ 參數更新成功 - 參數已變化")
                        return True
                    else:
                        print(f"[RPM_PARAMS_DEBUG] ❌ 參數更新失敗 - 數據載入失敗")
                        return False
                else:
                    print(f"[RPM_PARAMS_DEBUG] ❌ 參數更新失敗 - 數據管理器為空")
                    return False
            else:
                print(f"[RPM_PARAMS_DEBUG] 🔄 參數無變化，檢查是否需要首次載入...")
                # 如果是首次載入或沒有數據，仍然需要載入
                print(f"[RPM_PARAMS_DEBUG] _data_loaded 標記: {hasattr(self, '_data_loaded')}")
                if self.data_manager and not hasattr(self, '_data_loaded'):
                    print(f"[RPM_PARAMS_DEBUG] 📊 首次載入 - 呼叫 data_manager.load_rpm_data...")
                    success = self.data_manager.load_rpm_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    print(f"[RPM_PARAMS_DEBUG] 📊 首次載入結果: {success}")
                    if success:
                        self._data_loaded = True
                        print(f"[RPM_PARAMS_DEBUG] ✅ 參數更新成功 - 首次載入成功")
                        return True
                    else:
                        print(f"[RPM_PARAMS_DEBUG] ❌ 參數更新失敗 - 首次載入失敗")
                        return False
                else:
                    print(f"[RPM_PARAMS_DEBUG] ✅ 參數更新成功 - 無需載入")
                    return True
                
        except Exception as e:
            print(f"[ERROR] [RPM_PARAMS_DEBUG] 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False) -> bool:
        """更新圈速分析參數（包含車手和圈數）"""
        try:
            print(f"[RPM_MDI] ========== 圈速參數更新 ==========")
            print(f"[RPM_MDI] 收到參數: {year} {race} {session}")
            print(f"[RPM_MDI] 車手: {driver1} vs {driver2}")
            print(f"[RPM_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
            print(f"[RPM_MDI] 最速圈: {is_fastest}")
            
            # 檢查是否需要最速圈數據
            if is_fastest:
                print(f"[RPM_MDI] 🏁 用戶選擇了最速圈選項，檢查遙測分析數據...")
                fastest_laps = self._ensure_telemetry_data_for_fastest_laps()
                if fastest_laps:
                    # 使用最速圈數據更新圈數
                    if driver1 in fastest_laps:
                        lap1 = fastest_laps[driver1]
                        print(f"[RPM_MDI] 🏁 車手 {driver1} 最速圈: 第{lap1}圈")
                    if driver2 and driver2 in fastest_laps:
                        lap2 = fastest_laps[driver2]
                        print(f"[RPM_MDI] 🏁 車手 {driver2} 最速圈: 第{lap2}圈")
                else:
                    print(f"[RPM_MDI] ⚠️ 無法獲取最速圈數據，使用預設圈數")
            
            # 檢查參數是否有變化
            params_changed = (
                self.current_year != str(year) or 
                self.current_race != race or 
                self.current_session != session or
                self.driver1 != driver1 or
                self.driver2 != (driver2 or "VER") or  # 處理 None 值
                self.lap1 != lap1 or
                self.lap2 != lap2
            )
            
            print(f"[RPM_MDI] 參數是否變化: {params_changed}")
            
            # 更新所有參數
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.driver1 = driver1
            self.driver2 = driver2 or "VER"  # 如果沒有第二個車手，預設為 VER
            self.lap1 = lap1
            self.lap2 = lap2
            
            # 更新圖表組件的圈數顯示
            if self.rpm_chart_widget:
                self.rpm_chart_widget.set_lap_numbers(lap1, lap2)
                print(f"[RPM_MDI] ✅ 已更新圖表組件的圈數顯示")
            
            if params_changed:
                print(f"[RPM_MDI] 🔄 參數已變化，開始重載數據...")
                
                # 載入新數據
                if self.data_manager:
                    print(f"[RPM_MDI] 📡 調用數據管理器載入新數據...")
                    success = self.data_manager.load_rpm_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        print(f"[RPM_MDI] ✅ 圈速參數更新後數據重載成功")
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
                            print(f"[RPM_MDI] 🏷️ 視窗標題已更新為: {new_title}")
                        else:
                            print(f"[RPM_MDI] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
                        
                        return True
                    else:
                        print(f"[RPM_MDI] ❌ 圈速參數更新後數據重載失敗")
                        return False
                else:
                    print(f"[RPM_MDI] ❌ 數據管理器未初始化")
                    return False
            else:
                print(f"[RPM_MDI] ℹ️ 圈速參數未變化，保持現有數據")
                
                # 即使參數未變化，也確保視窗標題是正確的 - 使用統一的 get_window_title
                parent = getattr(self, 'parent_window', None)
                if parent and hasattr(parent, 'setWindowTitle'):
                    current_title = parent.windowTitle()
                    expected_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                    if current_title != expected_title:
                        parent.setWindowTitle(expected_title)
                        print(f"[RPM_MDI] 🏷️ 同步視窗標題: {expected_title}")
                else:
                    print(f"[RPM_MDI] ⚠️ 無法同步視窗標題 - 父視窗引用未設置")
                
                return True
                
        except Exception as e:
            print(f"[RPM_MDI] ❌ 圈速參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"圈速參數更新失敗: {str(e)}")
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 兼容其他模組的接口"""
        # 如果提供了參數，使用傳入的參數；否則使用內部狀態
        use_year = year if year is not None else self.current_year
        use_race = race if race is not None else self.current_race
        use_session = session if session is not None else self.current_session
        
        # 簡化標題格式，只顯示基本信息
        title = f"🔄 RPM分析 - {use_year} {use_race} {use_session}"
        
        # 如果有車手信息，添加到標題中
        if hasattr(self, 'driver1') and hasattr(self, 'driver2'):
            if self.driver1 and self.driver2 and self.driver1 != self.driver2:
                title += f" ({self.driver1} vs {self.driver2})"
            elif self.driver1:
                title += f" ({self.driver1})"
        
        # 如果有圈數信息，添加到標題中
        if hasattr(self, 'lap1') and hasattr(self, 'lap2'):
            if self.lap1 and self.lap2:
                title += f" 圈{self.lap1}-{self.lap2}"
        
        return title
    
    def update_window_title(self) -> None:
        """更新視窗標題"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'setWindowTitle'):
                new_title = self.get_window_title()
                self.parent_window.setWindowTitle(new_title)
                print(f"[RPM_MDI] 🏷️ 視窗標題已更新: {new_title}")
            else:
                print(f"[RPM_MDI] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 更新視窗標題失敗: {e}")
    
    def get_widget(self):
        """獲取主要Widget - 實現抽象方法"""
        return self.main_widget if self.main_widget else QWidget()
    
    def get_default_size(self):
        """獲取預設視窗大小 - 實現抽象方法"""
        return (600, 400)
    
    def load_data(self, **kwargs) -> bool:
        """載入數據 - 實現抽象方法"""
        try:
            year = kwargs.get('year', self.current_year)
            race = kwargs.get('race', self.current_race)
            session = kwargs.get('session', self.current_session)
            driver1 = kwargs.get('driver1', self.driver1)
            driver2 = kwargs.get('driver2', self.driver2)
            lap1 = kwargs.get('lap1', self.lap1)
            lap2 = kwargs.get('lap2', self.lap2)
            is_fastest = kwargs.get('is_fastest', False)

            if self.data_manager:
                return self.data_manager.load_rpm_data(
                    year=year, race=race, session=session,
                    driver1=driver1, driver2=driver2,
                    lap1=lap1, lap2=lap2, is_fastest=is_fastest
                )
            return False
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] load_data 失敗: {e}")
            return False

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據 - 實現抽象方法"""
        try:
            return {
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session,
                'driver1': self.driver1,
                'driver2': self.driver2,
                'lap1': self.lap1,
                'lap2': self.lap2,
                'module_type': 'rpm_analysis'
            }
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] get_current_data 失敗: {e}")
            return {}

    # 這些方法可能需要實現，取決於IAnalysisModule的要求
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return "rpm_analysis"

    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return "RPM分析"

    @property
    def version(self) -> str:
        """版本"""
        return "1.0.0"

    @property
    def description(self) -> str:
        """描述"""
        return "F1 RPM分析模組，支援雙車手RPM對比"
