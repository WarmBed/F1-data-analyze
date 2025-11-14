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
from modules.gui.interfaces.analysis_module import IAnalysisModule
from core.gui_i18n import tr
from core.api_base_url import resolve_api_base_url
import requests
import time

class CrossEventComparisonWorker(QThread):
    """跨賽事比較 API Worker - 調用 /api/v2/analysis/cross-event-comparison 端點（RPM 版本）"""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, driver1: str, year1: int, race1: str, session1: str, lap1: int,
                 driver2: str, year2: int, race2: str, session2: str, lap2: int,
                 force_refresh: bool = False, timeout: float = 120.0, parent=None):
        super().__init__(parent)
        self.driver1 = driver1
        self.year1 = year1
        self.race1 = race1
        self.session1 = session1
        self.lap1 = lap1
        
        self.driver2 = driver2
        self.year2 = year2
        self.race2 = race2
        self.session2 = session2
        self.lap2 = lap2
        
        self.force_refresh = force_refresh
        self.timeout = timeout
        self.base_url = resolve_api_base_url().rstrip('/')

    def run(self):
        try:
            self.progress.emit(20)
            endpoint = f"{self.base_url}/api/v2/analysis/cross-event-comparison"
            
            # 構建請求參數（RPM 分析）
            query_params: Dict[str, Any] = {
                "driver1": self.driver1,
                "year1": int(self.year1),
                "race1": self.race1,
                "session1": self.session1,
                "lap1": self.lap1,
                "driver2": self.driver2,
                "year2": int(self.year2),
                "race2": self.race2,
                "session2": self.session2,
                "lap2": self.lap2,
                "analysis_type": "rpm"  # 指定 RPM 分析
            }
            
            if self.force_refresh:
                query_params["force_refresh"] = True

            print(f"[RPM-CROSS-EVENT-WORKER] 請求 API: {endpoint}")
            print(f"[RPM-CROSS-EVENT-WORKER] 參數: {query_params}")
            
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(70)
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))

            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")

            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            meta = {
                "source": "cross_event_api",
                "cross_event": True,
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }

            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            print(f"[RPM-CROSS-EVENT-WORKER] ❌ 請求失敗: {exc}")
            import traceback
            traceback.print_exc()
            self.failure.emit(str(exc))
            
        finally:
            self.progress.emit(100)


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
        self.module_ref = None
        
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

            # 保存當前上下文，以供遙測資料檢查
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # 檢查最速圈選項並自動載入遙測分析
            if is_fastest or lap1 == "fastest" or lap2 == "fastest":
                print(f"🔄 [RPM_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")
                self._check_and_load_telemetry_if_needed()
                
                # 解析最速圈參數為實際圈數
                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)
                print(f"🔢 [RPM_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")
            
            print(f"[RPM_MDI_DATA] 🔗 創建 RPMAnalysisDataLoader...")
            
            # 使用現有的RPM分析數據載入器
            from .rpm_analysis_data_loader import RPMAnalysisDataLoader
            
            print(f"[RPM_MDI_DATA] 🚀 調用 load_rpm_data...")
            
            # 創建數據載入器並保存為實例變量防止垃圾回收
            self.rpm_loader = RPMAnalysisDataLoader()
            self.rpm_loader.data_loaded.connect(self._on_data_loaded)
            self.rpm_loader.load_error.connect(self._on_load_error)
            self.rpm_loader.status_changed.connect(self.status_changed.emit)
            self.rpm_loader.load_progress.connect(self.loading_progress.emit)
            
            # 開始載入數據
            success = self.rpm_loader.load_rpm_data(
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
            if hasattr(self, 'rpm_chart_widget') and self.rpm_chart_widget:
                self.rpm_chart_widget.rpm_loader = self.rpm_loader
                print(f"[RPM_MDI] ✅ 已將loader設置給chart widget")
            
            if success:
                print(f"[RPM_MDI_DATA] ✅ RPM數據載入請求提交成功")
                self.loading_progress.emit(50)
                return True
            else:
                print(f"[RPM_MDI_DATA] ❌ RPM數據載入請求失敗")
                self._is_loading = False
                self.error_occurred.emit("RPM數據載入請求失敗")
                return False
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI_DATA] 載入RPM數據時發生錯誤: {e}")
            self._is_loading = False
            self.error_occurred.emit(f"載入RPM數據失敗: {str(e)}")
            return False
    
    def _on_data_loaded(self, data):
        """數據載入完成回調"""
        try:
            print(f"[RPM_MDI_DATA] ✅ RPM數據載入完成")
            self._is_loading = False
            self.loading_progress.emit(100)
            self.status_changed.emit("RPM數據載入完成")
            self.data_loaded.emit(data)
        except Exception as e:
            print(f"[ERROR] [RPM_MDI_DATA] 處理載入完成回調時發生錯誤: {e}")
            self._on_load_error(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_msg):
        """數據載入錯誤回調"""
        print(f"[RPM_MDI_DATA] ❌ RPM數據載入錯誤: {error_msg}")
        self._is_loading = False
        self.loading_progress.emit(0)
        self.status_changed.emit(f"載入失敗: {error_msg}")
        self.error_occurred.emit(error_msg)
    
    def _check_and_load_telemetry_if_needed(self):
        """檢查遙測分析數據（最速圈用）"""
        try:
            print(f"[RPM_MDI_DATA] 🔍 檢查遙測分析數據可用性...")

            module_ref = getattr(self, "module_ref", None)
            if module_ref:
                return module_ref._check_and_load_telemetry_if_needed(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )

            telemetry_patterns = [
                f"all_drivers_telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"all_drivers_telemetry_analysis_{self.current_year}_{self.current_race}.json"
            ]

            search_dirs = ["json", "json_exports", "cache"]
            for directory in search_dirs:
                if os.path.exists(directory):
                    for pattern in telemetry_patterns:
                        file_path = os.path.join(directory, pattern)
                        if os.path.exists(file_path):
                            print(f"📁 [RPM_MDI_DATA] 找到現有遙測檔案: {file_path}")
                            return True

            print("⚠️ [RPM_MDI_DATA] API-ONLY 模式下未找到遙測檔案，請透過主視窗遙測模組或 REST API 取得資料")
            return False

        except Exception as e:
            print(f"❌ [RPM_MDI_DATA] 檢查遙測數據時發生錯誤: {e}")
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

    def cleanup(self):
        """
        清理 RPMDataManager 資源
        
        修復記憶體洩漏：清理 TelemetryDataLoader 的 API Worker 執行緒
        """
        try:
            print(f"[RPMDATAMANAGER] 🧹 開始清理資源...")
            
            # 1. 清理 TelemetryDataLoader 及其 QThread
            if hasattr(self, '_speed_loader') and self._speed_loader:
                try:
                    # 調用 loader 的 cleanup() 方法（清理 API worker 執行緒）
                    if hasattr(self._speed_loader, 'cleanup'):
                        self._speed_loader.cleanup()
                        print(f"[RPMDATAMANAGER] ✅ 已清理 loader 執行緒")
                    
                    # 斷開信號連接
                    try:
                        self._speed_loader.data_loaded.disconnect()
                    except Exception:
                        pass
                    try:
                        self._speed_loader.load_error.disconnect()
                    except Exception:
                        pass
                    try:
                        self._speed_loader.status_changed.disconnect()
                    except Exception:
                        pass
                    try:
                        self._speed_loader.load_progress.disconnect()
                    except Exception:
                        pass
                    
                    # 標記為待刪除
                    self._speed_loader.deleteLater()
                    self._speed_loader = None
                    
                except Exception as e:
                    print(f"[ERROR] [RPMDATAMANAGER] 清理 loader 失敗: {e}")
            
            # 🔴 關鍵修復：斷開循環引用（data_manager ← module_ref → module）
            if hasattr(self, 'module_ref') and self.module_ref:
                print(f"[RPMDATAMANAGER] 🔴 斷開循環引用：清理 data_manager.module_ref")
                self.module_ref = None
            
            # 2. 清理內部狀態
            self.current_year = None
            self.current_race = None
            self.current_session = None
            self._is_loading = False
            
            print(f"[RPMDATAMANAGER] ✅ 資源清理完成")
            
        except Exception as e:
            print(f"[ERROR] [RPMDATAMANAGER] cleanup() 失敗: {e}")
            import traceback
            traceback.print_exc()


