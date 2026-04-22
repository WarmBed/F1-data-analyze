#!/usr/bin/env python3
"""
LapTimeBoxPlotAnalysis - F1T 圈速箱型圖分析模組
==============================================

基於通用 MDI 架構實現的圈速箱型圖分析模組，支援：
- 所有車手圈速分佈箱型圖
- IQR 方法異常值過濾
- 進站圈過濾
- 統計指標計算（中位數、平均值、四分位數）
- 車隊顏色標記

數據來源：detailed_laptime_analysis JSON 檔案（CLI Function 28）
圖表類型：matplotlib boxplot

Author: F1T Team
Date: 2025-10-02
Version: 1.0.0
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QGridLayout, QPushButton, QComboBox,
    QCheckBox, QDoubleSpinBox, QFileDialog, QMessageBox,
    QTabWidget, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSignalBlocker
from PyQt5.QtGui import QFont

from core import local_requests as requests
import certifi
from core.api_base_url import resolve_api_base_url

# 導入翻譯函數與全域設定
from core.gui_i18n import tr
from core.gui_settings_manager import gui_settings_manager

# 共用圈速過濾工具
from modules.gui.driver_race.detailed_lap_analysis.lap_filter_utils import (
    extract_caution_laps,
    extract_red_flag_laps,
    lap_is_under_caution,
    lap_is_under_red_flag,
)

# 導入通用基礎類別
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
    from modules.gui.base.universal_stint_selector import UniversalStintSelector, StintInfo
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
    from modules.gui.base.universal_stint_selector import UniversalStintSelector, StintInfo


class LapTimeBoxPlotApiWorker(QThread):
    """Background worker that fetches detailed lap time data from the REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 75.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "http://localhost:8000").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout

    def run(self):
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            self.progress.emit(20)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 28,  # CLI Function 28: detailed_laptime_analysis
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )
            self.progress.emit(70)
            
            # ✅ 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                return
            
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
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }

            self.progress.emit(90)
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            self.failure.emit(str(exc))
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class LapTimeBoxPlotDataManager(UniversalDataLoader):
    """圈速箱型圖數據管理器"""
    
    # 自定義信號
    filter_settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        # 註冊圈速箱型圖分析類型（如果尚未註冊）
        if "laptime_boxplot" not in UniversalDataLoader.ANALYSIS_TYPES:
            boxplot_config = AnalysisConfig(
                display_name=tr("laptime_boxplot", "圈速箱型圖"),
                debug_prefix="[BOXPLOT_DATA]",
                data_source="api",
                cli_function="28",  # CLI Function 28
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=28,
                api_timeout=75.0,
                file_patterns=[
                    "detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json",
                    "detailed_laptime_analysis_{year}_{race}_{session}.json",
                    "detailed_driver_laptime_{year}_{race}_{session}.json"
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True
            )
            UniversalDataLoader.register_analysis_type("laptime_boxplot", boxplot_config)
        
        super().__init__("laptime_boxplot", parent)
        
        # 圈速箱型圖特定屬性
        self.driver_laptimes: Dict[str, List[float]] = {}
        self.statistics: Dict[str, Dict[str, float]] = {}
        self.filter_settings = {
            'filter_pit_laps': True,
            'filter_outliers': True,
            'outlier_threshold': 1.5,
            'filter_yellow_flags': True,
            'filter_red_flags': True,
            'filter_first_laps': True,
        }
        self.settings_manager = gui_settings_manager
        self._raw_data_cache: Optional[Dict[str, Any]] = None
        self._suppress_global_sync = False
        
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[LapTimeBoxPlotApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        fallback_state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(
            f"本地 JSON 後備已{fallback_state} (策略: {self._fallback_policy_reason})"
        )
        
        logger.debug(f"[BOXPLOT_DATA] 初始化完成, 搜索目錄: {self.config.search_directories}")
        logger.debug(f"[BOXPLOT_DATA] 文件模式: {self.config.file_patterns}")

        # 套用全域系統設定
        try:
            self._apply_global_settings(self.settings_manager.get_boxplot_settings())
            self.settings_manager.boxplot_settings_changed.connect(self._on_global_boxplot_settings_changed)
        except Exception as exc:
            self._debug(f"無法連結全域設定管理器: {exc}")
        
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        year = params.get('year')
        race = params.get('race') 
        session = params.get('session')
        
        if not year or not race or not session:
            self._debug("參數不完整：需要年份、比賽和賽段")
            return False
        return True
    
    def _determine_api_base_url(self) -> str:
        """Resolve the API base URL from environment variables or configuration."""
        return resolve_api_base_url(event_logger=self._debug)

    def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
        """Determine whether local JSON fallback is permitted."""
        # 修正：檢查 BoxPlot 專用環境變數
        env_value = os.getenv("F1T_ALLOW_BOXPLOT_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_BOXPLOT_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_BOXPLOT_JSON_FALLBACK={env_value}"
        
        # 修正：預設允許本地 JSON 後備（開發模式）
        return True, "預設策略 (允許本地 JSON 後備)"

    def set_local_fallback_allowed(self, allowed: bool, reason: Optional[str] = None) -> None:
        """Manually toggle whether local JSON fallback is allowed."""
        self._allow_local_fallback = bool(allowed)
        self._fallback_policy_reason = reason or "手動覆寫"
        state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(f"本地 JSON 後備手動設為{state} (原因: {self._fallback_policy_reason})")

    def _apply_global_settings(self, settings: Dict[str, Any]) -> None:
        """Synchronize filter preferences with the System Settings dialog."""
        if not isinstance(settings, dict):
            return

        updates: Dict[str, Any] = {}
        for key in ("filter_pit_laps", "filter_outliers", "outlier_threshold", "filter_yellow_flags", "filter_red_flags", "filter_first_laps"):
            if key in settings and self.filter_settings.get(key) != settings[key]:
                updates[key] = settings[key]

        if updates:
            self._debug(f"套用全域設定: {updates}")
            # 防止重新觸發全域同步時又回寫設定
            self._suppress_global_sync = True
            try:
                self.update_filter_settings(updates)
            finally:
                self._suppress_global_sync = False

    def _on_global_boxplot_settings_changed(self, settings: Dict[str, Any]) -> None:
        """Handle updates coming from the System Settings dialog."""
        if self._suppress_global_sync:
            return
        self._apply_global_settings(settings)

    def load_data_from_local(self, **kwargs) -> bool:
        """Force loading data via the legacy local JSON workflow for diagnostics."""
        previous_state = self._allow_local_fallback
        previous_reason = self._fallback_policy_reason
        try:
            self._allow_local_fallback = True
            self._fallback_policy_reason = "手動診斷模式"
            self._debug("以手動模式使用本地 JSON 後備流程")
            return super().load_data(**kwargs)
        finally:
            self._allow_local_fallback = previous_state
            self._fallback_policy_reason = previous_reason

    def load_data(self, **kwargs) -> bool:
        """載入降雨分析資料，優先透過 API，失敗時回退本地流程。"""
        if self.config.data_source != "api":
            return super().load_data(**kwargs)

        if self._is_loading:
            self._debug("已有載入請求執行中，忽略新的請求")
            return False

        if not self._validate_load_parameters(kwargs):
            self._error("API 載入參數驗證失敗")
            self.load_error.emit("載入參數不正確")
            return False

        self._is_loading = True
        self._pending_params = dict(kwargs)
        self._api_base_url = self._determine_api_base_url()

        self._debug(f"透過 API 載入降雨資料: base_url={self._api_base_url}, params={self._pending_params}")
        self.load_progress.emit(5)
        self.status_changed.emit("正在透過 API 載入降雨分析資料...")

        try:
            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            self._error(f"啟動 API 請求失敗: {exc}")
            self._is_loading = False
            self.status_changed.emit("API 載入失敗，改用本地資料")
            return super().load_data(**kwargs)

    def set_api_base_url(self, base_url: Optional[str]) -> None:
        """Allows external callers to override the API base URL."""
        if base_url:
            self._api_base_url = str(base_url).rstrip('/')
            self._debug(f"API base URL 更新為 {self._api_base_url}")

    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """Spawn the background worker that contacts the REST API."""
        self._cleanup_api_worker()

        worker_params = {
            "year": params.get("year"),
            "race": params.get("race"),
            "session": params.get("session"),
            "force_refresh": params.get("force_refresh", False),
        }

        timeout = getattr(self.config, "api_timeout", 75.0)
        self._api_worker = LapTimeBoxPlotApiWorker(self._api_base_url, worker_params, timeout=timeout, parent=self)
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()

    def _on_api_progress(self, value: int) -> None:
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        self._debug("========== API 成功回調 ==========")
        self._debug(f"Payload 類型: {type(payload)}")
        self._debug(f"Payload 鍵: {list(payload.keys()) if isinstance(payload, dict) else 'N/A'}")
        
        try:
            raw_data = payload.get("data")
            self._debug(f"原始數據類型: {type(raw_data)}")
            self._debug(f"原始數據鍵: {list(raw_data.keys())[:10] if isinstance(raw_data, dict) else 'N/A'}")
            
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"

            if not self._validate_data_format(raw_data):
                self._debug("❌ 數據驗證失敗")
                raise ValueError("API 回傳數據格式不符合預期")
            
            self._debug("✅ 數據驗證通過")

            processed_data = self._process_data(raw_data)
            self._debug(f"處理後數據類型: {type(processed_data)}")
            self._debug(f"處理後數據鍵: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'N/A'}")
            
            if isinstance(processed_data, dict):
                driver_count = len(processed_data.get('driver_laptimes', {}))
                self._debug(f"車手數量: {driver_count}")
                metadata = processed_data.setdefault("metadata", {})
                metadata.setdefault("data_source", "api")
                if self._last_api_meta:
                    metadata["api"] = self._last_api_meta

            self._current_data = processed_data
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit("已從 API 載入資料")
            
            self._debug("準備發出 data_loaded 信號...")
            self.data_loaded.emit(processed_data)
            self._debug("✅ data_loaded 信號已發出")
            self._debug("========== API 成功回調結束 ==========")

        except Exception as exc:
            self._debug(f"❌ 處理 API 數據時發生異常: {exc}")
            import traceback
            traceback.print_exc()
            self._error(f"處理 API 數據失敗: {exc}")
            self._is_loading = False
            self.status_changed.emit("API 資料格式錯誤，改用本地資料")
            self._fallback_to_local(str(exc))

    def _on_api_error(self, message: str) -> None:
        self._debug("========== API 錯誤回調 ==========")
        self._debug(f"錯誤訊息: {message}")
        self._error(f"API 請求失敗: {message}")
        self._is_loading = False
        self.status_changed.emit("API 請求失敗，改用本地資料")
        self._debug("開始執行本地 JSON 回退...")
        self._fallback_to_local(message)

    def _fallback_to_local(self, reason: str) -> None:
        self._debug("========== 本地 JSON 回退流程 ==========")
        self._debug(f"觸發原因: {reason}")
        
        params = self._pending_params or {}
        if not params:
            self._debug("❌ 缺少待處理參數")
            self.load_error.emit(f"API 載入失敗: {reason}")
            return

        self._debug(f"待處理參數: {params}")
        self._debug(f"允許本地回退: {self._allow_local_fallback}")
        self._debug(f"回退策略原因: {self._fallback_policy_reason}")

        if not self._allow_local_fallback:
            self._last_data_source = "local-fallback-disabled"
            self._last_api_meta = {}
            message = (
                "API 載入失敗，且本地 JSON 後備已被策略停用。"
                " 如需啟用，請設定環境變數 F1T_ALLOW_BOXPLOT_JSON_FALLBACK=1 或使用 set_local_fallback_allowed。"
            )
            self._debug(f"❌ 本地 JSON 後備被阻擋: {reason}")
            self._is_loading = False
            self.status_changed.emit("本地 JSON 後備已停用，請檢查 API 或手動啟用後備流程。")
            self.load_error.emit(message)
            return

        self._last_data_source = "local-json"
        self._last_api_meta = {}
        self._debug(f"✅ 啟動本地 JSON 後備流程")
        self._debug("調用父類 load_data() 方法...")
        self.status_changed.emit("使用本地 JSON 後備載入資料...")
        
        # 調用父類的 load_data (會搜尋本地 JSON)
        result = super().load_data(**params)
        self._debug(f"父類 load_data() 返回結果: {result}")
        
        if not result:
            self._debug("❌ 父類 load_data() 返回 False")
            self.load_error.emit(f"本地 JSON 載入失敗: {reason}")
        else:
            self._debug("✅ 父類 load_data() 返回 True")
        
        self._debug("========== 本地 JSON 回退流程結束 ===========")

    def _cleanup_api_worker(self) -> None:
        """
        異步清理 API Worker（方案 2: 信號驅動清理）
        ✅ 不阻塞主線程
        ✅ 使用信號自動清理
        """
        if self._api_worker:
            # 1. 斷開所有信號
            try:
                self._api_worker.progress.disconnect()
            except Exception:
                pass
            try:
                self._api_worker.success.disconnect()
            except Exception:
                pass
            try:
                self._api_worker.failure.disconnect()
            except Exception:
                pass
            try:
                self._api_worker.finished.disconnect()
            except Exception:
                pass
            
            if self._api_worker.isRunning():
                # 2. 請求中斷（非阻塞）
                self._api_worker.requestInterruption()
                self._api_worker.quit()
                
                # 3. 使用信號自動清理（當 Worker 停止時）
                def on_worker_stopped():
                    """Worker 停止後自動清理"""
                    if self._api_worker:
                        self._api_worker.deleteLater()
                    self._api_worker = None
                
                self._api_worker.finished.connect(on_worker_stopped)
                
                # 4. 延遲強制終止（200ms 後，但不阻塞主線程）
                from PyQt5.QtCore import QTimer
                def force_terminate():
                    # ✅ 安全檢查：確保 worker 仍然有效且未被刪除
                    try:
                        if self._api_worker and self._api_worker.isRunning():
                            self._api_worker.terminate()
                    except (RuntimeError, AttributeError):
                        # Worker 已被刪除，無需處理
                        pass
                
                QTimer.singleShot(200, force_terminate)
            else:
                # Worker 已停止，立即清理
                self._api_worker.deleteLater()
                self._api_worker = None

    def get_last_data_source(self) -> str:
        return getattr(self, "_last_data_source", "unknown")

    def get_last_api_metadata(self) -> Dict[str, Any]:
        return getattr(self, "_last_api_meta", {})
        
    def _build_filename_patterns(self, year: str, race: str, session: str, **kwargs) -> List[str]:
        """構建檔案名稱模式"""
        patterns = []
        for pattern in self.config.file_patterns:
            filename = pattern.format(year=year, race=race, session=session)
            patterns.append(filename)
        return patterns
        
    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式"""
        if not isinstance(data, dict):
            self._debug("數據格式錯誤：必須是字典格式")
            return False
            
        # 檢查 CLI Function 28 的標準輸出格式
        if "all_drivers_detailed_laptime" not in data:
            self._debug("數據格式錯誤：缺少 all_drivers_detailed_laptime 欄位")
            return False
            
        return True
        
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據的具體實現"""
        return self.process_loaded_data(data)
        
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用,系統只允許通過 API 獲取數據
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取詳細圈速分析數據")
        return False
        
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的圈速箱型圖數據"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")

            # 快取原始數據供後續重新處理（過濾設定變更時使用）
            self._raw_data_cache = data
                
            # 解析 JSON 結構 - 期望 all_drivers_detailed_laptime
            if "all_drivers_detailed_laptime" not in data:
                raise ValueError("找不到車手圈速數據：all_drivers_detailed_laptime")
            
            all_drivers = data["all_drivers_detailed_laptime"]
            
            # 提取所有車手的圈速
            driver_laptimes = self._extract_lap_times(all_drivers)
            
            # 應用過濾
            if self.filter_settings['filter_outliers']:
                driver_laptimes = self._filter_outliers_iqr(
                    driver_laptimes,
                    self.filter_settings['outlier_threshold']
                )
            
            # 計算統計
            statistics = self._calculate_statistics(driver_laptimes)
            
            # 儲存到實例
            self.driver_laptimes = driver_laptimes
            self.statistics = statistics
            
            # 返回處理後的數據
            processed_data = {
                'driver_laptimes': driver_laptimes,
                'statistics': statistics,
                'metadata': data.get('metadata', {})
            }

            metadata = processed_data.setdefault("metadata", {})
            if self._last_data_source:
                metadata["data_source"] = self._last_data_source
            if self._last_data_source == "api" and self._last_api_meta:
                existing_api_meta = metadata.get("api", {})
                merged_meta = dict(existing_api_meta)
                merged_meta.update(self._last_api_meta)
                metadata["api"] = merged_meta
            
            self._debug(f"成功處理 {len(driver_laptimes)} 位車手的圈速數據")
            
            return processed_data
            
        except Exception as e:
            self._debug(f"數據處理失敗: {str(e)}")
            raise
            
    def _extract_lap_times(self, all_drivers: Dict) -> Dict[str, List[float]]:
        """從 detailed_lap_data 中提取圈速"""
        driver_laptimes = {}
        
        for driver_code, driver_data in all_drivers.items():
            if not isinstance(driver_data, dict):
                continue
            
            detailed_laps = driver_data.get('detailed_lap_data', [])
            if not isinstance(detailed_laps, list):
                continue
            
            caution_laps: Optional[Set[int]] = None
            if self.filter_settings.get('filter_yellow_flags', True):
                caution_laps = extract_caution_laps(driver_data)

            red_flag_laps: Optional[Set[int]] = None
            if self.filter_settings.get('filter_red_flags', True):
                red_flag_laps = extract_red_flag_laps(driver_data)

            lap_times = []
            for lap in detailed_laps:
                if not isinstance(lap, dict):
                    continue
                
                # 優先使用 lap_time_seconds（數值格式），否則嘗試 lap_time（字串格式）
                lap_time_value = lap.get('lap_time_seconds') or lap.get('lap_time')
                if lap_time_value is None:
                    continue
                
                # 嘗試轉換為浮點數
                try:
                    lap_time_float = float(lap_time_value)
                except (ValueError, TypeError):
                    continue
                
                # 過濾無效值（<= 0）
                if lap_time_float <= 0:
                    continue
                
                # 過濾前兩圈 (Lap 1 & 2)
                lap_number = lap.get('lap_number')
                if self.filter_settings.get('filter_first_laps', True):
                    if lap_number in (1, 2):
                        continue
                
                # 過濾黃旗/安全車圈
                if self.filter_settings.get('filter_yellow_flags', True):
                    if lap_is_under_caution(lap_number, lap, caution_laps):
                        continue

                # 過濾紅旗圈
                if self.filter_settings.get('filter_red_flags', True):
                    if lap_is_under_red_flag(lap_number, lap, red_flag_laps):
                        continue

                # 過濾進站圈
                if self.filter_settings['filter_pit_laps']:
                    smart_markers = lap.get('smart_markers', {})
                    if isinstance(smart_markers, dict):
                        pit_stop = smart_markers.get('pit_stop_detection', {})
                        if isinstance(pit_stop, dict) and pit_stop.get('is_pit_lap'):
                            continue
                
                lap_times.append(lap_time_float)
            
            if lap_times:
                driver_laptimes[driver_code] = lap_times
        
        return driver_laptimes
        
    def _filter_outliers_iqr(self, driver_laptimes: Dict[str, List[float]], threshold: float = 1.5) -> Dict[str, List[float]]:
        """使用 IQR 方法過濾異常值"""
        filtered = {}
        
        for driver, lap_times in driver_laptimes.items():
            if len(lap_times) < 4:
                filtered[driver] = lap_times
                continue
            
            q1 = np.percentile(lap_times, 25)
            q3 = np.percentile(lap_times, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            filtered_times = [t for t in lap_times if lower_bound <= t <= upper_bound]
            
            if filtered_times:
                filtered[driver] = filtered_times
        
        return filtered
    
    def _calculate_statistics(self, driver_laptimes: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """計算統計指標"""
        statistics = {}
        
        for driver, lap_times in driver_laptimes.items():
            if not lap_times:
                continue
            
            statistics[driver] = {
                'mean': float(np.mean(lap_times)),
                'median': float(np.median(lap_times)),
                'q1': float(np.percentile(lap_times, 25)),
                'q3': float(np.percentile(lap_times, 75)),
                'iqr': float(np.percentile(lap_times, 75) - np.percentile(lap_times, 25)),
                'count': len(lap_times)
            }
        
        return statistics
    
    def update_filter_settings(self, settings: Dict[str, Any]):
        """更新過濾設定並重新處理數據"""
        if not isinstance(settings, dict):
            return

        updates: Dict[str, Any] = {}
        for key, value in settings.items():
            if key not in self.filter_settings:
                continue
            if self.filter_settings[key] != value:
                self.filter_settings[key] = value
                updates[key] = value

        if not updates:
            return

        logger.debug(f"[BOXPLOT_DATA] 過濾設定已更新: {updates}")

        if self._raw_data_cache:
            processed = self.process_loaded_data(self._raw_data_cache)
            self._current_data = processed
            self.data_loaded.emit(processed)
        else:
            self._debug("尚未快取原始數據，跳過重新處理")

        self.filter_settings_changed.emit(dict(self.filter_settings))
    
    def get_processed_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前處理後的數據"""
        if not self.driver_laptimes:
            return None
        
        return {
            'driver_laptimes': self.driver_laptimes,
            'statistics': self.statistics,
            'metadata': {}
        }


# 導入專用圖表組件
from .lap_box_plot_chart_widget import LapTimeBoxPlotChartWidget

from core.logger import get_logger
logger = get_logger(__name__)


class LapTimeBoxPlotControlWidget(QWidget):
    """圈速箱型圖控制面板"""
    
    # 信號定義
    settings_changed = pyqtSignal(dict)
    reload_requested = pyqtSignal()
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 過濾設定分組
        filter_group = QGroupBox(tr("filter_settings", "🔧 過濾設定"))
        filter_layout = QVBoxLayout()
        
        # 過濾進站圈
        self.filter_pit_checkbox = QCheckBox(tr("filter_pit_laps", "過濾進站圈"))
        self.filter_pit_checkbox.setChecked(True)
        self.filter_pit_checkbox.setToolTip("排除標記為進站的圈速數據")
        self.filter_pit_checkbox.stateChanged.connect(self._on_settings_changed)
        filter_layout.addWidget(self.filter_pit_checkbox)
        
        # 過濾異常值
        self.filter_outliers_checkbox = QCheckBox(tr("filter_outliers", "過濾異常值 (IQR 方法)"))
        self.filter_outliers_checkbox.setChecked(True)
        self.filter_outliers_checkbox.setToolTip("使用四分位數範圍 (IQR) 方法過濾異常圈速")
        self.filter_outliers_checkbox.stateChanged.connect(self._on_settings_changed)
        filter_layout.addWidget(self.filter_outliers_checkbox)
        
        # IQR 倍數調整
        iqr_layout = QHBoxLayout()
        iqr_label = QLabel(tr("iqr_multiplier", "IQR 倍數:"))
        iqr_label.setToolTip("異常值判定倍數（建議 1.5-3.0）")
        self.iqr_spinbox = QDoubleSpinBox()
        self.iqr_spinbox.setRange(0.5, 5.0)
        self.iqr_spinbox.setSingleStep(0.5)
        self.iqr_spinbox.setValue(1.5)
        self.iqr_spinbox.setDecimals(1)
        self.iqr_spinbox.setSuffix(" × IQR")
        self.iqr_spinbox.valueChanged.connect(self._on_settings_changed)
        iqr_layout.addWidget(iqr_label)
        iqr_layout.addWidget(self.iqr_spinbox)
        iqr_layout.addStretch()
        filter_layout.addLayout(iqr_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 操作按鈕分組
        action_group = QGroupBox(tr("actions", "⚙️ 操作"))
        action_layout = QVBoxLayout()
        
        # 重新載入按鈕
        self.reload_button = QPushButton(tr("reload_data", "🔄 重新載入數據"))
        self.reload_button.setToolTip("強制重新載入分析數據")
        self.reload_button.clicked.connect(self.reload_requested.emit)
        action_layout.addWidget(self.reload_button)
        
        # 匯出圖表按鈕
        self.export_button = QPushButton(tr("export_chart", "💾 匯出圖表"))
        self.export_button.setToolTip("將圖表儲存為圖片檔案")
        self.export_button.clicked.connect(self.export_requested.emit)
        action_layout.addWidget(self.export_button)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # 統計資訊區域
        stats_group = QGroupBox(tr("statistics", "📊 統計資訊"))
        stats_layout = QVBoxLayout()
        
        self.stats_label = QLabel(tr("waiting_for_data", "等待數據..."))
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("font-size: 10px; color: gray;")
        stats_layout.addWidget(self.stats_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
    def _on_settings_changed(self):
        """設定變更時發射信號"""
        settings = self.get_filter_settings()
        self.settings_changed.emit(settings)
    
    def get_filter_settings(self) -> Dict[str, Any]:
        """獲取當前過濾設定"""
        return {
            'filter_pit_laps': self.filter_pit_checkbox.isChecked(),
            'filter_outliers': self.filter_outliers_checkbox.isChecked(),
            'outlier_threshold': self.iqr_spinbox.value()
        }
    
    def update_statistics(self, stats_text: str):
        """更新統計資訊顯示"""
        self.stats_label.setText(stats_text)

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """同步控制面板狀態與全域系統設定。"""
        if not isinstance(settings, dict):
            return

        with QSignalBlocker(self.filter_pit_checkbox):
            self.filter_pit_checkbox.setChecked(settings.get('filter_pit_laps', True))

        with QSignalBlocker(self.filter_outliers_checkbox):
            self.filter_outliers_checkbox.setChecked(settings.get('filter_outliers', True))

        with QSignalBlocker(self.iqr_spinbox):
            self.iqr_spinbox.setValue(float(settings.get('outlier_threshold', 1.5)))


class LapTimeBoxPlotAnalysis(UniversalAnalysisMDI):
    """
    圈速箱型圖分析 MDI 模組
    
    基於通用 MDI 架構實現的完整圈速箱型圖分析功能，
    支援所有車手的圈速分佈視覺化和統計分析。
    """
    
    def __init__(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        parent=None,
        **kwargs,
    ):
        logger.debug(f"[BOXPLOT_MDI] LapTimeBoxPlotAnalysis 開始初始化...")
        
        # 註冊圈速箱型圖模組類型
        if "laptime_boxplot" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            boxplot_config = AnalysisMDIConfig(
                analysis_type="laptime_boxplot",
                display_name=tr("laptime_boxplot", "圈速箱型圖"),
                default_size=(1200, 700),
                requires_driver_params=False,  # 圈速箱型圖不需要單一車手參數（載入所有車手）
                requires_lap_params=False,     # 圈速箱型圖不需要圈數參數
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["boxplot"]
            )
            UniversalAnalysisMDI.register_mdi_module_type("laptime_boxplot", boxplot_config)

        super().__init__("laptime_boxplot", parent)
        logger.debug(f"[BOXPLOT_MDI] 基類初始化完成, 數據管理器: {self.data_manager}")

        # 控制面板與全域設定暫存
        self.control_widget: Optional[QWidget] = None
        self._pending_boxplot_settings: Optional[Dict[str, Any]] = None
        
        # Stint Selector 組件 (2026-01-12 新增)
        self.stint_selector: Optional[UniversalStintSelector] = None
        self.tab_widget: Optional[QTabWidget] = None
        self._raw_lap_data: Optional[Dict[str, Any]] = None  # 緩存原始圈速數據
        
        # 防抖動計時器 (2026-01-12 新增)
        from PyQt5.QtCore import QTimer
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(100)  # 100ms 防抖動
        self._debounce_timer.timeout.connect(self._execute_chart_update)
        self._pending_update_data: Optional[Dict[str, Any]] = None

        # 初始化模組組件
        logger.debug(f"[BOXPLOT_MDI] 開始初始化模組組件...")
        if not self.initialize_module():
            logger.error(f"[BOXPLOT_MDI] ❌ 模組組件初始化失敗")
            return

        logger.info(f"[BOXPLOT_MDI] ✅ 模組組件初始化完成")
        logger.debug(f"[BOXPLOT_MDI] 數據管理器: {self.data_manager}")
        logger.debug(f"[BOXPLOT_MDI] 圖表組件: {self.chart_widget}")

        # 設置響應式佈局
        self.set_responsive_layout()

        # 與全域系統設定同步
        self.settings_manager = gui_settings_manager
        try:
            self.settings_manager.boxplot_settings_changed.connect(self._on_global_boxplot_settings_changed)
        except Exception as exc:
            logger.debug(f"[BOXPLOT_MDI] 無法連接全域設定信號: {exc}")
        self._on_global_boxplot_settings_changed(self.settings_manager.get_boxplot_settings())

        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session

        if kwargs:
            self._debug(f"忽略未使用的初始化參數: {kwargs}")
        
    def create_data_manager(self) -> LapTimeBoxPlotDataManager:
        """創建圈速箱型圖數據管理器"""
        return LapTimeBoxPlotDataManager(self)
        
    def create_chart_widget(self) -> LapTimeBoxPlotChartWidget:
        """創建圈速箱型圖圖表組件"""
        # 修正：傳入 None 而非 self（self 是 QObject，不是 QWidget）
        return LapTimeBoxPlotChartWidget(parent=None)
        
    def create_additional_widgets(self) -> List[QWidget]:
        """建立控制面板並掛載至主視窗。"""
        widgets: List[QWidget] = []

        try:
            control_widget = self.create_control_widget()
            self.control_widget = control_widget
        except Exception as exc:
            logger.debug(f"[BOXPLOT_MDI] 建立控制面板失敗: {exc}")
            import traceback
            traceback.print_exc()
            self.control_widget = None
            control_widget = None

        if control_widget is not None:
            control_widget.setVisible(False)
            if self._pending_boxplot_settings:
                control_widget.apply_settings(self._pending_boxplot_settings)

        return widgets

    def create_control_widget(self) -> LapTimeBoxPlotControlWidget:
        """創建圈速箱型圖控制面板"""
        # 修正：傳入 main_widget 而非 self
        control_widget = LapTimeBoxPlotControlWidget(self.main_widget)
        
        # 連接信號
        control_widget.settings_changed.connect(self._on_filter_settings_changed)
        control_widget.reload_requested.connect(self._on_reload_requested)
        control_widget.export_requested.connect(self._on_export_requested)
        
        return control_widget
    
    def _setup_ui(self):
        """
        覆寫 UI 設置 - 添加 Tab 架構（2026-01-12 更新）
        
        Tab 1: 圖表顯示（圈速箱型圖）
        Tab 2: Stint Selection（使用 UniversalStintSelector）
        """
        logger.info("[BOXPLOT_MDI] _setup_ui() 開始執行 - Tab UI 架構")
        
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 創建 Tab Widget
        self.tab_widget = QTabWidget()
        
        # ============ Tab 1: 圖表顯示 ============
        chart_tab = QWidget()
        chart_tab_layout = QVBoxLayout(chart_tab)
        chart_tab_layout.setContentsMargins(5, 5, 5, 5)
        
        # 圖表區域
        if self.chart_widget and not self._is_widget_valid(self.chart_widget):
            self._debug("檢測到已失效的圖表組件，重新建立")
            self._disconnect_chart_widget_signals()
            try:
                self.chart_widget = self.create_chart_widget()
            except Exception as create_exc:
                self._error(f"重新建立圖表組件失敗: {create_exc}")
                self.chart_widget = None
            else:
                self._connect_chart_widget_signals()
        
        if self.chart_widget:
            chart_frame = QFrame()
            chart_frame.setFrameStyle(QFrame.StyledPanel)
            chart_frame.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            chart_frame.setFocusPolicy(Qt.NoFocus)
            
            chart_frame_layout = QVBoxLayout(chart_frame)
            chart_frame_layout.setContentsMargins(5, 5, 5, 5)
            chart_frame_layout.addWidget(self.chart_widget)
            chart_tab_layout.addWidget(chart_frame)
        
        self.tab_widget.addTab(chart_tab, tr("boxplot.tab.chart", "Chart"))
        
        # ============ Tab 2: Stint Selection ============
        stint_tab = QWidget()
        stint_tab_layout = QVBoxLayout(stint_tab)
        stint_tab_layout.setContentsMargins(5, 5, 5, 5)
        
        # 創建 Stint Selector (V0.15.1: 添加 module_id 和 Global Sync)
        try:
            self.stint_selector = UniversalStintSelector(module_id="lap_boxplot_driver_race")
            self.stint_selector.selection_changed.connect(self._on_stint_selection_changed)
            self.stint_selector.merge_mode_changed.connect(self._on_merge_mode_changed)
            # V0.15.1: 預設啟用全局同步
            self.stint_selector.enable_global_sync(True)
            stint_tab_layout.addWidget(self.stint_selector)
            logger.info("[BOXPLOT_MDI] Stint Selector 創建成功")
        except Exception as exc:
            logger.error(f"[BOXPLOT_MDI] Stint Selector 創建失敗: {exc}")
            import traceback
            traceback.print_exc()
            # 添加佔位標籤
            placeholder = QLabel(tr("boxplot.stint.error", "Stint Selector unavailable"))
            placeholder.setAlignment(Qt.AlignCenter)
            stint_tab_layout.addWidget(placeholder)
        
        self.tab_widget.addTab(stint_tab, tr("boxplot.tab.stint_selection", "Stint Selection"))
        
        # 添加 Tab Widget 到主佈局
        main_layout.addWidget(self.tab_widget)
        
        # 控制面板（隱藏，通過 create_additional_widgets 創建）
        additional_widgets = self.create_additional_widgets()
        for widget in additional_widgets:
            if widget:
                widget.setVisible(False)
        
        # 狀態列（可選）
        self.status_bar = None
        
        logger.info("[BOXPLOT_MDI] Tab UI 設置完成 (Chart + Stint Selection)")
    
    def _on_stint_selection_changed(self, selected_stints: List[StintInfo]) -> None:
        """處理 Stint 選擇變更（帶防抖動）"""
        logger.debug(f"[BOXPLOT_MDI] Stint 選擇變更: {len(selected_stints)} stints")
        
        if not self.stint_selector or not self.chart_widget:
            return
        
        # 準備更新數據
        self._pending_update_data = {'trigger': 'selection_changed'}
        
        # 重置防抖動計時器
        self._debounce_timer.stop()
        self._debounce_timer.start()
    
    def _on_merge_mode_changed(self, is_merge_mode: bool) -> None:
        """處理合併模式切換（帶防抖動）"""
        logger.info(f"[BOXPLOT_MDI] 合併模式切換: {'合併' if is_merge_mode else '分組'}")
        
        # 準備更新數據
        self._pending_update_data = {'trigger': 'merge_mode_changed', 'is_merge': is_merge_mode}
        
        # 重置防抖動計時器
        self._debounce_timer.stop()
        self._debounce_timer.start()
    
    def _execute_chart_update(self) -> None:
        """執行實際的圖表更新（防抖動後觸發）"""
        if not self.stint_selector or not self.chart_widget:
            return
        
        is_merge_mode = self.stint_selector.is_merge_mode()
        logger.info(f"[BOXPLOT_MDI] 執行圖表更新 - 模式: {'合併' if is_merge_mode else '分組'}")
        
        if is_merge_mode:
            # 合併模式：一個車手一個 Box
            driver_laptimes = self.stint_selector.get_selected_lap_times_by_driver()
            self._update_chart_merged_mode(driver_laptimes)
        else:
            # 分組模式：每個 Stint 一個 Box
            stint_laptimes = self.stint_selector.get_lap_times_by_stint()
            self._update_chart_stint_mode(stint_laptimes)
    
    def _update_chart_merged_mode(self, driver_laptimes: Dict[str, List[float]]) -> None:
        """合併模式：每個車手一個 Box"""
        if not driver_laptimes:
            logger.debug("[BOXPLOT_MDI] 沒有選中的圈速數據")
            return
        
        # 計算統計數據
        import numpy as np
        statistics = {}
        for driver, lap_times in driver_laptimes.items():
            if not lap_times:
                continue
            statistics[driver] = {
                'mean': float(np.mean(lap_times)),
                'median': float(np.median(lap_times)),
                'q1': float(np.percentile(lap_times, 25)),
                'q3': float(np.percentile(lap_times, 75)),
                'iqr': float(np.percentile(lap_times, 75) - np.percentile(lap_times, 25)),
                'count': len(lap_times)
            }
        
        # 準備圖表數據
        processed_data = {
            'driver_laptimes': driver_laptimes,
            'statistics': statistics,
            'metadata': {
                'data_source': 'stint_filtered',
                'stint_mode': 'merged'
            }
        }
        
        # 更新圖表
        if self.chart_widget and hasattr(self.chart_widget, 'update_data'):
            self.chart_widget.update_data(processed_data)
            logger.info(f"[BOXPLOT_MDI] 圖表已更新 (合併模式): {len(driver_laptimes)} 車手")
    
    def _update_chart_stint_mode(self, stint_laptimes: Dict[str, Dict[int, List[float]]]) -> None:
        """分組模式：每個 Stint 一個 Box"""
        if not stint_laptimes:
            logger.debug("[BOXPLOT_MDI] 沒有選中的 Stint 數據")
            return
        
        import numpy as np
        
        # 將 stint 數據轉換為圖表格式
        # 格式: "VER_S1", "VER_S2", "LEC_S1", ...
        driver_laptimes: Dict[str, List[float]] = {}
        statistics: Dict[str, Dict] = {}
        stint_labels: Dict[str, str] = {}  # 用於圖表標籤
        
        for driver, stints in stint_laptimes.items():
            for stint_num, lap_times in stints.items():
                if not lap_times:
                    continue
                
                # 創建唯一標籤: "VER_S1"
                label = f"{driver}_S{stint_num}"
                driver_laptimes[label] = lap_times
                stint_labels[label] = f"{driver} Stint {stint_num}"
                
                statistics[label] = {
                    'mean': float(np.mean(lap_times)),
                    'median': float(np.median(lap_times)),
                    'q1': float(np.percentile(lap_times, 25)),
                    'q3': float(np.percentile(lap_times, 75)),
                    'iqr': float(np.percentile(lap_times, 75) - np.percentile(lap_times, 25)),
                    'count': len(lap_times),
                    'driver': driver,
                    'stint': stint_num
                }
        
        # 按車手代碼排序
        sorted_labels = sorted(driver_laptimes.keys())
        driver_laptimes = {k: driver_laptimes[k] for k in sorted_labels}
        statistics = {k: statistics[k] for k in sorted_labels}
        
        # 準備圖表數據
        processed_data = {
            'driver_laptimes': driver_laptimes,
            'statistics': statistics,
            'stint_labels': stint_labels,
            'metadata': {
                'data_source': 'stint_filtered',
                'stint_mode': 'separate'
            }
        }
        
        # 更新圖表
        if self.chart_widget and hasattr(self.chart_widget, 'update_data'):
            self.chart_widget.update_data(processed_data)
            logger.info(f"[BOXPLOT_MDI] 圖表已更新 (分組模式): {len(driver_laptimes)} 個 Stint")
    
    def _update_chart_with_stint_data(self, driver_laptimes: Dict[str, List[float]]) -> None:
        """使用 Stint 過濾後的數據更新圖表（舊方法，保留向後兼容）"""
        self._update_chart_merged_mode(driver_laptimes)
    
    def _update_chart(self, data: dict):
        """
        覆寫基類方法 - 同時更新圖表和 Stint Selector
        
        當 API 數據載入完成時調用
        """
        try:
            logger.debug(f"[BOXPLOT_MDI] _update_chart 被調用")
            
            # 緩存原始數據供 Stint Selector 使用
            self._raw_lap_data = data
            
            # 調用基類方法更新圖表（默認行為）
            super()._update_chart(data)
            
            # 更新 Stint Selector
            self._populate_stint_selector(data)
            
        except Exception as e:
            logger.error(f"[BOXPLOT_MDI] 圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_stint_selector(self, data: dict) -> None:
        """
        從 API 數據填充 Stint Selector
        
        數據結構：
        {
            'driver_laptimes': {...},
            'statistics': {...},
            'metadata': {...}
        }
        
        原始數據在 data_manager._raw_data_cache 中
        """
        if not self.stint_selector:
            logger.debug("[BOXPLOT_MDI] Stint Selector 未初始化，跳過填充")
            return
        
        try:
            # 獲取原始圈速數據（包含進站標記）
            raw_data = None
            if hasattr(self, 'data_manager') and self.data_manager:
                raw_data = getattr(self.data_manager, '_raw_data_cache', None)
            
            if not raw_data:
                logger.debug("[BOXPLOT_MDI] 無原始數據緩存，使用當前數據")
                raw_data = data
            
            # V0.15.1: 設置 Session 資訊（用於 Global Sync 過濾）
            self.stint_selector.set_session_info(
                year=str(self.current_year),
                race=self.current_race,
                session=self.current_session
            )
            
            # 傳遞數據給 Stint Selector 進行 Stint 偵測
            self.stint_selector.set_data(raw_data)
            
            logger.debug("[BOXPLOT_MDI] Stint Selector 已更新")
            
        except Exception as e:
            logger.error(f"[BOXPLOT_MDI] Stint Selector 填充失敗: {e}")
            import traceback
            traceback.print_exc()
        
    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """更新圈速箱型圖分析參數"""
        try:
            logger.debug(f"[BOXPLOT_MDI] ========== 圈速箱型圖參數更新 ==========")
            logger.debug(f"[BOXPLOT_MDI] 收到參數: {year} {race} {session}")
            
            # 更新當前參數
            self.current_year = int(year) if isinstance(year, str) else year
            self.current_race = race
            self.current_session = session
            
            # 連接錯誤處理器 (只連接一次)
            if not hasattr(self, '_error_handler_connected'):
                if hasattr(self, 'data_manager') and self.data_manager:
                    self.data_manager.load_error.connect(self._on_data_load_error)
                    self._error_handler_connected = True
            
            # 更新數據管理器參數
            if hasattr(self, 'data_manager') and self.data_manager:
                logger.debug(f"[BOXPLOT_MDI] 更新數據管理器參數...")
                self.data_manager.year = self.current_year
                self.data_manager.race = self.current_race
                self.data_manager.session = self.current_session
                
                # 載入數據
                logger.debug(f"[BOXPLOT_MDI] 開始載入數據...")
                result = self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
                logger.debug(f"[BOXPLOT_MDI] 數據載入結果: {result}")
                
                if not result:
                    logger.warning(f"[BOXPLOT_MDI] ⚠️ 數據載入請求未成功提交")
                
                # 注意: 數據載入是異步的,實際數據會通過 data_loaded 信號傳遞
            
            logger.debug(f"[BOXPLOT_MDI] 參數更新完成")
            return True
            
        except Exception as e:
            logger.debug(f"[BOXPLOT_MDI] 參數更新失敗: {str(e)}")
            import traceback
            logger.debug(f"[BOXPLOT_MDI] 錯誤詳情:")
            traceback.print_exc()
            return False
    
    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        """更新分析參數"""
        try:
            # 更新當前參數
            self.update_lap_parameters(
                year=int(year) if isinstance(year, str) else year,
                race=race,
                session=session
            )
            
            # 觸發數據重新載入
            if hasattr(self, 'data_manager') and self.data_manager:
                return self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
            
            return True
            
        except Exception as e:
            self._debug(f"更新分析參數失敗: {str(e)}")
            return False
    
    def _on_filter_settings_changed(self, settings: Dict[str, Any]):
        """過濾設定變更處理"""
        logger.debug(f"[BOXPLOT_MDI] 過濾設定變更: {settings}")

        if not hasattr(self, 'settings_manager') or self.settings_manager is None:
            return

        # 以系統設定為真實資料來源，避免多重資料路徑
        global_settings = self.settings_manager.get_boxplot_settings()
        payload = dict(global_settings)
        payload.setdefault('filter_yellow_flags', True)
        payload.update({
            'filter_pit_laps': settings.get('filter_pit_laps', payload.get('filter_pit_laps', True)),
            'filter_outliers': settings.get('filter_outliers', payload.get('filter_outliers', True)),
            'outlier_threshold': settings.get('outlier_threshold', payload.get('outlier_threshold', 1.5)),
        })
        self.settings_manager.update_boxplot_settings(**payload)

    def _on_global_boxplot_settings_changed(self, settings: Dict[str, Any]) -> None:
        """全域系統設定更新時同步控制面板與圖表。"""
        if not isinstance(settings, dict):
            return

        self._pending_boxplot_settings = dict(settings)

        control_ready = hasattr(self, 'control_widget') and self.control_widget is not None
        data_ready = hasattr(self, 'data_manager') and self.data_manager is not None
        chart_ready = hasattr(self, 'chart_widget') and self.chart_widget is not None

        if control_ready:
            self.control_widget.apply_settings(settings)

        if not data_ready:
            return

        try:
            self.data_manager.update_filter_settings(settings)

            processed = self.data_manager.get_processed_data()
            if processed and chart_ready:
                self.chart_widget.update_data(processed)

                if control_ready:
                    driver_laptimes = processed.get('driver_laptimes', {}) or {}
                    total_drivers = len(driver_laptimes)
                    total_laps = sum(len(laps) for laps in driver_laptimes.values())
                    stats_text = f"✅ 車手: {total_drivers} | 圈數: {total_laps}"
                    self.control_widget.update_statistics(stats_text)

        except Exception as exc:
            logger.debug(f"[BOXPLOT_MDI] 全域設定套用失敗: {exc}")
            import traceback
            traceback.print_exc()
    
    def _on_data_load_error(self, error_message: str):
        """處理數據載入錯誤 - 向用戶顯示友好的錯誤提示"""
        logger.error(f"[BOXPLOT_MDI] ❌ 數據載入錯誤: {error_message}")
        
        # 更新控制面板統計信息
        if hasattr(self, 'control_widget') and self.control_widget:
            self.control_widget.update_statistics("❌ 數據載入失敗")
        
        # 顯示詳細錯誤訊息給用戶
        from PyQt5.QtWidgets import QMessageBox
        
        # 判斷錯誤類型並提供對應解決方案
        if "API" in error_message and "本地" in error_message:
            # API 失敗且本地 JSON 不存在
            solution_text = (
                f"無法載入{tr('laptime_boxplot', '圈速箱型圖')}數據:\n{error_message}\n\n"
                "請執行以下操作之一:\n\n"
                "方案 1: 啟動 API 服務器\n"
                "   開啟新終端執行: python refactored_api.py\n"
                "   然後點擊「重新載入」按鈕\n\n"
                "方案 2: 手動生成數據檔案\n"
                f"   執行: python f1_analysis_modular_main.py -f 28 -y {self.current_year} -r {self.current_race} -s {self.current_session}\n"
                "   然後點擊「重新載入」按鈕"
            )
        else:
            solution_text = f"數據載入失敗:\n{error_message}\n\n請檢查 API 服務器是否運行,或確認本地 JSON 檔案存在。"
        
        # 使用 warning 而非 critical 以保持 GUI 可用性
        QMessageBox.warning(
            self.main_widget,
            f"{tr('laptime_boxplot', '圈速箱型圖')} - 數據載入失敗",
            solution_text,
            QMessageBox.Ok
        )
    
    def _on_reload_requested(self):
        """重新載入數據"""
        logger.debug("[BOXPLOT_MDI] 重新載入數據...")
        
        if not self.data_manager:
            return
        
        # 強制重新載入
        success = self.data_manager.load_data(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            force_refresh=True
        )
        
        if not success:
            logger.debug("[BOXPLOT_MDI] 重新載入失敗")
            if self.control_widget:
                self.control_widget.update_statistics("❌ 重新載入失敗")
    
    def _on_export_requested(self):
        """匯出圖表"""
        logger.debug("[BOXPLOT_MDI] 匯出圖表...")
        
        if not self.chart_widget:
            return
        
        # 預設檔案名稱
        default_filename = f"boxplot_{self.current_year}_{self.current_race}_{self.current_session}.png"
        default_path = os.path.join(os.getcwd(), "exports", default_filename)
        
        # 選擇儲存路徑
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            tr("export_boxplot", "匯出圈速箱型圖"),
            default_path,
            "PNG 圖片 (*.png);;所有檔案 (*.*)"
        )
        
        if filepath:
            try:
                # 確保目錄存在
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # 匯出圖表
                self.chart_widget.export_chart(filepath)
                
                QMessageBox.information(
                    self,
                    tr("export_success", "匯出成功"),
                    f"{tr('chart_exported_to', '圖表已匯出至')}:\n{filepath}"
                )
            except Exception as e:
                logger.debug(f"[BOXPLOT_MDI] 匯出失敗: {e}")
                QMessageBox.warning(
                    self,
                    tr("export_failed", "匯出失敗"),
                    f"{tr('cannot_export_chart', '無法匯出圖表')}:\n{e}"
                )
    
    def resizeEvent(self, event):
        """MDI視窗大小調整時的響應邏輯"""
        try:
            # 調用基類的 resizeEvent
            super().resizeEvent(event)
            
            # 記錄尺寸變化
            old_size = event.oldSize()
            new_size = event.size()
            
            logger.debug(f"[BOXPLOT_MDI] resizeEvent: MDI視窗縮放 {old_size.width()}x{old_size.height()} -> {new_size.width()}x{new_size.height()}")
            
            # 通知圖表組件更新佈局
            if hasattr(self, 'chart_widget') and self.chart_widget:
                if hasattr(self.chart_widget, 'update_chart_layout'):
                    logger.debug("[BOXPLOT_MDI] resizeEvent: 觸發圖表重新佈局")
                    self.chart_widget.update_chart_layout()
                else:
                    logger.debug("[BOXPLOT_MDI] resizeEvent: 圖表組件不支援動態佈局更新")
            else:
                logger.debug("[BOXPLOT_MDI] resizeEvent: 圖表組件尚未初始化")
                
        except Exception as e:
            logger.error(f"[BOXPLOT_MDI] resizeEvent 處理失敗: {e}")
    
    def set_responsive_layout(self):
        """設置響應式佈局"""
        try:
            # 設置大小策略（必須在 QWidget 上調用，不是 QObject）
            from PyQt5.QtWidgets import QSizePolicy
            if hasattr(self, 'main_widget') and self.main_widget:
                self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # 確保圖表組件也有正確的大小策略
            if hasattr(self, 'chart_widget') and self.chart_widget:
                self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
            logger.debug("[BOXPLOT_MDI] 響應式佈局已設置")
            
        except Exception as e:
            logger.error(f"[BOXPLOT_MDI] 設置響應式佈局失敗: {e}")

    def get_module_info(self) -> Dict[str, Any]:
        """獲取模組信息"""
        return {
            "name": "下雨分析",
            "type": "rain",
            "version": "1.0.0",
            "description": "F1 比賽降雨天氣分析模組",
            "author": "F1T Team",
            "supports_realtime": False,
            "data_sources": ["JSON", "CLI Function 28"],
            "chart_types": ["箱型圖"],
            "parameters": {
                "requires_year": True,
                "requires_race": True,
                "requires_session": True,
                "requires_driver": False,
                "requires_lap": False
            },
            "features": [
                "圈速分布箱型圖",
                "IQR異常值過濾",
                "進站圈過濾",
                "統計指標顯示",
                "車隊配色方案"
            ]
        }
                
    def validate_parameters(self) -> Tuple[bool, str]:
        """驗證模組參數"""
        if not self.current_year:
            return False, "請選擇年份"
            
        if not self.current_race:
            return False, "請選擇比賽"
            
        if not self.current_session:
            return False, "請選擇賽段"
            
        return True, ""
        
    def get_analysis_summary(self) -> Dict[str, Any]:
        """獲取分析摘要"""
        if not self.data_manager:
            return {}
            
        try:
            # 獲取處理後的數據
            processed_data = self.data_manager.get_processed_data()
            
            if not processed_data:
                return {}
            
            driver_laptimes = processed_data.get('driver_laptimes', {})
            statistics = processed_data.get('statistics', {})
            
            # 計算總圈數和車手數
            total_laps = sum(len(laps) for laps in driver_laptimes.values())
            driver_count = len(driver_laptimes)
            
            # 獲取過濾設定
            filter_settings = self.data_manager.filter_settings
            
            summary = {
                "module": "圈速箱型圖分析",
                "parameters": {
                    "year": self.current_year,
                    "race": self.current_race,
                    "session": self.current_session
                },
                "data_info": {
                    "total_drivers": driver_count,
                    "total_laps": total_laps,
                    "filter_pit_laps": filter_settings.get('filter_pit_laps', True),
                    "filter_yellow_flags": filter_settings.get('filter_yellow_flags', True),
                    "filter_outliers": filter_settings.get('filter_outliers', True),
                    "outlier_threshold": filter_settings.get('outlier_threshold', 1.5)
                },
                "statistics_summary": {
                    driver: {
                        "lap_count": stats.get('count', 0),
                        "mean_time": round(stats.get('mean', 0), 3),
                        "median_time": round(stats.get('median', 0), 3)
                    }
                    for driver, stats in statistics.items()
                },
                "generated_at": self.get_current_timestamp()
            }
            
            # 添加數據源資訊
            data_source = getattr(self.data_manager, "get_last_data_source", lambda: "unknown")()
            summary["data_source"] = data_source
            if data_source == "api":
                api_meta = getattr(self.data_manager, "get_last_api_metadata", lambda: {})()
                if api_meta:
                    summary["api_meta"] = api_meta
                    
            return summary
            
        except Exception as e:
            self._debug(f"獲取分析摘要失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def reset_chart_view(self):
        """
        重置圖表視圖（主 GUI "Show All Data" 按鈕調用）
        
        這個方法會被主 GUI 的 show_all_data_in_current_tab() 調用
        用於恢復所有被隱藏的車手數據
        """
        try:
            logger.debug("[BOXPLOT_MDI] 🔄 收到 reset_chart_view 請求")
            
            # 檢查 chart_widget 是否存在
            if not hasattr(self, 'chart_widget') or not self.chart_widget:
                logger.warning("[BOXPLOT_MDI] ⚠️  chart_widget 不存在")
                return
            
            # 檢查 chart_widget 是否有 show_all_drivers 方法
            if not hasattr(self.chart_widget, 'show_all_drivers'):
                logger.warning("[BOXPLOT_MDI] ⚠️  chart_widget 沒有 show_all_drivers 方法")
                return
            
            # 調用 Widget 的 show_all_drivers() 方法
            logger.info("[BOXPLOT_MDI] ✅ 調用 chart_widget.show_all_drivers()")
            self.chart_widget.show_all_drivers()
            
        except Exception as e:
            logger.error(f"[BOXPLOT_MDI] ❌ reset_chart_view 失敗: {e}")
            import traceback

            traceback.print_exc()


# 模組註冊 - 確保在導入時自動註冊
def register_boxplot_analysis_module():
    """註冊圈速箱型圖分析模組"""
    try:
        # 這裡可以添加到全局模組註冊表
        logger.debug("[BOXPLOT_MDI] 圈速箱型圖分析模組已註冊")
    except Exception as e:
        logger.warning(f"圈速箱型圖分析模組註冊失敗: {str(e)}")


# 自動註冊
register_boxplot_analysis_module()


class LapBoxPlotAnalysisModule(LapTimeBoxPlotAnalysis):
    """向後相容的別名，供既有匯入路徑使用"""

    pass
