#!/usr/bin/env python3
"""
F1T 速度分析 MDI 模組
基於進站分析模組的成功架構設計
支援雙車手速度對比的 GUI 模組，使用新版模組更新機制
"""

import sys
import os
import json
import datetime
import traceback
import time
import requests
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

from core.logger import get_logger
logger = get_logger(__name__)


class CrossEventComparisonWorker(QThread):
    """跨賽事比較 API Worker - 調用 /api/v2/analysis/cross-event-comparison 端點"""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, driver1: str, year1: int, race1: str, session1: str, lap1: int,
                 driver2: str, year2: int, race2: str, session2: str, lap2: int,
                 force_refresh: bool = False, timeout: float = 120.0, parent=None):
        """初始化跨賽事比較 Worker - 強化 EXE 環境異常處理"""
        try:
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
            
            # ✅ 安全調用 resolve_api_base_url（防止 EXE 環境崩潰）
            try:
                self.base_url = resolve_api_base_url().rstrip('/')
                logger.info(f"[CROSS-EVENT-WORKER] ✅ API base URL: {self.base_url}")
            except Exception as e:
                # 如果解析失敗，使用硬編碼的公開 API
                from core.api_base_url import PUBLIC_API_BASE_URL
                self.base_url = PUBLIC_API_BASE_URL.rstrip('/')
                logger.warning(f"[CROSS-EVENT-WORKER] ⚠️ API URL 解析失敗，使用預設: {self.base_url}")
                logger.debug(f"[CROSS-EVENT-WORKER] 錯誤: {e}")
                
        except Exception as e:
            logger.error(f"[CROSS-EVENT-WORKER] Worker 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            raise  # 重新拋出異常，讓調用者知道初始化失敗

    def run(self):
        """執行 API 請求 - 強化 EXE 環境異常處理"""
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                logger.debug("[CROSS-EVENT-WORKER] 開始前已被中斷")
                return
            logger.debug(f"[CROSS-EVENT-WORKER] 開始執行 API 請求")
            self.progress.emit(20)
            
            # ✅ 防禦性檢查：確保 base_url 存在
            if not hasattr(self, 'base_url') or not self.base_url:
                raise RuntimeError("API base_url 未初始化")
            
            endpoint = f"{self.base_url}/api/v2/analysis/cross-event-comparison"
            logger.debug(f"[CROSS-EVENT-WORKER] 目標端點: {endpoint}")
            
            # 構建請求參數
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
            }
            
            if self.force_refresh:
                query_params["force_refresh"] = True

            logger.debug(f"[CROSS-EVENT-WORKER] 請求參數: {query_params}")
            
            start_ts = time.perf_counter()
            self.progress.emit(30)
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                logger.debug("[CROSS-EVENT-WORKER] HTTP 請求前被中斷")
                return
            
            # ✅ 防禦性檢查：確保 requests 模組可用
            if not hasattr(requests, 'post'):
                raise RuntimeError("requests 模組未正確載入")
            
            logger.debug(f"[CROSS-EVENT-WORKER] 發送 POST 請求...")
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(70)
            
            # ✅ 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                logger.debug("[CROSS-EVENT-WORKER] HTTP 請求後被中斷")
                return
            
            logger.debug(f"[CROSS-EVENT-WORKER] 收到回應，狀態碼: {response.status_code}")
            response.raise_for_status()

            payload = response.json()
            logger.debug(f"[CROSS-EVENT-WORKER] JSON 解析成功")
            
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
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                logger.debug("[CROSS-EVENT-WORKER] success 信號前被中斷")
                return
            logger.info(f"[CROSS-EVENT-WORKER] ✅ 請求成功，發送 success 信號")
            self.success.emit({"data": data, "meta": meta})
            
        except requests.exceptions.Timeout as e:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求超時 ({self.timeout}秒): {e}"
            logger.error(f"[CROSS-EVENT-WORKER] ❌ {error_msg}")
            self.failure.emit(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"無法連線到 API 伺服器: {e}"
            logger.error(f"[CROSS-EVENT-WORKER] ❌ {error_msg}")
            self.failure.emit(error_msg)
            
        except requests.exceptions.HTTPError as e:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"HTTP 錯誤 ({e.response.status_code}): {e}"
            logger.error(f"[CROSS-EVENT-WORKER] ❌ {error_msg}")
            self.failure.emit(error_msg)
            
        except Exception as exc:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"未預期的錯誤: {type(exc).__name__}: {exc}"
            logger.error(f"[CROSS-EVENT-WORKER] ❌ {error_msg}")
            try:
                import traceback
                traceback.print_exc()
            except:
                pass
            self.failure.emit(error_msg)
            
        finally:
            try:
                # ✅ 中斷檢查：被中斷時不發送 progress 信號
                if not self.isInterruptionRequested():
                    self.progress.emit(100)
                logger.debug(f"[CROSS-EVENT-WORKER] Worker 執行完成")
            except:
                pass  # 避免 finally 中的錯誤導致崩潰


class SpeedDataManager(QObject):
    """速度數據管理器 - 負責JSON緩存和CLI備援"""
    
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
        
    def load_speed_data(self, year: str, race: str, session: str, 
                       driver1: str = "VER", driver2: str = "VER",
                       lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:
        """載入速度對比數據"""
        try:
            logger.debug(f"[SPEED_MDI_DATA] ========== 載入速度數據 ==========")
            logger.debug(f"[SPEED_MDI_DATA] 參數: {year} {race} {session}")
            logger.debug(f"[SPEED_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            if self._is_loading:
                logger.warning(f"[SPEED_MDI_DATA] ⚠️ 數據載入中，忽略新請求")
                self.error_occurred.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.loading_progress.emit(0)
            self.status_changed.emit("開始載入速度數據...")

            # 儲存當前賽事上下文，供遙測資料及CLI命令使用
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # 檢查最速圈選項並自動載入遙測分析
            if is_fastest or lap1 == "fastest" or lap2 == "fastest":
                logger.debug(f"[SPEED_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")
                self._check_and_load_telemetry_if_needed()
                
                # 解析最速圈參數為實際圈數
                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)
                logger.debug(f"🔢 [SPEED_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")
            
            logger.debug(f"[SPEED_MDI_DATA] 🔗 創建 SpeedAnalysisDataLoader...")
            
            # 使用現有的速度分析數據載入器
            from .speed_analysis_data_loader import SpeedAnalysisDataLoader
            
            logger.debug(f"[SPEED_MDI_DATA] 🚀 調用 load_speed_data...")
            
            # ✅ 修復：創建數據載入器並保存為實例變數（防止垃圾回收）
            self._speed_loader = SpeedAnalysisDataLoader()
            self._speed_loader.data_loaded.connect(self._on_data_loaded)
            self._speed_loader.load_error.connect(self._on_load_error)
            self._speed_loader.status_changed.connect(self.status_changed.emit)
            self._speed_loader.load_progress.connect(self.loading_progress.emit)
            
            # 開始載入數據
            success = self._speed_loader.load_speed_data(
                year=int(year),
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest_lap=is_fastest  # 修正：使用傳入的is_fastest參數
            )
            
            # 將loader設置給chart widget以供直接更新
            if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
                self.speed_chart_widget.speed_loader = self._speed_loader
                logger.info(f"[SPEED_MDI] ✅ 已將loader設置給chart widget")
            
            if success:
                logger.info(f"[SPEED_MDI_DATA] ✅ 速度數據載入請求提交成功")
                self.loading_progress.emit(50)
                return True
            else:
                logger.error(f"[SPEED_MDI_DATA] ❌ 速度數據載入請求失敗")
                self._is_loading = False
                self.error_occurred.emit("速度數據載入請求失敗")
                return False
            
        except Exception as e:
            logger.error(f"[SPEED_MDI_DATA] 載入速度數據時發生錯誤: {e}")
            self._is_loading = False
            self.error_occurred.emit(f"載入速度數據失敗: {str(e)}")
            return False

    def _check_and_load_telemetry_if_needed(self):
        """檢查遙測分析數據（最速圈用）"""
        try:
            logger.debug(f"[SPEED_MDI_DATA] 檢查遙測分析數據可用性...")

            module_ref = getattr(self, "module_ref", None)
            if module_ref:
                logger.debug(f"[SPEED_MDI_DATA] 委派給module_ref檢查遙測數據")
                return module_ref._check_and_load_telemetry_if_needed()

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
                            logger.debug(f"[SPEED_MDI_DATA] 找到現有遙測檔案: {file_path}")
                            return True

            logger.debug("[SPEED_MDI_DATA] API-ONLY 模式下未找到遙測檔案，請透過主視窗遙測模組或 REST API 取得資料")
            return False

        except Exception as e:
            logger.debug(f"[SPEED_MDI_DATA] 檢查遙測數據時發生錯誤: {e}")
            return False

    def _get_fastest_lap_number(self, driver: str) -> int:
        """從遙測分析數據獲取指定車手的最速圈數"""
        try:
            logger.debug(f"[SPEED_MDI] 開始搜尋 {driver} 的最速圈數據...")
            
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
                            logger.debug(f"📁 [SPEED_MDI] 找到遙測檔案: {telemetry_file}")
                            break
                    if telemetry_file:
                        break
            
            if not telemetry_file:
                logger.error(f"[SPEED_MDI] 找不到遙測分析檔案，使用預設圈數 1")
                return 1
                
            # 讀取並解析遙測分析數據
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            logger.debug(f"[SPEED_MDI] 遙測檔案讀取成功，開始解析最速圈數據...")
            
            # 嘗試多種數據結構格式
            fastest_lap_num = None
            
            # 格式1: data.all_drivers_telemetry[driver].fastest_lap
            if 'data' in telemetry_data and 'all_drivers_telemetry' in telemetry_data['data']:
                driver_data = telemetry_data['data']['all_drivers_telemetry'].get(driver)
                if driver_data and 'fastest_lap' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap'].get('lap_number')
                    if fastest_lap_num:
                        logger.info(f"[SPEED_MDI] 從格式1找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                        return int(fastest_lap_num)
            
            # 格式2: data.fastest_laps中的列表
            if 'data' in telemetry_data and 'fastest_laps' in telemetry_data['data']:
                for fastest_data in telemetry_data['data']['fastest_laps']:
                    if fastest_data.get('driver') == driver:
                        fastest_lap_num = fastest_data.get('lap_number')
                        if fastest_lap_num:
                            logger.info(f"[SPEED_MDI] 從格式2找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                            return int(fastest_lap_num)
            
            # 格式3: 直接在data下按車手分組
            if 'data' in telemetry_data:
                driver_data = telemetry_data['data'].get(driver)
                if driver_data and 'fastest_lap_number' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap_number']
                    logger.info(f"[SPEED_MDI] 從格式3找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                    return int(fastest_lap_num)
            
            logger.warning(f"[SPEED_MDI] 無法找到 {driver} 的最速圈數據，使用預設圈數 1")
            return 1
            
        except Exception as e:
            logger.error(f"[SPEED_MDI] 解析最速圈數據時發生錯誤: {e}")
            return 1

    def _resolve_lap_numbers(self, lap1, lap2, driver1, driver2, is_fastest):
        """解析圈數參數，將'fastest'轉換為實際圈數"""
        try:
            resolved_lap1 = lap1
            resolved_lap2 = lap2
            
            # 處理lap1
            if lap1 == "fastest" or is_fastest:
                logger.debug(f"[SPEED_MDI] 解析 {driver1} 的最速圈...")
                resolved_lap1 = self._get_fastest_lap_number(driver1)
                
            # 處理lap2
            if lap2 == "fastest" or is_fastest:
                logger.debug(f"[SPEED_MDI] 解析 {driver2} 的最速圈...")
                resolved_lap2 = self._get_fastest_lap_number(driver2)
            
            logger.debug(f"[SPEED_MDI] 圈數解析結果: {driver1}=第{resolved_lap1}圈, {driver2}=第{resolved_lap2}圈")
            
            return int(resolved_lap1), int(resolved_lap2)
            
        except Exception as e:
            logger.error(f"[SPEED_MDI] 解析圈數時發生錯誤: {e}")
            return 1, 1
    
    def _on_data_loaded(self, data):
        """數據載入完成回調"""
        try:
            logger.debug(f"[SPEED_MDI_DATA] 速度數據載入完成")
            self._is_loading = False
            self.loading_progress.emit(100)
            self.status_changed.emit("速度數據載入完成")
            self.data_loaded.emit(data)
        except Exception as e:
            logger.error(f"[SPEED_MDI_DATA] 處理載入完成回調時發生錯誤: {e}")
            self._on_load_error(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_msg):
        """數據載入錯誤回調"""
        logger.debug(f"[SPEED_MDI_DATA] 速度數據載入錯誤: {error_msg}")
        self._is_loading = False
        self.loading_progress.emit(0)
        self.status_changed.emit(f"載入失敗: {error_msg}")
        self.error_occurred.emit(error_msg)

    def cleanup(self):
        """
        清理 SpeedDataManager 資源
        
        修復記憶體洩漏：清理 DataLoader 的 API Worker 執行緒
        """
        try:
            logger.debug(f"[SPEEDDATAMANAGER] 🧹 開始清理資源...")
            
            # 1. 清理 DataLoader 及其 QThread
            if hasattr(self, '_speed_loader') and self._speed_loader:
                try:
                    # 調用 loader 的 cleanup() 方法（清理 API worker 執行緒）
                    if hasattr(self._speed_loader, 'cleanup'):
                        self._speed_loader.cleanup()
                        logger.info(f"[SPEEDDATAMANAGER] ✅ 已清理 loader 執行緒")
                    
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
                    logger.error(f"[SPEEDDATAMANAGER] 清理 loader 失敗: {e}")
            
            # 2. 🔴 斷開循環引用：清理 module_ref
            if hasattr(self, 'module_ref'):
                logger.debug(f"[SPEEDDATAMANAGER] 🔴 斷開循環引用：清理 module_ref")
                self.module_ref = None
            
            # 3. 清理內部狀態
            self.current_year = None
            self.current_race = None
            self.current_session = None
            self._is_loading = False
            
            logger.info(f"[SPEEDDATAMANAGER] ✅ 資源清理完成")
            
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（SpeedDataManager 實例）
            logger.error(f"[SPEEDDATAMANAGER] cleanup() 失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()


class SpeedAnalysisModule(IAnalysisModule):
    """速度分析主模組"""
    
    # 信號定義
    module_error = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 設置分析類型（用於批次更新識別）- 統一命名與其他模組一致
        self.analysis_type = 'speed'
        
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
        
        # 🔧 [DRIVER_LAP_SYNC] 車手與圈數同步控制（顯示標題欄按鈕的關鍵屬性）
        self.sync_driver_lap_enabled = True  # 預設啟用同步
        
        # ⚠️ [全域共享參數池] 循環更新防護
        self._updating_from_shared = False  # 防止遞迴更新
        
        # 組件
        self.data_manager = None
        self.speed_chart_widget = None
        self.main_widget = None  # 主容器 widget
        self.parent_window = None  # MDI 子視窗引用
        
        # 初始化狀態
        self._initialized = False
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 實現抽象方法"""
        try:
            logger.debug(f"[SPEED_MDI] 初始化速度分析模組")
            
            # 創建數據管理器
            self.data_manager = SpeedDataManager()
            self.data_manager.module_ref = self
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            
            # 創建速度圖表組件
            from .speed_analysis_chart_widget import SpeedAnalysisChartWidget
            self.speed_chart_widget = SpeedAnalysisChartWidget()
            
            # 連接圈數變更信號
            self.speed_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
            
            # 設置初始圈數
            self.speed_chart_widget.set_lap_numbers(self.lap1, self.lap2)
            
            # 設置主界面
            self._setup_ui()
            
            # 註冊到分析模組管理器
            try:
                from ..analysis_module_manager import get_analysis_module_manager
                manager = get_analysis_module_manager()
                
                # 註冊模組
                module_id = f"speed_analysis_{id(self)}"
                manager.register_module(module_id, self, "speed_analysis")
                
                # 註冊圖表組件
                if self.speed_chart_widget:
                    manager.register_chart_widget(self.speed_chart_widget)
                
                # 保存管理器引用和模組ID
                self._analysis_manager = manager
                self._module_id = module_id
                
                logger.info(f"[SPEED_MDI] ✅ 已註冊到分析模組管理器: {module_id}")
                
            except ImportError as e:
                logger.warning(f"[SPEED_MDI] 無法導入分析模組管理器: {e}")
                self._analysis_manager = None
                self._module_id = None
            except Exception as e:
                logger.error(f"[SPEED_MDI] 註冊到分析模組管理器失敗: {e}")
                self._analysis_manager = None
                self._module_id = None
            
            self._initialized = True
            logger.info(f"[SPEED_MDI] 速度分析模組初始化完成")
            return True
            
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（SpeedAnalysisModule 實例）
            logger.error(f"[SPEED_MDI] 模組初始化失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 新增：參數資訊標籤（淺色背景）
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
        
        # 添加速度圖表
        if self.speed_chart_widget:
            layout.addWidget(self.speed_chart_widget)
        
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
                logger.debug(f"[SPEED_MDI] 同步模式：隱藏資訊標籤")
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
            logger.debug(f"[SPEED_MDI] 取消同步模式：顯示資訊標籤")
            
        except Exception as e:
            logger.error(f"[SPEED_MDI] 更新資訊標籤失敗: {e}")
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            logger.debug(f"[SPEED_MDI] ========== 更新速度圖表回調 ==========")
            logger.debug(f"[SPEED_MDI] 📦 接收到數據類型: {type(data)}")
            logger.debug(f"[SPEED_MDI] 📦 接收到數據鍵值: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if isinstance(data, dict) and 'speed_data' in data:
                speed_data = data['speed_data']
                logger.debug(f"[SPEED_MDI] 📊 speed_data 鍵值: {list(speed_data.keys())}")
                logger.debug(f"[SPEED_MDI] 📊 distance 點數: {len(speed_data.get('distance', []))}")
                logger.debug(f"[SPEED_MDI] 📊 driver1_speed 點數: {len(speed_data.get('driver1_speed', []))}")
                logger.debug(f"[SPEED_MDI] 📊 driver2_speed 點數: {len(speed_data.get('driver2_speed', []))}")
            if self.speed_chart_widget:
                logger.debug(f"[SPEED_MDI] 🎨 調用 speed_chart_widget.update_speed_data...")
                self.speed_chart_widget.update_speed_data(data)
                logger.info(f"[SPEED_MDI] ✅ 圖表更新完成")
                
                # 數據載入完成後，應用時間軸設定
                use_time_axis = getattr(self, 'use_time_axis', False)
                if use_time_axis and hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
                    logger.debug(f"[SPEED_MDI] ⏱️ 數據載入完成，應用時間軸模式: {use_time_axis}")
                    self.speed_chart_widget.set_time_axis_mode(use_time_axis)
                
                # 更新工具欄狀態信息
                self._update_toolbar_status(data)
            else:
                logger.error(f"[SPEED_MDI] ❌ speed_chart_widget 未初始化")
                
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（SpeedAnalysisModule 實例）
            logger.error(f"[SPEED_MDI] 圖表更新失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
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
            
            module_name = "速度分析"
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
            
            logger.debug(f"[SPEED_MDI] 已更新工具欄狀態: {module_name}")
            
        except Exception as e:
            logger.error(f"[SPEED_MDI] 更新工具欄狀態失敗: {e}")
    
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
            logger.error(f"[SPEED_MDI] 獲取主視窗失敗: {e}")
            return None
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        logger.error(f"[SPEED_MDI] {error_message}")
        self.module_error.emit(error_message)
    
    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更"""
        try:
            logger.debug(f"[SPEED_MDI] ========== 圈數變更處理 ==========")
            logger.debug(f"[SPEED_MDI] 新圈數: 第{lap1}圈 vs 第{lap2}圈")
            
            # 更新模組的圈數參數
            old_lap1, old_lap2 = self.lap1, self.lap2
            self.lap1 = lap1
            self.lap2 = lap2
            
            logger.debug(f"[SPEED_MDI] 圈數變更: 第{old_lap1}圈 vs 第{old_lap2}圈 → 第{lap1}圈 vs 第{lap2}圈")
            
            # 重新載入數據
            if self.data_manager:
                logger.debug(f"[SPEED_MDI] 🔄 因圈數變更重新載入數據...")
                success = self.data_manager.load_speed_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                
                if success:
                    logger.info(f"[SPEED_MDI] ✅ 圈數變更後數據重載成功")
                else:
                    logger.error(f"[SPEED_MDI] ❌ 圈數變更後數據重載失敗")
            else:
                logger.error(f"[SPEED_MDI] ❌ 數據管理器未初始化，無法重載數據")
                
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（SpeedAnalysisModule 實例）
            logger.error(f"[SPEED_MDI] 處理圈數變更失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
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
                    success = self.data_manager.load_speed_data(
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
                    success = self.data_manager.load_speed_data(
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
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（SpeedAnalysisModule 實例）
            logger.error(f"[SPEED_PARAMS_DEBUG] 參數更新失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False, use_time_axis: bool = False) -> bool:
        """更新圈速分析參數（包含車手和圈數）"""
        try:
            logger.debug(f"[SPEED_MDI] ========== 圈速參數更新 ==========")
            logger.debug(f"[SPEED_MDI] 收到參數: {year} {race} {session}")
            logger.debug(f"[SPEED_MDI] 車手: {driver1} vs {driver2}")
            logger.debug(f"[SPEED_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
            logger.debug(f"[SPEED_MDI] 最速圈: {is_fastest}")
            logger.debug(f"[TIME_AXIS_DEBUG] 步驟 4: MDI 收到 use_time_axis 參數")
            logger.debug(f"[TIME_AXIS_DEBUG]   use_time_axis 參數值: {use_time_axis}")
            logger.debug(f"[SPEED_MDI] ⏱️  使用時間軸: {use_time_axis}")
            
            # 儲存時間軸設定
            self.use_time_axis = use_time_axis
            logger.debug(f"[TIME_AXIS_DEBUG]   self.use_time_axis 已儲存: {self.use_time_axis}")
            
            # 檢查是否需要最速圈數據
            if is_fastest:
                logger.debug(f"[SPEED_MDI] 🏁 用戶選擇了最速圈選項，檢查遙測分析數據...")
                fastest_laps = self._ensure_telemetry_data_for_fastest_laps()
                if fastest_laps:
                    # 使用最速圈數據更新圈數
                    if driver1 in fastest_laps:
                        lap1 = fastest_laps[driver1]
                        logger.debug(f"[SPEED_MDI] 🏁 車手 {driver1} 最速圈: 第{lap1}圈")
                    if driver2 and driver2 in fastest_laps:
                        lap2 = fastest_laps[driver2]
                        logger.debug(f"[SPEED_MDI] 🏁 車手 {driver2} 最速圈: 第{lap2}圈")
                else:
                    logger.warning(f"[SPEED_MDI] ⚠️ 無法獲取最速圈數據，使用預設圈數")
            
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
            
            logger.debug(f"[SPEED_MDI] 參數是否變化: {params_changed}")
            
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
            if self.speed_chart_widget:
                self.speed_chart_widget.set_lap_numbers(lap1, lap2)
                logger.info(f"[SPEED_MDI] ✅ 已更新圖表組件的圈數顯示")
            
            if params_changed:
                logger.debug(f"[SPEED_MDI] 🔄 參數已變化，開始重載數據...")
                
                # 載入新數據
                if self.data_manager:
                    logger.debug(f"[SPEED_MDI] 📡 調用數據管理器載入新數據...")
                    success = self.data_manager.load_speed_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        logger.info(f"[SPEED_MDI] ✅ 圈速參數更新後數據重載成功")
                        
                        # 應用時間軸設定到圖表
                        logger.debug(f"[TIME_AXIS_DEBUG] 步驟 5: 準備設置圖表時間軸模式")
                        logger.debug(f"[TIME_AXIS_DEBUG]   self.speed_chart_widget 存在: {self.speed_chart_widget is not None}")
                        if self.speed_chart_widget:
                            logger.debug(f"[TIME_AXIS_DEBUG]   hasattr(speed_chart_widget, 'set_time_axis_mode'): {hasattr(self.speed_chart_widget, 'set_time_axis_mode')}")
                        
                        if self.speed_chart_widget and hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
                            logger.debug(f"[TIME_AXIS_DEBUG]   調用 speed_chart_widget.set_time_axis_mode({use_time_axis})")
                            self.speed_chart_widget.set_time_axis_mode(use_time_axis)
                            logger.debug(f"[SPEED_MDI] ⏱️  已設置圖表時間軸模式: {use_time_axis}")
                            logger.info(f"[TIME_AXIS_DEBUG]   ✅ set_time_axis_mode 調用完成")
                        else:
                            logger.error(f"[TIME_AXIS_DEBUG]   ❌ 無法調用 set_time_axis_mode (widget不存在或方法不存在)")
                        
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
                        
                        # 更新資訊標籤
                        self._update_info_label()
                        
                        # 更新視窗標題以反映新的參數 - 使用統一的 get_window_title
                        parent = getattr(self, 'parent_window', None)
                        if parent and hasattr(parent, 'setWindowTitle'):
                            new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                            parent.setWindowTitle(new_title)
                            logger.debug(f"[SPEED_MDI] 🏷️ 視窗標題已更新為: {new_title}")
                        else:
                            logger.warning(f"[SPEED_MDI] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
                        
                        return True
                    else:
                        logger.error(f"[SPEED_MDI] ❌ 圈速參數更新後數據重載失敗")
                        return False
                else:
                    logger.error(f"[SPEED_MDI] ❌ 數據管理器未初始化")
                    return False
            else:
                logger.debug(f"[SPEED_MDI] ℹ️ 圈速參數未變化，保持現有數據")
                
                # 即使參數未變化，也確保視窗標題是正確的 - 使用統一的 get_window_title
                parent = getattr(self, 'parent_window', None)
                if parent and hasattr(parent, 'setWindowTitle'):
                    current_title = parent.windowTitle()
                    expected_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                    if current_title != expected_title:
                        parent.setWindowTitle(expected_title)
                        logger.debug(f"[SPEED_MDI] 🏷️ 同步視窗標題: {expected_title}")
                else:
                    logger.warning(f"[SPEED_MDI] ⚠️ 無法同步視窗標題 - 父視窗引用未設置")
                
                return True
                
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（包含 bound method 和 self）
            logger.error(f"[SPEED_MDI] 圈速參數更新失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
            return False
    
    def update_cross_event_comparison(self, year1: str, race1: str, session1: str, driver1: str, lap1: int,
                                     year2: str, race2: str, session2: str, driver2: str, lap2: int,
                                     is_fastest: bool = False, use_time_axis: bool = False) -> bool:
        """更新跨賽事比較參數（支援跨年度/跨賽段）- 強化 EXE 環境異常處理"""
        try:
            logger.debug(f"[CROSS-EVENT] ========== 跨賽事比較更新 ==========")
            logger.debug(f"[CROSS-EVENT] 車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
            logger.debug(f"[CROSS-EVENT] 車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
            logger.debug(f"[CROSS-EVENT] 🕒 時間軸模式: {use_time_axis}")
            
            # ✅ 防禦性檢查：確保所有參數有效
            if not all([year1, race1, session1, driver1, year2, race2, session2, driver2]):
                error_msg = "跨賽事比較參數不完整"
                logger.error(f"[CROSS-EVENT] {error_msg}")
                return False
            
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
            logger.warning(f"[CROSS-EVENT] ⚠️ 已停用同步模式 (sync_driver_lap_enabled = False)")
            
            # 保存時間軸設定
            self.use_time_axis = use_time_axis
            logger.debug(f"[CROSS-EVENT] 🕒 已保存時間軸設定: use_time_axis={use_time_axis}")
            
            # 更新資訊標籤（顯示跨賽事比較資訊）
            try:
                self._update_info_label()
            except Exception as e:
                logger.warning(f"[CROSS-EVENT] 更新資訊標籤失敗: {e}")
            
            # 實作跨賽事比較邏輯：調用 API 端點
            logger.debug(f"[CROSS-EVENT] 開始調用 API 端點: /api/v2/analysis/cross-event-comparison")
            
            # ✅ 檢查是否有舊的 Worker 還在運行
            if hasattr(self, '_cross_event_worker') and self._cross_event_worker is not None:
                try:
                    if self._cross_event_worker.isRunning():
                        logger.warning(f"[CROSS-EVENT] ⚠️ 停止舊的 API Worker...")
                        self._cross_event_worker.requestInterruption()
                        self._cross_event_worker.wait(500)
                except:
                    pass
            
            # 創建 API Worker
            try:
                api_worker = CrossEventComparisonWorker(
                    driver1=driver1, year1=year1, race1=race1, session1=session1, lap1=lap1,
                    driver2=driver2, year2=year2, race2=race2, session2=session2, lap2=lap2,
                    force_refresh=False,
                    timeout=120
                )
                logger.info(f"[CROSS-EVENT] ✅ Worker 創建成功")
            except Exception as e:
                error_msg = f"創建 API Worker 失敗: {e}"
                logger.error(f"[CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            # 連接信號
            try:
                api_worker.success.connect(self._on_cross_event_data_loaded)
                api_worker.failure.connect(self._on_cross_event_load_error)
                api_worker.progress.connect(self._on_api_progress)
                logger.info(f"[CROSS-EVENT] ✅ 信號連接成功")
            except Exception as e:
                error_msg = f"連接 Worker 信號失敗: {e}"
                logger.error(f"[CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            # 保存 Worker 引用（防止被垃圾回收）
            self._cross_event_worker = api_worker
            
            # 啟動 Worker
            try:
                api_worker.start()
                logger.info(f"[CROSS-EVENT] ✅ API Worker 已啟動")
            except Exception as e:
                error_msg = f"啟動 API Worker 失敗: {e}"
                logger.error(f"[CROSS-EVENT] {error_msg}")
                import traceback
                traceback.print_exc()
                return False
            
            logger.debug(f"[CROSS-EVENT] API 請求已啟動")
            return True
                
        except Exception as e:
            logger.error(f"[CROSS-EVENT] 跨賽事比較更新失敗: {e}")
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
        """處理跨賽事比較數據載入成功"""
        try:
            logger.info(f"[CROSS-EVENT] ✅ 數據載入成功")
            
            # 提取數據
            data = result.get("data", {})
            meta = result.get("meta", {})
            
            logger.debug(f"[CROSS-EVENT] 數據鍵值: {list(data.keys())}")
            logger.debug(f"[CROSS-EVENT] 元數據: {meta}")
            
            # 檢查是否有遙測比較數據
            if "telemetry_comparison" in data:
                telemetry_comp = data["telemetry_comparison"]
                logger.debug(f"[CROSS-EVENT] 遙測參數: {list(telemetry_comp.keys())}")
                
                # 提取速度數據（如果存在）
                if "Speed" in telemetry_comp:
                    speed_telemetry = telemetry_comp["Speed"]
                    
                    # 構建符合 _update_chart 期望的數據格式
                    chart_data = {
                        "speed_data": {
                            "distance": speed_telemetry.get("distance", []),
                            "driver1_speed": speed_telemetry.get("driver1_data", []),
                            "driver2_speed": speed_telemetry.get("driver2_data", []),
                            # 🆕 新增時間數據
                            "driver1_time_seconds": speed_telemetry.get("driver1_time_seconds", []),
                            "driver2_time_seconds": speed_telemetry.get("driver2_time_seconds", []),
                        },
                        "comparison_info": data.get("comparison_info", {}),
                        "cross_event_metadata": data.get("cross_event_metadata", {}),
                        "use_time_axis": getattr(self, 'use_time_axis', False),  # 傳遞時間軸設定
                    }
                    
                    logger.debug(f"[CROSS-EVENT] 構建圖表數據:")
                    logger.debug(f"[CROSS-EVENT]   距離點數: {len(chart_data['speed_data']['distance'])}")
                    logger.debug(f"[CROSS-EVENT]   車手1速度點數: {len(chart_data['speed_data']['driver1_speed'])}")
                    logger.debug(f"[CROSS-EVENT]   車手2速度點數: {len(chart_data['speed_data']['driver2_speed'])}")
                    logger.debug(f"[CROSS-EVENT]   車手1 時間點數: {len(chart_data['speed_data']['driver1_time_seconds'])}")
                    logger.debug(f"[CROSS-EVENT]   車手2 時間點數: {len(chart_data['speed_data']['driver2_time_seconds'])}")
                    logger.debug(f"[CROSS-EVENT]   🕒 時間軸模式: {chart_data['use_time_axis']}")
                    
                    # ⚠️ 關鍵：先設置時間軸模式，再更新圖表
                    use_time_axis = chart_data.get('use_time_axis', False)
                    if self.speed_chart_widget and hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
                        logger.debug(f"[CROSS-EVENT] 🕒 設置圖表時間軸模式: {use_time_axis}")
                        self.speed_chart_widget.set_time_axis_mode(use_time_axis)
                    
                    # 直接調用圖表更新方法
                    logger.debug(f"[CROSS-EVENT] 開始更新圖表...")
                    self._update_chart(chart_data)
                    logger.info(f"[CROSS-EVENT] ✅ 跨賽事比較完成")
                else:
                    logger.warning(f"[CROSS-EVENT] ⚠️ 數據中沒有 Speed 遙測")
            else:
                logger.warning(f"[CROSS-EVENT] ⚠️ 數據中沒有 telemetry_comparison")
                
        except Exception as e:
            logger.error(f"[CROSS-EVENT] 數據處理失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_cross_event_load_error(self, error_msg: str) -> None:
        """處理跨賽事比較數據載入錯誤"""
        logger.error(f"[CROSS-EVENT] ❌ 數據載入失敗: {error_msg}")
        # 可選：顯示錯誤提示
        # self.module_error.emit(f"跨賽事比較失敗: {error_msg}")
    
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
            logger.warning(f"[SPEED_MDI] [SHARED_PARAMS] ⚠️  正在更新中，防止遞迴")
            return
        
        self._updating_from_shared = True
        try:
            logger.debug(f"[SPEED_MDI] [SHARED_PARAMS] 🔄 從全域共享池更新參數")
            logger.debug(f"[SPEED_MDI] [SHARED_PARAMS] 收到參數: {params}")
            
            # 更新所有參數
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
            
            # 檢測是否為跨賽事比較
            is_cross_event = (year1 != year2 or session1 != session2)
            
            if is_cross_event:
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS] 🌍 檢測到跨賽事比較:")
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS]   車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS]   車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
                
                # 調用跨賽事比較方法
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS] 🔄 調用 update_cross_event_comparison")
                success = self.update_cross_event_comparison(
                    year1=year1, race1=race1, session1=session1, driver1=driver1, lap1=lap1,
                    year2=year2, race2=race2, session2=session2, driver2=driver2, lap2=lap2,
                    is_fastest=False,
                    use_time_axis=use_time_axis
                )
                
                if success:
                    logger.info(f"[SPEED_MDI] [SHARED_PARAMS] ✅ 跨賽事比較更新成功")
                    # ⚠️ [參數資訊標籤] 更新資訊標籤顯示
                    self._update_info_label()
                    logger.debug(f"[SPEED_MDI] [SHARED_PARAMS] 📋 已更新資訊標籤")
                else:
                    logger.error(f"[SPEED_MDI] [SHARED_PARAMS] ❌ 跨賽事比較更新失敗")
            else:
                # 標準模式（同一賽事比較）
                logger.info(f"[SPEED_MDI] [SHARED_PARAMS] ✅ 標準比較模式:")
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS]   賽事: {year1} {race1} {session1}")
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS]   車手: {driver1} vs {driver2}")
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS]   圈數: 第{lap1}圈 vs 第{lap2}圈")
                
                # 調用標準更新方法
                logger.debug(f"[SPEED_MDI] [SHARED_PARAMS] 🔄 調用 update_lap_parameters")
                success = self.update_lap_parameters(
                    year=year1,
                    race=race1,
                    session=session1,
                    driver1=driver1,
                    driver2=driver2,
                    lap1=lap1,
                    lap2=lap2,
                    is_fastest=False,
                    use_time_axis=use_time_axis
                )
                
                if success:
                    logger.info(f"[SPEED_MDI] [SHARED_PARAMS] ✅ 標準參數更新成功")
                    # ⚠️ [參數資訊標籤] 更新資訊標籤顯示
                    self._update_info_label()
                    logger.debug(f"[SPEED_MDI] [SHARED_PARAMS] 📋 已更新資訊標籤")
                else:
                    logger.error(f"[SPEED_MDI] [SHARED_PARAMS] ❌ 標準參數更新失敗")
                
        except Exception as e:
            logger.error(f"[SPEED_MDI] [SHARED_PARAMS] 更新失敗: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._updating_from_shared = False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 只顯示模組名稱，不包含年份/賽事/賽段"""
        title = f"{tr('speed_analysis', '速度分析')}"
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
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（SpeedAnalysisModule 實例）
            logger.error(f"[SPEED_TITLE_DEBUG] 更新視窗標題失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
    
    def _delayed_title_update(self, title: str) -> None:
        """延遲標題更新 - 採用進站分析模式"""
        try:
            # 使用 parent_window 屬性而不是 parent() 方法
            parent = getattr(self, 'parent_window', None)
            if parent and hasattr(parent, 'setWindowTitle'):
                logger.debug(f"[SPEED_TITLE_DEBUG] 🔄 延遲標題更新: '{title}'")
                parent.setWindowTitle(title)
                parent.update()
                parent.repaint()
                
                # 再次驗證
                actual_title = parent.windowTitle()
                success = (actual_title == title)
                logger.debug(f"[SPEED_TITLE_DEBUG] 延遲更新結果: {success}, 實際標題: '{actual_title}'")
                
                if not success:
                    logger.error(f"[SPEED_TITLE_DEBUG] ❌ 延遲更新也失敗了！可能是視窗引用問題")
                    logger.debug(f"[SPEED_TITLE_DEBUG] 視窗類型: {type(parent)}")
                    logger.debug(f"[SPEED_TITLE_DEBUG] 視窗是否可見: {parent.isVisible()}")
        except Exception as e:
            logger.error(f"[SPEED_MDI] 延遲標題更新失敗: {e}")
    
    # 實現 IAnalysisModule 抽象方法
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return "speed_analysis"
    
    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return tr("speed_analysis", "速度分析")
    
    @property
    def description(self) -> str:
        """模組描述"""
        return tr("speed_analysis_description", "F1賽車速度分析模組，支援雙車手圈速對比")
    
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
            return self.speed_chart_widget
    
    def get_default_size(self):
        """獲取預設尺寸"""
        return (900, 600)
    
    def get_title(self) -> str:
        """返回模組標題 - 實現抽象方法"""
        return f"{tr('speed_analysis', '速度分析')} - {self.current_year} {self.current_race} {self.current_session}"
    
    def supports_sync(self) -> bool:
        """是否支援主程式同步 - 實現抽象方法"""
        return True
    
    def get_parameter_interface(self) -> Optional[QWidget]:
        """返回參數設定介面 - 實現抽象方法"""
        # 速度分析模組暫時不提供參數設定介面
        return None
    
    def reset_chart_view(self):
        """重置圖表視圖 - 與 Show All Data 按鈕整合"""
        logger.debug(f"[SPEED_MDI] 🔄 reset_chart_view() 被調用")
        if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
            logger.info(f"[SPEED_MDI] ✅ 找到 speed_chart_widget，調用 reset_chart_view()")
            self.speed_chart_widget.reset_chart_view()
        else:
            logger.error(f"[SPEED_MDI] ❌ 未找到 speed_chart_widget 屬性")
    
    def cleanup(self):
        """清理資源 - 實現抽象方法
        
        📌 回歸 RPM 模組的簡單清理架構
        清理順序：analysis_manager → data_manager → linkage_manager → chart_widget → main_widget
        """
        try:
            logger.debug(f"[SPEED_MDI] 🧹 開始清理資源...")
            
            # 從分析模組管理器解除註冊
            if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
                try:
                    # 解除註冊圖表組件
                    if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
                        self._analysis_manager.unregister_chart_widget(self.speed_chart_widget)
                    
                    # 解除註冊模組
                    self._analysis_manager.unregister_module(self._module_id)
                    logger.info(f"[SPEED_MDI] ✅ 已從分析模組管理器解除註冊: {self._module_id}")
                    
                except Exception as e:
                    logger.error(f"[SPEED_MDI] 從分析模組管理器解除註冊失敗: {e}")

            if hasattr(self, 'data_manager') and self.data_manager:
                # 🔴 斷開循環引用：先清空 module_ref
                logger.debug(f"[SPEED_MDI] 🔴 斷開循環引用：清理 data_manager.module_ref")
                if hasattr(self.data_manager, 'module_ref'):
                    self.data_manager.module_ref = None
                
                # 🔴 修復：直接調用 cleanup() 即可（內部已包含執行緒清理）
                # cleanup() 會調用 _cleanup_api_worker() 處理 QThread
                if hasattr(self.data_manager, 'cleanup'):
                    self.data_manager.cleanup()
            
            # 🔴 移除不存在的 cleanup_module() 調用（已在上方清理 data_manager）
            # self.cleanup_module()  ← 此方法不存在，導致異常提前退出
            
            if hasattr(self, 'speed_chart_widget') and self.speed_chart_widget:
                # 從連動管理器中取消註冊圖表組件（必須是內部的 chart_widget，不是容器）
                try:
                    logger.debug(f"[SPEED_MDI] [DEBUG] 嘗試導入 linkage_manager...")
                    from modules.gui.lap_analysis.linkage import linkage_manager
                    logger.debug(f"[SPEED_MDI] [DEBUG] linkage_manager 導入成功: {linkage_manager}")
                    
                    if linkage_manager:
                        # ✅ 關鍵修復：必須 unregister 內部的 SpeedChartWidget，不是外層的 SpeedAnalysisChartWidget
                        if hasattr(self.speed_chart_widget, 'chart_widget') and self.speed_chart_widget.chart_widget:
                            logger.debug(f"[SPEED_MDI] [DEBUG] 調用 unregister_module({self.speed_chart_widget.chart_widget})")
                            linkage_manager.unregister_module(self.speed_chart_widget.chart_widget)
                            logger.info(f"[SPEED_MDI] ✅ 已從連動管理器解除註冊圖表組件（內部 chart_widget）")
                        else:
                            logger.warning(f"[SPEED_MDI] [DEBUG] ⚠️ chart_widget 不存在，跳過 unregister")
                    else:
                        logger.warning(f"[SPEED_MDI] [DEBUG] ⚠️ linkage_manager 為 False/None，跳過 unregister")
                except Exception as e:
                    logger.error(f"[SPEED_MDI] 從連動管理器解除註冊失敗: {e}")
                    import traceback

                    traceback.print_exc()
                
                # 清理圖表組件
                if hasattr(self.speed_chart_widget, 'cleanup'):
                    self.speed_chart_widget.cleanup()
                self.speed_chart_widget.deleteLater()
                
            if hasattr(self, 'main_widget') and self.main_widget:
                # 清理主要組件
                self.main_widget.deleteLater()
                self.main_widget = None
            
            # 🔴 最後清理：斷開所有組件引用
            if hasattr(self, 'data_manager'):
                self.data_manager = None
            if hasattr(self, 'speed_chart_widget'):
                self.speed_chart_widget = None
                
            logger.debug(f"[CLEANUP] 速度分析模組資源清理完成")
        except Exception as e:
            logger.error(f"速度分析模組清理失敗: {e}")
    
    def load_data(self, **kwargs) -> bool:
        """載入數據 - 實現抽象方法"""
        try:
            year = str(kwargs.get('year', self.current_year))
            race = kwargs.get('race', self.current_race)
            session = kwargs.get('session', self.current_session)
            driver1 = kwargs.get('driver1', 'VER')
            driver2 = kwargs.get('driver2', 'VER')
            lap1 = kwargs.get('lap1', 1)
            lap2 = kwargs.get('lap2', 1)
            use_time_axis = kwargs.get('use_time_axis', False)
            
            logger.debug(f"[SPEED_MDI] load_data 參數: use_time_axis={use_time_axis}")
            
            # 儲存時間軸設定
            self.use_time_axis = use_time_axis
            
            success = self.data_manager.load_speed_data(
                year=year,
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2
            )
            
            # 數據載入成功後設置時間軸模式
            if success and use_time_axis and self.speed_chart_widget:
                if hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
                    logger.debug(f"[SPEED_MDI] 設置圖表時間軸模式: {use_time_axis}")
                    self.speed_chart_widget.set_time_axis_mode(use_time_axis)
            
            return success
        except Exception as e:
            logger.error(f"[SPEED_MDI] load_data 失敗: {e}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str,
                            driver1: str, driver2: str = None,
                            lap1: int = 1, lap2: int = None,
                            is_fastest: bool = False, use_time_axis: bool = False) -> bool:
        """更新圈速參數並重新載入數據 - 供統一更新介面使用"""
        try:
            logger.debug(f"[SPEED_MDI] 🔄 更新圈速參數...")
            logger.debug(f"[SPEED_MDI] 📊 基本參數: {year} {race} {session}")
            logger.debug(f"[SPEED_MDI] 🏎️ 車手參數: {driver1} vs {driver2}")
            logger.debug(f"[SPEED_MDI] 🏁 圈數參數: 第{lap1}圈 vs 第{lap2}圈")
            logger.debug(f"[SPEED_MDI] ⚡ 最速圈: {is_fastest}")
            logger.debug(f"[TIME_AXIS_DEBUG] 步驟 4: SpeedAnalysisModule.update_lap_parameters 接收參數")
            logger.debug(f"[TIME_AXIS_DEBUG]   use_time_axis 參數值: {use_time_axis}")
            
            # 儲存時間軸設定
            self.use_time_axis = use_time_axis
            logger.debug(f"[TIME_AXIS_DEBUG]   self.use_time_axis 已儲存: {self.use_time_axis}")
            
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
            
            # 重新載入數據
            logger.debug(f"[SPEED_MDI] 🚀 重新載入數據...")
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
                logger.info(f"[SPEED_MDI] ✅ 圈速參數更新成功")
                
                # 應用時間軸設定到圖表
                logger.debug(f"[TIME_AXIS_DEBUG] 步驟 5: SpeedAnalysisModule 準備設置圖表時間軸模式")
                logger.debug(f"[TIME_AXIS_DEBUG]   self.speed_chart_widget 存在: {self.speed_chart_widget is not None}")
                if self.speed_chart_widget:
                    logger.debug(f"[TIME_AXIS_DEBUG]   hasattr(speed_chart_widget, 'set_time_axis_mode'): {hasattr(self.speed_chart_widget, 'set_time_axis_mode')}")
                
                if self.speed_chart_widget and hasattr(self.speed_chart_widget, 'set_time_axis_mode'):
                    logger.debug(f"[TIME_AXIS_DEBUG]   調用 speed_chart_widget.set_time_axis_mode({use_time_axis})")
                    self.speed_chart_widget.set_time_axis_mode(use_time_axis)
                    logger.debug(f"[SPEED_MDI] ⏱️  已設置圖表時間軸模式: {use_time_axis}")
                    logger.info(f"[TIME_AXIS_DEBUG]   ✅ set_time_axis_mode 調用完成")
                else:
                    logger.error(f"[TIME_AXIS_DEBUG]   ❌ 無法調用 set_time_axis_mode (widget不存在或方法不存在)")
            else:
                logger.error(f"[SPEED_MDI] ❌ 數據載入失敗")
                
            return success
            
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（包含 bound method 和 self）
            logger.error(f"[SPEED_MDI] update_lap_parameters 失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
            return False
    
    def refresh_analysis(self) -> None:
        """刷新分析 - 實現抽象方法"""
        try:
            self.data_manager.load_speed_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver1="VER",
                driver2="VER",
                lap1=1,
                lap2=1
            )
        except Exception as e:
            logger.error(f"[SPEED_MDI] refresh_analysis 失敗: {e}")
    
    def clear_data(self):
        """清除數據 - 實現抽象方法"""
        try:
            if self.speed_chart_widget:
                # 清除速度圖表數據
                self.speed_chart_widget.reset_data()
            logger.debug(f"[SPEED_MDI] 數據已清除")
        except Exception as e:
            logger.error(f"[SPEED_MDI] clear_data 失敗: {e}")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據 - 實建抽象方法"""
        try:
            return {
                'module': 'speed_analysis',
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session,
                'initialized': self._initialized,
                'data_loaded': self.data_manager is not None
            }
        except Exception as e:
            logger.error(f"[SPEED_MDI] get_current_data 失敗: {e}")
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

            logger.debug(f"[speed_MDI] 🔍 [API-ONLY] 檢查遙測分析本地緩存: {{target_year}} {{target_race}} {{target_session}}")

            # ✅ 允許：檢查本地 JSON 緩存
            telemetry_file = self._find_telemetry_analysis_file(
                year=target_year,
                race=target_race,
                session=target_session
            )
            if telemetry_file:
                logger.debug(f"[speed_MDI] 📂 [API-ONLY] 找到本地遙測分析緩存: {{telemetry_file}}")
                return True

            # ❌ 禁止：自動創建視窗或啟動 CLI
            # 改為僅提示用戶通過 API 或主視窗遙測模組獲取數據
            logger.warning("[speed_MDI] [API-ONLY] 遙測分析數據不存在於本地緩存")
            logger.debug("💡 [speed_MDI] [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據")
            logger.debug("💡 [speed_MDI] [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8")
            return False

        except Exception as e:
            logger.error(f"[speed_MDI] _check_and_load_telemetry_if_needed 失敗: {{e}}")
            return False

    def _ensure_telemetry_data_for_fastest_laps(self) -> Optional[Dict[str, int]]:
        """確保遙測分析數據存在，並獲取最速圈數據
        
        Returns:
            Dict[str, int]: 車手代碼到最速圈數的映射，例如 {'VER': 15, 'LEC': 23}
        """
        try:
            logger.debug(f"[SPEED_MDI] 🔍 檢查遙測分析數據: {self.current_year} {self.current_race} {self.current_session}")
            
            # 檢查遙測分析JSON檔案是否存在
            telemetry_file = self._find_telemetry_analysis_file()
            
            if not telemetry_file:
                logger.debug(f"[SPEED_MDI] 📡 遙測分析數據不存在，開始自動載入...")
                success = self._trigger_telemetry_analysis()
                if success:
                    # 重新檢查檔案
                    telemetry_file = self._find_telemetry_analysis_file()
                else:
                    logger.error(f"[SPEED_MDI] ❌ 遙測分析載入失敗")
                    return None
            
            if telemetry_file:
                logger.debug(f"[SPEED_MDI] 📂 找到遙測分析檔案: {telemetry_file}")
                return self._extract_fastest_laps_from_telemetry(telemetry_file)
            else:
                logger.error(f"[SPEED_MDI] ❌ 無法獲取遙測分析數據")
                return None
                
        except Exception as e:
            logger.error(f"[SPEED_MDI] _ensure_telemetry_data_for_fastest_laps 失敗: {e}")
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
                    logger.debug(f"[SPEED_MDI] 🎯 找到遙測分析檔案: {matching_files[0]}")
                    return matching_files[0]
            
            # 如果沒找到精確匹配，嘗試模糊搜尋
            fuzzy_pattern = f"json*/telemetry_analysis*{self.current_year}*{self.current_race}*.json"
            matching_files = glob.glob(fuzzy_pattern)
            if matching_files:
                logger.debug(f"[SPEED_MDI] 🔍 模糊搜尋找到遙測分析檔案: {matching_files[0]}")
                return matching_files[0]
            
            logger.error(f"[SPEED_MDI] ❌ 未找到遙測分析檔案")
            return None
            
        except Exception as e:
            logger.error(f"[SPEED_MDI] _find_telemetry_analysis_file 失敗: {e}")
            return None

    def _trigger_telemetry_analysis(self) -> bool:
        """觸發遙測分析載入/生成"""
        try:
            logger.debug(f"[SPEED_MDI] 🚀 觸發遙測分析載入: {self.current_year} {self.current_race} {self.current_session}")
            
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
                            logger.debug(f"[SPEED_MDI] 🎯 找到現有遙測分析視窗: {window_title}")
                            # 激活並刷新遙測分析視窗
                            main_window.mdi_area.setActiveSubWindow(sub_window)
                            return True
                    
                    # API-ONLY 模式：不自動創建視窗
                    logger.debug(f"[SPEED_MDI] � [API-ONLY] 未找到現有遙測分析視窗")
                    logger.debug(f"[SPEED_MDI] 💡 提示：請手動開啟遙測分析模組或通過 API 獲取數據")
                    return False
            
            # 方法2: 透過 API 直接生成遙測分析數據（Function 13）
            logger.debug(f"[SPEED_MDI] 🔧 透過 API 生成遙測分析數據（Function 13）...")
            return self._generate_telemetry_via_api()
            
        except Exception as e:
            logger.error(f"[SPEED_MDI] _trigger_telemetry_analysis 失敗: {e}")
            return False

    def _generate_telemetry_via_api(self) -> bool:
        """透過 REST API 生成遙測分析數據（Function 13）"""
        try:
            from modules.gui.lap_analysis.linkage.telemetry_generation_helper import (
                ensure_telemetry_analysis_via_api,
            )

            year = self.current_year or "2025"
            race = self.current_race or "Japan"
            session = self.current_session or "R"
            driver1 = (self.driver1 or "VER").upper()
            driver2 = (self.driver2 or driver1).upper()

            parent = self.data_manager if hasattr(self, "data_manager") else None

            success, message = ensure_telemetry_analysis_via_api(
                year=int(year),
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                parent=parent,
                timeout_ms=65000,
                is_fastest_lap=True,
            )

            if success:
                logger.info("[SPEED_MDI] ✅ 遙測分析已透過 API 生成")
                return True

            logger.error(f"[SPEED_MDI] ❌ 遙測分析 API 生成失敗: {message}")
            return False

        except Exception as e:
            logger.error(f"[SPEED_MDI] _generate_telemetry_via_api 失敗: {e}")
            return False

    def _extract_fastest_laps_from_telemetry(self, telemetry_file: str) -> Optional[Dict[str, int]]:
        """從遙測分析JSON檔案中提取最速圈數據"""
        try:
            import json
            
            logger.debug(f"[SPEED_MDI] 📊 讀取遙測分析檔案: {telemetry_file}")
            
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
                            logger.debug(f"[SPEED_MDI] 🏁 {driver_code} 最速圈: 第{lap_number}圈")
                        except (ValueError, TypeError):
                            logger.warning(f"[SPEED_MDI] ⚠️ {driver_code} 最速圈數無效: {lap_number}")
            
            if fastest_laps:
                logger.info(f"[SPEED_MDI] ✅ 成功提取 {len(fastest_laps)} 個車手的最速圈數據")
                return fastest_laps
            else:
                logger.error(f"[SPEED_MDI] ❌ 未找到有效的最速圈數據")
                return None
                
        except Exception as e:
            logger.error(f"[SPEED_MDI] _extract_fastest_laps_from_telemetry 失敗: {e}")
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
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] ========== 收到主視窗更新通知 ==========")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] � 原始參數:")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] - param_type: {param_type}")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] - value: {value}")
            
            # 簡化的參數處理
            # 直接處理參數更新
            if param_type == 'year':
                self.current_year = str(value)
                logger.debug(f"[UPDATE] 年份更新為: {self.current_year}")
            elif param_type == 'race':
                self.current_race = str(value)
                logger.debug(f"[UPDATE] 賽事更新為: {self.current_race}")
            elif param_type == 'session':
                self.current_session = str(value)
                logger.debug(f"[UPDATE] 場次更新為: {self.current_session}")
            
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] 📊 當前模組狀態:")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] - 當前年份: {self.current_year}")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] - 當前賽事: {self.current_race}")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] - 當前賽段: {self.current_session}")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] - 當前車手: {self.driver1} vs {self.driver2}")
            logger.debug(f"[SPEED_NOTIFICATION_DEBUG] - 當前圈數: 第{self.lap1}圈 vs 第{self.lap2}圈")
            
            # [TOOL] 更新窗口標題（如果有父窗口）- 使用統一的 get_window_title
            parent = getattr(self, 'parent_window', None)
            if parent and hasattr(parent, 'setWindowTitle'):
                title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                parent.setWindowTitle(title)
                logger.debug(f"[TITLE] 窗口標題更新為: {title}")
            else:
                logger.warning(f"無法更新視窗標題 - 父視窗引用未設置")
            
            # 重新載入數據
            if self.data_manager:
                logger.debug(f"[REFRESH] 重新載入速度數據...")
                self.data_manager.load_speed_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
            logger.info(f"[NOTIFICATION] ⚡ 速度分析模組內容更新成功")
                
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（SpeedAnalysisModule 實例）
            logger.error(f"[NOTIFICATION] ⚡ 速度分析模組內容更新失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據 - 實現抽象方法"""
        try:
            logger.debug(f"[SPEED_MDI] 匯出數據功能尚未實現 (路徑: {export_path}, 格式: {export_format})")
            return False
        except Exception as e:
            logger.error(f"[SPEED_MDI] export_data 失敗: {e}")
            return False

# 註冊速度分析模組到工廠
try:
    from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
    ModuleFactory.register_module(ModuleTypes.TELEMETRY_SPEED, SpeedAnalysisModule)
    logger.info(f"[MODULE_FACTORY] Speed analysis module registered")
except ImportError as e:
    logger.warning(f"[MODULE_FACTORY] 速度分析模組註冊失敗: {e}")
