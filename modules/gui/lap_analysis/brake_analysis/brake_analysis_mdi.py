#!/usr/bin/env python3
"""
F1T brake分析 MDI 模組
基於速度分析模組的成功架構設計
支援雙車手brake對比的 GUI 模組，使用新版模組更新機制
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

class BrakeDataManager(QObject):
    """brake數據管理器 - 負責JSON緩存和CLI備援"""
    
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
        
    def load_brake_data(self, year: str, race: str, session: str, 
                      driver1: str = "VER", driver2: str = "VER",
                      lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:
        """載入brake對比數據"""
        try:
            print(f"[brake_MDI_DATA] ========== 載入brake數據 ==========")
            print(f"[brake_MDI_DATA] 參數: {year} {race} {session}")
            print(f"[brake_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            if self._is_loading:
                print(f"[brake_MDI_DATA] ⚠️ 數據載入中，忽略新請求")
                self.error_occurred.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.loading_progress.emit(0)
            self.status_changed.emit("開始載入brake數據...")
            
            # 檢查最速圈選項並自動載入遙測分析
            if is_fastest or lap1 == "fastest" or lap2 == "fastest":
                print(f"🔄 [brake_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")
                self._check_and_load_telemetry_if_needed()
                
                # 解析最速圈參數為實際圈數
                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)
                print(f"🔢 [brake_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")
            
            print(f"[brake_MDI_DATA] 🔗 創建 BrakeAnalysisDataLoader...")
            
            # 使用現有的brake分析數據載入器
            from .brake_analysis_data_loader import BrakeAnalysisDataLoader
            
            print(f"[brake_MDI_DATA] 🚀 調用 load_brake_data...")
            
            # 創建數據載入器並保存為實例變量防止垃圾回收
            self.brake_loader = BrakeAnalysisDataLoader()
            self.brake_loader.data_loaded.connect(self._on_data_loaded)
            self.brake_loader.load_error.connect(self._on_load_error)
            self.brake_loader.status_changed.connect(self.status_changed.emit)
            self.brake_loader.load_progress.connect(self.loading_progress.emit)
            
            # 開始載入數據
            success = self.brake_loader.load_brake_data(
                year=int(year),
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest_lap=is_fastest
            )
            
            # 將loader設置給chart widget以供直接更新
            if hasattr(self, 'brake_chart_widget') and self.brake_chart_widget:
                self.brake_chart_widget.brake_loader = self.brake_loader
                print(f"[brake_MDI] ✅ 已將loader設置給chart widget")
            
            if success:
                print(f"[brake_MDI_DATA] ✅ brake數據載入請求提交成功")
                self.loading_progress.emit(50)
                return True
            else:
                print(f"[brake_MDI_DATA] ❌ brake數據載入請求失敗")
                self._is_loading = False
                self.error_occurred.emit("brake數據載入請求失敗")
                return False
                
        except Exception as e:
            print(f"[ERROR] [brake_MDI_DATA] 載入brake數據時發生錯誤: {e}")
            self._is_loading = False
            self.error_occurred.emit(f"載入brake數據失敗: {str(e)}")
            return False
    
    def _on_data_loaded(self, data):
        """數據載入完成回調"""
        try:
            print(f"[brake_MDI_DATA] ✅ brake數據載入完成")
            self._is_loading = False
            self.loading_progress.emit(100)
            self.status_changed.emit("brake數據載入完成")
            self.data_loaded.emit(data)
        except Exception as e:
            print(f"[ERROR] [brake_MDI_DATA] 處理載入完成回調時發生錯誤: {e}")
            self._on_load_error(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_msg):
        """數據載入錯誤回調"""
        print(f"[brake_MDI_DATA] ❌ brake數據載入錯誤: {error_msg}")
        self._is_loading = False
        self.loading_progress.emit(0)
        self.status_changed.emit(f"載入失敗: {error_msg}")
        self.error_occurred.emit(error_msg)
    
    def _check_and_load_telemetry_if_needed(self):
        """檢查並載入遙測分析數據（最速圈用）"""
        try:
            print(f"[brake_MDI_DATA] 🔍 檢查遙測分析數據可用性...")
            
            # 檢查是否已有遙測分析檔案
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
                            print(f"📁 [brake_MDI_DATA] 找到現有遙測檔案: {telemetry_file}")
                            return True
            
            # 如果沒有找到，通過CLI生成Function 12數據
            print(f"[brake_MDI_DATA] � 未找到遙測數據，通過CLI生成...")
            return self._generate_telemetry_via_cli()
            
        except Exception as e:
            print(f"❌ [brake_MDI_DATA] 檢查遙測數據時發生錯誤: {e}")
            return False
    
    def _generate_telemetry_via_cli(self) -> bool:
        """通過CLI生成遙測分析數據（Function 12）"""
        try:
            import subprocess
            import time
            
            # 構建CLI命令 - 功能12是車手詳細遙測分析
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "12",  # 功能12: 車手詳細遙測分析
                "-y", str(self.current_year),
                "-r", self.current_race,
                "-s", self.current_session
            ]
            
            print(f"[brake_MDI_DATA] 🔧 執行CLI命令: {' '.join(command)}")
            
            # 同步執行CLI命令（因為brake分析需要立即使用結果）
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                cwd=os.getcwd()
            )
            
            stdout, stderr = process.communicate(timeout=300)  # 5分鐘超時
            
            if process.returncode == 0:
                print(f"[brake_MDI_DATA] ✅ 遙測分析CLI執行成功")
                time.sleep(2)  # 等待檔案寫入完成
                return True
            else:
                print(f"[brake_MDI_DATA] ❌ 遙測分析CLI執行失敗: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[brake_MDI_DATA] ⏰ 遙測分析CLI執行超時")
            return False
        except Exception as e:
            print(f"[ERROR] [brake_MDI_DATA] _generate_telemetry_via_cli 失敗: {e}")
            return False
    
    def _get_fastest_lap_number(self, driver: str) -> int:
        """從遙測分析數據獲取指定車手的最速圈數"""
        try:
            print(f"🔍 [brake_MDI] 開始搜尋 {driver} 的最速圈數據...")
            
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
                            print(f"📁 [brake_MDI] 找到遙測檔案: {telemetry_file}")
                            break
                    if telemetry_file:
                        break
            
            if not telemetry_file:
                print(f"❌ [brake_MDI] 找不到遙測分析檔案，使用預設圈數 1")
                return 1
                
            # 讀取並解析遙測分析數據
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            print(f"📊 [brake_MDI] 遙測檔案讀取成功，開始解析最速圈數據...")
            
            # 嘗試多種數據結構格式
            fastest_lap_num = None
            
            # 格式1: data.all_drivers_telemetry[driver].fastest_lap
            if 'data' in telemetry_data and 'all_drivers_telemetry' in telemetry_data['data']:
                driver_data = telemetry_data['data']['all_drivers_telemetry'].get(driver)
                if driver_data and 'fastest_lap' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap'].get('lap_number')
                    if fastest_lap_num:
                        print(f"✅ [brake_MDI] 從格式1找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                        return int(fastest_lap_num)
            
            # 格式2: data.fastest_laps中的列表
            if 'data' in telemetry_data and 'fastest_laps' in telemetry_data['data']:
                for fastest_data in telemetry_data['data']['fastest_laps']:
                    if fastest_data.get('driver') == driver:
                        fastest_lap_num = fastest_data.get('lap_number')
                        if fastest_lap_num:
                            print(f"✅ [brake_MDI] 從格式2找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                            return int(fastest_lap_num)
            
            # 格式3: 直接在data下按車手分組
            if 'data' in telemetry_data:
                driver_data = telemetry_data['data'].get(driver)
                if driver_data and 'fastest_lap_number' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap_number']
                    print(f"✅ [brake_MDI] 從格式3找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                    return int(fastest_lap_num)
            
            print(f"⚠️ [brake_MDI] 無法找到 {driver} 的最速圈數據，使用預設圈數 1")
            return 1
            
        except Exception as e:
            print(f"❌ [brake_MDI] 解析最速圈數據時發生錯誤: {e}")
            return 1

    def _resolve_lap_numbers(self, lap1, lap2, driver1, driver2, is_fastest):
        """解析圈數參數，將'fastest'轉換為實際圈數"""
        try:
            resolved_lap1 = lap1
            resolved_lap2 = lap2
            
            # 處理lap1
            if lap1 == "fastest" or is_fastest:
                print(f"🔄 [brake_MDI] 解析 {driver1} 的最速圈...")
                resolved_lap1 = self._get_fastest_lap_number(driver1)
                
            # 處理lap2
            if lap2 == "fastest" or is_fastest:
                print(f"🔄 [brake_MDI] 解析 {driver2} 的最速圈...")
                resolved_lap2 = self._get_fastest_lap_number(driver2)
            
            print(f"📊 [brake_MDI] 圈數解析結果: {driver1}=第{resolved_lap1}圈, {driver2}=第{resolved_lap2}圈")
            
            return int(resolved_lap1), int(resolved_lap2)
            
        except Exception as e:
            print(f"❌ [brake_MDI] 解析圈數時發生錯誤: {e}")
            return 1, 1

class BrakeAnalysisModule(IAnalysisModule):
    """brake分析主模組"""
    
    # 信號定義 - 與速度模組保持一致
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
        self.brake_chart_widget = None
        self.main_widget = None  # 主容器 widget
        self.parent_window = None  # MDI 子視窗引用
        
        # 初始化狀態
        self._initialized = False
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 實現抽象方法"""
        try:
            print(f"[brake_MDI] 初始化brake分析模組")
            
            # 創建數據管理器
            self.data_manager = BrakeDataManager()
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            
            # 創建brake圖表組件
            from .brake_analysis_chart_widget import BrakeAnalysisChartWidget
            self.brake_chart_widget = BrakeAnalysisChartWidget()
            
            # 連接圈數變更信號
            self.brake_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
            
            # 設置初始圈數
            self.brake_chart_widget.set_lap_numbers(self.lap1, self.lap2)
            
            # 設置主界面
            self._setup_ui()
            
            # 註冊到分析模組管理器
            try:
                from ..analysis_module_manager import get_analysis_module_manager
                manager = get_analysis_module_manager()
                
                # 註冊模組
                module_id = f"brake_analysis_{id(self)}"
                manager.register_module(module_id, self, "brake_analysis")
                
                # 註冊圖表組件
                if self.brake_chart_widget:
                    manager.register_chart_widget(self.brake_chart_widget)
                
                # 保存管理器引用和模組ID
                self._analysis_manager = manager
                self._module_id = module_id
                
                print(f"[brake_MDI] ✅ 已註冊到分析模組管理器: {module_id}")
                
            except ImportError as e:
                print(f"[WARNING] [brake_MDI] 無法導入分析模組管理器: {e}")
                self._analysis_manager = None
                self._module_id = None
            except Exception as e:
                print(f"[ERROR] [brake_MDI] 註冊到分析模組管理器失敗: {e}")
                self._analysis_manager = None
                self._module_id = None
            
            self._initialized = True
            print(f"[OK] [brake_MDI] brake分析模組初始化完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] [brake_MDI] 模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用（MDI 子視窗）"""
        self.parent_window = parent_window
        
        if parent_window:
            # 立即設置正確的標題
            self.update_window_title()
    
    def _create_placeholder_widget(self):
        """創建佔位組件（當brake圖表組件不可用時）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(tr('brake_chart_title', '🔄 煞車分析圖表'))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16pt; padding: 20px;")
        layout.addWidget(label)
        
        info_label = QLabel(tr('brake_chart_loading', '煞車圖表組件正在載入中...'))
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        return widget
    
    def _setup_ui(self):
        """設置用戶界面"""
        # 創建主容器 widget
        self.main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加brake圖表
        if self.brake_chart_widget:
            layout.addWidget(self.brake_chart_widget)
        
        # 設置佈局到主 widget
        self.main_widget.setLayout(layout)
    
    def get_widget(self) -> QWidget:
        """獲取主要UI組件"""
        return self.main_widget if self.main_widget else QWidget()
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 統一格式，不包含車手資訊以保持模組兼容性"""
        # 如果提供了參數，使用傳入的參數；否則使用內部狀態
        use_year = year if year is not None else self.current_year
        use_race = race if race is not None else self.current_race
        use_session = session if session is not None else self.current_session
        
        # 使用統一的簡潔標題格式，與其他模組保持一致
        title = f"{tr('brake_analysis', '煞車分析')}_{use_year}_{use_race}_{use_session}"
        
        print(f"[brake_TITLE_DEBUG] 🏷️ 生成視窗標題: '{title}'")
        print(f"[brake_TITLE_DEBUG]   📊 參數詳情:")
        print(f"[brake_TITLE_DEBUG]     - 年份: {use_year}")
        print(f"[brake_TITLE_DEBUG]     - 賽事: {use_race}")
        print(f"[brake_TITLE_DEBUG]     - 賽段: {use_session}")
        return title
    
    def update_window_title(self) -> None:
        """更新視窗標題"""
        try:
            print(f"[brake_TITLE_DEBUG] 🔄 開始更新視窗標題...")
            print(f"[brake_TITLE_DEBUG] 📋 當前狀態檢查:")
            
            # 檢查 parent_window 屬性（MDI 子視窗引用）
            parent = getattr(self, 'parent_window', None)
            print(f"[brake_TITLE_DEBUG]   - parent_window 存在: {parent is not None}")
            
            if parent and hasattr(parent, 'setWindowTitle'):
                old_title = parent.windowTitle()
                print(f"[brake_TITLE_DEBUG]   - 舊標題: '{old_title}'")
                
                new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                print(f"[brake_TITLE_DEBUG]   - 新標題: '{new_title}'")
                
                if old_title != new_title:
                    print(f"[brake_TITLE_DEBUG] 🔄 標題需要更新，執行更新...")
                    
                    # 直接更新標題
                    parent.setWindowTitle(new_title)
                    
                    # 驗證更新結果
                    updated_title = parent.windowTitle()
                    print(f"[brake_TITLE_DEBUG] ✅ 標題更新完成: '{updated_title}'")
                    
                    # 如果直接更新失敗，使用延遲更新
                    if updated_title != new_title:
                        print(f"[brake_TITLE_DEBUG] ⚠️ 直接更新失敗，嘗試延遲更新...")
                        self._delayed_title_update(new_title)
                else:
                    print(f"[brake_TITLE_DEBUG] ✅ 標題無需更新")
            else:
                print(f"[brake_TITLE_DEBUG] ⚠️ 無法更新標題:")
                print(f"[brake_TITLE_DEBUG]   - parent_window: {parent}")
                print(f"[brake_TITLE_DEBUG]   - 有setWindowTitle方法: {hasattr(parent, 'setWindowTitle') if parent else False}")
        
        except Exception as e:
            print(f"[ERROR] [brake_TITLE_DEBUG] 更新視窗標題失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _delayed_title_update(self, title: str) -> None:
        """延遲標題更新 - 採用進站分析模式"""
        print(f"[brake_TITLE_DEBUG] ⏰ 啟動延遲標題更新: '{title}'")
        
        def update_title():
            try:
                if self.parent_window and hasattr(self.parent_window, 'setWindowTitle'):
                    self.parent_window.setWindowTitle(title)
                    final_title = self.parent_window.windowTitle()
                    print(f"[brake_TITLE_DEBUG] ✅ 延遲更新完成: '{final_title}'")
                else:
                    print(f"[brake_TITLE_DEBUG] ❌ 延遲更新失敗: parent_window 不可用")
            except Exception as e:
                print(f"[ERROR] [brake_TITLE_DEBUG] 延遲更新異常: {e}")
        
        # 使用QTimer延遲執行
        QTimer.singleShot(100, update_title)
    
    def get_default_size(self) -> tuple:
        """獲取預設視窗大小"""
        return (1000, 700)  # brake分析需要較大的視窗來顯示詳細圖表

    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False) -> bool:
        """更新圈速分析參數（包含車手和圈數）- 與速度模組一致的接口"""
        try:
            print(f"[brake_MDI] ========== 圈速參數更新 ==========")
            print(f"[brake_MDI] 收到參數: {year} {race} {session}")
            print(f"[brake_MDI] 車手: {driver1} vs {driver2}")
            print(f"[brake_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
            print(f"[brake_MDI] 最速圈: {is_fastest}")
            
            # 檢查是否需要最速圈數據
            if is_fastest:
                print(f"[brake_MDI] 🏁 用戶選擇了最速圈選項，檢查遙測分析數據...")
                fastest_laps = self._ensure_telemetry_data_for_fastest_laps()
                if fastest_laps:
                    # 使用最速圈數據更新圈數
                    if driver1 in fastest_laps:
                        lap1 = fastest_laps[driver1]
                        print(f"[brake_MDI] 🏁 車手 {driver1} 最速圈: 第{lap1}圈")
                    if driver2 and driver2 in fastest_laps:
                        lap2 = fastest_laps[driver2]
                        print(f"[brake_MDI] 🏁 車手 {driver2} 最速圈: 第{lap2}圈")
                else:
                    print(f"[brake_MDI] ⚠️ 無法獲取最速圈數據，使用預設圈數")
            
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
            
            print(f"[brake_MDI] 參數是否變化: {params_changed}")
            
            # 更新所有參數 - 保持 driver2 的原始值（包括 None）
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.driver1 = driver1
            self.driver2 = driver2  # 保持原始值，支援單場賽事車手分析
            self.lap1 = lap1
            self.lap2 = lap2
            
            # 更新圖表組件的圈數顯示
            if self.brake_chart_widget:
                self.brake_chart_widget.set_lap_numbers(lap1, lap2)
                print(f"[brake_MDI] ✅ 已更新圖表組件的圈數顯示")
            
            if params_changed:
                print(f"[brake_MDI] 🔄 參數已變化，開始重載數據...")
                
                # 載入新數據
                if self.data_manager:
                    print(f"[brake_MDI] 📡 調用數據管理器載入新數據...")
                    success = self.data_manager.load_brake_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        print(f"[brake_MDI] ✅ 圈速參數更新後數據重載成功")
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
                        return True
                    else:
                        print(f"[brake_MDI] ❌ 圈速參數更新後數據重載失敗")
                        return False
                else:
                    print(f"[brake_MDI] ❌ 數據管理器未初始化")
                    return False
            else:
                print(f"[brake_MDI] ℹ️ 參數未變更，跳過數據重載")
                return True
                
        except Exception as e:
            print(f"[ERROR] [brake_MDI] update_lap_parameters 失敗: {str(e)}")
            return False
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            print(f"[brake_MDI] 更新brake圖表")
            if self.brake_chart_widget:
                self.brake_chart_widget.update_brake_data(data)
                
                # 更新工具欄狀態信息
                self._update_toolbar_status(data)
                
        except Exception as e:
            print(f"[ERROR] [brake_MDI] 圖表更新失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] [brake_MDI] {error_message}")
        self.module_error.emit(error_message)
    
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
            
            module_name = "brake分析"
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
            
            print(f"[brake_MDI] 已更新工具欄狀態: {module_name}")
            
        except Exception as e:
            print(f"[ERROR] [brake_MDI] 更新工具欄狀態失敗: {e}")
    
    def _get_main_window(self):
        """獲取主視窗引用"""
        try:
            # 通過MDI子視窗獲取主視窗
            if hasattr(self, '_sub_window') and self._sub_window:
                mdi_area = self._sub_window.parent()
                if mdi_area:
                    # 查找主視窗
                    widget = mdi_area.parent()
                    while widget and not hasattr(widget, 'update_toolbar_status'):
                        widget = widget.parent()
                    return widget
            return None
        except Exception as e:
            print(f"[ERROR] [brake_MDI] 獲取主視窗失敗: {e}")
            return None

    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更"""
        try:
            print(f"[brake_MDI] ========== 圈數變更處理 ==========")
            print(f"[brake_MDI] 新圈數: 第{lap1}圈 vs 第{lap2}圈")
            
            # 更新模組的圈數參數
            old_lap1, old_lap2 = self.lap1, self.lap2
            self.lap1 = lap1
            self.lap2 = lap2
            
            print(f"[brake_MDI] 圈數變更: 第{old_lap1}圈 vs 第{old_lap2}圈 → 第{lap1}圈 vs 第{lap2}圈")
            
            # 重新載入數據
            if self.data_manager:
                print(f"[brake_MDI] 🔄 因圈數變更重新載入數據...")
                success = self.data_manager.load_brake_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                
                if success:
                    print(f"[brake_MDI] ✅ 圈數變更後數據重載成功")
                else:
                    print(f"[brake_MDI] ❌ 圈數變更後數據重載失敗")
            else:
                print(f"[brake_MDI] ❌ 數據管理器未初始化，無法重載數據")
                
        except Exception as e:
            print(f"[ERROR] [brake_MDI] 處理圈數變更失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"處理圈數變更失敗: {str(e)}")
    
    def cleanup_module(self):
        """清理模組資源和信號連接"""
        try:
            print(f"[brake_MDI] 🧹 清理brake分析模組...")
            
            if self.data_manager:
                # 斷開所有信號連接
                try:
                    self.data_manager.data_loaded.disconnect()
                    self.data_manager.error_occurred.disconnect()
                    self.data_manager.loading_progress.disconnect()
                    self.data_manager.status_changed.disconnect()
                except Exception as e:
                    print(f"[WARNING] [brake_MDI] 斷開數據管理器信號時發生警告: {e}")
            
            if self.brake_chart_widget and hasattr(self.brake_chart_widget, 'lap_numbers_changed'):
                try:
                    self.brake_chart_widget.lap_numbers_changed.disconnect()
                except Exception as e:
                    print(f"[WARNING] [brake_MDI] 斷開圖表組件信號時發生警告: {e}")
            
            print(f"[brake_MDI] ✅ 模組清理完成")
                
        except Exception as e:
            print(f"[WARNING] [brake_MDI] 清理模組時發生警告: {e}")
    
    def cleanup(self):
        """清理資源 - 實現抽象方法"""
        try:
            # 從分析模組管理器解除註冊
            if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
                try:
                    # 解除註冊圖表組件
                    if hasattr(self, 'brake_chart_widget') and self.brake_chart_widget:
                        self._analysis_manager.unregister_chart_widget(self.brake_chart_widget)
                    
                    # 解除註冊模組
                    self._analysis_manager.unregister_module(self._module_id)
                    print(f"[brake_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                    
                except Exception as e:
                    print(f"[ERROR] [brake_MDI] 從分析模組管理器解除註冊失敗: {e}")
            
            # 調用模組清理
            self.cleanup_module()
            
            if hasattr(self, 'brake_chart_widget') and self.brake_chart_widget:
                # 清理圖表組件
                if hasattr(self.brake_chart_widget, 'cleanup'):
                    self.brake_chart_widget.cleanup()
                self.brake_chart_widget.deleteLater()
                
            if hasattr(self, 'main_widget') and self.main_widget:
                # 清理主要組件
                self.main_widget.deleteLater()
                
            print(f"[CLEANUP] brake分析模組資源清理完成")
        except Exception as e:
            print(f"[ERROR] brake分析模組清理失敗: {e}")
    
    # ========== 遙測分析整合功能 ==========
    
    def _ensure_telemetry_data_for_fastest_laps(self) -> Optional[Dict[str, int]]:
        """確保最速圈數據的遙測分析可用 - 與速度分析相同功能"""
        try:
            print(f"[brake_MDI] 🔍 檢查最速圈遙測數據可用性...")
            
            # 首先檢查是否已有遙測分析檔案
            telemetry_file = self._find_telemetry_analysis_file()
            
            if not telemetry_file:
                print(f"[brake_MDI] 📡 遙測分析數據不存在，開始自動載入...")
                success = self._check_and_load_telemetry_if_needed()
                if success:
                    # 重新檢查檔案
                    telemetry_file = self._find_telemetry_analysis_file()
                else:
                    print(f"[brake_MDI] ❌ 遙測分析載入失敗")
                    return None
            
            if telemetry_file:
                print(f"[brake_MDI] 📂 找到遙測分析檔案: {telemetry_file}")
                return self._extract_fastest_laps_from_telemetry(telemetry_file)
            else:
                print(f"[brake_MDI] ⚠️ 無法獲取遙測分析數據")
                return None
                
        except Exception as e:
            print(f"[ERROR] [brake_MDI] _ensure_telemetry_data_for_fastest_laps 失敗: {e}")
            return None
    
    def _find_telemetry_analysis_file(self) -> Optional[str]:
        """尋找遙測分析JSON檔案 - 與速度分析相同功能"""
        try:
            # 構建可能的檔案名稱模式
            year = self.current_year
            race = self.current_race.replace(' ', '_')
            session = self.current_session
            
            # 檢查JSON目錄
            json_dir = "json"
            if os.path.exists(json_dir):
                for filename in os.listdir(json_dir):
                    if (filename.startswith(f"telemetry_analysis_{year}_{race}_{session}") and 
                        filename.endswith('.json')):
                        full_path = os.path.join(json_dir, filename)
                        print(f"[brake_MDI] 📂 找到遙測分析檔案: {full_path}")
                        return full_path
            
            print(f"[brake_MDI] 📂 未找到遙測分析檔案")
            return None
            
        except Exception as e:
            print(f"[ERROR] [brake_MDI] _find_telemetry_analysis_file 失敗: {e}")
            return None
    
    def _trigger_telemetry_analysis(self) -> bool:
        """觸發遙測分析載入/生成 - 與速度分析相同功能"""
        try:
            print(f"[brake_MDI] 🚀 觸發遙測分析載入: {self.current_year} {self.current_race} {self.current_session}")
            
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
                            print(f"[brake_MDI] 🎯 找到現有遙測分析視窗: {window_title}")
                            # 激活並刷新遙測分析視窗
                            main_window.mdi_area.setActiveSubWindow(sub_window)
                            return True
                    
                    # 如果沒有遙測分析視窗，嘗試創建一個
                    print(f"[brake_MDI] 📡 嘗試創建遙測分析視窗...")
                    if hasattr(main_window, 'create_telemetry_analysis'):
                        main_window.create_telemetry_analysis()
                        return True
            
            # 方法2: 通過CLI生成遙測分析數據（Function 12）
            print(f"[brake_MDI] 🔧 通過CLI生成遙測分析數據（Function 12）...")
            return self._check_and_load_telemetry_if_needed()
            
        except Exception as e:
            print(f"[ERROR] [brake_MDI] _trigger_telemetry_analysis 失敗: {e}")
            return False
    
    def _extract_fastest_laps_from_telemetry(self, telemetry_file: str) -> Optional[Dict[str, int]]:
        """從遙測分析JSON檔案中提取最速圈數據 - 與速度分析相同功能"""
        try:
            print(f"[brake_MDI] 📊 從遙測分析中提取最速圈數據: {telemetry_file}")
            
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            fastest_laps = {}
            
            # 檢查遙測數據結構並提取最速圈信息
            if 'data' in telemetry_data and 'fastest_laps' in telemetry_data['data']:
                fastest_lap_data = telemetry_data['data']['fastest_laps']
                
                for driver_code, lap_info in fastest_lap_data.items():
                    if isinstance(lap_info, dict) and 'lap_number' in lap_info:
                        fastest_laps[driver_code] = lap_info['lap_number']
                    elif isinstance(lap_info, int):
                        fastest_laps[driver_code] = lap_info
            
            print(f"[brake_MDI] ✅ 最速圈數據提取完成: {fastest_laps}")
            return fastest_laps if fastest_laps else None
            
        except Exception as e:
            print(f"[ERROR] [brake_MDI] _extract_fastest_laps_from_telemetry 失敗: {e}")
            return None
    
    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數更新通知 - 與速度分析相同功能"""
        try:
            print(f"[brake_NOTIFICATION_DEBUG] ========== 收到主視窗更新通知 ==========")
            print(f"[brake_NOTIFICATION_DEBUG] 📡 原始參數:")
            print(f"[brake_NOTIFICATION_DEBUG]   - param_type: {param_type}")
            print(f"[brake_NOTIFICATION_DEBUG]   - value: {value}")
            
            # 更新內部狀態
            if param_type == "year":
                self.current_year = str(value)
                print(f"[UPDATE] 年份更新為: {self.current_year}")
            elif param_type == "race":
                self.current_race = value
                print(f"[UPDATE] 賽事更新為: {self.current_race}")
            elif param_type == "session":
                self.current_session = value
                print(f"[UPDATE] 場次更新為: {self.current_session}")
            
            print(f"[brake_NOTIFICATION_DEBUG] 📊 當前模組狀態:")
            print(f"[brake_NOTIFICATION_DEBUG]   - 當前年份: {self.current_year}")
            print(f"[brake_NOTIFICATION_DEBUG]   - 當前賽事: {self.current_race}")
            print(f"[brake_NOTIFICATION_DEBUG]   - 當前賽段: {self.current_session}")
            print(f"[brake_NOTIFICATION_DEBUG]   - 當前車手: {getattr(self, 'driver1', 'VER')} vs {getattr(self, 'driver2', 'VER')}")
            print(f"[brake_NOTIFICATION_DEBUG]   - 當前圈數: 第{getattr(self, 'lap1', 1)}圈 vs 第{getattr(self, 'lap2', 1)}圈")
            
            # 更新視窗標題
            self.update_window_title()
            
            # 重新載入數據 - 與速度分析模組保持一致
            if hasattr(self, 'data_manager') and self.data_manager:
                print(f"[REFRESH] 重新載入brake數據...")
                self.data_manager.load_brake_data(
                    year=int(self.current_year),
                    race=self.current_race,
                    session=self.current_session,
                    driver1=getattr(self, 'driver1', 'VER'),
                    driver2=getattr(self, 'driver2', 'VER'),
                    lap1=getattr(self, 'lap1', 1),
                    lap2=getattr(self, 'lap2', 1)
                )
            elif not hasattr(self, 'data_manager') or self.data_manager is None:
                print(f"[WARNING] 數據管理器未初始化，嘗試創建...")
                try:
                    self.data_manager = BrakeDataManager()
                    self.data_manager.data_loaded.connect(self._update_chart)
                    self.data_manager.error_occurred.connect(self._handle_error)
                    print(f"[OK] 數據管理器創建成功，開始載入數據...")
                    self.data_manager.load_brake_data(
                        year=int(self.current_year),
                        race=self.current_race,
                        session=self.current_session,
                        driver1=getattr(self, 'driver1', 'VER'),
                        driver2=getattr(self, 'driver2', 'VER'),
                        lap1=getattr(self, 'lap1', 1),
                        lap2=getattr(self, 'lap2', 1)
                    )
                except Exception as e:
                    print(f"[ERROR] 創建數據管理器失敗: {e}")
            else:
                print(f"[WARNING] 無法重新載入數據 - 數據管理器狀態異常")
            
            print(f"[OK] [NOTIFICATION] ⚡ brake分析模組內容更新成功")
            
        except Exception as e:
            print(f"[ERROR] [brake_MDI] receive_main_window_update_notification 失敗: {e}")
            import traceback
            traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據 - 實現抽象方法"""
        try:
            print(f"[brake_MDI] 匯出數據功能尚未實現 (路徑: {export_path}, 格式: {export_format})")
            return False
        except Exception as e:
            print(f"[ERROR] [brake_MDI] export_data 失敗: {e}")
            return False

        # ========== 實現抽象方法 ==========

    @property
    def module_name(self) -> str:
        """模組名稱"""
        return "brake_analysis"

    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return tr("brake_analysis", "煞車分析")

    @property
    def description(self) -> str:
        """模組描述"""
        return tr("brake_analysis_description", "F1賽車煞車分析模組，支援雙車手煞車對比")

    @property
    def version(self) -> str:
        """模組版本"""
        return "1.0.0"

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
                return self.data_manager.load_brake_data(
                    year=year, race=race, session=session,
                    driver1=driver1, driver2=driver2,
                    lap1=lap1, lap2=lap2, is_fastest=is_fastest
                )
            return False
        except Exception as e:
            print(f"[ERROR] [brake_MDI] load_data 失敗: {e}")
            return False

    def get_current_data(self) -> dict:
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
                'module_type': 'brake_analysis'
            }
        except Exception as e:
            print(f"[ERROR] [brake_MDI] get_current_data 失敗: {e}")
            return {}

    def clear_data(self) -> None:
        """清除數據 - 實現抽象方法"""
        try:
            print(f"[brake_MDI] 清除數據...")
            if self.brake_chart_widget and hasattr(self.brake_chart_widget, 'clear_chart'):
                self.brake_chart_widget.clear_chart()
            
            if self.status_label:
                self.status_label.setText(tr('cleared', '已清除'))
            
            if self.progress_bar:
                self.progress_bar.setVisible(False)
                
        except Exception as e:
            print(f"[ERROR] [brake_MDI] clear_data 失敗: {e}")

    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """更新分析參數 - 實現抽象方法"""
        try:
            print(f"[brake_PARAMS_DEBUG] ========== brake參數更新開始 ==========")
            print(f"[brake_PARAMS_DEBUG] 收到參數: year={year}, race={race}, session={session}")
            print(f"[brake_PARAMS_DEBUG] 當前參數: year={self.current_year}, race={self.current_race}, session={self.current_session}")
            
            # 檢查參數是否有變化
            old_year = str(self.current_year) if self.current_year else None
            old_race = self.current_race
            old_session = self.current_session
            
            new_year = str(year)
            new_race = race
            new_session = session
            
            params_changed = (
                old_year != new_year or 
                old_race != new_race or 
                old_session != new_session
            )
            
            print(f"[brake_PARAMS_DEBUG] 參數變化檢查: {params_changed}")
            print(f"[brake_PARAMS_DEBUG] 舊參數: {old_year} {old_race} {old_session}")
            print(f"[brake_PARAMS_DEBUG] 新參數: {new_year} {new_race} {new_session}")
            
            # 更新內部參數
            self.current_year = new_year
            self.current_race = new_race
            self.current_session = new_session
            
            # 更新視窗標題
            self.update_window_title()
            
            # 檢查是否需要載入數據
            print(f"[brake_PARAMS_DEBUG] 檢查數據載入需求...")
            if params_changed or not hasattr(self, '_data_loaded'):
                print(f"[brake_PARAMS_DEBUG] 需要載入數據：參數變化={params_changed}, 未載入過={not hasattr(self, '_data_loaded')}")
                
                # 重新載入數據 - 與速度分析模組保持一致
                if hasattr(self, 'data_manager') and self.data_manager:
                    print(f"[REFRESH] 重新載入brake數據...")
                    success = self.data_manager.load_brake_data(
                        year=int(self.current_year),
                        race=self.current_race,
                        session=self.current_session,
                        driver1=getattr(self, 'driver1', 'VER'),
                        driver2=getattr(self, 'driver2', 'VER'),
                        lap1=getattr(self, 'lap1', 1),
                        lap2=getattr(self, 'lap2', 1)
                    )
                    
                    if success:
                        self._data_loaded = True
                        print(f"[brake_PARAMS_DEBUG] ✅ brake 數據重載成功")
                        return True
                    else:
                        print(f"[brake_PARAMS_DEBUG] ❌ brake 數據重載失敗")
                        return False
                else:
                    # 檢查並創建數據管理器
                    print(f"[brake_PARAMS_DEBUG] 數據管理器不存在，嘗試創建...")
                    try:
                        self.data_manager = BrakeDataManager()
                        self.data_manager.data_loaded.connect(self._update_chart)
                        self.data_manager.error_occurred.connect(self._handle_error)
                        print(f"[brake_PARAMS_DEBUG] ✅ 數據管理器創建成功，開始載入數據...")
                        
                        success = self.data_manager.load_brake_data(
                            year=int(self.current_year),
                            race=self.current_race,
                            session=self.current_session,
                            driver1=getattr(self, 'driver1', 'VER'),
                            driver2=getattr(self, 'driver2', 'VER'),
                            lap1=getattr(self, 'lap1', 1),
                            lap2=getattr(self, 'lap2', 1)
                        )
                        
                        if success:
                            self._data_loaded = True
                            print(f"[brake_PARAMS_DEBUG] ✅ brake 數據載入成功")
                            return True
                        else:
                            print(f"[brake_PARAMS_DEBUG] ❌ brake 數據載入失敗")
                            return False
                            
                    except Exception as e:
                        print(f"[brake_PARAMS_DEBUG] ❌ 數據管理器創建失敗: {e}")
                        print(f"[brake_PARAMS_DEBUG] ⚠️ 參數更新完成（無數據載入）: {self.current_year} {self.current_race} {self.current_session}")
                        return False
            else:
                print(f"[brake_PARAMS_DEBUG] 跳過數據載入：參數無變化且已載入過")
                return True
            
        except Exception as e:
            print(f"[ERROR] [brake_PARAMS_DEBUG] update_parameters 失敗: {e}")
            print(f"[ERROR] [brake_PARAMS_DEBUG] update_parameters 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def refresh_analysis(self) -> None:
        """重新分析 - 實現抽象方法"""
        try:
            print(f"[brake_MDI] 重新分析...")
            self._refresh_data()
        except Exception as e:
            print(f"[ERROR] [brake_MDI] refresh_analysis 失敗: {e}")

# 主程式測試
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試brake分析模組
    module = BrakeAnalysisModule()
    if module.initialize_module():
        widget = module.get_widget()
        widget.setWindowTitle(module.get_window_title())
        widget.resize(*module.get_default_size())
        widget.show()
        
        # 測試數據載入
        module._refresh_data()
        
        sys.exit(app.exec_())
    else:
        print("模組初始化失敗")
        sys.exit(1)

# 註冊brake分析模組到工廠
try:
    from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
    ModuleFactory.register_module(ModuleTypes.TELEMETRY_BRAKE, BrakeAnalysisModule)
    print(f"[OK] [MODULE_FACTORY] brake分析模組已註冊")
except ImportError as e:
    print(f"[WARNING] [MODULE_FACTORY] brake分析模組註冊失敗: {e}")
