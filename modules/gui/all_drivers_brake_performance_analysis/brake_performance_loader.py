#!/usr/bin/env python3
"""GUI data loader for the all-drivers straight-line speed analysis (Function 34)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader


class BrakePerformanceDataLoader(UniversalDataLoader):
    """Unified loader for Function 34 results with API-first behaviour."""

    ANALYSIS_TYPE = "brake_performance"

    def __init__(self, parent=None):
        config = AnalysisConfig(
            display_name=tr("brake_performance_analysis", "煞車性能分析"),
            debug_prefix="BRAKE_PERF",
            data_source="json",
            cli_function="34",
            file_patterns=["all_drivers_brake_performance_*.json", "brake_performance_*.json"],
        )

        if self.ANALYSIS_TYPE not in self.ANALYSIS_TYPES:
            self.register_analysis_type(self.ANALYSIS_TYPE, config)

        super().__init__(self.ANALYSIS_TYPE, parent)

        self._api_base_url = self._determine_api_base_url()
        self._api_timeout = 45.0
        self._last_api_payload: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_data(self, **kwargs) -> bool:  # type: ignore[override]
        """Load straight-line speed data, fetching from API when needed."""

        if not self._validate_load_parameters(kwargs):
            self._error(tr("brake_perf_load_param_validation_failed", "載入參數驗證失敗"))
            self.load_error.emit(tr("brake_perf_load_param_invalid", "載入參數不正確"))
            return False

        existing = self._find_data_file(**kwargs)
        if not existing:
            self._debug(tr("brake_perf_no_local_file", "找不到本地煞車性能檔案，準備透過 API 取得最新資料"))
            # ✅ 方案 2：API 調用成功後直接處理數據，不依賴檔案系統
            api_result = self._fetch_via_api_and_cache(**kwargs)
            if api_result:
                self._debug(f"✅ API 調用成功，檔案已儲存至: {api_result}")
            
            # ✅ 如果 API 成功返回數據，直接處理 payload
            if self._last_api_payload:
                self._debug("✅ 使用 API 返回的數據（不依賴檔案系統）")
                try:
                    # 驗證數據格式
                    if not self._validate_data_format(self._last_api_payload):
                        self._error("API 返回的數據格式驗證失敗")
                        self.load_error.emit(tr("brake_perf_invalid_data_format", "數據格式不正確"))
                        return False
                    
                    # 處理數據
                    processed_data = self._process_data(self._last_api_payload)
                    self._current_data = processed_data
                    
                    # 發送成功信號
                    self.load_progress.emit(100)
                    self.status_changed.emit(tr("brake_perf_load_success", "煞車性能數據載入完成"))
                    self.data_loaded.emit(processed_data)
                    
                    self._debug("✅ API 數據處理完成，已發送 data_loaded 信號")
                    return True
                    
                except Exception as e:
                    self._error(f"處理 API 數據時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    self.load_error.emit(f"數據處理失敗: {str(e)}")
                    return False
            else:
                self._debug("⚠️ API 調用失敗，嘗試回退到基類方法")

        return super().load_data(**kwargs)

    # ------------------------------------------------------------------
    # UniversalDataLoader contract
    # ------------------------------------------------------------------

    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        year = params.get("year")
        race = params.get("race")
        session = params.get("session")

        try:
            year_int = int(year)
        except (TypeError, ValueError):
            return False

        if year_int < 2000 or year_int > 2100:
            return False
        if not isinstance(race, str) or len(race.strip()) < 2:
            return False
        if not isinstance(session, str) or not session.strip():
            return False
        return True

    def _build_filename_patterns(self, **kwargs) -> List[str]:
        year = kwargs.get("year", "*")
        race = kwargs.get("race", "*")
        session = kwargs.get("session", "*")

        race_slug = self._sanitize_for_filename(race)
        session_slug = self._sanitize_for_filename(session)

        return [
            f"all_drivers_brake_performance_{year}_{race}_{session}.json",
            f"all_drivers_brake_performance_{year}_{race_slug}_{session_slug}.json",
            f"all_drivers_brake_performance_*_{race}_{session}.json",
            f"all_drivers_brake_performance_*_{race_slug}_{session_slug}.json",
            f"brake_performance_{year}_{race}_{session}.json",
            f"brake_performance_{year}_{race_slug}_{session_slug}.json",
        ]

    def _generate_data_via_cli(self, **kwargs) -> bool:
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用 (Function 34)")
        self._debug("💡 請透過 API 或手動執行 CLI 生成 JSON")
        return False

    def _validate_data_format(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, dict):
            return False
        if not raw_data.get("success", False):
            return False

        # ⚠️ 修正：API 返回的數據可能有多層嵌套，需要遞歸穿透
        # 嘗試找到包含 'driver_brakes' 的層級
        current = raw_data.get("data")
        max_depth = 20  # 防止無限遞歸
        depth = 0
        
        while isinstance(current, dict) and depth < max_depth:
            # 檢查是否到達實際數據層
            if "driver_brakes" in current:
                driver_brakes = current.get("driver_brakes")
                if isinstance(driver_brakes, list):
                    self._debug(f"✅ 在第 {depth + 1} 層找到有效的 driver_brakes (車手數: {len(driver_brakes)})")
                    return True
                else:
                    self._error(f"driver_brakes 不是列表: {type(driver_brakes)}")
                    return False
            
            # 繼續往下一層穿透
            if "data" in current:
                current = current["data"]
                depth += 1
            else:
                # 沒有更多嵌套但也沒找到 driver_brakes
                self._error(f"在第 {depth + 1} 層找不到 'driver_brakes' 鍵")
                self._error(f"當前層的鍵: {list(current.keys())}")
                return False
        
        if depth >= max_depth:
            self._error(f"數據嵌套層數超過 {max_depth}，可能存在循環引用")
            return False
        
        self._error("無法找到包含 'driver_brakes' 的數據層")
        return False

    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        # ⚠️ 修正：API 返回的數據可能有多層嵌套，需要遞歸穿透找到實際數據
        current = raw_data.get("data", {}) if isinstance(raw_data, dict) else {}
        max_depth = 20
        depth = 0
        
        # 穿透嵌套找到包含 'driver_brakes' 的層級
        while isinstance(current, dict) and depth < max_depth:
            if "driver_brakes" in current:
                # 找到實際數據層
                payload = current
                self._debug(f"✅ 在第 {depth + 1} 層找到實際數據")
                break
            
            if "data" in current:
                current = current["data"]
                depth += 1
            else:
                # 沒找到，使用當前層作為 fallback
                payload = current
                self._debug(f"⚠️ 在第 {depth + 1} 層停止穿透，使用當前層")
                break
        else:
            # 超過最大深度或 current 不是字典
            payload = current if isinstance(current, dict) else {}
            self._debug(f"⚠️ 使用最終層級 (depth={depth})")
        
        metadata = dict(payload.get("metadata") or {})
        summary = payload.get("summary") or {}
        chart = payload.get("chart_data")

        metadata.setdefault("function_id", raw_data.get("function_id", "34"))
        metadata.setdefault("message", raw_data.get("message"))
        metadata.setdefault("source", raw_data.get("source", "local-json"))
        metadata.setdefault("success", raw_data.get("success"))
        if self._last_api_payload and raw_data is self._last_api_payload:
            metadata["source"] = "api"
        metadata.setdefault("drivers_total", len(payload.get("driver_brakes") or []))

        processed = {
            "metadata": metadata,
            "driver_brakes": payload.get("driver_brakes") or [],
            "reference_brake_zone": payload.get("reference_brake_zone") or {},
            "summary": summary,
            "chart_data": chart,
            "raw_payload": raw_data,
        }
        return processed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_via_api_and_cache(self, **kwargs) -> Optional[str]:
        try:
            year = int(kwargs["year"])
            race = str(kwargs["race"])
            session = str(kwargs["session"])
        except (KeyError, TypeError, ValueError) as exc:
            self._error(tr("brake_perf_api_missing_params", "缺少必要參數，無法呼叫 API: {error}").format(error=str(exc)))
            self.load_error.emit(tr("brake_perf_load_missing_params", "缺少必要參數，無法載入煞車性能分析"))
            return None

        params = {
            "function_id": 34,
            "year": year,
            "race": race,
            "session": session,
        }
        if kwargs.get("force_refresh"):
            params["force_refresh"] = True

        endpoint = f"{self._api_base_url}/api/v2/analysis/execute"
        self.status_changed.emit(tr("brake_perf_loading_via_api", "透過 API 載入全部車手煞車性能資料..."))
        self.load_progress.emit(25)

        try:
            response = requests.post(
                endpoint,
                params=params,
                timeout=self._api_timeout,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # broad catch to emit signal and log
            self._error(tr("brake_perf_api_load_failed", "API 載入失敗: {error}").format(error=str(exc)))
            # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
            # API 失敗是正常情況，讓用戶通過其他方式獲取數據
            self._debug("💡 提示: API 暫時不可用，請稍後重試或檢查網絡連接")
            return None

        if not isinstance(payload, dict) or not payload.get("success", False):
            message = payload.get("message") if isinstance(payload, dict) else tr("brake_perf_unknown_error", "未知錯誤")
            self._error(tr("brake_perf_api_return_failed", "API 返回失敗: {message}").format(message=message))
            # ⚠️ [API-ONLY 模式修正] 不發送 load_error 信號，避免彈窗
            self._debug("💡 提示: API 響應異常，請檢查後端服務狀態")
            return None

        self._last_api_payload = payload

        # ✅ [API-ONLY 模式] 禁止自動寫入 JSON 檔案
        # API 數據僅保存在記憶體中，不寫入磁碟
        self._debug("✅ API 數據已載入至記憶體（API-ONLY 模式：不寫入本地檔案）")
        self.load_progress.emit(60)
        
        # 返回 None 表示沒有檔案生成（這是正確的行為）
        return None

    # ❌ [API-ONLY 模式] 已禁用自動寫入功能
    # def _write_payload_to_cache(self, payload: Dict[str, Any], year: int, race: str, session: str) -> Optional[str]:
    #     """
    #     [已禁用] 寫入 API 結果到本地緩存
    #     
    #     ⚠️ API-ONLY 模式: 此方法已禁用，GUI 不應自動生成 JSON 檔案
    #     API 數據僅保存在記憶體中（self._last_api_payload）
    #     """
    #     try:
    #         os.makedirs("json", exist_ok=True)
    #         filename = self._make_filename(year, race, session)
    #         path = os.path.join("json", filename)
    #         with open(path, "w", encoding="utf-8") as handle:
    #             json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
    #         self._debug(tr("brake_perf_api_result_saved", "API 結果已寫入 {path}").format(path=path))
    #         return path
    #     except Exception as exc:
    #         self._error(tr("brake_perf_write_json_failed", "寫入 JSON 檔案失敗: {error}").format(error=str(exc)))
    #         return None

    def _make_filename(self, year: int, race: str, session: str) -> str:
        race_slug = self._sanitize_for_filename(race)
        session_slug = self._sanitize_for_filename(session)
        return f"all_drivers_brake_performance_{year}_{race_slug}_{session_slug}.json"

    def _sanitize_for_filename(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return "unknown"
        sanitized = []
        for ch in text:
            if ch.isalnum() or ch in {"-", "_"}:
                sanitized.append(ch)
            else:
                sanitized.append("_")
        collapsed = "".join(sanitized)
        while "__" in collapsed:
            collapsed = collapsed.replace("__", "_")
        return collapsed.strip("_") or "value"

    def _determine_api_base_url(self) -> str:
        return resolve_api_base_url(event_logger=self._debug)


__all__ = ["BrakePerformanceDataLoader"]
