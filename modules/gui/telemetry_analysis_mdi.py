#!/usr/bin/env python3
"""
F1T 遙測分析 MDI 模組
基於開發設計文檔實現的車手遙測分析 GUI 模組
參考進站分析模組的UI風格和架構
"""

import sys
import os
import json
import datetime
import traceback
# import threading  # ⚠️ [API-ONLY] 已移除：GUI 不再使用 threading 執行 CLI
# import subprocess  # ⚠️ [API-ONLY] 已移除：GUI 不再調用 subprocess 執行 CLI
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import requests
from core.api_base_url import resolve_api_base_url
from core.api_runtime_state import is_api_available
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QStatusBar, QToolBar, QAction,
    QHeaderView, QDialog, QDialogButtonBox, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QTextEdit, QMessageBox, QFrame,
    QTabWidget, QScrollArea, QSplitter, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 導入翻譯函數
from core.gui_i18n import tr

# 導入分析模組介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule, ModuleFactory, ModuleTypes
except ImportError:
    # 如果都失敗，定義一個基本的接口
    from PyQt5.QtCore import QObject
    class IAnalysisModule(QObject):
        def __init__(self, parent=None):
            super().__init__(parent)


class TelemetryAnalysisApiWorker(QThread):
    """背景 API worker，用於載入遙測分析資料 (Function 12)。"""

    progress = pyqtSignal(int, str)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 75.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout

    def run(self) -> None:
        try:
            self.progress.emit(12, "呼叫 API 取得遙測分析資料...")
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 12,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(55, "API 回應解析中...")
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API 回傳必須為 JSON 物件")
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API 回傳 success=False"))

            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API 回傳缺少 data 欄位")

            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }

            self.progress.emit(90, "API 遙測分析載入完成")
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:
            self.failure.emit(str(exc))
        finally:
            self.progress.emit(100, "API 任務結束")