class RPMAnalysisModule(IAnalysisModule):
    """RPM分析主模組"""
    
    # 信號定義 - 與速度模組保持一致
    module_error = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 設置分析類型（用於批次更新識別）
        self.analysis_type = 'rpm'
        
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
        
        # ⚠️ [全域共享參數池] 循環更新防護
        self._updating_from_shared = False   # 防止遞迴更新
        
        # 🔧 [DRIVER_LAP_SYNC] 車手與圈數同步控制（顯示標題欄按鈕的關鍵屬性）
        self.sync_driver_lap_enabled = True  # 預設啟用同步
        
        # ⚠️ [跨賽事比較] 支援跨年度/跨賽段參數（但暫不實作跨賽事比較功能）
        self.driver1_year = "2025"
        self.driver1_race = "Japan"
        self.driver1_session = "R"
        self.driver2_year = "2025"
        self.driver2_race = "Japan"
        self.driver2_session = "R"
        self.use_cross_event_comparison = False  # 是否為跨賽事比較模式
        self.use_time_axis = False  # 時間軸模式
        
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
            print(f"[RPM_MDI] 初始化RPM分析模組")
            
            # 創建數據管理器
            self.data_manager = RPMDataManager()
            self.data_manager.module_ref = self
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            
            # 創建RPM圖表組件
            from .rpm_analysis_chart_widget import RPMAnalysisChartWidget
            self.rpm_chart_widget = RPMAnalysisChartWidget()
            
            # 連接圈數變更信號
            self.rpm_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
            
            # 設置初始圈數
            self.rpm_chart_widget.set_lap_numbers(self.lap1, self.lap2)
            
            # 設置主界面
            self._setup_ui()
            
            # 註冊到分析模組管理器
            try:
                from ..analysis_module_manager import get_analysis_module_manager
                manager = get_analysis_module_manager()
                
                # 註冊模組
                module_id = f"rpm_analysis_{id(self)}"
                manager.register_module(module_id, self, "rpm_analysis")
                
                # 註冊圖表組件
                if self.rpm_chart_widget:
                    manager.register_chart_widget(self.rpm_chart_widget)
                
                # 保存管理器引用和模組ID
                self._analysis_manager = manager
                self._module_id = module_id
                
                print(f"[RPM_MDI] ✅ 已註冊到分析模組管理器: {module_id}")
                
            except ImportError as e:
                print(f"[WARNING] [RPM_MDI] 無法導入分析模組管理器: {e}")
                self._analysis_manager = None
                self._module_id = None
            except Exception as e:
                print(f"[ERROR] [RPM_MDI] 註冊到分析模組管理器失敗: {e}")
                self._analysis_manager = None
                self._module_id = None
            
            self._initialized = True
            print(f"[OK] [RPM_MDI] RPM分析模組初始化完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 模組初始化失敗: {e}")
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
        """創建佔位組件（當RPM圖表組件不可用時）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("🔄 RPM分析圖表")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16pt; padding: 20px;")
        layout.addWidget(label)
        
        info_label = QLabel("RPM圖表組件正在載入中...")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        return widget
    
    def _setup_ui(self):
        """設置用戶界面"""
        # 創建主容器 widget
        self.main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # ⚠️ [參數資訊標籤] 新增：參數資訊標籤（淺色背景）
        # 複製自 Speed Analysis 模組
        self.info_label = QLabel()
        self.info_label.setObjectName("AnalysisInfoLabel")
        self.info_label.setStyleSheet("""
            QLabel#AnalysisInfoLabel {
                background-color: #F0F0F0;
                color: #333333;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11pt;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.info_label.setWordWrap(True)
        self._update_info_label()  # 初始化標籤內容
        layout.addWidget(self.info_label)
        
        # 添加RPM圖表
        if self.rpm_chart_widget:
            layout.addWidget(self.rpm_chart_widget)
        
        # 設置佈局到主 widget
        self.main_widget.setLayout(layout)
    
    def _update_info_label(self):
        """更新參數資訊標籤（只在取消同步時顯示）"""
        try:
            # 檢查同步狀態
            sync_enabled = getattr(self, 'sync_driver_lap_enabled', True)
            
            if sync_enabled:
                # 同步模式：隱藏資訊標籤
                if hasattr(self, 'info_label'):
                    self.info_label.hide()
                print(f"[RPM_MDI] 同步模式：隱藏資訊標籤")
                return
            
            # 取消同步模式：顯示資訊標籤
            if hasattr(self, 'info_label'):
                self.info_label.show()
            
            # 獲取當前參數
            year1 = getattr(self, 'driver1_year', self.current_year)
            race1 = getattr(self, 'driver1_race', self.current_race)
            session1 = getattr(self, 'driver1_session', self.current_session)
            driver1 = self.driver1
            lap1 = self.lap1
            
            year2 = getattr(self, 'driver2_year', self.current_year)
            race2 = getattr(self, 'driver2_race', self.current_race)
            session2 = getattr(self, 'driver2_session', self.current_session)
            driver2 = self.driver2
            lap2 = self.lap2
            
            # 檢測是否為跨賽事比較
            is_cross_event = (year1 != year2) or (session1 != session2)
            
            if is_cross_event:
                # 跨賽事比較格式
                driver1_label = tr("driver_1_info", "Driver 1:")
                driver2_label = tr("driver_2_info", "Driver 2:")
                versus_label = tr("versus", "vs")
                info_text = (
                    f"<b>{driver1_label}</b> {year1} {race1} {session1} - {driver1} Lap {lap1}  "
                    f"<b style='color: #999;'>{versus_label}</b>  "
                    f"<b>{driver2_label}</b> {year2} {race2} {session2} - {driver2} Lap {lap2}"
                )
            else:
                # 標準比較格式
                race_label = tr("race_info", "Race:")
                driver_label = tr("driver_info", "Driver:")
                versus_label = tr("versus", "vs")
                info_text = (
                    f"<b>{race_label}</b> {year1} {race1} {session1}  |  "
                    f"<b>{driver_label}</b> {driver1} (Lap {lap1}) {versus_label} {driver2} (Lap {lap2})"
                )
            
            self.info_label.setText(info_text)
            print(f"[RPM_MDI] 取消同步模式：顯示資訊標籤")
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 更新資訊標籤失敗: {e}")
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            print(f"[RPM_MDI] ========== 更新RPM圖表回調 ==========")
            print(f"[RPM_MDI] 📦 接收到數據類型: {type(data)}")
            print(f"[RPM_MDI] 📦 接收到數據鍵值: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if isinstance(data, dict) and 'rpm_data' in data:
                rpm_data = data['rpm_data']
                print(f"[RPM_MDI] 📊 rpm_data 鍵值: {list(rpm_data.keys())}")
                print(f"[RPM_MDI] 📊 distance 點數: {len(rpm_data.get('distance', []))}")
                print(f"[RPM_MDI] 📊 driver1_rpm 點數: {len(rpm_data.get('driver1_rpm', []))}")
                print(f"[RPM_MDI] 📊 driver2_rpm 點數: {len(rpm_data.get('driver2_rpm', []))}")
            
            if self.rpm_chart_widget:
                print(f"[RPM_MDI] 🎨 調用 rpm_chart_widget.update_rpm_data...")
                self.rpm_chart_widget.update_rpm_data(data)
                print(f"[RPM_MDI] ✅ 圖表更新完成")
                
                # 更新工具欄狀態信息
                self._update_toolbar_status(data)
            else:
                print(f"[RPM_MDI] ❌ rpm_chart_widget 未初始化")
                
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（RPMAnalysisModule 實例）
            print(f"[ERROR] [RPM_MDI] 圖表更新失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def get_widget(self) -> QWidget:
        """獲取主要UI組件"""
        return self.main_widget if self.main_widget else QWidget()
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 只顯示模組名稱，不包含年份/賽事/賽段"""
        title = f"{tr('rpm_analysis', 'RPM分析')}"
        
        print(f"[RPM_TITLE_DEBUG] 🏷️ 生成視窗標題: '{title}'")
        return title
        return title
    
    def update_window_title(self) -> None:
        """更新視窗標題"""
        try:
            print(f"[RPM_TITLE_DEBUG] 🔄 開始更新視窗標題...")
            print(f"[RPM_TITLE_DEBUG] 📋 當前狀態檢查:")
            
            # 檢查 parent_window 屬性（MDI 子視窗引用）
            parent = getattr(self, 'parent_window', None)
            print(f"[RPM_TITLE_DEBUG]   - parent_window 存在: {parent is not None}")
            
            if parent and hasattr(parent, 'setWindowTitle'):
                old_title = parent.windowTitle()
                print(f"[RPM_TITLE_DEBUG]   - 舊標題: '{old_title}'")
                
                new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                print(f"[RPM_TITLE_DEBUG]   - 新標題: '{new_title}'")
                
                if old_title != new_title:
                    print(f"[RPM_TITLE_DEBUG] 🔄 標題需要更新，執行更新...")
                    
                    # 直接更新標題
                    parent.setWindowTitle(new_title)
                    
                    # 驗證更新結果
                    updated_title = parent.windowTitle()
                    print(f"[RPM_TITLE_DEBUG] ✅ 標題更新完成: '{updated_title}'")
                    
                    # 如果直接更新失敗，使用延遲更新
                    if updated_title != new_title:
                        print(f"[RPM_TITLE_DEBUG] ⚠️ 直接更新失敗，嘗試延遲更新...")
                        self._delayed_title_update(new_title)
                else:
                    print(f"[RPM_TITLE_DEBUG] ✅ 標題無需更新")
            else:
                print(f"[RPM_TITLE_DEBUG] ⚠️ 無法更新標題:")
                print(f"[RPM_TITLE_DEBUG]   - parent_window: {parent}")
                print(f"[RPM_TITLE_DEBUG]   - 有setWindowTitle方法: {hasattr(parent, 'setWindowTitle') if parent else False}")
        
        except Exception as e:
            print(f"[ERROR] [RPM_TITLE_DEBUG] 更新視窗標題失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _delayed_title_update(self, title: str) -> None:
        """延遲標題更新 - 採用進站分析模式"""
        print(f"[RPM_TITLE_DEBUG] ⏰ 啟動延遲標題更新: '{title}'")
        
        def update_title():
            try:
                if self.parent_window and hasattr(self.parent_window, 'setWindowTitle'):
                    self.parent_window.setWindowTitle(title)
                    final_title = self.parent_window.windowTitle()
                    print(f"[RPM_TITLE_DEBUG] ✅ 延遲更新完成: '{final_title}'")
                else:
                    print(f"[RPM_TITLE_DEBUG] ❌ 延遲更新失敗: parent_window 不可用")
            except Exception as e:
                print(f"[ERROR] [RPM_TITLE_DEBUG] 延遲更新異常: {e}")
        
        # 使用QTimer延遲執行
        QTimer.singleShot(100, update_title)
    
    def get_default_size(self) -> tuple:
        """獲取預設視窗大小"""
        return (1000, 700)  # RPM分析需要較大的視窗來顯示詳細圖表

    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False,
                            use_time_axis: bool = False) -> bool:
        """更新圈速分析參數（包含車手和圈數）- 與速度模組一致的接口"""
        try:
            print(f"[RPM_MDI] ========== 圈速參數更新 ==========")
            print(f"[RPM_MDI] 收到參數: {year} {race} {session}")
            print(f"[RPM_MDI] 車手: {driver1} vs {driver2}")
            print(f"[RPM_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
            print(f"[RPM_MDI] 最速圈: {is_fastest}")
            print(f"🕒 [TIME_AXIS_DEBUG] 步驟 4: MDI 收到 use_time_axis 參數")
            print(f"🕒 [TIME_AXIS_DEBUG]   use_time_axis 參數值: {use_time_axis}")
            print(f"[RPM_MDI] ⏱️  使用時間軸: {use_time_axis}")
            
            # 儲存時間軸設定
            self.use_time_axis = use_time_axis
            print(f"🕒 [TIME_AXIS_DEBUG]   self.use_time_axis 已儲存: {self.use_time_axis}")
            
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
                self.driver2 != driver2 or  # 正確處理 None 值比較
                self.lap1 != lap1 or
                self.lap2 != lap2
            )
            
            print(f"[RPM_MDI] 參數是否變化: {params_changed}")
            
            # 更新所有參數 - 保持 driver2 的原始值（包括 None）
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.driver1 = driver1
            self.driver2 = driver2  # 保持原始值，支援單場賽事車手分析
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
                        
                        # 應用時間軸設定到圖表
                        print(f"🕒 [TIME_AXIS_DEBUG] 步驟 5: 準備設置圖表時間軸模式")
                        print(f"🕒 [TIME_AXIS_DEBUG]   self.rpm_chart_widget 存在: {self.rpm_chart_widget is not None}")
                        if self.rpm_chart_widget:
                            print(f"🕒 [TIME_AXIS_DEBUG]   hasattr(rpm_chart_widget, 'set_time_axis_mode'): {hasattr(self.rpm_chart_widget, 'set_time_axis_mode')}")
                        
                        if self.rpm_chart_widget and hasattr(self.rpm_chart_widget, 'set_time_axis_mode'):
                            print(f"🕒 [TIME_AXIS_DEBUG]   調用 rpm_chart_widget.set_time_axis_mode({use_time_axis})")
                            self.rpm_chart_widget.set_time_axis_mode(use_time_axis)
                            print(f"[RPM_MDI] ⏱️  已設置圖表時間軸模式: {use_time_axis}")
                            print(f"🕒 [TIME_AXIS_DEBUG]   ✅ set_time_axis_mode 調用完成")
                        else:
                            print(f"🕒 [TIME_AXIS_DEBUG]   ❌ 無法調用 set_time_axis_mode (widget不存在或方法不存在)")
                        
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
                        
                        # ✅ 修復：更新資訊標籤
                        self._update_info_label()
                        print(f"[RPM_MDI] 📋 已更新資訊標籤")
                        
                        # ✅ 修復：更新視窗標題（與 Speed Analysis 一致）
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
                print(f"[RPM_MDI] ℹ️ 參數未變更，跳過數據重載")
                return True
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] update_lap_parameters 失敗: {str(e)}")
            return False
    
    def update_cross_event_comparison(self, year1: str, race1: str, session1: str, driver1: str, lap1: int,
                                     year2: str, race2: str, session2: str, driver2: str, lap2: int,
                                     is_fastest: bool = False, use_time_axis: bool = False) -> bool:
        """更新跨賽事比較參數（支援跨年度/跨賽段） - RPM Analysis 版本"""
        try:
            print(f"[RPM-CROSS-EVENT] ========== 跨賽事比較更新 ==========")
            print(f"[RPM-CROSS-EVENT] 車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
            print(f"[RPM-CROSS-EVENT] 車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
            print(f"[RPM-CROSS-EVENT] 🕒 時間軸模式: {use_time_axis}")
            
            # 保存跨賽事比較的參數
            self.driver1_year = year1
            self.driver1_race = race1
            self.driver1_session = session1
            self.driver1 = driver1
            self.lap1 = lap1
            
            self.driver2_year = year2
            self.driver2_race = race2
            self.driver2_session = session2
            self.driver2 = driver2
            self.lap2 = lap2
            
            # ⚠️ 關鍵：跨賽事比較時停用同步，避免被 Update All Analysis 覆蓋
            self.sync_driver_lap_enabled = False
            print(f"[RPM-CROSS-EVENT] ⚠️ 已停用同步模式 (sync_driver_lap_enabled = False)")
            
            # 保存時間軸設定
            self.use_time_axis = use_time_axis
            print(f"[RPM-CROSS-EVENT] 🕒 已保存時間軸設定: use_time_axis={use_time_axis}")
            
            # 更新資訊標籤（顯示跨賽事比較資訊）
            self._update_info_label()
            
            # 實作跨賽事比較邏輯：調用 API 端點
            print(f"[RPM-CROSS-EVENT] 開始調用 API 端點: /api/v2/analysis/cross-event-comparison")
            
            # 創建 API Worker
            api_worker = CrossEventComparisonWorker(
                driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
                driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
                force_refresh=False,
                timeout=120
            )
            
            # 連接信號
            api_worker.success.connect(self._on_cross_event_data_loaded)
            api_worker.failure.connect(self._on_cross_event_load_error)
            api_worker.progress.connect(self._on_api_progress)
            
            # 啟動 Worker
            api_worker.start()
            
            print(f"[RPM-CROSS-EVENT] API 請求已啟動")
            return True
                
        except Exception as e:
            print(f"[ERROR] [RPM-CROSS-EVENT] 跨賽事比較更新失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _on_api_progress(self, value: int) -> None:
        """處理 API 請求進度"""
        try:
            # 如果模組有進度信號，轉發進度
            if hasattr(self, 'loading_progress'):
                bounded = max(0, min(int(value), 100))
                # 不要發送信號，避免干擾現有的載入進度
                # self.loading_progress.emit(bounded)
                pass
        except Exception:
            pass
    
    def _on_cross_event_data_loaded(self, result: Dict[str, Any]) -> None:
        """處理跨賽事比較數據載入成功 - RPM Analysis 版本"""
        try:
            print(f"[RPM-CROSS-EVENT] ✅ 數據載入成功")
            
            # 提取數據
            data = result.get("data", {})
            meta = result.get("meta", {})
            
            print(f"[RPM-CROSS-EVENT] 數據鍵值: {list(data.keys())}")
            print(f"[RPM-CROSS-EVENT] 元數據: {meta}")
            
            # 檢查是否有遙測比較數據
            if "telemetry_comparison" in data:
                telemetry_comp = data["telemetry_comparison"]
                print(f"[RPM-CROSS-EVENT] 遙測參數: {list(telemetry_comp.keys())}")
                
                # 提取 RPM 數據（如果存在）
                if "RPM" in telemetry_comp:
                    rpm_telemetry = telemetry_comp["RPM"]
                    
                    # 構建符合 _update_chart 期望的數據格式
                    chart_data = {
                        "rpm_data": {
                            "distance": rpm_telemetry.get("distance", []),
                            "driver1_rpm": rpm_telemetry.get("driver1_data", []),
                            "driver2_rpm": rpm_telemetry.get("driver2_data", []),
                            # 🆕 新增時間數據
                            "driver1_time_seconds": rpm_telemetry.get("driver1_time_seconds", []),
                            "driver2_time_seconds": rpm_telemetry.get("driver2_time_seconds", []),
                        },
                        "comparison_info": data.get("comparison_info", {}),
                        "cross_event_metadata": data.get("cross_event_metadata", {}),
                        "use_time_axis": getattr(self, 'use_time_axis', False),  # 傳遞時間軸設定
                    }
                    
                    print(f"[RPM-CROSS-EVENT] 構建圖表數據:")
                    print(f"[RPM-CROSS-EVENT]   距離點數: {len(chart_data['rpm_data']['distance'])}")
                    print(f"[RPM-CROSS-EVENT]   車手1 RPM點數: {len(chart_data['rpm_data']['driver1_rpm'])}")
                    print(f"[RPM-CROSS-EVENT]   車手2 RPM點數: {len(chart_data['rpm_data']['driver2_rpm'])}")
                    print(f"[RPM-CROSS-EVENT]   車手1 時間點數: {len(chart_data['rpm_data']['driver1_time_seconds'])}")
                    print(f"[RPM-CROSS-EVENT]   車手2 時間點數: {len(chart_data['rpm_data']['driver2_time_seconds'])}")
                    print(f"[RPM-CROSS-EVENT]   🕒 時間軸模式: {chart_data['use_time_axis']}")
                    
                    # ⚠️ 關鍵：先設置時間軸模式，再更新圖表
                    use_time_axis = chart_data.get('use_time_axis', False)
                    if self.rpm_chart_widget and hasattr(self.rpm_chart_widget, 'set_time_axis_mode'):
                        print(f"[RPM-CROSS-EVENT] 🕒 設置圖表時間軸模式: {use_time_axis}")
                        self.rpm_chart_widget.set_time_axis_mode(use_time_axis)
                    
                    # 直接調用圖表更新方法
                    print(f"[RPM-CROSS-EVENT] 開始更新圖表...")
                    self._update_chart(chart_data)
                    print(f"[RPM-CROSS-EVENT] ✅ 跨賽事比較完成")
                else:
                    print(f"[WARNING] [RPM-CROSS-EVENT] API 回應中沒有 RPM 遙測數據")
                    self.module_error.emit("跨賽事比較失敗: API 回應中沒有 RPM 數據")
            else:
                print(f"[WARNING] [RPM-CROSS-EVENT] API 回應中沒有 telemetry_comparison")
                self.module_error.emit("跨賽事比較失敗: API 回應格式錯誤")
                
        except Exception as e:
            print(f"[ERROR] [RPM-CROSS-EVENT] 數據處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"跨賽事比較數據處理失敗: {str(e)}")
    
    def _on_cross_event_load_error(self, error_msg: str) -> None:
        """處理跨賽事比較數據載入錯誤"""
        try:
            print(f"[ERROR] [RPM-CROSS-EVENT] 數據載入失敗: {error_msg}")
            self.module_error.emit(f"跨賽事比較失敗: {error_msg}")
        except Exception as e:
            print(f"[ERROR] [RPM-CROSS-EVENT] 錯誤處理失敗: {e}")
    
    def update_from_shared_params(self, params: dict):
        """
        從全域共享參數池更新參數（跨模組同步功能）
        
        當用戶取消勾選"與主視窗同步車手與圈數"時，此方法會被主 GUI 調用
        所有停用同步的視窗（Speed/RPM/Gear 等）會共享同一組參數
        
        參數：
        - params: 全域共享參數字典
          {
              'year1': str,      # 車手 1 年份
              'race1': str,      # 車手 1 賽事
              'session1': str,   # 車手 1 賽段
              'driver1': str,    # 車手 1 代號
              'lap1': int,       # 車手 1 圈數
              'year2': str,      # 車手 2 年份
              'race2': str,      # 車手 2 賽事
              'session2': str,   # 車手 2 賽段
              'driver2': str,    # 車手 2 代號
              'lap2': int,       # 車手 2 圈數
              'use_time_axis': bool  # 時間軸模式
          }
        """
        if self._updating_from_shared:
            print(f"[RPM_MDI] [SHARED_PARAMS] ⚠️  正在更新中，防止遞迴")
            return
        
        self._updating_from_shared = True
        try:
            print(f"[RPM_MDI] [SHARED_PARAMS] 🔄 從全域共享池更新參數")
            print(f"[RPM_MDI] [SHARED_PARAMS] 收到參數: {params}")
            
            # ✅ 修復：使用局部變數接收參數（避免提前覆蓋 self 屬性）
            year1 = params.get('year1', self.driver1_year)
            race1 = params.get('race1', self.driver1_race)
            session1 = params.get('session1', self.driver1_session)
            driver1 = params.get('driver1', self.driver1)
            lap1 = params.get('lap1', self.lap1)
            
            year2 = params.get('year2', self.driver2_year)
            race2 = params.get('race2', self.driver2_race)
            session2 = params.get('session2', self.driver2_session)
            driver2 = params.get('driver2', self.driver2)
            lap2 = params.get('lap2', self.lap2)
            
            use_time_axis = params.get('use_time_axis', self.use_time_axis)
            
            # 檢測是否為跨賽事比較（使用局部變數檢查）
            is_cross_event = (year1 != year2 or session1 != session2)
            
            if is_cross_event:
                print(f"[RPM_MDI] [SHARED_PARAMS] 🌍 檢測到跨賽事比較:")
                print(f"[RPM_MDI] [SHARED_PARAMS]   車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
                print(f"[RPM_MDI] [SHARED_PARAMS]   車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
                
                # ✅ RPM 模組已支援跨賽事比較
                print(f"[RPM_MDI] [SHARED_PARAMS] ✅ RPM 模組支援跨賽事比較功能")
                print(f"[RPM_MDI] [SHARED_PARAMS] � 將通過全域參數池更新")
                
                # 更新 self 屬性（使用車手 1 的參數）
                self.driver1_year = year1
                self.driver1_race = race1
                self.driver1_session = session1
                self.driver1 = driver1
                self.lap1 = lap1
                
                self.driver2_year = year2
                self.driver2_race = race2
                self.driver2_session = session2
                self.driver2 = driver2
                self.lap2 = lap2
                
                self.use_time_axis = use_time_axis
                
                # 使用車手 1 的參數進行標準分析
                self.current_year = year1
                self.current_race = race1
                self.current_session = session1
            else:
                # 標準模式（同一賽事比較）
                print(f"[RPM_MDI] [SHARED_PARAMS] ✅ 標準比較模式:")
                print(f"[RPM_MDI] [SHARED_PARAMS]   賽事: {year1} {race1} {session1}")
                print(f"[RPM_MDI] [SHARED_PARAMS]   車手: {driver1} vs {driver2}")
                print(f"[RPM_MDI] [SHARED_PARAMS]   圈數: 第{lap1}圈 vs 第{lap2}圈")
                
                # 更新 self 屬性
                self.driver1_year = year1
                self.driver1_race = race1
                self.driver1_session = session1
                self.driver1 = driver1
                self.lap1 = lap1
                
                self.driver2_year = year2
                self.driver2_race = race2
                self.driver2_session = session2
                self.driver2 = driver2
                self.lap2 = lap2
                
                self.use_time_axis = use_time_axis
                
                self.current_year = year1
                self.current_race = race1
                self.current_session = session1
            
            # 更新圖表組件的時間軸模式
            if self.rpm_chart_widget and hasattr(self.rpm_chart_widget, 'set_time_axis_mode'):
                self.rpm_chart_widget.set_time_axis_mode(self.use_time_axis)
                print(f"[RPM_MDI] [SHARED_PARAMS] 🕒 已設置時間軸模式: {self.use_time_axis}")
            
            # ⚠️ [參數資訊標籤] 更新資訊標籤顯示
            self._update_info_label()
            print(f"[RPM_MDI] [SHARED_PARAMS] 📋 已更新資訊標籤")
            
            # 調用標準更新方法重新載入數據
            print(f"[RPM_MDI] [SHARED_PARAMS] 🔄 調用 update_lap_parameters 重新載入數據")
            success = self.update_lap_parameters(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver1=self.driver1,
                driver2=self.driver2,
                lap1=self.lap1,
                lap2=self.lap2,
                is_fastest=False,
                use_time_axis=self.use_time_axis
            )
            
            if success:
                print(f"[RPM_MDI] [SHARED_PARAMS] ✅ 全域參數同步完成")
            else:
                print(f"[RPM_MDI] [SHARED_PARAMS] ❌ 數據重載失敗")
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] [SHARED_PARAMS] 更新失敗: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._updating_from_shared = False
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            print(f"[RPM_MDI] 更新RPM圖表")
            if self.rpm_chart_widget:
                self.rpm_chart_widget.update_rpm_data(data)
                
                # 更新工具欄狀態信息
                self._update_toolbar_status(data)
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 圖表更新失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] [RPM_MDI] {error_message}")
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
            print(f"[ERROR] [RPM_MDI] 獲取主視窗失敗: {e}")
            return None

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
    
    def cleanup_module(self):
        """清理模組資源和信號連接"""
        try:
            print(f"[RPM_MDI] 🧹 清理RPM分析模組...")
            
            if self.data_manager:
                # 斷開所有信號連接
                try:
                    self.data_manager.data_loaded.disconnect()
                    self.data_manager.error_occurred.disconnect()
                    self.data_manager.loading_progress.disconnect()
                    self.data_manager.status_changed.disconnect()
                except Exception as e:
                    print(f"[WARNING] [RPM_MDI] 斷開數據管理器信號時發生警告: {e}")
            
            if self.rpm_chart_widget and hasattr(self.rpm_chart_widget, 'lap_numbers_changed'):
                try:
                    self.rpm_chart_widget.lap_numbers_changed.disconnect()
                except Exception as e:
                    print(f"[WARNING] [RPM_MDI] 斷開圖表組件信號時發生警告: {e}")
            
            print(f"[RPM_MDI] ✅ 模組清理完成")
                
        except Exception as e:
            print(f"[WARNING] [RPM_MDI] 清理模組時發生警告: {e}")
    
    def reset_chart_view(self):
        """重置圖表視圖 - 與 Show All Data 按鈕整合"""
        print(f"[RPM_MDI] 🔄 reset_chart_view() 被調用")
        if hasattr(self, 'rpm_chart_widget') and self.rpm_chart_widget:
            print(f"[RPM_MDI] ✅ 找到 rpm_chart_widget，調用 reset_chart_view()")
            self.rpm_chart_widget.reset_chart_view()
        else:
            print(f"[RPM_MDI] ❌ 未找到 rpm_chart_widget 屬性")
    
    def cleanup(self):
        """清理資源 - 實現抽象方法"""
        try:
            # 從分析模組管理器解除註冊
            if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
                try:
                    # 解除註冊圖表組件
                    if hasattr(self, 'rpm_chart_widget') and self.rpm_chart_widget:
                        self._analysis_manager.unregister_chart_widget(self.rpm_chart_widget)
                    
                    # 解除註冊模組
                    self._analysis_manager.unregister_module(self._module_id)
                    print(f"[RPM_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                    
                except Exception as e:
                    print(f"[ERROR] [RPM_MDI] 從分析模組管理器解除註冊失敗: {e}")

            if hasattr(self, 'data_manager') and self.data_manager:
                # 清理數據管理器
                if hasattr(self.data_manager, 'cleanup'):
                    self.data_manager.cleanup()
            
            # 調用模組清理
            self.cleanup_module()
            
            if hasattr(self, 'rpm_chart_widget') and self.rpm_chart_widget:
                # 🔧 修復：從連動管理器中取消註冊圖表組件（內部 chart_widget）
                try:
                    from modules.gui.lap_analysis.linkage import linkage_manager
                    if linkage_manager:
                        # ✅ 正確：取消註冊內部 chart_widget（而不是容器）
                        if hasattr(self.rpm_chart_widget, 'chart_widget') and self.rpm_chart_widget.chart_widget:
                            linkage_manager.unregister_module(self.rpm_chart_widget.chart_widget)
                            print(f"[RPM_MDI] ✅ 已從連動管理器解除註冊內部圖表組件 (chart_widget)")
                except Exception as e:
                    print(f"[ERROR] [RPM_MDI] 從連動管理器解除註冊失敗: {e}")
                
                # 清理圖表組件
                if hasattr(self.rpm_chart_widget, 'cleanup'):
                    self.rpm_chart_widget.cleanup()
                self.rpm_chart_widget.deleteLater()
                
            if hasattr(self, 'main_widget') and self.main_widget:
                # 清理主要組件
                self.main_widget.deleteLater()
                
            print(f"[CLEANUP] RPM分析模組資源清理完成")
        except Exception as e:
            print(f"[ERROR] RPM分析模組清理失敗: {e}")
    
    # ========== 遙測分析整合功能 ==========
    
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

            print(f"[RPM_MDI] 🔍 [API-ONLY] 檢查遙測分析本地緩存: {target_year} {target_race} {target_session}")

            # ✅ 允許：檢查本地 JSON 緩存
            telemetry_file = self._find_telemetry_analysis_file(
                year=target_year,
                race=target_race,
                session=target_session
            )
            if telemetry_file:
                print(f"[RPM_MDI] 📂 [API-ONLY] 找到本地遙測分析緩存: {telemetry_file}")
                return True

            # ❌ 禁止：自動創建視窗或啟動 CLI
            # 改為僅提示用戶通過 API 或主視窗遙測模組獲取數據
            print("⚠️ [RPM_MDI] [API-ONLY] 遙測分析數據不存在於本地緩存")
            print("💡 [RPM_MDI] [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據")
            print("💡 [RPM_MDI] [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8")
            return False

        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _check_and_load_telemetry_if_needed 失敗: {e}")
            return False

    def _ensure_telemetry_data_for_fastest_laps(self) -> Optional[Dict[str, int]]:
        """確保最速圈數據的遙測分析可用 - 與速度分析相同功能"""
        try:
            print(f"[RPM_MDI] 🔍 檢查最速圈遙測數據可用性...")
            
            # 首先檢查是否已有遙測分析檔案
            telemetry_file = self._find_telemetry_analysis_file()
            
            if not telemetry_file:
                print(f"[RPM_MDI] 📡 遙測分析數據不存在，開始自動載入...")
                success = self._check_and_load_telemetry_if_needed()
                if success:
                    # 重新檢查檔案
                    telemetry_file = self._find_telemetry_analysis_file()
                else:
                    print(f"[RPM_MDI] ❌ 遙測分析載入失敗")
                    return None
            
            if telemetry_file:
                print(f"[RPM_MDI] 📂 找到遙測分析檔案: {telemetry_file}")
                return self._extract_fastest_laps_from_telemetry(telemetry_file)
            else:
                print(f"[RPM_MDI] ⚠️ 無法獲取遙測分析數據")
                return None
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _ensure_telemetry_data_for_fastest_laps 失敗: {e}")
            return None
    
    def _find_telemetry_analysis_file(self, year: Optional[str] = None,
                                      race: Optional[str] = None,
                                      session: Optional[str] = None) -> Optional[str]:
        """尋找遙測分析JSON檔案"""
        try:
            target_year = str(year or self.current_year or "").strip()
            target_race_raw = (race or self.current_race or "").strip()
            target_session = str(session or self.current_session or "").strip()

            if not (target_year and target_race_raw and target_session):
                print("⚠️ [RPM_MDI] 遙測檔案搜尋缺少必要參數")
                return None

            race_key = (target_race_raw
                        .replace(' ', '_')
                        .replace('/', '_')
                        .replace('-', '_'))

            candidate_prefixes = [
                f"telemetry_analysis_{target_year}_{race_key}_{target_session}",
                f"all_drivers_telemetry_analysis_{target_year}_{race_key}_{target_session}",
                f"all_drivers_telemetry_analysis_{target_year}_{race_key}"
            ]

            json_dir = "json"
            if os.path.exists(json_dir):
                for filename in os.listdir(json_dir):
                    if (filename.endswith('.json') and
                            any(filename.startswith(prefix) for prefix in candidate_prefixes)):
                        full_path = os.path.join(json_dir, filename)
                        print(f"[RPM_MDI] 📂 找到遙測分析檔案: {full_path}")
                        return full_path

            print(f"[RPM_MDI] 📂 未找到遙測分析檔案 ({target_year} {race_key} {target_session})")
            return None

        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _find_telemetry_analysis_file 失敗: {e}")
            return None
    
    def _trigger_telemetry_analysis(self) -> bool:
        """觸發遙測分析載入/生成 - 與速度分析相同功能"""
        try:
            print(f"[RPM_MDI] 🚀 觸發遙測分析載入: {self.current_year} {self.current_race} {self.current_session}")
            
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
                            print(f"[RPM_MDI] 🎯 找到現有遙測分析視窗: {window_title}")
                            # 激活並刷新遙測分析視窗
                            main_window.mdi_area.setActiveSubWindow(sub_window)
                            return True
                    
                    # API-ONLY 模式：不自動創建視窗
                    print(f"[RPM_MDI] � [API-ONLY] 未找到現有遙測分析視窗")
                    print(f"[RPM_MDI] 💡 提示：請手動開啟遙測分析模組或通過 API 獲取數據")
                    return False
            
            # 方法2: 透過 API 檢查本地數據（不自動創建）
            print(f"[RPM_MDI] 🔍 檢查本地遙測分析數據...")
            return self._check_and_load_telemetry_if_needed()
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _trigger_telemetry_analysis 失敗: {e}")
            return False
    
    def _extract_fastest_laps_from_telemetry(self, telemetry_file: str) -> Optional[Dict[str, int]]:
        """從遙測分析JSON檔案中提取最速圈數據 - 與速度分析相同功能"""
        try:
            print(f"[RPM_MDI] 📊 從遙測分析中提取最速圈數據: {telemetry_file}")
            
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
            
            print(f"[RPM_MDI] ✅ 最速圈數據提取完成: {fastest_laps}")
            return fastest_laps if fastest_laps else None
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _extract_fastest_laps_from_telemetry 失敗: {e}")
            return None
    
    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數更新通知 - 與速度分析相同功能"""
        try:
            print(f"[RPM_NOTIFICATION_DEBUG] ========== 收到主視窗更新通知 ==========")
            print(f"[RPM_NOTIFICATION_DEBUG] 📡 原始參數:")
            print(f"[RPM_NOTIFICATION_DEBUG]   - param_type: {param_type}")
            print(f"[RPM_NOTIFICATION_DEBUG]   - value: {value}")
            
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
            
            print(f"[RPM_NOTIFICATION_DEBUG] 📊 當前模組狀態:")
            print(f"[RPM_NOTIFICATION_DEBUG]   - 當前年份: {self.current_year}")
            print(f"[RPM_NOTIFICATION_DEBUG]   - 當前賽事: {self.current_race}")
            print(f"[RPM_NOTIFICATION_DEBUG]   - 當前賽段: {self.current_session}")
            print(f"[RPM_NOTIFICATION_DEBUG]   - 當前車手: {getattr(self, 'driver1', 'VER')} vs {getattr(self, 'driver2', 'VER')}")
            print(f"[RPM_NOTIFICATION_DEBUG]   - 當前圈數: 第{getattr(self, 'lap1', 1)}圈 vs 第{getattr(self, 'lap2', 1)}圈")
            
            # 更新視窗標題
            self.update_window_title()
            
            # 重新載入數據 - 與速度分析模組保持一致
            if hasattr(self, 'data_manager') and self.data_manager:
                print(f"[REFRESH] 重新載入RPM數據...")
                self.data_manager.load_rpm_data(
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
                    self.data_manager = RPMDataManager()
                    self.data_manager.data_loaded.connect(self._update_chart)
                    self.data_manager.error_occurred.connect(self._handle_error)
                    print(f"[OK] 數據管理器創建成功，開始載入數據...")
                    self.data_manager.load_rpm_data(
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
            
            print(f"[OK] [NOTIFICATION] ⚡ RPM分析模組內容更新成功")
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] receive_main_window_update_notification 失敗: {e}")
            import traceback
            traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據 - 實現抽象方法"""
        try:
            print(f"[RPM_MDI] 匯出數據功能尚未實現 (路徑: {export_path}, 格式: {export_format})")
            return False
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] export_data 失敗: {e}")
            return False

        # ========== 實現抽象方法 ==========

    @property
    def closeEvent(self, event):
        """
        ⚠️ 關鍵修復：MDI 視窗關閉時清理執行緒資源
        
        修復執行緒洩漏問題 - 確保 TelemetryApiWorker 執行緒正確終止
        問題：用戶關閉 MDI 視窗時，背景執行緒繼續運行導致 Dummy-11 到 Dummy-47+ 洩漏
        """
        print(f"[RPM_MDI] 🧹 視窗關閉事件觸發，開始清理資源...")
        
        try:
            # 清理數據載入器的執行緒
            if hasattr(self, 'data_manager') and self.data_manager:
                if hasattr(self.data_manager, '_rpm_loader'):
                    print(f"[RPM_MDI] 清理 DataLoader 執行緒...")
                    self.data_manager._rpm_loader.cleanup_threads()
            
            # 斷開所有信號連接
            if hasattr(self, 'data_manager') and self.data_manager:
                try:
                    self.data_manager.data_loaded.disconnect()
                    self.data_manager.error_occurred.disconnect()
                except Exception:
                    pass
            
            print(f"[RPM_MDI] ✅ 資源清理完成")
            
        except Exception as e:
            print(f"[RPM_MDI] ⚠️ 清理過程發生錯誤: {e}")
        
        # 調用父類的 closeEvent
        super().closeEvent(event)

    def module_name(self) -> str:
        """模組名稱"""
        return "rpm_analysis"

    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return tr("rpm_analysis", "RPM分析")

    @property
    def description(self) -> str:
        """模組描述"""
        return tr("rpm_analysis_description", "F1賽車RPM轉速對比分析工具")

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
                return self.data_manager.load_rpm_data(
                    year=year, race=race, session=session,
                    driver1=driver1, driver2=driver2,
                    lap1=lap1, lap2=lap2, is_fastest=is_fastest
                )
            return False
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] load_data 失敗: {e}")
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
                'module_type': 'rpm_analysis'
            }
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] get_current_data 失敗: {e}")
            return {}

    def clear_data(self) -> None:
        """清除數據 - 實現抽象方法"""
        try:
            print(f"[RPM_MDI] 清除數據...")
            if self.rpm_chart_widget and hasattr(self.rpm_chart_widget, 'clear_chart'):
                self.rpm_chart_widget.clear_chart()
            
            if self.status_label:
                self.status_label.setText("已清除")
            
            if self.progress_bar:
                self.progress_bar.setVisible(False)
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] clear_data 失敗: {e}")

    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """更新分析參數 - 實現抽象方法"""
        try:
            print(f"[RPM_PARAMS_DEBUG] ========== RPM參數更新開始 ==========")
            print(f"[RPM_PARAMS_DEBUG] 收到參數: year={year}, race={race}, session={session}")
            print(f"[RPM_PARAMS_DEBUG] 當前參數: year={self.current_year}, race={self.current_race}, session={self.current_session}")
            
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
            
            print(f"[RPM_PARAMS_DEBUG] 參數變化檢查: {params_changed}")
            print(f"[RPM_PARAMS_DEBUG] 舊參數: {old_year} {old_race} {old_session}")
            print(f"[RPM_PARAMS_DEBUG] 新參數: {new_year} {new_race} {new_session}")
            
            # 更新內部參數
            self.current_year = new_year
            self.current_race = new_race
            self.current_session = new_session
            
            # 更新視窗標題
            self.update_window_title()
            
            # 檢查是否需要載入數據
            print(f"[RPM_PARAMS_DEBUG] 檢查數據載入需求...")
            if params_changed or not hasattr(self, '_data_loaded'):
                print(f"[RPM_PARAMS_DEBUG] 需要載入數據：參數變化={params_changed}, 未載入過={not hasattr(self, '_data_loaded')}")
                
                # 重新載入數據 - 與速度分析模組保持一致
                if hasattr(self, 'data_manager') and self.data_manager:
                    print(f"[REFRESH] 重新載入RPM數據...")
                    success = self.data_manager.load_rpm_data(
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
                        print(f"[RPM_PARAMS_DEBUG] ✅ RPM 數據重載成功")
                        return True
                    else:
                        print(f"[RPM_PARAMS_DEBUG] ❌ RPM 數據重載失敗")
                        return False
                else:
                    # 檢查並創建數據管理器
                    print(f"[RPM_PARAMS_DEBUG] 數據管理器不存在，嘗試創建...")
                    try:
                        self.data_manager = RPMDataManager()
                        self.data_manager.data_loaded.connect(self._update_chart)
                        self.data_manager.error_occurred.connect(self._handle_error)
                        print(f"[RPM_PARAMS_DEBUG] ✅ 數據管理器創建成功，開始載入數據...")
                        
                        success = self.data_manager.load_rpm_data(
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
                            print(f"[RPM_PARAMS_DEBUG] ✅ RPM 數據載入成功")
                            return True
                        else:
                            print(f"[RPM_PARAMS_DEBUG] ❌ RPM 數據載入失敗")
                            return False
                            
                    except Exception as e:
                        print(f"[RPM_PARAMS_DEBUG] ❌ 數據管理器創建失敗: {e}")
                        print(f"[RPM_PARAMS_DEBUG] ⚠️ 參數更新完成（無數據載入）: {self.current_year} {self.current_race} {self.current_session}")
                        return False
            else:
                print(f"[RPM_PARAMS_DEBUG] 跳過數據載入：參數無變化且已載入過")
                return True
            
        except Exception as e:
            print(f"[ERROR] [RPM_PARAMS_DEBUG] update_parameters 失敗: {e}")
            print(f"[ERROR] [RPM_PARAMS_DEBUG] update_parameters 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def refresh_analysis(self) -> None:
        """重新分析 - 實現抽象方法"""
        try:
            print(f"[RPM_MDI] 重新分析...")
            self._refresh_data()
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] refresh_analysis 失敗: {e}")

# 主程式測試
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試RPM分析模組
    module = RPMAnalysisModule()
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

# 註冊RPM分析模組到工廠
try:
    from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
    ModuleFactory.register_module(ModuleTypes.TELEMETRY_RPM, RPMAnalysisModule)
    print(f"[OK] [MODULE_FACTORY] RPM analysis module registered")
except ImportError as e:
    print(f"[WARNING] [MODULE_FACTORY] RPM分析模組註冊失敗: {e}")
