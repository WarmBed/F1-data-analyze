#!/usr/bin/env python3
"""GUI data loader for the all-drivers straight-line speed analysis (Function 48)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader


class StraightLineSpeedDataLoader(UniversalDataLoader):
    """Unified loader for Function 48 results with API-first behaviour."""

    ANALYSIS_TYPE = "straight_line_speed"

    def __init__(self, parent=None):
        config = AnalysisConfig(
            display_name=tr("straight_line_speed_analysis", "直線速度分析"),
            debug_prefix="STRAIGHT_SPEED",
            data_source="json",
            cli_function="48",
            file_patterns=["all_drivers_straight_line_speed_*.json", "straight_line_speed_*.json"],
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
            self._error("載入參數驗證失敗")
            self.load_error.emit("載入參數不正確")
            return False

        existing = self._find_data_file(**kwargs)
        if not existing:
            self._debug("找不到本地直線速度檔案，準備透過 API 取得最新資料")
            if not self._fetch_via_api_and_cache(**kwargs):
                return False

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
            f"all_drivers_straight_line_speed_{year}_{race}_{session}.json",
            f"all_drivers_straight_line_speed_{year}_{race_slug}_{session_slug}.json",
            f"all_drivers_straight_line_speed_*_{race}_{session}.json",
            f"all_drivers_straight_line_speed_*_{race_slug}_{session_slug}.json",
            f"straight_line_speed_{year}_{race}_{session}.json",
            f"straight_line_speed_{year}_{race_slug}_{session_slug}.json",
        ]

    def _generate_data_via_cli(self, **kwargs) -> bool:
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用 (Function 48)")
        self._debug("💡 請透過 API 或手動執行 CLI 生成 JSON")
        return False

    def _validate_data_format(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, dict):
            return False
        if not raw_data.get("success", False):
            return False

        payload = raw_data.get("data")
        if not isinstance(payload, dict):
            return False

        driver_speeds = payload.get("driver_speeds")
        if not isinstance(driver_speeds, list):
            return False

        return True

    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        payload = raw_data.get("data", {}) if isinstance(raw_data, dict) else {}
        metadata = dict(payload.get("metadata") or {})
        summary = payload.get("summary") or {}
        chart = payload.get("chart_data")

        metadata.setdefault("function_id", raw_data.get("function_id", "48"))
        metadata.setdefault("message", raw_data.get("message"))
        metadata.setdefault("source", raw_data.get("source", "local-json"))
        metadata.setdefault("success", raw_data.get("success"))
        if self._last_api_payload and raw_data is self._last_api_payload:
            metadata["source"] = "api"
        metadata.setdefault("drivers_total", len(payload.get("driver_speeds") or []))

        processed = {
            "metadata": metadata,
            "driver_speeds": payload.get("driver_speeds") or [],
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
            self._error(f"缺少必要參數，無法呼叫 API: {exc}")
            self.load_error.emit("缺少必要參數，無法載入直線速度分析")
            return None

        params = {
            "function_id": 48,
            "year": year,
            "race": race,
            "session": session,
        }
        if kwargs.get("force_refresh"):
            params["force_refresh"] = True

        endpoint = f"{self._api_base_url}/api/v2/analysis/execute"
        self.status_changed.emit("透過 API 載入全部車手直線速度資料...")
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
            self._error(f"API 載入失敗: {exc}")
            self.load_error.emit(f"API 載入失敗: {exc}")
            return None

        if not isinstance(payload, dict) or not payload.get("success", False):
            message = payload.get("message") if isinstance(payload, dict) else "未知錯誤"
            self._error(f"API 返回失敗: {message}")
            self.load_error.emit(f"API 返回失敗: {message}")
            return None

        self._last_api_payload = payload

        output_path = self._write_payload_to_cache(payload, year, race, session)
        if output_path:
            self.load_progress.emit(60)
            return output_path

        self.load_error.emit("儲存 API 結果時發生錯誤")
        return None

    def _write_payload_to_cache(self, payload: Dict[str, Any], year: int, race: str, session: str) -> Optional[str]:
        try:
            os.makedirs("json", exist_ok=True)
            filename = self._make_filename(year, race, session)
            path = os.path.join("json", filename)
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            self._debug(f"API 結果已寫入 {path}")
            return path
        except Exception as exc:
            self._error(f"寫入 JSON 檔案失敗: {exc}")
            return None

    def _make_filename(self, year: int, race: str, session: str) -> str:
        race_slug = self._sanitize_for_filename(race)
        session_slug = self._sanitize_for_filename(session)
        return f"all_drivers_straight_line_speed_{year}_{race_slug}_{session_slug}.json"

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


__all__ = ["StraightLineSpeedDataLoader"]
