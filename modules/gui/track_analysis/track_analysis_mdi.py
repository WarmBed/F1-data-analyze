#!/usr/bin/env python3
"""
TrackAnalysisUniversal - F1T 通用賽道分析模組
=============================================

基於通用 MDI 架構實現的賽道分析模組，支援：
- 賽道位置數據可視化
- 車手軌跡路線繪製
- 賽道邊界和距離分析
- 互動式地圖縮放和平移
- 位置點詳細資訊顯示

數據來源：CLI -f2 生成的賽道位置 JSON 檔案
圖表類型：賽道地圖可視化

Author: F1T Team
Date: 2025-10-02
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
    QCheckBox, QSpinBox, QSlider, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSignalBlocker
from PyQt5.QtGui import QFont

import requests
from core.api_base_url import resolve_api_base_url

# 導入翻譯函數
try:
    from core.gui_i18n import tr
except ImportError:
    def tr(key, default):
        return default

# 導入通用基礎類別
try:
    from ..base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from ..base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig

# 導入賽道分析專用組件
try:
    from .track_data_loader import TrackUniversalDataLoader
    from .track_map_widget import TrackMapWidget
except ImportError:
    TrackUniversalDataLoader = None
    TrackMapWidget = None
    print("[ERROR] 無法導入 TrackUniversalDataLoader 或 TrackMapWidget")


class TrackAnalysisApiWorker(QThread):
    """Background worker for fetching track analysis data via REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 30.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout

    def run(self):
        try:
            self.progress.emit(20)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 2,
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

            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
        except Exception as exc:
            self.failure.emit(str(exc))
        finally:
            self.progress.emit(100)


