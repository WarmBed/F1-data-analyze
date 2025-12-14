#!/usr/bin/env python3
"""
RainAnalysisUniversal - F1T 通用下雨分析模組
=============================================

基於通用 MDI 架構實現的下雨分析模組，支援：
- 降雨狀態分析（有雨/無雨）
- 溫度變化分析（氣溫、賽道溫度）
- 濕度和風速分析
- 雙Y軸圖表顯示
- 圈數對應天氣數據

數據來源：enhanced_rain_analysis JSON 檔案
圖表類型：雙Y軸折線圖、柱狀圖

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


    logger = get_logger(component="rain_analysis_mdi")


class RainAnalysisApiWorker(QThread):
    """Background worker that fetches rain analysis data from the REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 20.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout

    def run(self):
        try:
            # 檢查是否已被請求中斷
            if self.isInterruptionRequested():
                logger.debug("[RAIN_API_WORKER] 啟動前已被請求中斷，跳過執行")
                return
                
            self.progress.emit(20)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 1,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            # 再次檢查中斷（在發送請求前）
            if self.isInterruptionRequested():
                logger.debug("[RAIN_API_WORKER] 發送請求前被請求中斷")
                return
                
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            
            # 請求完成後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[RAIN_API_WORKER] API 回應後被請求中斷，放棄處理結果")
                return
                
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
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }

            # 發送信號前最後檢查中斷
            if self.isInterruptionRequested():
                logger.debug("[RAIN_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
                return
                
            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:
            # 如果被中斷，不發送失敗信號
            if not self.isInterruptionRequested():
                self.failure.emit(str(exc))
        finally:
            # 只有在未中斷時才發送完成信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class RainAnalysisDataManager(UniversalDataLoader):
    """下雨分析數據管理器"""
    
    def __init__(self, parent=None):
        # 註冊下雨分析類型（如果尚未註冊）
        if "rain_weather" not in UniversalDataLoader.ANALYSIS_TYPES:
            rain_config = AnalysisConfig(
                display_name="Rain Analysis",
                debug_prefix="[RAIN_ANALYSIS]",
                data_source="api",
                cli_function="run_rain_intensity_analysis_json",
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=1,
                api_timeout=60.0,
                file_patterns=[
                    "enhanced_rain_analysis_{year}_{race}_{session}.json",
                    "rain_analysis_{year}_{race}_{session}.json",
                    "weather_data_{year}_{race}_{session}.json"
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True
            )
            UniversalDataLoader.register_analysis_type("rain_weather", rain_config)
        
        super().__init__("rain_weather", parent)
        
        # 下雨分析特定屬性
        self.weather_data = {}
        self.lap_weather_mapping = {}
        self.summary_stats = {}
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[RainAnalysisApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        fallback_state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(
            f"本地 JSON 後備已{fallback_state} (策略: {self._fallback_policy_reason})"
        )
        
        logger.debug("[RAIN_DATA_MANAGER] 初始化完成, 搜索目錄: %s", self.config.search_directories)
        logger.debug("[RAIN_DATA_MANAGER] 文件模式: %s", self.config.file_patterns)
        
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
        env_value = os.getenv("F1T_ALLOW_RAIN_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_RAIN_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_RAIN_JSON_FALLBACK={env_value}"
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

        timeout = getattr(self.config, "api_timeout", 60.0)
        self._api_worker = RainAnalysisApiWorker(self._api_base_url, worker_params, timeout=timeout, parent=self)
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
            self.status_changed.emit("已從 API 載入降雨分析資料")
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
                " 如需啟用，請設定環境變數 F1T_ALLOW_RAIN_JSON_FALLBACK=1 或使用 set_local_fallback_allowed。"
            )
            self._debug(f"本地 JSON 後備被阻擋: {reason}")
            self._is_loading = False
            self.status_changed.emit("本地 JSON 後備已停用，請檢查 API 或手動啟用後備流程。")
            self.load_error.emit(message)
            return

        self._last_data_source = "local-json"
        self._last_api_meta = {}
        self._debug(f"啟動本地 JSON/CLI 後備流程: {reason}")
        self.status_changed.emit("使用本地 JSON/CLI 後備載入降雨資料...")
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
            
        if "lap_weather_data" not in data:
            self._debug("數據格式錯誤：缺少 lap_weather_data 欄位")
            return False
            
        return True
        
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據的具體實現"""
        return self.process_loaded_data(data)
        
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用，系統只允許通過 API 獲取數據
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取降雨分析數據")
        return False
        
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的下雨分析數據"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")
                
            # 解析 JSON 結構
            if "lap_weather_data" in data:
                self.lap_weather_mapping = data["lap_weather_data"]
            else:
                raise ValueError("找不到圈數天氣數據：lap_weather_data")
                
            if "summary" in data:
                self.summary_stats = data["summary"]
            else:
                self.summary_stats = {}
                
            # 轉換為分析用數據格式
            processed_data = {
                "lap_data": self._process_lap_weather_data(),
                "summary": self.summary_stats,
                "metadata": data.get("metadata", {}),
                "charts_data": self._prepare_chart_data()
            }

            metadata = processed_data.setdefault("metadata", {})
            if self._last_data_source:
                metadata["data_source"] = self._last_data_source
            if self._last_data_source == "api" and self._last_api_meta:
                existing_api_meta = metadata.get("api", {})
                merged_meta = dict(existing_api_meta)
                merged_meta.update(self._last_api_meta)
                metadata["api"] = merged_meta
            
            self._debug(f"成功處理 {len(self.lap_weather_mapping)} 圈天氣數據")
            
            return processed_data
            
        except Exception as e:
            self._debug(f"數據處理失敗: {str(e)}")
            raise
            
    def _process_lap_weather_data(self) -> Dict[str, List]:
        """處理圈數天氣數據"""
        laps = []
        rainfall = []
        air_temp = []
        track_temp = []
        humidity = []
        wind_speed = []
        pressure = []
        
        # 按圈數順序處理數據
        lap_numbers = sorted([int(lap) for lap in self.lap_weather_mapping.keys()])
        
        for lap_num in lap_numbers:
            lap_str = str(lap_num)
            lap_data = self.lap_weather_mapping[lap_str]
            
            laps.append(lap_num)
            
            # 降雨狀態（布林值轉數值）
            rainfall_status = lap_data.get("weather", {}).get("rainfall", False)
            rainfall.append(1 if rainfall_status else 0)
            
            # 溫度數據
            temp_data = lap_data.get("temperature", {})
            air_temp.append(temp_data.get("air_temp", 0))
            track_temp.append(temp_data.get("track_temp", 0))
            
            # 其他天氣數據
            humidity.append(lap_data.get("humidity", 0))
            
            wind_data = lap_data.get("wind", {})
            wind_speed.append(wind_data.get("speed", 0))
            
            weather_data = lap_data.get("weather", {})
            pressure.append(weather_data.get("pressure", 0))
            
        return {
            "laps": laps,
            "rainfall": rainfall,
            "air_temp": air_temp,
            "track_temp": track_temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "pressure": pressure
        }
        
    def _prepare_chart_data(self) -> Dict[str, Any]:
        """準備圖表數據"""
        lap_data = self._process_lap_weather_data()
        
        return {
            # 主要圖表數據（降雨 + 溫度）
            "primary": {
                "x_data": lap_data["laps"],
                "y1_data": lap_data["rainfall"],  # 左Y軸：降雨狀態
                "y2_data": lap_data["air_temp"],  # 右Y軸：氣溫
                "y1_label": "降雨狀態",
                "y2_label": "氣溫 (°C)",
                "title": "降雨狀態與氣溫變化"
            },
            
            # 溫度對比圖表
            "temperature": {
                "x_data": lap_data["laps"],
                "y1_data": lap_data["air_temp"],
                "y2_data": lap_data["track_temp"],
                "y1_label": "氣溫 (°C)",
                "y2_label": tr("track_temperature", "賽道溫度 (°C)"),
                "title": tr("air_track_temp_comparison", "氣溫與賽道溫度對比")
            },
            
            # 濕度與風速圖表
            "humidity_wind": {
                "x_data": lap_data["laps"],
                "y1_data": lap_data["humidity"],
                "y2_data": lap_data["wind_speed"],
                "y1_label": "濕度 (%)",
                "y2_label": "風速 (m/s)",
                "title": "濕度與風速變化"
            },
            
            # 氣壓圖表
            "pressure": {
                "x_data": lap_data["laps"],
                "y_data": lap_data["pressure"],
                "y_label": "氣壓 (hPa)",
                "title": "氣壓變化"
            }
        }
        
    def get_rain_summary(self) -> Dict[str, Any]:
        """獲取降雨摘要統計"""
        return {
            "total_laps": self.summary_stats.get("total_laps", 0),
            "rain_laps": self.summary_stats.get("rain_laps", 0),
            "rain_percentage": self.summary_stats.get("rain_percentage", 0.0),
            "has_rain_data": self.summary_stats.get("has_rain_data", False),
            "rain_timing": self.summary_stats.get("rain_timing_analysis", {})
        }


# 導入專用圖表組件
from .rain_analysis_chart_widget import RainAnalysisChartWidget

from core.logger import get_logger
logger = get_logger(__name__)


class RainAnalysisControlWidget(QWidget):
    """下雨分析控制面板"""
    
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
        chart_group = QGroupBox(tr("chart_type", "Chart Type"))
        chart_layout = QGridLayout(chart_group)
        
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            tr("main_chart_rain_temperature", "主要圖表 (降雨+氣溫)"),
            tr("temperature_comparison_air_track", "溫度對比 (氣溫vs賽道溫度)"),
            tr("humidity_windspeed", "濕度風速 (濕度+風速)"),
            tr("pressure_changes", "氣壓變化")
        ])
        self.chart_combo.currentTextChanged.connect(self._on_chart_type_changed)
        
        chart_layout.addWidget(QLabel(tr("select_chart", "選擇圖表:")), 0, 0)
        chart_layout.addWidget(self.chart_combo, 0, 1)
        
        layout.addWidget(chart_group)
        
        # 顯示選項群組
        display_group = QGroupBox(tr("display_options", "Display Options"))
        display_layout = QGridLayout(display_group)
        
        self.show_grid_cb = QCheckBox(tr("show_grid_checkbox", "Show Grid"))
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_grid", x))
        
        self.show_legend_cb = QCheckBox(tr("show_legend_checkbox", "Show Legend"))
        self.show_legend_cb.setChecked(True)
        self.show_legend_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_legend", x))
        
        display_layout.addWidget(self.show_grid_cb, 0, 0)
        display_layout.addWidget(self.show_legend_cb, 0, 1)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        
    def _on_chart_type_changed(self, text: str):
        """圖表類型改變處理"""
        chart_type_map = {
            # 英文映射 (tr() 傳回 fallback 後的字串)
            "Main Chart (Rain+Temperature)": "primary",
            "Temperature Comparison (Air vs Track)": "temperature", 
            "Humidity & Wind Speed": "humidity_wind",
            "Pressure Changes": "pressure",
            # 若未來支援其他語言，在此添加
        }
        
        if text in chart_type_map:
            self.chart_type_changed.emit(chart_type_map[text])


class RainAnalysisUniversal(UniversalAnalysisMDI):
    """
    通用下雨分析 MDI 模組
    
    基於通用 MDI 架構實現的完整下雨分析功能，
    支援多種天氣數據的視覺化和分析。
    """
    
    def __init__(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        parent=None,
        **kwargs,
    ):
        logger.info("[RAIN_MDI] RainAnalysisUniversal 開始初始化...")
        
        # 註冊下雨分析模組類型
        if "rain_weather" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            rain_config = AnalysisMDIConfig(
                analysis_type="rain_weather",
                display_name="Rain Analysis",
                default_size=(1400, 900),
                requires_driver_params=False,  # 下雨分析不需要車手參數
                requires_lap_params=False,     # 下雨分析不需要圈數參數
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["primary", "temperature", "humidity_wind", "pressure"]
            )
            UniversalAnalysisMDI.register_mdi_module_type("rain_weather", rain_config)
            
        super().__init__("rain_weather", parent)
        logger.info("[RAIN_MDI] 基類初始化完成, 數據管理器: %s", self.data_manager)
        
        # 初始化模組組件
        logger.info("[RAIN_MDI] 開始初始化模組組件...")
        if not self.initialize_module():
            logger.error("[RAIN_MDI] ❌ 模組組件初始化失敗")
            return
        
        logger.info("[RAIN_MDI] ✅ 模組組件初始化完成")
        logger.debug("[RAIN_MDI] 數據管理器: %s", self.data_manager)
        logger.debug("[RAIN_MDI] 圖表組件: %s", self.chart_widget)
        
        # 參照遙測分析：設置響應式佈局
        self.set_responsive_layout()

        # 儲存初始參數但避免在建構時即觸發資料載入
        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session

        # 吸收額外關鍵字參數，維持向後相容
        if kwargs:
            self._debug(f"忽略未使用的初始化參數: {kwargs}")
        
    def create_data_manager(self) -> RainAnalysisDataManager:
        """創建下雨分析數據管理器"""
        return RainAnalysisDataManager(self)
        
    def create_chart_widget(self) -> RainAnalysisChartWidget:
        """創建下雨分析圖表組件"""
        return RainAnalysisChartWidget(self)
        
    def create_control_widget(self) -> RainAnalysisControlWidget:
        """創建下雨分析控制面板"""
        control_widget = RainAnalysisControlWidget(self)
        
        # 連接信號
        control_widget.chart_type_changed.connect(self._on_chart_type_changed)
        control_widget.parameter_changed.connect(self._on_parameter_changed)
        
        return control_widget
        
    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """更新降雨分析參數"""
        try:
            logger.info("[RAIN_MDI] ========== 降雨參數更新 ==========")
            logger.info("[RAIN_MDI] 收到參數: %s %s %s", year, race, session)
            
            # 更新當前參數
            self.current_year = int(year) if isinstance(year, str) else year
            self.current_race = race
            self.current_session = session
            
            # ✅ 更新視窗標題（響應賽事切換）
            logger.debug("[RAIN_MDI] 更新視窗標題...")
            self.update_window_title()
            
            # 更新數據管理器參數
            if hasattr(self, 'data_manager') and self.data_manager:
                logger.debug("[RAIN_MDI] 更新數據管理器參數...")
                self.data_manager.year = self.current_year
                self.data_manager.race = self.current_race
                self.data_manager.session = self.current_session
                
                # 載入數據 - 傳遞正確的參數
                logger.info("[RAIN_MDI] 開始載入數據...")
                result = self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
                logger.info("[RAIN_MDI] 數據載入結果: %s", result)
                
                # 如果有數據，更新圖表
                if result and hasattr(self, 'chart_widget') and self.chart_widget:
                    current_data = self.data_manager.get_current_data()
                    charts_payload = None
                    if current_data and isinstance(current_data, dict):
                        charts_payload = current_data.get("charts_data")
                    if charts_payload is None:
                        charts_payload = self.data_manager._prepare_chart_data()
                    if charts_payload:
                        logger.info("[RAIN_MDI] 更新圖表數據...")
                        chart_data = {"charts_data": charts_payload}
                        self.chart_widget.update_data(chart_data)
            
            logger.info("[RAIN_MDI] 參數更新完成")
            return True
            
        except Exception as e:
            logger.exception("[RAIN_MDI] 參數更新失敗", exc_info=e)
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
            
            logger.debug(
                "[RAIN_MDI] resizeEvent: MDI視窗縮放 %sx%s -> %sx%s",
                old_size.width(),
                old_size.height(),
                new_size.width(),
                new_size.height(),
            )
            
            # 通知圖表組件更新佈局
            if hasattr(self, 'chart_widget') and self.chart_widget:
                if hasattr(self.chart_widget, 'update_chart_layout'):
                    logger.debug("[RAIN_MDI] resizeEvent: 觸發圖表重新佈局")
                    self.chart_widget.update_chart_layout()
                else:
                    logger.debug("[RAIN_MDI] resizeEvent: 圖表組件不支援動態佈局更新")
            else:
                logger.debug("[RAIN_MDI] resizeEvent: 圖表組件尚未初始化")
                
        except Exception as e:
            logger.exception("[ERROR] [RAIN_MDI] resizeEvent 處理失敗", exc_info=e)
    
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
                self._debug("⚠️ 無法取得主要 Widget，略過 sizePolicy 設定")
            
            # 確保圖表組件也有正確的大小策略
            if hasattr(self, 'chart_widget') and self.chart_widget:
                self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
            logger.info("[RAIN_MDI] 響應式佈局已設置")
            
        except Exception as e:
            logger.exception("[ERROR] [RAIN_MDI] 設置響應式佈局失敗", exc_info=e)

    def get_module_info(self) -> Dict[str, Any]:
        """獲取模組信息"""
        return {
            "name": "下雨分析",
            "type": "rain",
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
            rain_summary = self.data_manager.get_rain_summary()
            
            summary = {
                "module": "下雨分析",
                "parameters": {
                    "year": self.current_year,
                    "race": self.current_race,
                    "session": self.current_session
                },
                "data_info": {
                    "total_laps": rain_summary.get("total_laps", 0),
                    "rain_laps": rain_summary.get("rain_laps", 0),
                    "rain_percentage": rain_summary.get("rain_percentage", 0.0),
                    "has_weather_data": rain_summary.get("has_rain_data", False)
                },
                "generated_at": self.get_current_timestamp()
            }
            data_source = getattr(self.data_manager, "get_last_data_source", lambda: "unknown")()
            summary["data_source"] = data_source
            if data_source == "api":
                api_meta = getattr(self.data_manager, "get_last_api_metadata", lambda: {})()
                if api_meta:
                    summary["api_meta"] = api_meta
            return summary
            
        except Exception as e:
            self._debug(f"獲取分析摘要失敗: {str(e)}")
            return {}


# 模組註冊 - 確保在導入時自動註冊
def register_rain_analysis_module():
    """註冊下雨分析模組"""
    try:
        # 這裡可以添加到全局模組註冊表
        pass
    except Exception as e:
        logger.warning("[WARNING] 下雨分析模組註冊失敗: %s", str(e))


# 自動註冊
register_rain_analysis_module()


class RainAnalysisModule(RainAnalysisUniversal):
    """向後相容的別名，供既有匯入路徑使用"""

    pass
