#!/usr/bin/env python3
"""
Historical Track Map Data Loader
歷年賽道旗幟統計數據載入器

負責通過 API 載入歷年旗幟統計數據 (Function 100)
支援 FastF1 遙測數據和 OpenF1 旗幟事件

僅支援 API 模式，不提供本地 JSON 回退

Author: F1T Team
Date: 2025-11-11
Version: 1.0.0
"""

import os
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import QThread, pyqtSignal

from core.api_base_url import resolve_api_base_url
from core.api_runtime_state import is_api_available
from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)

# 導入通用基礎類別
try:
    from ..base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig


class HistoricalTrackMapApiWorker(QThread):
    """
    歷年賽道旗幟統計 API 請求工作執行緒
    
    調用 Function 100 + FastF1 遙測數據
    API 端點: POST /api/v2/analysis/execute?function_id=100
    """
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (year, race, session, etc.)
            base_url: API 基礎 URL (預設: https://api.f1telemetrystationpro.org)
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        """執行 API 請求"""
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # 構建查詢參數 (Function 100 - Historical Flags Analysis)
            # Function 100 只需要 race 參數，year/session 都是可選的
            query_params: Dict[str, Any] = {
                "function_id": 100,
                "race": self.params.get("race"),
            }
            
            # year 為可選參數（Function 100 預設分析 2022-2025）
            if self.params.get("year"):
                query_params["year"] = int(self.params.get("year"))
            
            # session 為可選參數（預設為 'R'）
            if self.params.get("session"):
                query_params["session"] = self.params.get("session")
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            logger.debug(f"[HISTORICAL_MAP_API] 調用 API: {endpoint}")
            logger.debug(f"[HISTORICAL_MAP_API] 參數: {query_params}")
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(70)
            
            # ✅ 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                return
            
            response.raise_for_status()
            payload = response.json()
            
            if not isinstance(payload, dict):
                raise ValueError(tr("api_response_must_be_json", "API response must be a JSON object"))
            
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", tr("api_returned_failure", "API returned success=False")))
            
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError(tr("api_missing_data", "API response missing 'data' object"))
            
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
            
            logger.debug(f"[HISTORICAL_MAP_API] API 調用成功")
            logger.debug(f"[HISTORICAL_MAP_API] 延遲: {meta['latency_ms']}ms")
            
            self.progress.emit(90)
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"{tr('api_request_failed', 'API request failed')}: {str(exc)}"
            logger.debug(f"[HISTORICAL_MAP_API] {error_msg}")
            import traceback
            traceback.print_exc()
            self.failure.emit(error_msg)
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class HistoricalTrackMapDataLoader(UniversalDataLoader):
    """歷年賽道旗幟統計數據載入器"""
    
    def __init__(self, parent=None):
        # 註冊歷年旗幟分析類型
        if "historical_track_map" not in UniversalDataLoader.ANALYSIS_TYPES:
            config = AnalysisConfig(
                display_name=tr("historical_track_map_analysis", "Historical Track Map Analysis"),
                debug_prefix="[HISTORICAL_TRACK_MAP]",
                data_source="api",
                cli_function="run_historical_flags_analysis_json",
                api_endpoint="/api/v2/analysis/execute",
                api_function_id=100,
                api_timeout=60.0,
                file_patterns=[
                    "historical_flags_{race}_{year}-{end_year}_{session}.json",
                ],
                search_directories=["json"],
                supports_realtime=False,
                cache_enabled=True
            )
            UniversalDataLoader.register_analysis_type("historical_track_map", config)
        
        super().__init__("historical_track_map", parent)
        
        # 歷年旗幟分析特定屬性
        self.yearly_summary = {}
        self.corner_analysis = {}
        self.position_records = []
        self.track_data = {}
        
        self._api_base_url = self._determine_api_base_url()
        self._api_worker: Optional[HistoricalTrackMapApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        
        # ⚠️ API-ONLY 模式: 禁用本地 JSON 回退
        self._allow_local_fallback = False
        self._fallback_policy_reason = "API-ONLY 模式強制啟用"
        
        self._debug(f"{tr('local_json_fallback_disabled', '本地 JSON 後備已停用')} ({self._fallback_policy_reason})")
        
        logger.debug(f"[HISTORICAL_TRACK_MAP_LOADER] 初始化完成")
        logger.debug(f"[HISTORICAL_TRACK_MAP_LOADER] API 基礎 URL: {self._api_base_url}")
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """
        驗證載入參數
        
        Function 100 只需要 race 參數（year 和 session 都是可選的）
        """
        race = params.get('race')
        
        if not race:
            self._debug(tr("params_incomplete", "參數不完整：Function 100 需要賽道名稱 (race)"))
            return False
        
        self._debug(f"✅ 參數驗證通過: race={race}")
        return True
    
    def _determine_api_base_url(self) -> str:
        """解析 API 基礎 URL"""
        return resolve_api_base_url(event_logger=self._debug)
    
    def _is_api_available(self) -> bool:
        """檢查 API 是否可用"""
        available = is_api_available()
        if not available:
            self._debug(tr("api_marked_offline", "API 標記為離線"))
        return available
    
    def set_api_base_url(self, base_url: Optional[str]) -> None:
        """設置 API 基礎 URL"""
        if base_url:
            self._api_base_url = str(base_url).rstrip('/')
            self._debug(f"{tr('api_base_url_updated', 'API 基礎 URL 更新為')} {self._api_base_url}")
    
    def load_data(self, **kwargs) -> bool:
        """
        載入歷年賽道旗幟統計數據
        
        ⚠️ API-ONLY 模式: 僅支援 API，不提供本地 JSON 回退
        """
        if self._is_loading:
            self._debug(tr("load_in_progress", "已有載入請求執行中，忽略新的請求"))
            return False
        
        if not self._validate_load_parameters(kwargs):
            self._error(tr("api_load_params_invalid", "API 載入參數驗證失敗"))
            self.load_error.emit(tr("invalid_load_params", "載入參數不正確"))
            return False
        
        self._is_loading = True
        self._pending_params = dict(kwargs)
        self._api_base_url = self._determine_api_base_url()
        
        self._debug(f"{tr('loading_via_api', '透過 API 載入歷年旗幟數據')}: base_url={self._api_base_url}, params={self._pending_params}")
        self.load_progress.emit(5)
        self.status_changed.emit(tr("loading_historical_flags_data", "正在透過 API 載入歷年旗幟統計數據..."))
        
        if not self._is_api_available():
            self._debug(tr("api_health_check_failed", "API 健康檢查失敗"))
            self._is_loading = False
            self.status_changed.emit(tr("api_unavailable", "API 服務不可用，請啟動 API 伺服器"))
            self.load_error.emit(tr("api_unavailable_no_fallback", "API 服務不可用且未啟用本地 JSON 後備"))
            return False
        
        try:
            self._start_api_request(self._pending_params)
            return True
        except Exception as exc:
            self._error(f"{tr('api_request_start_failed', '啟動 API 請求失敗')}: {exc}")
            self._is_loading = False
            self.status_changed.emit(tr("api_load_failed", "API 載入失敗"))
            self.load_error.emit(str(exc))
            return False
    
    def _start_api_request(self, params: Dict[str, Any]) -> None:
        """啟動 API 請求背景執行緒"""
        self._cleanup_api_worker()
        
        # Function 100 只需要 race 參數（year 和 session 可選）
        worker_params = {
            "race": params.get("race"),
            "force_refresh": params.get("force_refresh", False),
        }
        
        # 只在提供時才加入 year 和 session（可選參數）
        if params.get("year"):
            worker_params["year"] = params.get("year")
        if params.get("session"):
            worker_params["session"] = params.get("session")
        
        timeout = getattr(self.config, "api_timeout", 60.0)
        # ✅ 修正參數順序：params, base_url, timeout（不接受 parent）
        self._api_worker = HistoricalTrackMapApiWorker(
            worker_params,           # 第一個參數：params
            self._api_base_url,      # 第二個參數：base_url
            timeout=timeout
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()
    
    def _on_api_progress(self, value: int) -> None:
        """API 進度更新"""
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:
            pass
    
    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        """API 請求成功處理"""
        try:
            # ✅ 修正：正確提取雙層嵌套的數據
            # API 返回: response.data (Level 1) → response.data.data (Level 2)
            raw_data = payload.get("data")  # Level 1
            meta = payload.get("meta", {})
            self._last_api_meta = meta or {}
            self._last_data_source = "api"
            
            # ✅ 處理雙層嵌套格式：提取 Level 2 的數據
            if isinstance(raw_data, dict) and "data" in raw_data:
                # Level 2: 真正的分析數據 (yearly_summary, corner_analysis, etc.)
                raw_data = raw_data["data"]
            
            if not self._validate_data_format(raw_data):
                raise ValueError(tr("api_data_format_invalid", "API 回傳數據格式不符合預期"))
            
            processed_data = self._process_data(raw_data)
            if isinstance(processed_data, dict):
                metadata = processed_data.setdefault("metadata", {})
                metadata.setdefault("data_source", "api")
                if self._last_api_meta:
                    metadata["api"] = self._last_api_meta
            
            self._current_data = processed_data
            self._is_loading = False
            self.load_progress.emit(100)
            self.status_changed.emit(tr("loaded_from_api", "已從 API 載入歷年旗幟統計數據"))
            self.data_loaded.emit(processed_data)
            
        except Exception as exc:
            self._error(f"{tr('api_data_processing_failed', '處理 API 數據失敗')}: {exc}")
            self._is_loading = False
            self.status_changed.emit(tr("api_data_format_error", "API 資料格式錯誤"))
            self.load_error.emit(str(exc))
    
    def _on_api_error(self, message: str) -> None:
        """API 請求失敗處理"""
        self._error(f"{tr('api_request_failed_short', 'API 請求失敗')}: {message}")
        self._is_loading = False
        self.status_changed.emit(tr("api_request_failed_status", "API 請求失敗"))
        self.load_error.emit(message)
    
    def _cleanup_api_worker(self) -> None:
        """清理 API Worker"""
        if self._api_worker:
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
                self._api_worker.requestInterruption()
                self._api_worker.quit()
                
                def on_worker_stopped():
                    if self._api_worker:
                        self._api_worker.deleteLater()
                    self._api_worker = None
                
                self._api_worker.finished.connect(on_worker_stopped)
                
                from PyQt5.QtCore import QTimer

                def force_terminate():
                    try:
                        if self._api_worker and self._api_worker.isRunning():
                            self._api_worker.terminate()
                    except (RuntimeError, AttributeError):
                        pass
                
                QTimer.singleShot(200, force_terminate)
            else:
                self._api_worker.deleteLater()
                self._api_worker = None
    
    def get_last_data_source(self) -> str:
        """獲取最後數據源"""
        return self._last_data_source
    
    def get_last_api_metadata(self) -> Dict[str, Any]:
        """獲取最後 API 元數據"""
        return self._last_api_meta
    
    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式"""
        if not isinstance(data, dict):
            self._debug(tr("data_format_error_must_be_dict", "數據格式錯誤：必須是字典格式"))
            return False
        
        # 檢查必要欄位
        required_fields = ["yearly_summary", "corner_analysis"]
        for field in required_fields:
            if field not in data:
                self._debug(f"{tr('data_format_error_missing_field', '數據格式錯誤：缺少欄位')} {field}")
                return False
        
        return True
    
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據"""
        return self.process_loaded_data(data)
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用
        """
        self._debug(f"[API-ONLY] {tr('cli_call_disabled', 'CLI 調用已禁用')}")
        self._debug(f"{tr('cli_use_api_hint', '提示: 請使用 API 獲取數據')}")
        return False
    
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的歷年旗幟統計數據"""
        try:
            if not isinstance(data, dict):
                raise ValueError(tr("data_format_incorrect", "數據格式不正確：必須是字典格式"))
            
            # 提取各部分數據
            self.yearly_summary = data.get("yearly_summary", {})
            self.corner_analysis = data.get("corner_analysis", {})
            self.position_records = data.get("detailed_position_records", [])
            
            # 🏁 儲存 sector_boundaries 數據（供 _extract_track_data() 使用）
            self.sector_boundaries = data.get("sector_boundaries", [])
            logger.debug(f"[DATA_LOADER] 儲存 sector_boundaries: {len(self.sector_boundaries)} 個")
            
            # 🎯 儲存 speed_distribution 數據（供 _extract_track_data() 使用）
            self.speed_distribution = data.get("speed_distribution")
            if self.speed_distribution:
                logger.info(f"[DATA_LOADER] ✅ 儲存 speed_distribution: Low={self.speed_distribution.get('low_speed_percentage', 0):.1f}%, Mid={self.speed_distribution.get('mid_speed_percentage', 0):.1f}%, High={self.speed_distribution.get('high_speed_percentage', 0):.1f}%")
            else:
                logger.warning(f"[DATA_LOADER] ⚠️  未找到 speed_distribution 數據")
            
            # ✅ 修復：儲存 official_corners 供 _extract_track_data() 使用
            self.official_corners_data = data.get("official_corners", {
                "available": False,
                "count": 0,
                "corners": []
            })
            
            logger.debug(f"\n[DEBUG] [DATA_LOADER] API 返回的 official_corners:")
            logger.debug(f"- available: {self.official_corners_data.get('available')}")
            logger.debug(f"- count: {self.official_corners_data.get('count')}")
            logger.debug(f"- corners 數量: {len(self.official_corners_data.get('corners', []))}")
            
            # 構建處理後的數據
            processed_data = {
                "yearly_summary": self.yearly_summary,
                "corner_analysis": self.corner_analysis,
                "position_records": self.position_records,
                "metadata": data.get("metadata", {}),
                "track_data": self._extract_track_data(),
                "chart_data": self._prepare_chart_data(),
                "race_top3_drivers_2022_2023": data.get("race_top3_drivers_2022_2023", {})  # ✅ 新增：車手名次數據
            }
            
            # 🏆 調試：確認 race_top3_drivers_2022_2023 是否被包含
            top3_data = processed_data.get("race_top3_drivers_2022_2023", {})
            logger.debug(f"[DATA_LOADER] 🏆 race_top3_drivers_2022_2023 存在: {bool(top3_data)}")
            if top3_data:
                logger.debug(f"[DATA_LOADER] 🏆 available: {top3_data.get('available')}")
                logger.debug(f"[DATA_LOADER] 🏆 years_data 數量: {len(top3_data.get('years_data', []))}")
            
            metadata = processed_data.setdefault("metadata", {})
            if self._last_data_source:
                metadata["data_source"] = self._last_data_source
            if self._last_data_source == "api" and self._last_api_meta:
                existing_api_meta = metadata.get("api", {})
                merged_meta = dict(existing_api_meta)
                merged_meta.update(self._last_api_meta)
                metadata["api"] = merged_meta
            
            self._debug(f"{tr('data_processing_success', '成功處理數據')}")
            self._debug(f"  - {tr('yearly_summary_count', '年度統計')}: {len(self.yearly_summary)} {tr('years', '年')}")
            self._debug(f"  - {tr('corner_analysis_count', '彎道分析')}: {len(self.corner_analysis)} {tr('corners', '個彎道')}")
            self._debug(f"  - {tr('position_records_count', '位置記錄')}: {len(self.position_records)} {tr('points', '點')}")
            
            return processed_data
            
        except Exception as e:
            self._debug(f"{tr('data_processing_failed', '數據處理失敗')}: {str(e)}")
            raise
    
    def _extract_track_data(self) -> Dict[str, Any]:
        """從位置記錄中提取賽道數據（參考 demo Line 645-670）"""
        logger.debug(f"\n[DEBUG] _extract_track_data() 開始執行")
        logger.debug(f"position_records 數量: {len(self.position_records)}")
        
        if not self.position_records:
            logger.warning(f"⚠️  position_records 為空，返回空字典")
            return {}
        
        # 轉換為 TrackMapWidget 格式
        position_records = []
        for i, record in enumerate(self.position_records):
            position_records.append({
                "position_x": record.get("position_x", 0.0),
                "position_y": record.get("position_y", 0.0),
                "distance_m": record.get("distance_m", 0.0),
                "elevation": record.get("z", 0.0),
                "z": record.get("z", 0.0),
                "speed": record.get("speed", 0.0)
            })
            
            # 調試輸出前 3 個位置點
            if i < 3:
                logger.debug(f"position_record[{i}]: x={position_records[i]['position_x']:.1f}, y={position_records[i]['position_y']:.1f}, dist={position_records[i]['distance_m']:.1f}m")
        
        logger.debug(f"轉換後 position_records 數量: {len(position_records)}")
        
        # ✅ 修復：使用從 API 數據提取的 official_corners（不再硬編碼為空）
        official_corners_data = getattr(self, 'official_corners_data', {
            "available": False,
            "count": 0,
            "corners": []
        })
        
        logger.debug(f"_extract_track_data() 使用的 official_corners:")
        logger.debug(f"- available: {official_corners_data.get('available')}")
        logger.debug(f"- count: {official_corners_data.get('count')}")
        logger.debug(f"- corners 數量: {len(official_corners_data.get('corners', []))}")
        
        # 🏁 提取 sector_boundaries（如果存在）
        sector_boundaries_data = getattr(self, 'sector_boundaries', [])
        if not sector_boundaries_data:
            # 嘗試從 position_records 的原始數據中提取（如果 process_loaded_data 沒有儲存）
            sector_boundaries_data = []
        
        logger.debug(f"_extract_track_data() sector_boundaries 數量: {len(sector_boundaries_data)}")
        
        # 🎯 提取 speed_distribution（如果存在）
        speed_distribution_data = getattr(self, 'speed_distribution', None)
        if speed_distribution_data:
            logger.info(f"_extract_track_data() ✅ speed_distribution 存在: Low={speed_distribution_data.get('low_speed_percentage', 0):.1f}%")
        else:
            logger.warning(f"_extract_track_data() ⚠️  speed_distribution 不存在")
        
        result = {
            "position_records": position_records,
            "official_corners": official_corners_data,  # ✅ 預留欄位（將在 MDI 層從 API 數據提取）
            "sector_boundaries": sector_boundaries_data,  # 🏁 新增：Sector 邊界數據
            "speed_distribution": speed_distribution_data,  # 🎯 新增：速度分布數據
            "metadata": {}
        }
        
        logger.debug(f"_extract_track_data() 返回鍵: {list(result.keys())}")
        
        return result
    
    def _prepare_chart_data(self) -> Dict[str, Any]:
        """準備圖表數據"""
        logger.debug(f"\n[DEBUG] _prepare_chart_data() 開始執行")
        logger.debug(f"position_records 數量: {len(self.position_records)}")
        
        # 提取高程數據
        track_outline = []
        for i, record in enumerate(self.position_records):
            track_outline.append({
                "x": record.get("position_x", 0.0),
                "y": record.get("position_y", 0.0),
                "distance_m": record.get("distance_m", 0.0),
                "elevation": record.get("z", 0.0) / 10.0,  # FastF1 Z 軸需除以 10
                "z": record.get("z", 0.0) / 10.0
            })
            
            # 調試輸出前 3 個位置點
            if i < 3:
                logger.debug(f"track_outline[{i}]: x={track_outline[i]['x']:.1f}, y={track_outline[i]['y']:.1f}, elevation={track_outline[i]['elevation']:.2f}m")
        
        logger.debug(f"track_outline 數量: {len(track_outline)}")
        
        # ✅ 修復：使用從 API 數據提取的 official_corners（供高程圖表使用）
        official_corners_data = getattr(self, 'official_corners_data', {
            "available": False,
            "count": 0,
            "corners": []
        })
        
        logger.debug(f"_prepare_chart_data() 使用的 official_corners:")
        logger.debug(f"- available: {official_corners_data.get('available')}")
        logger.debug(f"- count: {official_corners_data.get('count')}")
        logger.debug(f"- corners 數量: {len(official_corners_data.get('corners', []))}")
        
        result = {
            "track_outline": track_outline,
            "official_corners": official_corners_data  # ✅ 預留欄位（將在 MDI 層填充）
        }
        
        logger.debug(f"_prepare_chart_data() 返回鍵: {list(result.keys())}")
        
        return result
    
    def get_flags_summary(self) -> Dict[str, Any]:
        """獲取旗幟統計摘要"""
        years = sorted(self.yearly_summary.keys())
        
        total_yellow = sum(self.yearly_summary.get(y, {}).get("yellow_flags", 0) for y in years)
        total_double_yellow = sum(self.yearly_summary.get(y, {}).get("double_yellow_flags", 0) for y in years)
        total_red = sum(self.yearly_summary.get(y, {}).get("red_flags", 0) for y in years)
        total_safety_car = sum(self.yearly_summary.get(y, {}).get("safety_cars", 0) for y in years)
        
        return {
            "total_years": len(years),
            "years": years,
            "total_yellow_flags": total_yellow,
            "total_double_yellow_flags": total_double_yellow,
            "total_red_flags": total_red,
            "total_safety_cars": total_safety_car,
            "total_incidents": total_yellow + total_double_yellow + total_red + total_safety_car,
            "corner_count": len(self.corner_analysis)
        }
