#!/usr/bin/env python3
"""
TireAnalysisUniversal - F1T 通用輪胎策略分析模組
===============================================

基於通用 MDI 架構實現的輪胎策略分析模組，支援：
- 輪胎配方策略分析（SOFT/MEDIUM/HARD）
- Stint 時間分析和比較
- 橫向長條圖顯示
- CLI -f26 數據生成
- 車手輪胎策略視覺化

數據來源：CLI -f26 生成的 tire_strategy JSON 檔案
圖表類型：橫向長條圖

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QGridLayout, QPushButton, QComboBox,
    QCheckBox, QSpinBox, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

import requests
from core.api_base_url import resolve_api_base_url
from core.api_runtime_state import is_api_available

# 導入翻譯函數
from core.gui_i18n import tr

# 導入通用基礎類別
try:
    from ..base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from ..base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
    from ..base.universal_chart_widget_base import TelemetryChartWidgetBase, ChartTheme
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
    from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase, ChartTheme


class TireAnalysisApiWorker(QThread):
    """Background worker that fetches tire analysis data from the REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 60.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout

    def run(self):
        try:
            self.progress.emit(15)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 26,
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
            self.progress.emit(65)
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
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:
            self.failure.emit(str(exc))
        finally:
            self.progress.emit(100)