class TelemetryDataManager(QObject):
    """
    遙測數據管理器 - 專門處理Function 12的遙測分析數據
    支援JSON優先載入和CLI自動生成
    參考進站分析的數據管理器架構
    """
    
    # 信號定義
    telemetry_loaded = pyqtSignal(dict)          # 遙測數據載入完成
    telemetry_reload_requested = pyqtSignal()    # 遙測數據重載請求
    loading_started = pyqtSignal()               # 開始載入
    loading_finished = pyqtSignal()              # 載入完成
    error_occurred = pyqtSignal(str)             # 錯誤發生
    loading_progress = pyqtSignal(int)           # 載入進度
    status_changed = pyqtSignal(str)             # 狀態變更
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        self.current_year = None
        self.current_race = None
        self.current_session = None
        self.current_data = {}
        self._is_loading = False
        self._generation_params = None
        self._pending_params: Dict[str, Any] = {}
        self._cli_generation_context: Dict[str, Any] = {}
        self._api_base_url = self._determine_api_base_url()
        self._api_timeout = 10.0
        self._api_worker: Optional[TelemetryAnalysisApiWorker] = None
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        
        # 檔案生成監控定時器（參考進站分析）
        self._generation_timer = QTimer()
        self._generation_timer.timeout.connect(self._check_generation_progress)
        
        self._generation_timeout_timer = QTimer()
        self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)

        fallback_state = "啟用" if self._allow_local_fallback else "停用"
        print(
            f"[TELEMETRY_MANAGER] 初始化完成，API 基底網址: {self._api_base_url}，"
            f"本地 JSON 後備已{fallback_state} (策略: {self._fallback_policy_reason})"
        )
    
    def loadTelemetryData(self, year: str, race: str, session: str, force_refresh: bool = False) -> bool:
        """載入遙測分析資料 - API 優先，失敗時可回退至 JSON/CLI。"""
        if self._is_loading:
            print("[TELEMETRY] 正在載入中，跳過重複請求")
            return False

        self._stop_generation_monitoring()
        self._cleanup_api_worker()

        self._is_loading = True
        self.loading_started.emit()
        self.loading_progress.emit(5)
        self.status_changed.emit("準備載入遙測分析資料...")

        self.current_year = year
        self.current_race = race
        self.current_session = session

        self._pending_params = {
            "year": year,
            "race": race,
            "session": session,
            "force_refresh": force_refresh,
        }
        self._api_base_url = self._determine_api_base_url()

        try:
            # 在測試或指定情境下優先使用本地快取，避免外部 API 造成測試不穩定
            if self._should_prioritize_local_cache():
                json_file = self._find_telemetry_file(year, race, session)
                if json_file:
                    self.status_changed.emit("使用本地 JSON 快取載入遙測資料")
                    self.loading_progress.emit(60)
                    self._cli_generation_context = {
                        "fallback_reason": "prioritize-local-cache",
                        "generated_via_cli": False,
                        "force_refresh": force_refresh,
                        "data_source": "local-json",
                    }
                    QTimer.singleShot(
                        0,
                        lambda: self._load_telemetry_json(
                            json_file,
                            data_source="local-json",
                            fallback_reason="prioritize-local-cache",
                            generated_via_cli=False,
                            force_refresh=force_refresh,
                        )
                    )
                    return True

            self.loading_progress.emit(10)
            self.status_changed.emit("正在透過 API 載入遙測分析資料...")

            if not self._is_api_available():
                msg = "偵測到 API 服務未啟動，改用本地 JSON 後備"
                print(f"[TELEMETRY] {msg}")
                self.status_changed.emit(msg)
                if self._fallback_to_local("API 服務未啟動"):
                    return True

                self.error_occurred.emit("找不到可用的遙測資料來源，請啟動 API 或提供本地 JSON")
                self.loading_finished.emit()
                self._is_loading = False
                return False

            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            print(f"[TELEMETRY] 啟動 API 請求失敗: {exc}")
            self.status_changed.emit("API 請求初始化失敗，改用本地 JSON/CLI 後備流程")
            if self._fallback_to_local(str(exc)):
                return True

            self.error_occurred.emit(f"載入遙測數據失敗: {exc}")
            self.loading_finished.emit()
            self._is_loading = False
            return False

    def _should_prioritize_local_cache(self) -> bool:
        """判斷是否應優先使用本地快取以提升測試穩定性"""
        try:
            if os.getenv("F1T_FORCE_LOCAL_TELEMETRY_CACHE") in {"1", "true", "True"}:
                return True
            # Pytest 執行期間預設優先使用本地快取，避免網路波動導致測試失敗
            if os.getenv("PYTEST_CURRENT_TEST"):
                return True
        except Exception:
            pass
        return False
    def _determine_api_base_url(self) -> str:
        return resolve_api_base_url(
            event_logger=lambda message: print(f"[TELEMETRY] {message}")
        )

    def _is_api_available(self) -> bool:
        available = is_api_available()
        if not available:
            self._debug("API marked offline by shared runtime cache")
        return available
    def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
        env_value = os.getenv("F1T_ALLOW_TELEMETRY_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_TELEMETRY_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_TELEMETRY_JSON_FALLBACK={env_value}"
        return True, "預設策略 (允許本地 JSON 後備)"

    def set_local_fallback_allowed(self, allowed: bool, reason: Optional[str] = None) -> None:
        self._allow_local_fallback = bool(allowed)
        self._fallback_policy_reason = reason or "手動覆寫"
        state = "啟用" if self._allow_local_fallback else "停用"
        print(f"[TELEMETRY_MANAGER] 本地 JSON 後備手動設為{state} (原因: {self._fallback_policy_reason})")

    def set_api_base_url(self, base_url: Optional[str]) -> None:
        if base_url:
            self._api_base_url = str(base_url).rstrip('/')
            print(f"[TELEMETRY_MANAGER] API 基底網址更新為 {self._api_base_url}")

    def _cleanup_api_worker(self) -> None:
        """
        異步清理 API Worker（方案 2: 信號驅動清理）
        ✅ 不阻塞主線程
        ✅ 使用信號自動清理
        """
        if self._api_worker:
            try:
                if self._api_worker.isRunning():
                    # 1. 請求中斷（非阻塞）
                    self._api_worker.requestInterruption()
                    self._api_worker.quit()
                    
                    # 2. 使用信號自動清理（當 Worker 停止時）
                    def on_worker_stopped():
                        """Worker 停止後自動清理"""
                        if self._api_worker:
                            self._api_worker.deleteLater()
                        self._api_worker = None
                    
                    self._api_worker.finished.connect(on_worker_stopped)
                    
                    # 3. 延遲強制終止（1 秒後，但不阻塞主線程）
                    from PyQt5.QtCore import QTimer
                    def force_terminate():
                        # ✅ 安全檢查：確保 worker 仍然有效且未被刪除
                        try:
                            if self._api_worker and self._api_worker.isRunning():
                                print("[WARNING] telemetry_analysis API Worker 未在 1 秒內停止，強制終止")
                                self._api_worker.terminate()
                        except (RuntimeError, AttributeError):
                            # Worker 已被刪除，無需處理
                            pass
                    
                    QTimer.singleShot(1000, force_terminate)
                else:
                    # Worker 已停止，立即清理
                    self._api_worker.deleteLater()
                    self._api_worker = None
            except Exception as e:
                print(f"[ERROR] telemetry_analysis cleanup exception: {e}")
                self._api_worker = None

    def _start_api_request(self, params: Dict[str, Any]) -> None:
        self._cleanup_api_worker()

        timeout = getattr(self, "_api_timeout", 75.0)
        self._api_worker = TelemetryAnalysisApiWorker(
            self._api_base_url,
            params,
            timeout=timeout,
            parent=self
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()

    def _on_api_progress(self, value: int, message: str) -> None:
        try:
            bounded = max(0, min(int(value), 100))
            self.loading_progress.emit(bounded)
            if message:
                self.status_changed.emit(message)
        except Exception:
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        try:
            raw_data = payload.get("data")
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"
            self._cli_generation_context = {}

            if not self._validate_telemetry_data(raw_data):
                raise ValueError("API 回傳數據格式不符合遙測分析預期")

            processed_data = raw_data
            if isinstance(processed_data, dict):
                metadata = processed_data.setdefault("metadata", {})
                metadata.setdefault("data_source", "api")
                metadata.setdefault("year", self.current_year)
                metadata.setdefault("race", self.current_race)
                metadata.setdefault("session", self.current_session)
                if self._pending_params.get("force_refresh"):
                    metadata["requested_force_refresh"] = True
                if self._last_api_meta:
                    metadata["api"] = self._last_api_meta

            self.current_data = processed_data
            self.loading_progress.emit(100)
            self.status_changed.emit("已從 API 載入遙測分析資料")
            self.telemetry_loaded.emit(processed_data)
            self.loading_finished.emit()
            self._is_loading = False

        except Exception as exc:
            print(f"[TELEMETRY] 處理 API 回傳失敗: {exc}")
            self.status_changed.emit("API 數據格式錯誤，改用本地 JSON/CLI")
            if self._fallback_to_local(str(exc)):
                return
            self.error_occurred.emit(f"API 數據處理失敗: {exc}")
            self.loading_finished.emit()
            self._is_loading = False

    def _on_api_error(self, message: str) -> None:
        print(f"[TELEMETRY] API 請求失敗: {message}")
        self.status_changed.emit("API 請求失敗，改用本地 JSON/CLI 後備流程")
        if self._fallback_to_local(message):
            return
        self.error_occurred.emit(f"API 請求失敗: {message}")
        self.loading_finished.emit()
        self._is_loading = False

    def _fallback_to_local(self, reason: str) -> bool:
        params = dict(self._pending_params) if self._pending_params else {}
        if not params:
            params = {
                "year": self.current_year,
                "race": self.current_race,
                "session": self.current_session,
                "force_refresh": False,
            }

        if not self._allow_local_fallback:
            message = (
                "API 載入失敗，且本地 JSON 後備已停用。"
                " 如需啟用，請設定環境變數 F1T_ALLOW_TELEMETRY_JSON_FALLBACK=1 或呼叫 set_local_fallback_allowed(True)。"
            )
            print(f"[TELEMETRY] {message} 詳細: {reason}")
            return False

        self.status_changed.emit("API 失敗，改用本地 JSON/CLI 數據")
        self.loading_progress.emit(35)
        success = self._start_local_workflow(params, fallback_reason=reason)
        if not success:
            print(f"[TELEMETRY] 本地 JSON 後備啟動失敗: {reason}")
        return success

    def _start_local_workflow(self, params: Dict[str, Any], fallback_reason: Optional[str] = None) -> bool:
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")

        if not year or not race or not session:
            print("[TELEMETRY] 本地工作流程缺少必要參數")
            return False

        json_file = self._find_telemetry_file(year, race, session)
        if json_file:
            print(f"[TELEMETRY] 使用本地遙測JSON檔案: {json_file}")
            self.loading_progress.emit(70)
            self.status_changed.emit("使用本地 JSON 快取載入遙測資料")
            self._cli_generation_context = {
                "fallback_reason": fallback_reason,
                "force_refresh": params.get("force_refresh", False),
                "generated_via_cli": False,
                "data_source": "local-json",
            }
            QTimer.singleShot(
                10,
                lambda: self._load_telemetry_json(
                    json_file,
                    data_source="local-json",
                    fallback_reason=fallback_reason,
                    generated_via_cli=False,
                    force_refresh=params.get("force_refresh", False)
                )
            )
            return True

        print("[TELEMETRY] 找不到遙測JSON，且 CLI 生成在 API-ONLY 模式下已禁用")
        self.loading_progress.emit(40)
        self.status_changed.emit("未找到本地遙測 JSON，請先啟動 API 或手動生成資料")
        self.error_occurred.emit(
            "找不到遙測資料檔案，且自動 CLI 生成已禁用。請啟動 API 或手動執行 CLI 生成 JSON 後重試。"
        )
        self._is_loading = False
        return False
    
    def _find_telemetry_file(self, year: str, race: str, session: str) -> Optional[str]:
        """搜尋遙測分析數據檔案"""
        try:
            print(f"[TELEMETRY] 搜尋遙測數據檔案: {year} {race} {session}")
            
            search_dirs = ["json", "json_exports", "cache"]
            
            # 檔案命名模式
            patterns = [
                f"all_drivers_telemetry_analysis_{year}_{race}_{session}.json",
                f"telemetry_analysis_{year}_{race}_{session}.json",
                f"all_drivers_telemetry_{year}_{race}_{session}.json",
                f"driver_telemetry_analysis_{year}_{race}_{session}.json",
            ]
            
            # 搜尋多個目錄
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                    
                for pattern in patterns:
                    search_path = os.path.join(search_dir, pattern)
                    if os.path.exists(search_path):
                        print(f"[FOUND] 遙測JSON檔案: {search_path}")
                        return search_path
            
            # 模糊搜尋 - 嚴格匹配賽事名稱，避免誤判比較遙測檔案
            import glob
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                    
                # 只使用包含賽事名稱的模糊模式，避免載入錯誤檔案
                fuzzy_patterns = [
                    f"*telemetry*{year}*{race}*{session}*.json",
                    f"*telemetry*{year}*{race}*.json",
                ]
                
                for fuzzy_pattern in fuzzy_patterns:
                    search_path = os.path.join(search_dir, fuzzy_pattern)
                    files = glob.glob(search_path)
                    if files:
                        # 三重檢查：確保檔案名稱包含正確的賽事名稱且不是比較遙測檔案
                        for file_path in files:
                            filename = os.path.basename(file_path).lower()
                            
                            # 排除比較遙測檔案和其他非分析檔案
                            if any(exclude_pattern in filename for exclude_pattern in [
                                "comparison", "compare", "vs", "_vs_", "raw_data", "export"
                            ]):
                                print(f"[SKIP] 跳過非分析檔案: {file_path}")
                                continue
                                
                            # 確保包含賽事名稱
                            if race.lower() in filename:
                                # 優先選擇包含 "analysis" 或 "all_drivers" 的檔案
                                if any(priority_pattern in filename for priority_pattern in [
                                    "analysis", "all_drivers", "telemetry_analysis"
                                ]):
                                    # 快速驗證檔案內容是否為有效的遙測分析檔案
                                    if self._quick_validate_file(file_path):
                                        print(f"[FUZZY] 遙測JSON檔案 (優先): {file_path}")
                                        return file_path
                                    else:
                                        print(f"[SKIP] 檔案驗證失敗: {file_path}")
                                        continue
                                else:
                                    print(f"[FUZZY] 遙測JSON檔案 (備選): {file_path}")
                                    backup_file = file_path
                        
                        # 如果沒找到優先檔案，驗證並使用備選檔案
                        if 'backup_file' in locals():
                            if self._quick_validate_file(backup_file):
                                print(f"[FUZZY] 使用備選遙測JSON檔案: {backup_file}")
                                return backup_file
                            else:
                                print(f"[SKIP] 備選檔案驗證失敗: {backup_file}")
            
            print(f"[NOT_FOUND] 未找到遙測JSON檔案")
            return None
                
        except Exception as e:
            print(f"[ERROR] 搜尋遙測檔案時發生錯誤: {str(e)}")
            self.error_occurred.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None
    
    def _quick_validate_file(self, file_path: str) -> bool:
        """快速驗證檔案是否為有效的遙測分析檔案"""
        try:
            # 簡單檢查檔案內容的前幾行，避免完整載入大檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                # 讀取前1000個字符來快速檢查
                preview = f.read(1000)
                
            # 檢查是否包含遙測分析的關鍵字段
            required_patterns = ['all_drivers_telemetry', 'driver_info', 'lap_time_analysis']
            exclude_patterns = ['comparison', 'compare', 'vs']
            
            # 確保包含必要字段
            if not any(pattern in preview for pattern in required_patterns):
                return False
                
            # 確保不包含排除字段
            if any(pattern in preview for pattern in exclude_patterns):
                return False
                
            return True
            
        except Exception as e:
            print(f"[ERROR] 快速驗證檔案失敗: {e}")
            return False
    
    def _load_telemetry_json(
        self,
        file_path: str,
        *,
        data_source: str = "local-json",
        fallback_reason: Optional[str] = None,
        generated_via_cli: bool = False,
        force_refresh: bool = False
    ):
        """載入遙測JSON檔案並附加來源中繼資料"""
        try:
            print(f"[LOAD] 開始載入遙測檔案: {file_path}")
            self.loading_progress.emit(70)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 驗證數據格式
            if self._validate_telemetry_data(data):
                self.current_data = data
                self._last_data_source = data_source
                metadata = self.current_data.setdefault("metadata", {})
                metadata.setdefault("data_source", data_source)
                metadata.setdefault("year", self.current_year)
                metadata.setdefault("race", self.current_race)
                metadata.setdefault("session", self.current_session)
                metadata.setdefault("fallback_policy", self._fallback_policy_reason)
                if fallback_reason:
                    metadata["fallback_reason"] = fallback_reason
                if generated_via_cli:
                    metadata["generated_via_cli"] = True
                if force_refresh:
                    metadata["requested_force_refresh"] = True
                self.loading_progress.emit(100)
                self.status_changed.emit("遙測數據載入完成")
                self.telemetry_loaded.emit(data)
                print(f"[SUCCESS] 遙測數據載入完成")
            else:
                self.error_occurred.emit("載入的遙測數據格式無效")
                
        except Exception as e:
            print(f"[ERROR] 載入遙測JSON檔案失敗: {e}")
            self.error_occurred.emit(f"載入JSON檔案失敗: {str(e)}")
        
        finally:
            self._cli_generation_context = {}
            self._generation_params = None
            self.loading_finished.emit()
            self._is_loading = False
    
    def _validate_telemetry_data(self, data: dict) -> bool:
        """驗證遙測數據格式 - 增強版，排除比較遙測檔案"""
        try:
            if not isinstance(data, dict):
                print(f"[ERROR] 遙測數據不是字典格式")
                return False
            
            # 首先檢查是否為比較遙測檔案（應該被排除）
            comparison_indicators = [
                'comparison_data', 'driver_comparison', 'lap_comparison', 
                'telemetry_comparison', 'compare_analysis'
            ]
            
            for indicator in comparison_indicators:
                if indicator in data:
                    print(f"[ERROR] 檢測到比較遙測檔案，拒絕載入: {indicator}")
                    return False
            
            # 檢查不同可能的數據格式
            telemetry_data = None
            
            # 格式1: 標準格式 - data.all_drivers_telemetry
            if 'data' in data and isinstance(data['data'], dict):
                if 'all_drivers_telemetry' in data['data']:
                    telemetry_data = data['data']['all_drivers_telemetry']
                    print(f"[INFO] 檢測到標準格式：data.all_drivers_telemetry")
            
            # 格式2: 直接格式 - all_drivers_telemetry
            elif 'all_drivers_telemetry' in data:
                telemetry_data = data['all_drivers_telemetry']
                print(f"[INFO] 檢測到直接格式：all_drivers_telemetry")
            
            if telemetry_data and isinstance(telemetry_data, dict):
                # 檢查是否有車手數據且數量合理（比較遙測通常只有2個車手）
                if len(telemetry_data) > 0:
                    # 檢查第一個車手的數據結構
                    first_driver = list(telemetry_data.values())[0]
                    required_keys = ['driver_info', 'lap_time_analysis', 'sector_analysis']
                    
                    for key in required_keys:
                        if key not in first_driver:
                            print(f"[ERROR] 缺少必需的遙測數據字段: {key}")
                            return False
                    
                    # 額外檢查：所有車手分析通常包含多位車手（>= 3）
                    # 比較遙測通常只有2位車手
                    driver_count = len(telemetry_data)
                    if driver_count >= 3:
                        print(f"[OK] 遙測數據格式驗證通過，包含 {driver_count} 位車手（符合所有車手分析）")
                        return True
                    elif driver_count == 2:
                        # 檢查是否真的是所有車手分析（可能是只有2位車手的比賽）
                        # 檢查是否有analysis_summary等指標
                        if 'analysis_summary' in data.get('data', {}):
                            print(f"[OK] 遙測數據格式驗證通過，包含 {driver_count} 位車手（含分析摘要）")
                            return True
                        else:
                            print(f"[WARNING] 只有2位車手且無分析摘要，可能是比較遙測檔案")
                            return False
                    else:
                        print(f"[ERROR] 車手數量不足: {driver_count}")
                        return False
            
            print(f"[ERROR] 無效的遙測數據格式")
            return False
            
        except Exception as e:
            print(f"[ERROR] 驗證遙測數據時發生錯誤: {e}")
            return False
    
    def _generate_telemetry_via_cli(self, year: str, race: str, session: str, force_refresh: bool = False) -> bool:
        """透過 CLI 生成遙測分析數據（已於 API-ONLY 模式中禁用）"""
        print("[TELEMETRY] ⚠️  [API-ONLY] CLI 調用已禁用，無法自動生成遙測數據")
        print("[TELEMETRY] 💡 請使用 API 取得最新資料或手動執行 CLI 後再重試")
        self.error_occurred.emit(
            "API 載入失敗且本地無快取。請手動執行 CLI 生成遙測 JSON 或啟動 API 後重試。"
        )
        self._is_loading = False
        return False
    
    def _start_cli_generation(self, year: str, race: str, session: str) -> bool:
        """
        [已禁用] 啟動 CLI 生成流程
        
        ⚠️ API-ONLY 模式: 此方法已改為提示訊息，不再執行 CLI
        
        GUI 模組不應自動調用 CLI 進程。請使用以下替代方案：
        
        方案 1 [推薦]: 通過 REST API 調用
            - 確保 API 服務器正在運行 (refactored_api.py)
            - 使用 POST /api/v2/analysis/execute
            - 參數: {"function_id": "12", "year": "{year}", "race": "{race}", "session": "{session}"}
        
        方案 2: 使用已存在的本地 JSON 檔案
            - 檢查 json/ 目錄是否有對應的遙測分析結果
        
        方案 3: 手動執行 CLI 命令生成數據
            - PowerShell 執行: python f1_analysis_modular_main.py -f 12 -y {year} -r {race} -s {session}
            - 等待完成後，GUI 會自動檢測並載入生成的 JSON
        
        Args:
            year: 賽季年份
            race: 賽事名稱
            session: 賽事階段 (R/Q/FP1/FP2/FP3)
        
        Returns:
            False (固定返回 False，表示不執行)
        """
        command = f"python f1_analysis_modular_main.py -f 12 -y {year} -r {race} -s {session}"
        
        print("\n" + "="*80)
        print("⚠️  [API-ONLY 模式] GUI 不再自動執行 CLI 命令")
        print("="*80)
        print("\n💡 方案 1 [推薦]: 通過 REST API 調用")
        print(f"   - 確保 API 服務器正在運行: python refactored_api.py")
        print(f"   - POST /api/v2/analysis/execute")
        print(f'   - Payload: {{"function_id": "12", "year": "{year}", "race": "{race}", "session": "{session}"}}')
        print("\n💡 方案 2: 使用已存在的本地 JSON 檔案")
        print("   - 檢查 json/ 目錄")
        print("\n💡 方案 3: 手動執行 CLI 命令")
        print(f"   - PowerShell: {command}")
        print("="*80 + "\n")
        
        return False
    
    def _start_generation_monitoring(self, year: str, race: str, session: str):
        """啟動檔案生成監控"""
        # 確保定時器存在
        if not hasattr(self, '_generation_timer'):
            self._generation_timer = QTimer()
            self._generation_timer.timeout.connect(self._check_generation_progress)
        
        if not hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer = QTimer()
            self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._generation_timer.start(5000)
        self._generation_timeout_timer.start(180000)
        self.loading_progress.emit(40)
        
    def _check_generation_progress(self):
        """檢查檔案生成進度"""
        if hasattr(self, '_generation_params') and self._generation_params:
            params = self._generation_params
            if isinstance(params, dict):
                year = params.get("year")
                race = params.get("race")
                session = params.get("session")
            else:
                year, race, session = params
                params = {
                    "year": year,
                    "race": race,
                    "session": session,
                    "force_refresh": False,
                }
            
            # 檢查是否有新檔案生成
            json_file = self._find_telemetry_file(year, race, session)
            
            if json_file:
                print(f"[OK] [CLI_GEN] 遙測檔案生成完成: {json_file}")
                
                # 停止監控
                self._stop_generation_monitoring()
                
                # 載入新生成的檔案
                context = self._cli_generation_context or {}
                QTimer.singleShot(
                    10,
                    lambda: self._load_telemetry_json(
                        json_file,
                        data_source=context.get("data_source", "local-json"),
                        fallback_reason=context.get("fallback_reason"),
                        generated_via_cli=context.get("generated_via_cli", True),
                        force_refresh=context.get("force_refresh", False)
                    )
                )
            else:
                print(f"⏳ [CLI_GEN] 繼續等待遙測檔案生成...")
                self.loading_progress.emit(50)
                
    def _on_generation_timeout(self):
        """處理生成超時"""
        print(f"[TIME] [CLI_GEN] 遙測檔案生成超時")
        self._stop_generation_monitoring()
        self.error_occurred.emit("遙測數據生成超時，請檢查網路連線或稍後重試")
        self._generation_params = None
        self._cli_generation_context = {}
        self.loading_finished.emit()
        self._is_loading = False
        
    def _stop_generation_monitoring(self):
        """停止生成監控"""
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()


class NumericTableWidgetItem(QTableWidgetItem):
    """支援數值排序的表格項目"""
    def __init__(self, text, sort_value=None):
        super().__init__(text)
        self._sort_value = sort_value
    
    def __lt__(self, other):
        """重寫小於比較，用於排序"""
        try:
            # 如果有自定義排序值，使用它
            if hasattr(self, '_sort_value') and self._sort_value is not None:
                if hasattr(other, '_sort_value') and other._sort_value is not None:
                    return self._sort_value < other._sort_value
            
            # 否則嘗試數值比較
            try:
                return float(self.text()) < float(other.text())
            except ValueError:
                # 如果轉換失敗，使用字串比較
                return self.text() < other.text()
        except:
            return super().__lt__(other)


class DriverTelemetryOverviewWidget(QWidget):
    """
    車手遙測概覽控件 - 分頁1
    基於Function 12的所有車手遙測數據顯示概覽統計
    參考進站分析的表格風格
    """
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        print(f"📊 [TELEMETRY_OVERVIEW] 初始化概覽Widget...")
        self.data_manager = data_manager
        self.telemetry_data = {}
        self.setupUI()
        print(f"✅ [TELEMETRY_OVERVIEW] 概覽Widget初始化完成")
        
    def setupUI(self):
        """設置使用者界面"""
        print(f"📊 [TELEMETRY_OVERVIEW] 設置概覽UI...")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 統計卡片區域
        self.setup_statistics_cards()
        
        # 車手概覽表格
        self.setup_overview_table()
        
        print(f"✅ [TELEMETRY_OVERVIEW] 概覽UI設置完成")
        
    def setup_statistics_cards(self):
        """設置統計卡片"""
        cards_layout = QHBoxLayout()
        
        # 創建統計卡片 - 只顯示最快車手和平均圈速
        # self.total_drivers_card = self.create_stat_card(tr("total_drivers", "總車手數"), "0", "👥")  # 隱藏
        self.fastest_driver_card = self.create_stat_card(tr("fastest_driver", "最快車手"), "N/A", "🏆")
        self.avg_laptime_card = self.create_stat_card(tr("avg_laptime", "平均圈速"), "N/A", "⏱️")
        # self.total_pitstops_card = self.create_stat_card(tr("total_pitstops", "總進站次數"), "0", "🛞")  # 隱藏
        
        # cards_layout.addWidget(self.total_drivers_card)  # 隱藏
        cards_layout.addWidget(self.fastest_driver_card)
        cards_layout.addWidget(self.avg_laptime_card)
        # cards_layout.addWidget(self.total_pitstops_card)  # 隱藏
        cards_layout.addStretch()
        
        self.layout().addLayout(cards_layout)
        
    def create_stat_card(self, title, value, icon):
        """創建統計卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setFixedSize(150, 80)
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 標題和圖標
        title_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 數值
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(title_layout)
        layout.addWidget(value_label)
        
        # 保存數值標籤的引用
        setattr(card, 'value_label', value_label)
        
        return card
        
    def setup_overview_table(self):
        """設置車手概覽表格"""
        self.overview_table = QTableWidget()
        
        # 設置表格標題
        headers = [
            "車手", "車隊", "初始排名", "最終排名", 
            "最快圈時間", "最速圈數", "平均圈速", "圈速穩定性",
            "最佳S1", "最佳S2", "最佳S3", "進站次數"
        ]
        
        self.overview_table.setColumnCount(len(headers))
        self.overview_table.setHorizontalHeaderLabels(headers)
        
        # 設置表格樣式（參考進站分析）
        self.configure_table_style()
        
        self.layout().addWidget(self.overview_table)
        
    def configure_table_style(self):
        """設置表格樣式"""
        # 設置欄位寬度
        widths = [60, 120, 80, 80, 100, 80, 100, 100, 80, 80, 80, 80]
        for i, width in enumerate(widths):
            self.overview_table.setColumnWidth(i, width)
        
        # 表格樣式（參考進站分析的風格）
        self.overview_table.setAlternatingRowColors(True)
        self.overview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.overview_table.horizontalHeader().setStretchLastSection(True)
        
        # 啟用Qt內建排序功能
        self.overview_table.setSortingEnabled(True)
        
        # 移除自定義排序邏輯，使用Qt內建排序
        # self.overview_table.horizontalHeader().setSectionsClickable(True)
        # self.overview_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        self.overview_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #dee2e6;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
    def on_header_clicked(self, logical_index):
        """處理表格標題點擊事件，實現自定義排序"""
        print(f"[SORT] 點擊欄位 {logical_index}")
        
        # 獲取當前欄位的排序狀態，預設為升序
        current_order = self._sort_columns.get(logical_index, Qt.AscendingOrder)
        
        # 切換排序方向
        new_order = Qt.DescendingOrder if current_order == Qt.AscendingOrder else Qt.AscendingOrder
        self._sort_columns[logical_index] = new_order
        
        print(f"[SORT] 欄位 {logical_index} 排序: {'降序' if new_order == Qt.DescendingOrder else '升序'}")
        
        if logical_index in [4, 5, 7, 8, 9]:  # 時間相關欄位
            self.sort_by_time_column(logical_index, new_order)
        elif logical_index in [2, 3, 6, 10]:  # 數值欄位
            self.sort_by_numeric_column(logical_index, new_order)
        else:
            # 文字欄位使用簡單排序
            self.sort_by_text_column(logical_index, new_order)
    
    def sort_by_time_column(self, column, sort_order):
        """按時間欄位排序"""
        try:
            print(f"[SORT] 時間排序 - 欄位 {column}, 順序: {'降序' if sort_order == Qt.DescendingOrder else '升序'}")
            
            # 獲取所有行的數據
            rows_data = []
            for row in range(self.overview_table.rowCount()):
                row_data = []
                for col in range(self.overview_table.columnCount()):
                    item = self.overview_table.item(row, col)
                    row_data.append(item.text() if item else "")
                rows_data.append(row_data)
            
            # 按時間排序
            def time_sort_key(row):
                time_text = row[column]
                parsed_time = self.parse_time_to_seconds(time_text)
                return parsed_time if parsed_time is not None else float('inf')
            
            reverse = (sort_order == Qt.DescendingOrder)
            rows_data.sort(key=time_sort_key, reverse=reverse)
            
            # 更新表格
            self._update_table_with_sorted_data(rows_data)
            
            # 更新排序指示器
            header = self.overview_table.horizontalHeader()
            header.setSortIndicator(column, sort_order)
            
        except Exception as e:
            print(f"[ERROR] 時間排序失敗: {e}")
    
    def sort_by_numeric_column(self, column, sort_order):
        """按數值欄位排序"""
        try:
            print(f"[SORT] 數值排序 - 欄位 {column}, 順序: {'降序' if sort_order == Qt.DescendingOrder else '升序'}")
            
            # 獲取所有行的數據
            rows_data = []
            for row in range(self.overview_table.rowCount()):
                row_data = []
                for col in range(self.overview_table.columnCount()):
                    item = self.overview_table.item(row, col)
                    row_data.append(item.text() if item else "")
                rows_data.append(row_data)
            
            # 按數值排序
            def numeric_sort_key(row):
                value_text = row[column]
                try:
                    # 特殊處理排名欄位：移除可能的非數字字符
                    if column in [2, 3]:  # 排名欄位
                        # 提取數字部分，處理如 "9位" 或 "第9名" 的情況
                        import re
                        numbers = re.findall(r'\d+', str(value_text))
                        if numbers:
                            return int(numbers[0])
                    
                    # 一般數值處理
                    return float(value_text)
                except (ValueError, IndexError):
                    return float('inf')  # 無效值排到最後
            
            reverse = (sort_order == Qt.DescendingOrder)
            rows_data.sort(key=numeric_sort_key, reverse=reverse)
            
            # 更新表格
            self._update_table_with_sorted_data(rows_data)
            
            # 更新排序指示器
            header = self.overview_table.horizontalHeader()
            header.setSortIndicator(column, sort_order)
            
        except Exception as e:
            print(f"[ERROR] 數值排序失敗: {e}")
    
    def sort_by_text_column(self, column, sort_order):
        """按文字欄位排序"""
        try:
            print(f"[SORT] 文字排序 - 欄位 {column}, 順序: {'降序' if sort_order == Qt.DescendingOrder else '升序'}")
            
            # 獲取所有行的數據
            rows_data = []
            for row in range(self.overview_table.rowCount()):
                row_data = []
                for col in range(self.overview_table.columnCount()):
                    item = self.overview_table.item(row, col)
                    row_data.append(item.text() if item else "")
                rows_data.append(row_data)
            
            # 按文字排序
            reverse = (sort_order == Qt.DescendingOrder)
            rows_data.sort(key=lambda row: row[column].lower(), reverse=reverse)
            
            # 更新表格
            self._update_table_with_sorted_data(rows_data)
            
            # 更新排序指示器
            header = self.overview_table.horizontalHeader()
            header.setSortIndicator(column, sort_order)
            
        except Exception as e:
            print(f"[ERROR] 文字排序失敗: {e}")
    
    def _update_table_with_sorted_data(self, rows_data):
        """使用排序後的數據更新表格"""
        for row, row_data in enumerate(rows_data):
            for col, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                
                # 為時間和數值欄位設置對齊方式
                if col in [2, 3, 4, 5, 6, 7, 8, 9, 10]:  # 數值和時間欄位
                    item.setTextAlignment(Qt.AlignCenter)
                
                self.overview_table.setItem(row, col, item)
        
    def update_overview_data(self, data: Dict[str, Any]):
        """更新概覽數據"""
        print(f"📊 [TELEMETRY_OVERVIEW] 開始更新概覽數據...")
        
        if "data" not in data or "all_drivers_telemetry" not in data["data"]:
            print(f"⚠️ [TELEMETRY_OVERVIEW] 數據格式不正確，跳過更新")
            return
            
        self.telemetry_data = data["data"]["all_drivers_telemetry"]
        print(f"📊 [TELEMETRY_OVERVIEW] 已載入 {len(self.telemetry_data)} 位車手的遙測數據")
        
        # 延遲更新UI確保數據準備完成
        QTimer.singleShot(100, self.populate_overview_display)
        
    def populate_overview_display(self):
        """填充概覽顯示"""
        if not self.telemetry_data:
            print(f"⚠️ [TELEMETRY_OVERVIEW] 無遙測數據，跳過顯示更新")
            return
            
        print(f"📊 [TELEMETRY_OVERVIEW] 開始填充概覽顯示，車手數量: {len(self.telemetry_data)}")
        
        # 更新統計卡片
        self.update_statistics_cards()
        
        # 更新概覽表格
        self.populate_overview_table()
        
        print(f"✅ [TELEMETRY_OVERVIEW] 概覽顯示更新完成")
        
    def update_statistics_cards(self):
        """更新統計卡片"""
        drivers_count = len(self.telemetry_data)
        fastest_driver = self.find_fastest_driver()
        avg_laptime = self.calculate_average_laptime()
        total_pitstops = self.calculate_total_pitstops()
        
        # 更新卡片數值 - 只更新顯示的卡片
        # self.total_drivers_card.value_label.setText(str(drivers_count))  # 隱藏
        if hasattr(self, 'fastest_driver_card') and self.fastest_driver_card:
            self.fastest_driver_card.value_label.setText(fastest_driver)
        if hasattr(self, 'avg_laptime_card') and self.avg_laptime_card:
            self.avg_laptime_card.value_label.setText(avg_laptime)
        # self.total_pitstops_card.value_label.setText(str(total_pitstops))  # 隱藏
        
        print(f"📊 [TELEMETRY_OVERVIEW] 統計卡片已更新: 最快車手={fastest_driver}, 平均圈速={avg_laptime}")
        
    def format_lap_time(self, time_str):
        """格式化圈速時間為M:SS.000格式"""
        if not time_str or time_str == 'N/A':
            return 'N/A'
        
        try:
            # 處理 pandas timedelta 格式 "0 days 00:01:31.125000" 或 "0 day 00:01:31.125000"
            if 'day' in time_str:
                parts = time_str.split()
                if len(parts) >= 3:  # ["0", "days/day", "00:01:31.125000"]
                    time_part = parts[2]  # "00:01:31.125000"
                    # 解析 HH:MM:SS.ffffff 格式
                    time_components = time_part.split(':')
                    if len(time_components) == 3:
                        hours = int(time_components[0])
                        minutes = int(time_components[1])
                        seconds = float(time_components[2])
                        total_minutes = hours * 60 + minutes
                        # 格式為M:SS.000 (去掉前導零)
                        return f"{total_minutes}:{seconds:06.3f}"
            
            # 處理各種可能的時間格式
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    # 確保格式為M:SS.000 (去掉前導零)
                    return f"{minutes}:{seconds:06.3f}"
            
            # 如果是純秒數格式
            try:
                total_seconds = float(time_str.replace('s', ''))
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                return f"{minutes}:{seconds:06.3f}"
            except:
                pass
                
            return time_str
        except Exception as e:
            print(f"⚠️ [FORMAT] 時間格式化失敗: {time_str}, 錯誤: {e}")
            return time_str
    
    def parse_time_to_seconds(self, time_str):
        """將時間字符串解析為總秒數"""
        if not time_str or time_str == 'N/A':
            return None
            
        try:
            # 處理 pandas timedelta 格式 "0 days 00:01:31.125000" 或 "0 day 00:01:31.125000"
            if 'day' in time_str:
                parts = time_str.split()
                if len(parts) >= 3:  # ["0", "days/day", "00:01:31.125000"]
                    time_part = parts[2]  # "00:01:31.125000"
                    # 解析 HH:MM:SS.ffffff 格式
                    time_components = time_part.split(':')
                    if len(time_components) == 3:
                        hours = int(time_components[0])
                        minutes = int(time_components[1])
                        seconds = float(time_components[2])
                        return hours * 3600 + minutes * 60 + seconds
            
            # 處理 MM:SS.mmm 格式
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            
            # 處理純秒數格式 (如 "3.495s")
            if 's' in time_str:
                return float(time_str.replace('s', ''))
                
            # 嘗試直接轉換為浮點數
            return float(time_str)
            
        except Exception as e:
            print(f"⚠️ [PARSE] 時間解析失敗: {time_str}, 錯誤: {e}")
            return None
    
    def seconds_to_formatted_time(self, total_seconds):
        """將總秒數轉換為M:SS.000格式"""
        if total_seconds is None:
            return "N/A"
            
        try:
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:06.3f}"
        except:
            return "N/A"
    
    def find_fastest_driver(self):
        """找出最快車手"""
        fastest_time = float('inf')
        fastest_driver = "N/A"
        
        for driver_code, driver_data in self.telemetry_data.items():
            lap_analysis = driver_data.get('lap_time_analysis', {})
            fastest_lap = lap_analysis.get('fastest_lap', {})
            lap_time_str = fastest_lap.get('lap_time', '')
            
            if lap_time_str and lap_time_str != 'N/A':
                total_seconds = self.parse_time_to_seconds(lap_time_str)
                if total_seconds is not None and total_seconds < fastest_time:
                    fastest_time = total_seconds
                    fastest_driver = driver_code
        
        return fastest_driver
        
    def calculate_average_laptime(self):
        """計算平均圈速"""
        total_seconds = 0
        count = 0
        
        for driver_data in self.telemetry_data.values():
            lap_analysis = driver_data.get('lap_time_analysis', {})
            fastest_lap = lap_analysis.get('fastest_lap', {})
            lap_time_str = fastest_lap.get('lap_time', '')
            
            if lap_time_str and lap_time_str != 'N/A':
                total_seconds_value = self.parse_time_to_seconds(lap_time_str)
                if total_seconds_value is not None:
                    total_seconds += total_seconds_value
                    count += 1
        
        if count > 0:
            avg_seconds = total_seconds / count
            return self.seconds_to_formatted_time(avg_seconds)
        
        return "N/A"
        
    def calculate_total_pitstops(self):
        """計算總進站次數"""
        total = 0
        for driver_data in self.telemetry_data.values():
            pitstop_analysis = driver_data.get('pitstop_analysis', {})
            pitstop_count = pitstop_analysis.get('pitstop_count', 0)
            if isinstance(pitstop_count, int):
                total += pitstop_count
        return total
        
    def populate_overview_table(self):
        """填充概覽表格"""
        # 暫時禁用排序功能避免在填充期間觸發排序
        self.overview_table.setSortingEnabled(False)
        
        # 按最終排名排序車手，而不是按代碼字母順序
        def get_final_position(driver_code):
            driver_data = self.telemetry_data[driver_code]
            driver_info = driver_data.get('driver_info', {})
            
            # 獲取最終排名
            final_pos = driver_info.get('final_position')
            if final_pos is None or final_pos == 'N/A' or final_pos == '':
                final_pos = driver_info.get('position', 'N/A')
            
            # 嘗試轉換為數字，無效值排到最後
            try:
                return int(final_pos)
            except (ValueError, TypeError):
                return 999  # 無效排名排到最後
        
        sorted_drivers = sorted(self.telemetry_data.keys(), key=get_final_position)
        self.overview_table.setRowCount(len(sorted_drivers))
        
        for row, driver_code in enumerate(sorted_drivers):
            driver_data = self.telemetry_data[driver_code]
            
            # 基本信息
            driver_info = driver_data.get('driver_info', {})
            lap_analysis = driver_data.get('lap_time_analysis', {})
            sector_analysis = driver_data.get('sector_analysis', {})
            pitstop_analysis = driver_data.get('pitstop_analysis', {})
            
            # 獲取初始排名，確保有預設值
            starting_pos = driver_info.get('starting_position')
            if starting_pos is None or starting_pos == 'N/A' or starting_pos == '':
                starting_pos = driver_info.get('grid_position', 'N/A')
            
            # 獲取最終排名
            final_pos = driver_info.get('final_position')
            if final_pos is None or final_pos == 'N/A' or final_pos == '':
                final_pos = driver_info.get('position', 'N/A')
            
            # 格式化圈速時間
            fastest_lap_time = self.format_lap_time(lap_analysis.get('fastest_lap', {}).get('lap_time', 'N/A'))
            fastest_lap_number = lap_analysis.get('fastest_lap', {}).get('lap_number', 'N/A')
            avg_lap_time = self.format_lap_time(lap_analysis.get('statistics', {}).get('average_lap_time', 'N/A'))
            sector1_time = self.format_lap_time(sector_analysis.get('sector_1', {}).get('best_time', 'N/A'))
            sector2_time = self.format_lap_time(sector_analysis.get('sector_2', {}).get('best_time', 'N/A'))
            sector3_time = self.format_lap_time(sector_analysis.get('sector_3', {}).get('best_time', 'N/A'))
            
            # 填充表格數據
            items = [
                driver_info.get('driver_code', 'N/A'),
                driver_info.get('team_name', 'N/A'),
                str(starting_pos),
                str(final_pos),
                fastest_lap_time,
                str(fastest_lap_number),  # 新增：最速圈數
                avg_lap_time,
                lap_analysis.get('statistics', {}).get('lap_time_std', 'N/A'),
                sector1_time,
                sector2_time,
                sector3_time,
                str(pitstop_analysis.get('pitstop_count', 'N/A'))
            ]
            
            for col, item in enumerate(items):
                # 為不同類型的欄位使用適當的表格項目
                if col == 2:  # 初始排名
                    try:
                        sort_value = int(starting_pos) if starting_pos != 'N/A' else 999
                        table_item = NumericTableWidgetItem(str(item), sort_value)
                    except:
                        table_item = NumericTableWidgetItem(str(item), 999)
                elif col == 3:  # 最終排名  
                    try:
                        sort_value = int(final_pos) if final_pos != 'N/A' else 999
                        table_item = NumericTableWidgetItem(str(item), sort_value)
                    except:
                        table_item = NumericTableWidgetItem(str(item), 999)
                elif col == 4:  # 最快圈時間
                    # 為時間欄位設置秒數作為排序值
                    seconds = self.parse_time_to_seconds(str(item))
                    table_item = NumericTableWidgetItem(str(item), seconds)
                elif col == 5:  # 最速圈數
                    try:
                        sort_value = int(item) if item != 'N/A' else 999
                        table_item = NumericTableWidgetItem(str(item), sort_value)
                    except:
                        table_item = NumericTableWidgetItem(str(item), 999)
                elif col in [6, 8, 9, 10]:  # 時間欄位（平均圈速、最佳S1、最佳S2、最佳S3）
                    # 為時間欄位設置秒數作為排序值
                    seconds = self.parse_time_to_seconds(str(item))
                    table_item = NumericTableWidgetItem(str(item), seconds)
                elif col == 7:  # 圈速穩定性（數值）
                    try:
                        sort_value = float(item) if item != 'N/A' else float('inf')
                        table_item = NumericTableWidgetItem(str(item), sort_value)
                    except:
                        table_item = NumericTableWidgetItem(str(item), float('inf'))
                elif col == 11:  # 進站次數
                    try:
                        sort_value = int(item) if item != 'N/A' else 0
                        table_item = NumericTableWidgetItem(str(item), sort_value)
                    except:
                        table_item = NumericTableWidgetItem(str(item), 0)
                else:
                    # 文字欄位使用普通項目
                    table_item = QTableWidgetItem(str(item))
                
                table_item.setTextAlignment(Qt.AlignCenter)
                self.overview_table.setItem(row, col, table_item)
        
        # 重新啟用排序功能
        self.overview_table.setSortingEnabled(True)
        print(f"📊 [TELEMETRY_OVERVIEW] 概覽表格已填充完成，共 {len(sorted_drivers)} 位車手（按最終排名排序）")


class TelemetryAnalysisModule(IAnalysisModule):
    """遙測分析模組 - 實現IAnalysisModule介面，提供車手遙測分析功能"""
    
    # 信號定義
    parameter_update_received = pyqtSignal(str, str, str)  # year, race, session
    
    # 屬性方法 (IAnalysisModule 必需)
    @property
    def module_name(self) -> str:
        return self._module_name
        
    @property
    def display_name(self) -> str:
        return self._display_name
        
    @property
    def version(self) -> str:
        return self._version
        
    @property
    def description(self) -> str:
        return self._description
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設置分析類型（用於批次更新識別）
        self.analysis_type = 'telemetry'
        
        # 模組基本資訊
        self._module_name = "DriverAnalysis"
        self._display_name = "🚗 Driver Analysis"
        self._version = "1.0.0"
        self._description = "F1 single-race driver performance dashboard (Function 12)"
        
        # 參數
        self.current_year = None
        self.current_race = None
        self.current_session = None
        
        # 同步設定
        self.sync_enabled = True
        
        # UI 組件
        self._main_widget = None
        self.tab_widget = None
        self.overview_widget = None
        self.comparison_widget = None
        self.trend_widget = None
        self.sector_widget = None
        self.tire_widget = None
        
        # 初始化數據管理器
        self.data_manager = TelemetryDataManager(self)
        self.setup_connections()
    
    @property
    def module_name(self) -> str:
        """返回模組名稱"""
        return self._module_name
        
    @property
    def display_name(self) -> str:
        """返回顯示名稱"""
        return self._display_name
        
    @property
    def version(self) -> str:
        """返回模組版本"""
        return self._version
        
    @property
    def description(self) -> str:
        """返回模組描述"""
        return self._description
    
    def setup_connections(self):
        """設置數據管理器連接"""
        # 連接數據載入信號
        self.data_manager.telemetry_loaded.connect(self.on_telemetry_data_loaded)
        self.data_manager.error_occurred.connect(self.on_error_occurred)
        self.data_manager.loading_started.connect(self.on_loading_started)
        self.data_manager.loading_finished.connect(self.on_loading_finished)
        self.data_manager.status_changed.connect(self.on_status_changed)
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組"""
        try:
            if parent_widget:
                self._parent_widget = parent_widget
            
            # 創建主要 Widget
            if not self._main_widget:
                self._main_widget = QWidget(parent_widget)
            
            # 設置UI
            self.setup_ui()
            
            # 設置初始化標記
            self._is_initialized = True
            
            print(f"✅ [TELEMETRY_MODULE] 模組已初始化，等待參數同步...")
            
            # 如果已經有預設參數，立即載入數據
            if self.current_year and self.current_race and self.current_session:
                print(f"🚀 [TELEMETRY_MODULE] 檢測到預設參數，開始載入數據: {self.current_year} {self.current_race} {self.current_session}")
                # 短暫延遲確保UI完全初始化
                QTimer.singleShot(500, self.load_data)
                
            return True
            
        except Exception as e:
            print(f"❌ [TELEMETRY_MODULE] 模組初始化失敗: {e}")
            return False
    
    def get_widget(self):
        """
        返回模組的主要 Widget
        
        實現 IAnalysisModule 介面方法
        
        Returns:
            QWidget: 分頁控件
        """
        print(f"📊 [TELEMETRY_MODULE] get_widget 被調用...")
        
        if not self._main_widget:
            print(f"📊 [TELEMETRY_MODULE] 主要Widget不存在，調用setup_ui...")
            self.setup_ui()
        else:
            print(f"📊 [TELEMETRY_MODULE] 主要Widget已存在")
            
        if not hasattr(self, 'tab_widget') or not self.tab_widget:
            print(f"📊 [TELEMETRY_MODULE] tab_widget不存在，重新設置UI...")
            self.setup_ui()
        else:
            print(f"📊 [TELEMETRY_MODULE] tab_widget已存在，有 {self.tab_widget.count()} 個分頁")
            
        print(f"📊 [TELEMETRY_MODULE] 返回主要Widget: {self._main_widget}")
        return self._main_widget
    
    def setup_ui(self):
        """設置使用者界面"""
        if hasattr(self, 'tab_widget') and self.tab_widget:
            print(f"📊 [TELEMETRY_MODULE] UI 已存在，跳過重複設置")
            return  # 避免重複設置
            
        if not self._main_widget:
            print(f"📊 [TELEMETRY_MODULE] 創建新的主要Widget")
            self._main_widget = QWidget()
        else:
            print(f"📊 [TELEMETRY_MODULE] 使用現有的主要Widget")
            
        layout = QVBoxLayout(self._main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 創建分頁容器
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 創建各分頁
        self.setup_tabs()
        
        print(f"✅ [TELEMETRY_MODULE] UI 設置完成，包含 {self.tab_widget.count()} 個分頁")
        
    def setup_tabs(self):
        """設置所有分頁"""
        print(f"📊 [TELEMETRY_MODULE] 開始設置分頁...")
        
        # 分頁1: 車手遙測概覽 (Function 12)
        print(f"📊 [TELEMETRY_MODULE] 創建車手概覽分頁...")
        self.overview_widget = DriverTelemetryOverviewWidget(self.data_manager)
        self.tab_widget.addTab(self.overview_widget, "🏎️ 車手概覽")
        print(f"✅ [TELEMETRY_MODULE] 車手概覽分頁已添加")
        
        # 分頁2-5: 暫時使用佔位符（後續實現）
        self.comparison_widget = QLabel("⚔️ 對比分析功能開發中...")
        self.comparison_widget.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(self.comparison_widget, "⚔️ 對比分析")
        
        self.trend_widget = QLabel("📈 圈速趨勢功能開發中...")
        self.trend_widget.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(self.trend_widget, "📈 圈速趨勢")
        
        self.sector_widget = QLabel("🏁 區間分析功能開發中...")
        self.sector_widget.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(self.sector_widget, "🏁 區間分析")
        
        self.tire_widget = QLabel("🛞 輪胎策略功能開發中...")
        self.tire_widget.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(self.tire_widget, "🛞 輪胎策略")
        
        # 連接分頁切換信號
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        print(f"✅ [TELEMETRY_MODULE] 所有分頁設置完成，共 {self.tab_widget.count()} 個分頁")
        
    def on_tab_changed(self, index):
        """分頁切換處理"""
        # 確保切換分頁時數據是最新的
        if self.current_year and self.current_race and self.current_session:
            # 如果是第一個分頁（車手概覽），確保數據已載入
            if index == 0 and hasattr(self.overview_widget, 'telemetry_data'):
                if not self.overview_widget.telemetry_data:
                    self.load_data()
    
    def get_title(self) -> str:
        """返回模組標題 - 模組工廠需要的方法"""
        from core.gui_i18n import tr
        year = self.current_year or "2025"
        race = self.current_race or "Unknown"
        session = self.current_session or "R"
        return f"{tr('driver_analysis', 'Driver Analysis')}_{year}_{race}_{session}"
    
    def get_window_title(self, year: str, race: str, session: str) -> str:
        """生成視窗標題 - 只顯示模組名稱，不包含年份/賽事/賽段"""
        from core.gui_i18n import tr
        return f"🚗 {tr('driver_analysis', 'Driver Analysis')}"
    
    def get_default_size(self):
        """獲取預設視窗大小"""
        return (1000, 700)  # 寬度, 高度
    
    def validate_parameters(self, year: int, race: str, session: str) -> bool:
        """驗證分析參數"""
        try:
            # 驗證年份
            if not isinstance(year, (int, str)) or int(year) < 2020 or int(year) > 2030:
                return False
            
            # 驗證賽段
            if session not in ["FP1", "FP2", "FP3", "Q", "S", "R"]:
                return False
                
            return True
        except:
            return False
    
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """
        更新分析參數
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段
            
        Returns:
            bool: 更新是否成功
        """
        print(f"🔄 [TELEMETRY_MODULE] update_parameters 被調用: {year}, {race}, {session}")
        
        try:
            # 驗證參數
            if not self.validate_parameters(year, race, session):
                print(f"❌ [TELEMETRY_MODULE] 參數驗證失敗: {year}, {race}, {session}")
                self.emit_error(f"無效的遙測分析參數: {year}, {race}, {session}")
                return False
                
            # 檢查參數是否有變化
            params_changed = (
                self.current_year is None or str(self.current_year) != str(year) or 
                self.current_race is None or self.current_race != race or 
                self.current_session is None or self.current_session != session
            )
            
            print(f"📊 [TELEMETRY_MODULE] 當前參數: {self.current_year}, {self.current_race}, {self.current_session}")
            print(f"📊 [TELEMETRY_MODULE] 新參數: {year}, {race}, {session}")
            print(f"📊 [TELEMETRY_MODULE] 參數是否變化: {params_changed}")
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race  
            self.current_session = session
            
            # 如果參數有變化，重新載入數據
            if params_changed:
                print(f"🔄 [TELEMETRY_MODULE] 參數變更觸發數據重載: {year} {race} {session}")
                
                # 發出參數更新信號
                params = {
                    'year': year,
                    'race': race,
                    'session': session,
                    'module': self.module_name
                }
                self.emit_parameters_updated(params)
                
                # 確保 UI 已經設置完成再載入數據
                if hasattr(self, 'overview_widget') and self.overview_widget is not None:
                    # 立即載入數據，但有短暫延遲確保UI完全準備好
                    QTimer.singleShot(100, self.load_data)
                    print(f"📅 [TELEMETRY_MODULE] 已安排遙測數據載入任務: {year} {race} {session}")
                else:
                    # UI 還沒準備好，稍後再試
                    print(f"🔄 [TELEMETRY_MODULE] UI 未準備好，延遲載入: {year} {race} {session}")
                    QTimer.singleShot(500, self.load_data)
            else:
                print(f"📊 [TELEMETRY_MODULE] 參數無變化，跳過重載")
                
            return True
            
        except Exception as e:
            print(f"❌ [TELEMETRY_MODULE] 更新參數異常: {e}")
            traceback.print_exc()
            self.emit_error(f"更新遙測分析參數時發生錯誤: {str(e)}")
            return False
    
    def load_data(self):
        """載入遙測數據"""
        if not self.current_year or not self.current_race or not self.current_session:
            print(f"[TELEMETRY_MODULE] 參數不完整，跳過載入")
            return
            
        print(f"🔄 [TELEMETRY_MODULE] 開始載入遙測數據: {self.current_year} {self.current_race} {self.current_session}")
        
        # 使用數據管理器載入數據
        success = self.data_manager.loadTelemetryData(
            self.current_year, 
            self.current_race, 
            self.current_session
        )
        
        if not success:
            self.emit_error("遙測數據載入失敗")
    
    def on_telemetry_data_loaded(self, data):
        """遙測數據載入完成處理"""
        print(f"✅ [TELEMETRY_MODULE] 遙測數據載入完成")
        
        # 更新第一個分頁（車手概覽）
        if self.overview_widget:
            self.overview_widget.update_overview_data(data)
        
        # TODO: 更新其他分頁
        
        # 發出數據載入完成信號 - 暫時註解，避免錯誤
        # self.emit_data_loaded({
        #     'type': 'telemetry_analysis',
        #     'data': data,
        #     'year': self.current_year,
        #     'race': self.current_race,
        #     'session': self.current_session
        # })
        
        print(f"📊 [TELEMETRY_MODULE] 已通知分頁更新遙測數據，包含 {len(data.get('data', {}).get('all_drivers_telemetry', {}))} 位車手")
    
    def on_error_occurred(self, error_message):
        """錯誤處理"""
        print(f"❌ [TELEMETRY_MODULE] 錯誤: {error_message}")
        # self.emit_error(error_message)  # 暫時註解，避免錯誤
    
    def on_loading_started(self):
        """載入開始處理"""
        print(f"⏳ [TELEMETRY_MODULE] 開始載入遙測數據...")
        # self.emit_status_update("正在載入遙測數據...")  # 暫時註解，避免錯誤
    
    def on_loading_finished(self):
        """載入完成處理"""
        print(f"✅ [TELEMETRY_MODULE] 遙測數據載入完成")
        # self.emit_status_update("遙測數據載入完成")  # 暫時註解，避免錯誤
    
    def on_status_changed(self, status):
        """狀態變更處理"""
        print(f"📊 [TELEMETRY_MODULE] 狀態更新: {status}")
        # self.emit_status_update(status)  # 暫時註解，避免錯誤
    
    def cleanup(self):
        """清理資源"""
        try:
            # 停止數據管理器的所有定時器
            if hasattr(self.data_manager, '_stop_generation_monitoring'):
                self.data_manager._stop_generation_monitoring()
            
            print(f"🧹 [TELEMETRY_MODULE] 資源清理完成")
            
        except Exception as e:
            print(f"⚠️ [TELEMETRY_MODULE] 清理資源時發生錯誤: {e}")
    
    def get_status_info(self) -> dict:
        """獲取模組狀態信息"""
        return {
            'module_name': self.module_name,
            'display_name': self.display_name,
            'version': self.version,
            'description': self.description,
            'current_year': self.current_year,
            'current_race': self.current_race,
            'current_session': self.current_session,
            'is_loading': self.data_manager._is_loading if hasattr(self.data_manager, '_is_loading') else False,
            'data_loaded': bool(self.data_manager.current_data)
        }

    # ===== 實現抽象方法 =====
    
    def clear_data(self):
        """清除數據"""
        try:
            # 清除數據管理器中的數據
            if hasattr(self.data_manager, 'current_data'):
                self.data_manager.current_data = {}
            
            # 清除各分頁的數據
            if hasattr(self, 'overview_widget') and self.overview_widget:
                self.overview_widget.telemetry_data = {}
                if hasattr(self.overview_widget, 'overview_table'):
                    self.overview_widget.overview_table.setRowCount(0)
            
            if hasattr(self, 'comparison_widget') and self.comparison_widget:
                self.comparison_widget.telemetry_data = {}
                
            if hasattr(self, 'trend_widget') and self.trend_widget:
                self.trend_widget.telemetry_data = {}
                
            if hasattr(self, 'sector_widget') and self.sector_widget:
                self.sector_widget.telemetry_data = {}
                
            if hasattr(self, 'tire_widget') and self.tire_widget:
                self.tire_widget.telemetry_data = {}
                
            print(f"🧹 [TELEMETRY_MODULE] 數據已清除")
            self.emit_status_update("數據已清除")
            
        except Exception as e:
            print(f"⚠️ [TELEMETRY_MODULE] 清除數據時發生錯誤: {e}")

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """導出數據"""
        try:
            if not self.data_manager.current_data:
                print(f"⚠️ [TELEMETRY_MODULE] 沒有可導出的數據")
                return False
                
            import json
            from datetime import datetime
            
            # 如果export_path是目錄，構造完整檔案名
            if os.path.isdir(export_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"telemetry_analysis_export_{self.current_year}_{self.current_race}_{self.current_session}_{timestamp}.json"
                export_path = os.path.join(export_path, filename)
            
            # 準備導出數據
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "module": "telemetry_analysis",
                    "parameters": {
                        "year": self.current_year,
                        "race": self.current_race,
                        "session": self.current_session
                    }
                },
                "telemetry_data": self.data_manager.current_data
            }
            
            # 寫入檔案
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ [TELEMETRY_MODULE] 數據已導出到: {export_path}")
            return True
            
        except Exception as e:
            print(f"⚠️ [TELEMETRY_MODULE] 導出數據時發生錯誤: {e}")
            return False

    def get_current_data(self) -> dict:
        """獲取當前數據"""
        try:
            if hasattr(self.data_manager, 'current_data'):
                return self.data_manager.current_data
            else:
                return {}
        except Exception as e:
            print(f"⚠️ [TELEMETRY_MODULE] 獲取當前數據時發生錯誤: {e}")
            return {}

    def refresh_analysis(self) -> bool:
        """刷新分析"""
        try:
            if self.current_year and self.current_race and self.current_session:
                print(f"🔄 [TELEMETRY_MODULE] 刷新遙測分析: {self.current_year} {self.current_race} {self.current_session}")
                
                # 重新載入數據
                success = self.data_manager.loadTelemetryData(
                    self.current_year, 
                    self.current_race, 
                    self.current_session,
                    force_refresh=True
                )
                
                if success:
                    self.emit_status_update("遙測分析已刷新")
                    return True
                else:
                    self.emit_status_update("刷新失敗")
                    return False
            else:
                print(f"⚠️ [TELEMETRY_MODULE] 無法刷新：參數不完整")
                self.emit_status_update("無法刷新：參數不完整")
                return False
                
        except Exception as e:
            print(f"⚠️ [TELEMETRY_MODULE] 刷新分析時發生錯誤: {e}")
            self.emit_status_update(f"刷新失敗: {str(e)}")
            return False


# === ModuleFactory 註冊 ===
def create_telemetry_analysis_module() -> TelemetryAnalysisModule:
    """創建遙測分析模組實例"""
    return TelemetryAnalysisModule()

# 註冊到模組工廠
try:
    ModuleFactory.register_module(ModuleTypes.TELEMETRY_ANALYSIS, create_telemetry_analysis_module)
    print("✅ [MODULE_FACTORY] 遙測分析模組已註冊")
except Exception as e:
    print(f"⚠️ [MODULE_FACTORY] 遙測分析模組註冊失敗: {e}")