class TrackAnalysisDataManager(UniversalDataLoader):
    """賽道分析數據管理器"""
    
    def __init__(self, parent=None):
        # 註冊賽道分析類型（如果尚未註冊）
        if "track_analysis" not in UniversalDataLoader.ANALYSIS_TYPES:
            track_config = AnalysisConfig(
                display_name="賽道分析",
                debug_prefix="[TRACK_ANALYSIS]",
                data_source="api",
                cli_function="2",
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=2,
                api_timeout=45.0,
                file_patterns=[
                    "track_positions_{year}_{race}_{session}.json",
                    "track_analysis_{year}_{race}_{session}.json",
                    "track_data_{year}_{race}_{session}.json",
                    "*track*_{year}_{race}_{session}.json"
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True
            )
            UniversalDataLoader.register_analysis_type("track_analysis", track_config)
        
        super().__init__("track_analysis", parent)
        
        # 賽道分析特定屬性
        self.track_data = {}
        self.position_records = []
        self.track_bounds = {}
        self.session_info = {}
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[TrackAnalysisApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        fallback_state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(
            f"本地 JSON 後備已{fallback_state} (策略: {self._fallback_policy_reason})"
        )
        
        print(f"[TRACK_DATA_MANAGER] 初始化完成，搜索目錄: {self.config.search_directories}")
        print(f"[TRACK_DATA_MANAGER] 文件模式: {self.config.file_patterns}")
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        year = params.get('year')
        race = params.get('race')
        session = params.get('session')

        if not year or not race or not session:
            self._debug("參數不完整：需要年份、比賽和賽段")
            return False

        try:
            year_int = int(year)
        except (TypeError, ValueError):
            self._debug(f"年份參數無法轉換為整數: {year}")
            return False

        if year_int < 2020 or year_int > 2030:
            self._debug(f"年份參數無效: {year_int}")
            return False
        
        return True
    
    def _build_filename_patterns(self, year: str, race: str, session: str, **kwargs) -> List[str]:
        """構建檔案名稱模式"""
        patterns = []
        for pattern in self.config.file_patterns:
            filename = pattern.format(year=year, race=race, session=session)
            patterns.append(filename)
        return patterns
    
    def _extract_analysis_payload(self, data: Any, *, attach_metadata: bool = False) -> Tuple[Any, Dict[str, Any]]:
        """Handle API envelope structures and return core analysis payload."""
        envelope_meta: Dict[str, Any] = {}

        if isinstance(data, dict):
            # API/CLI responses may wrap the payload inside a top-level envelope
            candidate = data.get("data")
            has_core_fields = isinstance(candidate, dict) and (
                "position_records" in candidate or "detailed_position_records" in candidate
            )
            if has_core_fields:
                envelope_meta = {
                    "success": data.get("success"),
                    "message": data.get("message"),
                    "source": data.get("source"),
                    "execution_time": data.get("execution_time"),
                    "request_id": data.get("request_id"),
                    "timestamp": data.get("timestamp"),
                    "cache_used": data.get("cache_used"),
                    "function_id": data.get("function_id"),
                }
                if attach_metadata:
                    metadata = candidate.setdefault("metadata", {})
                    if isinstance(metadata, dict):
                        existing = metadata.get("api_envelope")
                        if isinstance(existing, dict):
                            existing.update({k: v for k, v in envelope_meta.items() if v is not None})
                        else:
                            metadata["api_envelope"] = {k: v for k, v in envelope_meta.items() if v is not None}
                return candidate, envelope_meta

        return data, envelope_meta

    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式"""
        payload, _ = self._extract_analysis_payload(data, attach_metadata=False)

        if not isinstance(payload, dict):
            self._debug("數據格式錯誤：必須是字典格式")
            return False

        # API/CLI 皆須至少包含位置資料
        has_position_data = bool(
            payload.get("detailed_position_records")
            or payload.get("position_records")
        )
        if not has_position_data:
            self._debug("數據格式錯誤：缺少 position_records")
            return False

        # session_info 在 CLI 輸出中存在，但 API 可能缺失
        if "session_info" not in payload:
            self._debug("提示：資料缺少 session_info，將採用當前 GUI 參數填補")

        return True
    
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據的具體實現"""
        return self.process_loaded_data(data)

    def _determine_api_base_url(self) -> str:
        """Resolve API base URL from environment/config."""
        return resolve_api_base_url(event_logger=self._debug)

    def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
        """Determine whether local JSON fallback is permitted."""
        env_value = os.getenv("F1T_ALLOW_TRACK_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_TRACK_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_TRACK_JSON_FALLBACK={env_value}"
        return True, "預設策略 (允許本地 JSON 後備)"

    def _is_api_available(self) -> bool:
        """快速檢查 API 是否可用，以避免測試時殘留背景執行緒。"""
        try:
            health_url = f"{self._api_base_url}/health"
            response = requests.get(health_url, timeout=2.0)
            if response.status_code == 200:
                return True
            return response.status_code < 500
        except Exception:
            return False

    def set_local_fallback_allowed(self, allowed: bool, reason: Optional[str] = None) -> None:
        """Manually toggle local JSON fallback policy."""
        self._allow_local_fallback = bool(allowed)
        self._fallback_policy_reason = reason or "手動覆寫"
        state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(f"本地 JSON 後備手動設為{state} (原因: {self._fallback_policy_reason})")

    def load_data_from_local(self, **kwargs) -> bool:
        """Force loading data via legacy local JSON workflow for diagnostics."""
        previous_state = self._allow_local_fallback
        previous_reason = self._fallback_policy_reason
        try:
            self._allow_local_fallback = True
            self._fallback_policy_reason = "手動診斷模式"
            self._debug("以手動模式使用本地 JSON 後備流程")
            self._last_data_source = "local-json"
            return super().load_data(**kwargs)
        finally:
            self._allow_local_fallback = previous_state
            self._fallback_policy_reason = previous_reason

    def load_data(self, **kwargs) -> bool:
        """載入賽道分析資料，優先透過 API，失敗時回退本地流程。"""
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
        self.current_session = dict(kwargs)
        self._pending_params = dict(kwargs)
        self._api_base_url = self._determine_api_base_url()

        self._debug(f"透過 API 載入賽道資料: base_url={self._api_base_url}, params={self._pending_params}")
        self.load_progress.emit(5)
        self.status_changed.emit("正在透過 API 載入賽道分析資料...")

        try:
            if not self._is_api_available():
                self._debug("API 健康檢查失敗，改用本地 JSON 後備")
                self.status_changed.emit("偵測到 API 服務未啟動，改用本地資料")
                self._last_data_source = "local-json"
                self._is_loading = False
                return super().load_data(**kwargs)

            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            self._error(f"啟動 API 請求失敗: {exc}")
            self._is_loading = False
            self.status_changed.emit("API 載入失敗，改用本地資料")
            self._last_data_source = "local-json"
            return super().load_data(**kwargs)

    def set_api_base_url(self, base_url: Optional[str]) -> None:
        """Allows external callers to override API base URL."""
        if base_url:
            self._api_base_url = str(base_url).rstrip('/')
            self._debug(f"API base URL 更新為 {self._api_base_url}")

    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """Spawn background worker contacting REST API."""
        self._cleanup_api_worker()

        worker_params = {
            "year": params.get("year"),
            "race": params.get("race"),
            "session": params.get("session"),
            "force_refresh": params.get("force_refresh", False),
        }

        timeout = getattr(self.config, "api_timeout", 45.0)
        self._api_worker = TrackAnalysisApiWorker(self._api_base_url, worker_params, timeout=timeout, parent=self)
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

            if not self._validate_data_format(raw_data):
                raise ValueError("API 回傳數據格式不符合預期")

            processed_data = self._process_data(raw_data)
            if isinstance(processed_data, dict):
                metadata = processed_data.setdefault("metadata", {})
                metadata.setdefault("data_source", "api")
                if self._last_api_meta:
                    metadata["api"] = dict(self._last_api_meta)

            self._current_data = processed_data
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit("已從 API 載入賽道分析資料")
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
                " 如需啟用，請設定環境變數 F1T_ALLOW_TRACK_JSON_FALLBACK=1 或使用 set_local_fallback_allowed。"
            )
            self._debug(f"本地 JSON 後備被阻擋: {reason}")
            self._is_loading = False
            self.status_changed.emit("本地 JSON 後備已停用，請檢查 API 或手動啟用後備流程。")
            self.load_error.emit(message)
            return

        self._last_data_source = "local-json"
        self._last_api_meta = {}
        self._debug(f"啟動本地 JSON/CLI 後備流程: {reason}")
        self.status_changed.emit("使用本地 JSON/CLI 後備載入賽道資料...")
        self.load_error.emit(f"API 載入失敗，使用本地資料: {reason}")
        super().load_data(**params)

    def _cleanup_api_worker(self) -> None:
        if self._api_worker:
            if self._api_worker.isRunning():
                self._api_worker.requestInterruption()
                self._api_worker.wait(200)
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
            self._api_worker.deleteLater()
            self._api_worker = None

    def get_last_data_source(self) -> str:
        return getattr(self, "_last_data_source", "unknown")

    def get_last_api_metadata(self) -> Dict[str, Any]:
        return getattr(self, "_last_api_meta", {})
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用，系統只允許通過 API 獲取數據
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取賽道分析數據")
        return False
    
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的賽道分析數據"""
        try:
            payload, envelope_meta = self._extract_analysis_payload(data, attach_metadata=True)

            if not isinstance(payload, dict):
                raise ValueError("數據格式不正確：必須是字典格式")

            current_params = self._pending_params or self.current_session or {}

            # 提取會話資訊，若缺少則使用 GUI 參數填補
            session_info = payload.get("session_info") or {
                "year": current_params.get("year"),
                "event_name": current_params.get("race"),
                "track_name": current_params.get("race"),
                "session": current_params.get("session"),
                "session_type": current_params.get("session"),
            }
            self.session_info = session_info

            # 提取位置記錄（支援 API/CLI 兩種鍵名）
            records = payload.get("detailed_position_records") or payload.get("position_records") or []
            self.position_records = records

            # 統一賽道分析資訊
            position_analysis = payload.get("position_analysis") or {}
            track_bounds = position_analysis.get("track_bounds") or payload.get("track_bounds") or {}
            distance_val = position_analysis.get("distance_covered_m") or payload.get("distance_covered")
            total_points = position_analysis.get("total_position_records") or len(records)

            position_analysis_normalized = {
                "track_bounds": track_bounds,
                "distance_covered_m": distance_val,
                "total_position_records": total_points,
                "fastest_lap_info": (
                    position_analysis.get("fastest_lap_info")
                    or payload.get("fastest_lap_info")
                ),
            }
            self.track_bounds = track_bounds

            statistics = payload.get("statistics") or {}
            if not statistics and distance_val is not None:
                statistics = {
                    "distance_covered_m": distance_val,
                    "position_point_count": total_points,
                }

            metadata = payload.get("metadata") or {}
            if not metadata:
                metadata = {
                    "analysis_type": "track_analysis",
                    "data_source": self.get_last_data_source(),
                    "year": current_params.get("year"),
                    "race": current_params.get("race"),
                    "session": current_params.get("session"),
                }
            else:
                metadata.setdefault("analysis_type", "track_analysis")
                metadata.setdefault("data_source", self.get_last_data_source())

            if self._last_data_source == "api" and self._last_api_meta:
                if isinstance(metadata.get("api"), dict):
                    metadata["api"].update(self._last_api_meta)
                else:
                    metadata["api"] = dict(self._last_api_meta)

            if envelope_meta:
                metadata.setdefault("api_envelope", envelope_meta)

            processed_data = {
                "session_info": self.session_info,
                "position_records": self.position_records,
                "track_bounds": self.track_bounds,
                "position_analysis": position_analysis_normalized,
                "statistics": statistics,
                "metadata": metadata,
                "raw_data": payload,
            }

            self._debug(f"成功處理 {len(self.position_records)} 個位置點數據")
            self._debug(f"賽道: {self.session_info.get('track_name', '未知')}")
            self._debug(f"賽道邊界: {self.track_bounds}")
            
            return processed_data
            
        except Exception as e:
            self._error(f"數據處理失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


class TrackAnalysisControlWidget(QWidget):
    """賽道分析控制面板"""
    
    # 信號定義
    display_mode_changed = pyqtSignal(str)  # 顯示模式變更（軌跡/熱圖/速度）
    zoom_changed = pyqtSignal(float)  # 縮放倍率變更
    show_grid_changed = pyqtSignal(bool)  # 網格顯示切換
    show_markers_changed = pyqtSignal(bool)  # 標記顯示切換
    dynamic_marker_visibility_changed = pyqtSignal(bool)  # 連動游標顯示
    fixed_marker_visibility_changed = pyqtSignal(bool)  # 固定游標顯示
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # === 顯示模式組 ===
        display_group = QGroupBox("顯示模式")
        display_layout = QVBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "軌跡路線",
            "速度熱圖",
            "位置點",
            "完整地圖"
        ])
        self.mode_combo.currentTextChanged.connect(self.display_mode_changed.emit)
        display_layout.addWidget(QLabel("地圖模式:"))
        display_layout.addWidget(self.mode_combo)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # === 顯示選項組 ===
        options_group = QGroupBox("顯示選項")
        options_layout = QVBoxLayout()
        
        self.show_grid_check = QCheckBox("顯示座標網格")
        self.show_grid_check.setChecked(True)
        self.show_grid_check.toggled.connect(self.show_grid_changed.emit)
        options_layout.addWidget(self.show_grid_check)
        
        self.show_markers_check = QCheckBox("顯示距離標記")
        self.show_markers_check.setChecked(True)
        self.show_markers_check.toggled.connect(self.show_markers_changed.emit)
        options_layout.addWidget(self.show_markers_check)

        self.show_linkage_cursor_check = QCheckBox("同步游標")
        self.show_linkage_cursor_check.setChecked(True)
        self.show_linkage_cursor_check.toggled.connect(self.dynamic_marker_visibility_changed.emit)
        options_layout.addWidget(self.show_linkage_cursor_check)

        self.show_fixed_cursor_check = QCheckBox("固定游標")
        self.show_fixed_cursor_check.setChecked(True)
        self.show_fixed_cursor_check.toggled.connect(self.fixed_marker_visibility_changed.emit)
        options_layout.addWidget(self.show_fixed_cursor_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # === 縮放控制組 ===
        zoom_group = QGroupBox("縮放控制")
        zoom_layout = QVBoxLayout()
        
        zoom_label = QLabel("縮放倍率: 1.0x")
        self.zoom_label = zoom_label
        zoom_layout.addWidget(zoom_label)
        
        zoom_slider = QSlider(Qt.Horizontal)
        zoom_slider.setMinimum(50)  # 0.5x
        zoom_slider.setMaximum(300)  # 3.0x
        zoom_slider.setValue(100)  # 1.0x
        zoom_slider.setTickPosition(QSlider.TicksBelow)
        zoom_slider.setTickInterval(50)
        zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_layout.addWidget(zoom_slider)
        
        # 縮放按鈕
        zoom_buttons_layout = QHBoxLayout()
        reset_zoom_btn = QPushButton("重置")
        reset_zoom_btn.clicked.connect(lambda: zoom_slider.setValue(100))
        zoom_buttons_layout.addWidget(reset_zoom_btn)
        
        fit_btn = QPushButton("適應視窗")
        fit_btn.clicked.connect(lambda: self.zoom_changed.emit(0.0))  # 0.0 表示自動適應
        zoom_buttons_layout.addWidget(fit_btn)
        
        zoom_layout.addLayout(zoom_buttons_layout)
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        # === 資訊顯示組 ===
        info_group = QGroupBox("賽道資訊")
        info_layout = QVBoxLayout()
        
        self.track_info_label = QLabel("載入中...")
        self.track_info_label.setWordWrap(True)
        info_layout.addWidget(self.track_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 添加彈性空間
        layout.addStretch()
    
    def _on_zoom_changed(self, value):
        """縮放滑桿變更"""
        zoom_factor = value / 100.0
        self.zoom_label.setText(f"縮放倍率: {zoom_factor:.1f}x")
        self.zoom_changed.emit(zoom_factor)
    
    def update_track_info(self, session_info: Dict[str, Any]):
        """更新賽道資訊顯示"""
        track_name = session_info.get('track_name', '未知賽道')
        event_name = session_info.get('event_name', '未知賽事')
        session_type = session_info.get('session_type', '未知')
        
        info_text = f"""
<b>賽道:</b> {track_name}<br>
<b>賽事:</b> {event_name}<br>
<b>賽段:</b> {session_type}
        """.strip()
        
        self.track_info_label.setText(info_text)

    def set_marker_visibility(self, dynamic_visible: bool, fixed_visible: bool) -> None:
        with QSignalBlocker(self.show_linkage_cursor_check):
            self.show_linkage_cursor_check.setChecked(bool(dynamic_visible))
        with QSignalBlocker(self.show_fixed_cursor_check):
            self.show_fixed_cursor_check.setChecked(bool(fixed_visible))

    def get_marker_visibility(self) -> Tuple[bool, bool]:
        return (
            self.show_linkage_cursor_check.isChecked(),
            self.show_fixed_cursor_check.isChecked(),
        )

    def set_linkage_controls_enabled(self, enabled: bool) -> None:
        self.show_linkage_cursor_check.setEnabled(enabled)
        self.show_fixed_cursor_check.setEnabled(enabled)


class TrackAnalysisUniversal(UniversalAnalysisMDI):
    """
    賽道分析通用 MDI 模組
    
    基於 UniversalAnalysisMDI 實現的完整賽道分析系統，
    提供賽道地圖可視化和位置數據分析功能。
    """
    
    def __init__(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        main_window=None,
        parent=None,
        **kwargs,
    ):
        # 先註冊 track_analysis 模組類型（如果尚未註冊）
        analysis_type = "track_analysis"
        if analysis_type not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            config = AnalysisMDIConfig(
                analysis_type=analysis_type,
                display_name="Track Analysis",
                default_size=(1000, 700),
                requires_driver_params=False,  # 賽道分析不需要車手參數
                requires_lap_params=False,     # 賽道分析不需要圈數參數
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type(analysis_type, config)
        
        # 調用父類初始化
        mdi_parent = main_window if main_window is not None else parent
        super().__init__(analysis_type, mdi_parent)

        # Marker visibility state shared between control panel與賽道地圖
        self._dynamic_marker_visible: bool = True
        self._fixed_marker_visible: bool = True
        self._linkage_enabled: bool = True
        self._saved_marker_visibility: Tuple[bool, bool] = (True, True)

        # 檢查組件是否可用
        if TrackUniversalDataLoader is None or TrackMapWidget is None:
            print("[ERROR] TrackAnalysisUniversal: 缺少必要組件")

        # 初始化模組（創建數據管理器、圖表組件等）
        self.initialize_module()

        print(f"[TRACK_ANALYSIS_MDI] 初始化完成")

        # 儲存初始參數以供後續使用，避免即時載入資料
        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session

        if kwargs:
            self._debug(f"忽略未使用的初始化參數: {kwargs}")
    
    def create_data_manager(self):
        """創建數據管理器 - UniversalAnalysisMDI 需要此方法"""
        return TrackAnalysisDataManager(self)
    
    def create_chart_widget(self) -> QWidget:
        """創建圖表組件（賽道地圖）"""
        if TrackMapWidget is None:
            # 如果 TrackMapWidget 不可用，返回佔位符
            placeholder = QLabel("賽道地圖組件不可用")
            placeholder.setAlignment(Qt.AlignCenter)
            return placeholder
        
        track_map = TrackMapWidget()
        if hasattr(track_map, "set_dynamic_marker_visibility"):
            track_map.set_dynamic_marker_visibility(getattr(self, "_dynamic_marker_visible", True))
        if hasattr(track_map, "set_fixed_marker_visibility"):
            track_map.set_fixed_marker_visibility(getattr(self, "_fixed_marker_visible", True))
        if hasattr(track_map, "set_linkage_enabled"):
            track_map.set_linkage_enabled(getattr(self, "_linkage_enabled", True))
        print("[TRACK_ANALYSIS_MDI] 創建 TrackMapWidget")
        return track_map
    
    def create_control_widget(self) -> Optional[QWidget]:
        """創建控制面板"""
        control_panel = TrackAnalysisControlWidget(self)
        
        # 連接控制面板信號
        control_panel.display_mode_changed.connect(self._on_display_mode_changed)
        control_panel.zoom_changed.connect(self._on_zoom_changed)
        control_panel.show_grid_changed.connect(self._on_show_grid_changed)
        control_panel.show_markers_changed.connect(self._on_show_markers_changed)
        control_panel.dynamic_marker_visibility_changed.connect(self._on_dynamic_marker_visibility_changed)
        control_panel.fixed_marker_visibility_changed.connect(self._on_fixed_marker_visibility_changed)

        control_panel.set_marker_visibility(
            getattr(self, "_dynamic_marker_visible", True),
            getattr(self, "_fixed_marker_visible", True),
        )
        control_panel.set_linkage_controls_enabled(getattr(self, "_linkage_enabled", True))
        self._on_dynamic_marker_visibility_changed(getattr(self, "_dynamic_marker_visible", True))
        self._on_fixed_marker_visibility_changed(getattr(self, "_fixed_marker_visible", True))
        
        self.control_panel = control_panel
        print("[TRACK_ANALYSIS_MDI] 創建控制面板")
        return control_panel
    
    def _connect_data_manager_signals(self):
        """連接數據管理器信號 - UniversalAnalysisMDI 需要此方法"""
        if self.data_manager:
            self.data_manager.data_loaded.connect(self.on_data_loaded)
            self.data_manager.load_error.connect(self.on_data_error)
            self.data_manager.status_changed.connect(self.on_status_changed)
            self.data_manager.load_progress.connect(self.on_load_progress)
            print("[TRACK_ANALYSIS_MDI] 數據管理器信號連接完成")
    
    def _connect_chart_widget_signals(self):
        """連接圖表組件信號 - UniversalAnalysisMDI 需要此方法"""
        # TrackMapWidget 目前沒有需要連接的信號
        pass
    
    def _setup_initial_parameters(self):
        """設置初始參數 - UniversalAnalysisMDI 需要此方法"""
        # 賽道分析使用基本參數（年份、賽事、賽段）
        pass
    
    def _load_data_with_current_parameters(self):
        """使用當前參數載入數據 - UniversalAnalysisMDI 需要此方法"""
        if self.data_manager:
            self.data_manager.load_data(
                year=int(self.current_year),
                race=self.current_race,
                session=self.current_session
            )
    
    def get_current_data(self):
        """獲取當前數據 - UniversalAnalysisMDI 需要此方法"""
        if self.data_manager and hasattr(self.data_manager, '_current_data'):
            return self.data_manager._current_data
        return None
    
    def update_window_title(self):
        """更新視窗標題 - UniversalAnalysisMDI 需要此方法"""
        # 視窗標題由 PopoutSubWindow 管理，這裡不需要實現
        pass
    
    def _update_status(self, status: str):
        """更新狀態 - UniversalAnalysisMDI 需要此方法"""
        print(f"[TRACK_ANALYSIS_MDI] 狀態: {status}")
    
    def _register_to_analysis_manager(self):
        """註冊到分析管理器 - UniversalAnalysisMDI 需要此方法"""
        # 由 GUI 主程式管理，這裡不需要實現
        pass
    
    def on_data_loaded(self, data: Dict[str, Any]):
        """數據載入完成處理"""
        try:
            print(f"[TRACK_ANALYSIS_MDI] 數據載入完成")
            
            # 更新圖表組件
            if self.chart_widget and isinstance(self.chart_widget, TrackMapWidget):
                position_records = data.get('position_records', [])
                track_bounds = data.get('track_bounds', {})
                
                # 構建 track_data 結構
                track_data = {
                    'detailed_position_records': position_records,
                    'position_analysis': {
                        'track_bounds': track_bounds
                    },
                    'session_info': data.get('session_info', {}),
                    'statistics': data.get('statistics', {})
                }
                
                success = self.chart_widget.load_track_data(track_data)
                if success:
                    print(f"[TRACK_ANALYSIS_MDI] 賽道數據已載入至地圖組件")
                    self.chart_widget.update()  # 強制重繪
                else:
                    print(f"[TRACK_ANALYSIS_MDI] 地圖組件載入數據失敗")
            
            # 更新控制面板資訊
            if hasattr(self, 'control_panel') and self.control_panel:
                session_info = data.get('session_info', {})
                self.control_panel.update_track_info(session_info)
            
            # 更新狀態
            self.on_status_changed("賽道數據載入完成")
            
        except Exception as e:
            print(f"[ERROR] 處理賽道數據失敗: {e}")
            import traceback
            traceback.print_exc()
            self.on_data_error(f"處理數據失敗: {str(e)}")
    
    def on_data_error(self, error_msg: str):
        """數據載入錯誤處理"""
        print(f"[TRACK_ANALYSIS_MDI] 數據載入錯誤: {error_msg}")
        
        # 顯示錯誤信息
        if self.chart_widget and isinstance(self.chart_widget, QLabel):
            self.chart_widget.setText(f"載入失敗:\n{error_msg}")
        
        # 更新狀態
        self.on_status_changed(f"錯誤: {error_msg}")
    
    def on_status_changed(self, status: str):
        """狀態變更處理"""
        print(f"[TRACK_ANALYSIS_MDI] 狀態: {status}")
        # 可以在這裡更新狀態欄或其他 UI 元素
    
    def on_load_progress(self, progress: int):
        """載入進度更新"""
        # 可以在這裡顯示進度條
        pass
    
    # === 控制面板事件處理 ===
    
    def _on_display_mode_changed(self, mode: str):
        """顯示模式變更"""
        print(f"[TRACK_ANALYSIS_MDI] 顯示模式變更: {mode}")
        # 根據模式更新地圖顯示
        # 目前 TrackMapWidget 是佔位符，這裡僅記錄
    
    def _on_zoom_changed(self, zoom_factor: float):
        """縮放倍率變更"""
        print(f"[TRACK_ANALYSIS_MDI] 縮放變更: {zoom_factor}x")
        # 更新地圖縮放
        if self.chart_widget and hasattr(self.chart_widget, 'set_zoom'):
            if zoom_factor == 0.0:
                # 自動適應
                self.chart_widget.fit_to_view()
            else:
                self.chart_widget.set_zoom(zoom_factor)
    
    def _on_show_grid_changed(self, show: bool):
        """網格顯示切換"""
        print(f"[TRACK_ANALYSIS_MDI] 網格顯示: {show}")
        if self.chart_widget and hasattr(self.chart_widget, 'set_show_grid'):
            self.chart_widget.set_show_grid(show)
    
    def _on_show_markers_changed(self, show: bool):
        """標記顯示切換"""
        print(f"[TRACK_ANALYSIS_MDI] 標記顯示: {show}")
        if self.chart_widget and hasattr(self.chart_widget, 'set_show_markers'):
            self.chart_widget.set_show_markers(show)

    def _on_dynamic_marker_visibility_changed(self, visible: bool):
        """同步游標顯示切換"""
        self._dynamic_marker_visible = bool(visible)
        if self.chart_widget and hasattr(self.chart_widget, 'set_dynamic_marker_visibility'):
            self.chart_widget.set_dynamic_marker_visibility(self._dynamic_marker_visible)

    def _on_fixed_marker_visibility_changed(self, visible: bool):
        """固定游標顯示切換"""
        self._fixed_marker_visible = bool(visible)
        if self.chart_widget and hasattr(self.chart_widget, 'set_fixed_marker_visibility'):
            self.chart_widget.set_fixed_marker_visibility(self._fixed_marker_visible)

    # === 連動控制 ===

    def set_linkage_enabled(self, enabled: bool) -> None:
        new_state = bool(enabled)
        if getattr(self, "_linkage_enabled", True) == new_state:
            return

        if not new_state:
            self._saved_marker_visibility = (
                getattr(self, "_dynamic_marker_visible", True),
                getattr(self, "_fixed_marker_visible", True),
            )
            self._dynamic_marker_visible = False
            self._fixed_marker_visible = False
        else:
            saved_dynamic, saved_fixed = getattr(self, "_saved_marker_visibility", (True, True))
            self._dynamic_marker_visible = saved_dynamic
            self._fixed_marker_visible = saved_fixed

        self._linkage_enabled = new_state

        if self.chart_widget and hasattr(self.chart_widget, "set_linkage_enabled"):
            self.chart_widget.set_linkage_enabled(new_state)
            if hasattr(self.chart_widget, "set_dynamic_marker_visibility"):
                self.chart_widget.set_dynamic_marker_visibility(self._dynamic_marker_visible)
            if hasattr(self.chart_widget, "set_fixed_marker_visibility"):
                self.chart_widget.set_fixed_marker_visibility(self._fixed_marker_visible)

        if hasattr(self, 'control_panel') and self.control_panel:
            self.control_panel.set_linkage_controls_enabled(new_state)
            self.control_panel.set_marker_visibility(
                self._dynamic_marker_visible,
                self._fixed_marker_visible,
            )

        # 重新整理狀態
        if not new_state:
            # 確保 UI 立即清除標記
            if self.chart_widget and hasattr(self.chart_widget, "update"):
                self.chart_widget.update()

    def is_linkage_enabled(self) -> bool:
        return getattr(self, "_linkage_enabled", True)


class TrackAnalysisModule(TrackAnalysisUniversal):
    """向後相容的別名，供既有匯入路徑使用"""

    pass


# 在模組導入時註冊到模組工廠
try:
    from ..interfaces.analysis_module import ModuleFactory, ModuleTypes
    if not ModuleFactory.module_exists(ModuleTypes.TRACK_ANALYSIS):
        ModuleFactory.register_module(ModuleTypes.TRACK_ANALYSIS, TrackAnalysisUniversal)
except Exception as exc:
    print(f"[TRACK_ANALYSIS_MDI] 無法註冊到 ModuleFactory: {exc}")


# ========== 測試代碼 ==========
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    track_mdi = TrackAnalysisUniversal()
    track_mdi.show()
    
    # 測試載入數據
    track_mdi.update_parameters(year=2025, race="Japan", session="R")
    
    sys.exit(app.exec_())