class TireAnalysisDataManager(UniversalDataLoader):
    """輪胎策略分析數據管理器"""
    
    def __init__(self, parent=None):
        # 註冊輪胎策略分析類型（如果尚未註冊）
        if "tire_strategy" not in UniversalDataLoader.ANALYSIS_TYPES:
            tire_config = AnalysisConfig(
                display_name="輪胎策略分析",
                debug_prefix="[TIRE_ANALYSIS]",
                data_source="api",
                cli_function="26",  # CLI -f26: 輪胎換胎時機推論
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=26,
                api_timeout=60.0,
                file_patterns=[
                    "tire_strategy_{year}_{race}_{session}.json",           # 新格式 (不含 all_drivers)
                    "tire_strategy_{year}_{race}_{session}_all_drivers.json", # 新格式變體
                    "tire_timing_inference_{year}_{race_full}_None_all_drivers.json"  # 向下兼容舊格式
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True
            )
            UniversalDataLoader.register_analysis_type("tire_strategy", tire_config)
        
        super().__init__("tire_strategy", parent)
        
        # 輪胎策略分析特定屬性
        self.tire_data = {}
        self.stint_mapping = {}
        self.strategy_stats = {}
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[TireAnalysisApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        fallback_state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(
            f"本地 JSON 後備已{fallback_state} (策略: {self._fallback_policy_reason})"
        )
        
        print(f"[TIRE_ANALYSIS] 初始化完成, 搜索目錄: {self.config.search_directories}")
        print(f"[TIRE_ANALYSIS] 文件模式: {self.config.file_patterns}")
        
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
        env_value = os.getenv("F1T_ALLOW_TIRE_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_TIRE_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_TIRE_JSON_FALLBACK={env_value}"
        return False, "預設策略 (API 優先，不允許本地回退)"

    def _is_api_available(self) -> bool:
        available = is_api_available()
        if not available:
            self._debug("API marked offline by shared runtime cache")
        return available
    def set_local_fallback_allowed(self, allowed: bool, reason: Optional[str] = None) -> None:
        """Manually toggle whether local JSON fallback is allowed."""
        self._allow_local_fallback = bool(allowed)
        self._fallback_policy_reason = reason or "手動覆寫"
        state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(f"本地 JSON 後備手動設為{state} (原因: {self._fallback_policy_reason})")

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
        """載入輪胎策略分析資料，優先透過 API，失敗時視策略回退本地流程。"""
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

        self._debug(f"透過 API 載入輪胎策略資料: base_url={self._api_base_url}, params={self._pending_params}")
        self.load_progress.emit(5)
        self.status_changed.emit("正在透過 API 載入輪胎策略資料...")

        if not self._is_api_available():
            self._debug("API 健康檢查失敗，跳過背景執行緒啟動")
            self._is_loading = False
            self.status_changed.emit("API 服務不可用，請啟動 API 或使用本地資料")
            if self._allow_local_fallback:
                return super().load_data(**kwargs)
            self.load_error.emit("API 服務不可用且未啟用本地 JSON 後備")
            return False

        try:
            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            self._error(f"啟動 API 請求失敗: {exc}")
            self._is_loading = False
            self.status_changed.emit("API 載入失敗，改用本地資料")
            return super().load_data(**kwargs)

    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """Spawn the background worker that contacts the REST API."""
        self._cleanup_api_worker()

        worker_params = {
            "year": params.get("year"),
            "race": params.get("race"),
            "session": params.get("session"),
            "force_refresh": params.get("force_refresh", False),
        }

        timeout = getattr(self.config, "api_timeout", 60.0)
        self._api_worker = TireAnalysisApiWorker(self._api_base_url, worker_params, timeout=timeout, parent=self)
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
        try:
            raw_data = payload.get("data")
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"

            # 🔧 處理雙層嵌套格式：API 返回 {success, data: {success, data: {metadata, analysis}}}
            if isinstance(raw_data, dict) and "data" in raw_data and "success" in raw_data:
                raw_data = raw_data["data"]

            if not self._validate_data_format(raw_data):
                raise ValueError("API 回傳數據格式不符合預期")

            processed_data = self._process_data(raw_data)
            if isinstance(processed_data, dict):
                metadata = processed_data.setdefault("metadata", {})
                metadata.setdefault("data_source", "api")
                if self._last_api_meta:
                    metadata["api"] = self._last_api_meta

            self._current_data = processed_data
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit("已從 API 載入輪胎策略資料")
            self.data_loaded.emit(processed_data)

        except Exception as exc:
            self._error(f"處理 API 數據失敗: {exc}")
            self._is_loading = False
            self.status_changed.emit("API 資料格式錯誤，改用本地資料")
            self._fallback_to_local(str(exc))

    def _on_api_error(self, message: str) -> None:
        self._error(f"API 請求失敗: {message}")
        self._is_loading = False
        self.status_changed.emit("API 請求失敗，改用本地資料")
        self._fallback_to_local(message)

    def _fallback_to_local(self, reason: str) -> None:
        params = self._pending_params or {}
        if not params:
            self.load_error.emit(f"API 載入失敗: {reason}")
            return

        if not self._allow_local_fallback:
            self._last_data_source = "local-fallback-disabled"
            self._last_api_meta = {}
            message = (
                "API 載入失敗，且本地 JSON 後備已被策略停用。"
                " 如需啟用，請設定環境變數 F1T_ALLOW_TIRE_JSON_FALLBACK=1 或使用 set_local_fallback_allowed。"
            )
            self._debug(f"本地 JSON 後備被阻擋: {reason}")
            self._is_loading = False
            self.status_changed.emit("本地 JSON 後備已停用，請檢查 API 或手動啟用後備流程。")
            self.load_error.emit(message)
            return

        self._last_data_source = "local-json"
        self._last_api_meta = {}
        self._debug(f"啟動本地 JSON/CLI 後備流程: {reason}")
        self.status_changed.emit("使用本地 JSON/CLI 後備載入輪胎策略資料...")
        self.load_error.emit(f"API 載入失敗，使用本地資料: {reason}")
        super().load_data(**params)

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
        """構建檔案名稱模式 - 優先使用新的 CLI 參數格式"""
        patterns = []
        
        # 將賽事名稱轉換為完整格式（用於向下兼容）
        if race == "Japan":
            race_full = "Japanese_Grand_Prix"
        elif race == "Australia":
            race_full = "Australian_Grand_Prix"
        else:
            # 其他賽事可能需要特殊處理，暫時使用 {race}_Grand_Prix 格式
            race_full = f"{race}_Grand_Prix"
        
        for pattern in self.config.file_patterns:
            try:
                # 嘗試使用新格式（CLI 參數格式）
                if "race_full" not in pattern:
                    filename = pattern.format(
                        year=year, 
                        race=race,
                        session=session
                    )
                else:
                    # 向下兼容舊格式
                    filename = pattern.format(
                        year=year, 
                        race_full=race_full
                    )
                patterns.append(filename)
                self._debug(f"生成精確模式: {filename}")
            except KeyError as e:
                self._debug(f"模式格式錯誤: {pattern}, 錯誤: {e}")
                continue
        
        self._debug(f"總共生成 {len(patterns)} 個搜尋模式")
        return patterns

    def _start_generation_monitoring(self):
        """重寫監控方法，支援新舊格式"""
        self._debug("========== 啟動監控系統 ==========")
        
        if not hasattr(self, '_generation_params') or not self._generation_params:
            self._debug("❌ 沒有生成參數，無法啟動監控")
            return
            
        # 擴展生成參數，同時添加新舊格式支援
        expanded_params = self._generation_params.copy()
        race = expanded_params.get('race', '')
        if race == "Japan":
            expanded_params['race_full'] = "Japanese_Grand_Prix"
        else:
            expanded_params['race_full'] = f"{race}_Grand_Prix"
        
        self._debug(f"生成參數: {self._generation_params}")
        self._debug(f"擴展參數: {expanded_params}")
        
        # 檢查預期生成的檔案路徑（支援多種格式）
        if expanded_params:
            expected_patterns = []
            for pattern in self.config.file_patterns:
                try:
                    formatted_pattern = pattern.format(**expanded_params)
                    expected_patterns.append(formatted_pattern)
                except KeyError as e:
                    self._debug(f"⚠️ 格式化模式失敗: {pattern}, 錯誤: {e}")
                    continue
            self._debug(f"📋 預期檔案模式: {expected_patterns}")
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._debug("啟動主監控計時器 (每5秒檢查)")
        if hasattr(self, '_generation_timer'):
            self._generation_timer.start(5000)
        
        self._debug("啟動超時計時器 (180秒)")
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.start(180000)
        
        self._debug("✅ 監控系統已啟動")
        
    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式 - 支援多種輪胎分析 JSON 格式"""
        if not isinstance(data, dict):
            self._debug("數據格式錯誤：必須是字典格式")
            return False
        
        # 支援多種 JSON 格式
        valid_formats = [
            "drivers_analysis",           # CLI -f26 v2 新格式
            "tire_timing_corrected",      # CLI -f26 舊格式
            "all_drivers_tire_strategy",  # 舊格式
            "corrected_stint_analysis"    # 另一種格式
        ]
        
        has_valid_format = any(key in data for key in valid_formats)
        if not has_valid_format:
            self._debug(f"數據格式錯誤：缺少必要欄位，支援格式: {valid_formats}")
            self._debug(f"實際數據鍵值: {list(data.keys())}")
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
        self._debug("💡 提示: 請使用 API 獲取輪胎分析數據")
        return False
        
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的輪胎策略數據 - 支援多種 JSON 格式"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")
                
            # 儲存完整的原始數據
            self.data = data
            
            # 支援多種 JSON 格式的數據解析
            if "drivers_analysis" in data:
                # CLI -f26 v2 新格式
                self.tire_data = data["drivers_analysis"]
                self._debug("使用 drivers_analysis 格式 (CLI -f26 v2)")
            elif "tire_timing_corrected" in data:
                # CLI -f26 舊格式
                self.tire_data = data["tire_timing_corrected"]
                self._debug("使用 tire_timing_corrected 格式")
            elif "all_drivers_tire_strategy" in data:
                # 舊格式
                self.tire_data = data["all_drivers_tire_strategy"]
                self._debug("使用 all_drivers_tire_strategy 格式")
            elif "corrected_stint_analysis" in data:
                # 另一種格式
                self.tire_data = data["corrected_stint_analysis"]
                self._debug("使用 corrected_stint_analysis 格式")
            else:
                raise ValueError("找不到支援的輪胎策略數據格式")
                
            # 獲取摘要數據
            if "summary" in data:
                self.strategy_stats = data["summary"]
            elif "overall_statistics" in data:
                # 新格式的統計數據
                self.strategy_stats = data["overall_statistics"]
                self._debug("使用 overall_statistics 作為摘要數據")
            else:
                self.strategy_stats = {}
                
            # 轉換為分析用數據格式
            processed_data = {
                "tire_data": self._process_tire_strategy_data(),
                "summary": self.strategy_stats,
                "metadata": data.get("metadata", {}),
                "analysis_mode": data.get("analysis_mode", "unknown"),
                "drivers_analyzed": list(self.tire_data.keys()),  # 修復：使用實際的車手列表
                "charts_data": self._prepare_tire_chart_data()
            }

            metadata = processed_data.setdefault("metadata", {})
            if self._last_data_source:
                metadata["data_source"] = self._last_data_source
            if self._last_data_source == "api" and self._last_api_meta:
                existing_api_meta = metadata.get("api", {})
                merged_meta = dict(existing_api_meta)
                merged_meta.update(self._last_api_meta)
                metadata["api"] = merged_meta
            
            self._debug(f"成功處理 {len(self.tire_data)} 車手輪胎策略數據")
            
            return processed_data
            
        except Exception as e:
            self._debug(f"數據處理失敗: {str(e)}")
            raise
    
    def _calculate_compound_statistics(self, drivers_data) -> Dict[str, int]:
        """計算輪胎配方使用統計"""
        compound_count = {}
        
        for driver_info in drivers_data:
            for compound in driver_info["compounds_used"]:
                compound_count[compound] = compound_count.get(compound, 0) + 1
        
        return compound_count
            
    def _process_tire_strategy_data(self) -> Dict[str, List]:
        """處理輪胎策略數據"""
        drivers_data = []
        
        # 處理所有車手的輪胎策略數據
        for driver_code, driver_data in self.tire_data.items():
            if not isinstance(driver_data, dict):
                continue

            stint_data = (
                driver_data.get("stint_analysis")
                or driver_data.get("corrected_stint_analysis")
                or driver_data.get("original_stint_analysis")
                or driver_data.get("stints")
                or []
            )

            if not stint_data:
                continue

            driver_info = {
                "driver": driver_code,
                "stints": [],
                "total_laps": 0,
                "compounds_used": set(),
            }

            for index, stint in enumerate(stint_data, start=1):
                if not isinstance(stint, dict):
                    continue

                stint_number = (
                    stint.get("stint_number")
                    or stint.get("stint")
                    or index
                )
                compound = (
                    stint.get("compound")
                    or stint.get("tyre_compound")
                    or "UNKNOWN"
                )
                
                # 修復：使用明確的 None 檢查，避免 0 被視為假值
                start_lap = stint.get("start_lap")
                if start_lap is None:
                    start_lap = stint.get("lap_start")
                    if start_lap is None:
                        start_lap = stint.get("startLap")
                        if start_lap is None:
                            start_lap = 1
                
                # 修復：優先使用 end_lap，但要檢查其是否有效（> 0）
                end_lap = stint.get("end_lap")
                if end_lap is None or end_lap <= 0:
                    end_lap = stint.get("lap_end")
                    if end_lap is None or end_lap <= 0:
                        end_lap = stint.get("endLap")
                        if end_lap is None or end_lap <= 0:
                            # 嘗試使用 length 欄位計算 end_lap
                            length = stint.get("length")
                            if length is not None and length > 0:
                                end_lap = start_lap + length - 1
                            else:
                                # 最後的回退：使用 start_lap（單圈 stint）
                                end_lap = start_lap

                laps = stint.get("laps")
                if laps is None:
                    length = stint.get("length")
                    if length is not None:
                        laps = length
                    else:
                        try:
                            laps = max(0, int(end_lap) - int(start_lap) + 1)
                        except Exception:
                            laps = 0

                avg_laptime = (
                    stint.get("avg_laptime")
                    or stint.get("avg_lap_time")
                    or stint.get("avg_time")
                    or 0.0
                )

                stint_info = {
                    "stint_number": int(stint_number),
                    "compound": compound,
                    "start_lap": int(start_lap) if isinstance(start_lap, (int, float)) or str(start_lap).isdigit() else start_lap,
                    "end_lap": int(end_lap) if isinstance(end_lap, (int, float)) or str(end_lap).isdigit() else end_lap,
                    "laps": int(laps) if isinstance(laps, (int, float)) else laps,
                    "avg_laptime": float(avg_laptime) if isinstance(avg_laptime, (int, float)) else avg_laptime,
                }

                driver_info["stints"].append(stint_info)
                driver_info["compounds_used"].add(compound)

            if not driver_info["stints"]:
                continue

            if driver_data.get("driver_summary"):
                total_laps = driver_data["driver_summary"].get("total_laps")
            else:
                total_laps = None

            if total_laps is None:
                total_laps = sum(
                    stint.get("laps", 0) for stint in driver_info["stints"] if isinstance(stint, dict)
                )

            driver_info["total_laps"] = total_laps or 0
            driver_info["compounds_used"] = sorted(driver_info["compounds_used"])
            drivers_data.append(driver_info)
        
        return {
            "drivers": drivers_data,
            "total_drivers": len(drivers_data)
        }
        
    def _prepare_tire_chart_data(self) -> Dict[str, Any]:
        """準備輪胎圖表數據 - 構建圖表組件期望的數據結構"""
        if not hasattr(self, 'data') or not self.data:
            return {}
        
        # 構建圖表組件期望的數據結構
        chart_data = {
            # 原始 JSON 數據的關鍵字段
            "drivers_analyzed": list(self.tire_data.keys()),
            "tire_analysis": self.tire_data,  # 新格式使用 drivers_analysis
            "all_drivers_tire_strategy": self.tire_data,  # 為了兼容性
            
            # 保留原始數據供圖表組件使用
            "analysis_info": self.data.get("analysis_info", {}),
            "overall_statistics": self.data.get("overall_statistics", {}),
            "metadata": self.data.get("metadata", {})
        }
        
        self._debug(f"圖表數據已準備：{len(chart_data['drivers_analyzed'])} 個車手")
        
        return chart_data
        
    def get_tire_summary(self) -> Dict[str, Any]:
        """獲取輪胎策略摘要統計"""
        return {
            "total_drivers": len(self.tire_data),
            "total_stints": sum(len(driver_data.get("stint_analysis", [])) 
                              for driver_data in self.tire_data.values() 
                              if isinstance(driver_data, dict)),
            "compounds_used": list(set(
                stint.get("compound", "UNKNOWN")
                for driver_data in self.tire_data.values()
                if isinstance(driver_data, dict)
                for stint in driver_data.get("stint_analysis", [])
            )),
            "has_tire_data": len(self.tire_data) > 0,
            "strategy_analysis": self.strategy_stats.get("strategy_analysis", {})
        }


# 導入專用圖表組件
from .tire_analysis_chart_widget import TireAnalysisChartWidget


class TireAnalysisControlWidget(QWidget):
    """輪胎策略分析控制面板"""
    
    # 信號定義
    chart_type_changed = pyqtSignal(str)
    parameter_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        
        # 圖表選擇群組
        chart_group = QGroupBox("圖表類型")
        chart_layout = QGridLayout(chart_group)
        
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "輪胎策略分析",
            "輪胎配方使用統計"
        ])
        self.chart_combo.currentTextChanged.connect(self._on_chart_type_changed)
        
        chart_layout.addWidget(QLabel(tr("select_chart", "選擇圖表:")), 0, 0)
        chart_layout.addWidget(self.chart_combo, 0, 1)
        
        layout.addWidget(chart_group)
        
        # 顯示選項群組
        display_group = QGroupBox("顯示選項")
        display_layout = QGridLayout(display_group)
        
        self.show_grid_cb = QCheckBox("顯示網格")
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_grid", x))
        
        self.show_legend_cb = QCheckBox("顯示圖例")
        self.show_legend_cb.setChecked(True)
        self.show_legend_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_legend", x))
        
        display_layout.addWidget(self.show_grid_cb, 0, 0)
        display_layout.addWidget(self.show_legend_cb, 0, 1)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        
    def _on_chart_type_changed(self, text: str):
        """圖表類型改變處理"""
        chart_type_map = {
            "主要圖表 (降雨+氣溫)": "primary",
            "溫度對比 (氣溫vs賽道溫度)": "temperature",
            "濕度風速 (濕度+風速)": "humidity_wind",
            "氣壓變化": "pressure"
        }
        
        if text in chart_type_map:
            self.chart_type_changed.emit(chart_type_map[text])


class TireAnalysisUniversal(UniversalAnalysisMDI):
    """
    通用輪胎策略分析 MDI 模組
    
    基於通用 MDI 架構實現的完整輪胎策略分析功能，
    支援輪胎配方、Stint 和進站策略的視覺化和分析。
    """
    
    def __init__(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        parent=None,
        **kwargs,
    ):
        print(f"[TIRE_MDI] TireAnalysisUniversal 開始初始化...")
        
        # 註冊輪胎策略分析模組類型
        if "tire_analysis" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            tire_config = AnalysisMDIConfig(
                analysis_type="tire_analysis",
                display_name="輪胎策略分析",
                default_size=(1400, 900),
                requires_driver_params=False,  # 輪胎策略分析不需要車手參數
                requires_lap_params=False,     # 輪胎策略分析不需要圈數參數
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["primary", "stint_comparison", "compound_analysis", "strategy_overview"]
            )
            UniversalAnalysisMDI.register_mdi_module_type("tire_analysis", tire_config)

        super().__init__("tire_analysis", parent)
        print(f"[TIRE_MDI] 基類初始化完成, 數據管理器: {self.data_manager}")

        # 初始化模組組件
        print(f"[TIRE_MDI] 開始初始化模組組件...")
        if not self.initialize_module():
            print(f"[TIRE_MDI] ❌ 模組組件初始化失敗")
            return

        print(f"[TIRE_MDI] ✅ 模組組件初始化完成")
        print(f"[TIRE_MDI] 數據管理器: {self.data_manager}")
        print(f"[TIRE_MDI] 圖表組件: {self.chart_widget}")

        # 參照遙測分析：設置響應式佈局
        self.set_responsive_layout()

        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session

        if kwargs:
            self._debug(f"忽略未使用的初始化參數: {kwargs}")
        
    def create_data_manager(self) -> TireAnalysisDataManager:
        """創建輪胎策略分析數據管理器"""
        return TireAnalysisDataManager(self)
        
    def create_chart_widget(self) -> TireAnalysisChartWidget:
        """創建輪胎策略分析圖表組件"""
        return TireAnalysisChartWidget(parent=None)
        
    def create_control_widget(self) -> TireAnalysisControlWidget:
        """創建輪胎策略分析控制面板"""
        control_widget = TireAnalysisControlWidget(self)
        
        # 連接信號
        control_widget.chart_type_changed.connect(self._on_chart_type_changed)
        control_widget.parameter_changed.connect(self._on_parameter_changed)
        
        return control_widget
        
    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """更新輪胎策略分析參數"""
        try:
            print(f"[TIRE_MDI] ========== 輪胎策略參數更新 ==========")
            print(f"[TIRE_MDI] 收到參數: {year} {race} {session}")
            
            # 更新當前參數
            self.current_year = int(year) if isinstance(year, str) else year
            self.current_race = race
            self.current_session = session
            
            # 更新數據管理器參數
            if hasattr(self, 'data_manager') and self.data_manager:
                print(f"[TIRE_MDI] 更新數據管理器參數...")
                self.data_manager.year = self.current_year
                self.data_manager.race = self.current_race
                self.data_manager.session = self.current_session
                
                # 載入數據 - 傳遞正確的參數
                print(f"[TIRE_MDI] 開始載入數據...")
                result = self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
                print(f"[TIRE_MDI] 數據載入結果: {result}")
                
                # 注意：此處不直接更新圖表，等待 data_manager 發送 data_loaded 信號
                # 基類已綁定 data_loaded -> _update_chart -> chart_widget.update_data
                # 這可以避免非同步載入尚未完成時傳遞空資料
                if result:
                    print("[TIRE_MDI] 等待 data_loaded 信號進行圖表更新 (非同步載入) ...")
            
            print(f"[TIRE_MDI] 參數更新完成")
            return True
            
        except Exception as e:
            print(f"[TIRE_MDI] 參數更新失敗: {str(e)}")
            import traceback
            print(f"[TIRE_MDI] 錯誤詳情:")
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
    
    def resizeEvent(self, event):
        """參照遙測分析：MDI視窗大小調整時的響應邏輯"""
        try:
            # 調用基類的 resizeEvent
            super().resizeEvent(event)
            
            # 記錄尺寸變化
            old_size = event.oldSize()
            new_size = event.size()
            
            print(f"[tire_MDI] resizeEvent: MDI視窗縮放 {old_size.width()}x{old_size.height()} -> {new_size.width()}x{new_size.height()}")
            
            # 通知圖表組件更新佈局
            if hasattr(self, 'chart_widget') and self.chart_widget:
                if hasattr(self.chart_widget, 'update_chart_layout'):
                    print("[tire_MDI] resizeEvent: 觸發圖表重新佈局")
                    self.chart_widget.update_chart_layout()
                else:
                    print("[tire_MDI] resizeEvent: 圖表組件不支援動態佈局更新")
            else:
                print("[tire_MDI] resizeEvent: 圖表組件尚未初始化")
                
        except Exception as e:
            print(f"[ERROR] [tire_MDI] resizeEvent 處理失敗: {e}")
    
    def set_responsive_layout(self):
        """參照遙測分析：設置響應式佈局"""
        try:
            # 設置大小策略
            from PyQt5.QtWidgets import QSizePolicy, QWidget

            target_widget = None
            if hasattr(self, 'main_widget') and isinstance(getattr(self, 'main_widget'), QWidget):
                target_widget = self.main_widget
            elif hasattr(self, 'get_widget'):
                candidate = self.get_widget()
                if isinstance(candidate, QWidget):
                    target_widget = candidate

            if target_widget:
                target_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            else:
                print("[tire_MDI] ⚠️ 無法取得主要 Widget，略過 sizePolicy 設定")
            
            # 確保圖表組件也有正確的大小策略
            if hasattr(self, 'chart_widget') and self.chart_widget:
                self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
            print("[tire_MDI] 響應式佈局已設置")
            
        except Exception as e:
            print(f"[ERROR] [tire_MDI] 設置響應式佈局失敗: {e}")

    def get_module_info(self) -> Dict[str, Any]:
        """獲取模組信息"""
        return {
            "name": "下雨分析",
            "type": "tire",
            "version": "1.0.0",
            "description": "F1 比賽降雨天氣分析模組",
            "author": "F1T Team",
            "supports_realtime": False,
            "data_sources": ["JSON"],
            "chart_types": ["雙Y軸折線圖", "柱狀圖", "趨勢圖"],
            "parameters": {
                "requires_year": True,
                "requires_race": True,
                "requires_session": True,
                "requires_driver": False,
                "requires_lap": False
            }
        }
        
    def _on_chart_type_changed(self, chart_type: str):
        """處理圖表類型改變"""
        if hasattr(self.chart_widget, 'switch_chart_type'):
            self.chart_widget.switch_chart_type(chart_type)
            
    def _on_parameter_changed(self, param_name: str, value):
        """處理參數改變"""
        self._debug(f"參數改變: {param_name} = {value}")
        
        # 根據參數類型進行處理
        if param_name in ["show_grid", "show_legend"]:
            # 更新圖表顯示選項
            if hasattr(self.chart_widget, 'update_display_options'):
                self.chart_widget.update_display_options(param_name, value)
                
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
            tire_summary = self.data_manager.get_tire_summary()
            
            return {
                "module": "輪胎策略分析",
                "parameters": {
                    "year": self.current_year,
                    "race": self.current_race,
                    "session": self.current_session
                },
                "data_info": {
                    "total_laps": tire_summary.get("total_laps", 0),
                    "tire_laps": tire_summary.get("tire_laps", 0),
                    "tire_percentage": tire_summary.get("tire_percentage", 0.0),
                    "has_tire_data": tire_summary.get("has_tire_data", False)
                },
                "generated_at": self.get_current_timestamp()
            }
            
        except Exception as e:
            self._debug(f"獲取分析摘要失敗: {str(e)}")
            return {}


# 模組註冊 - 確保在導入時自動註冊
def register_tire_analysis_module():
    """註冊下雨分析模組"""
    try:
        # 這裡可以添加到全局模組註冊表
        pass
    except Exception as e:
        print(f"[WARNING] 下雨分析模組註冊失敗: {str(e)}")


# 自動註冊
register_tire_analysis_module()


class TireAnalysisModule(TireAnalysisUniversal):
    """向後相容的別名，供既有匯入路徑使用"""

    pass
