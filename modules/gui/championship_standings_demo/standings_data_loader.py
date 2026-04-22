#!/usr/bin/env python3
"""Championship standings data loader for the standalone demo."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import certifi
from core import local_requests as requests
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from modules.gui.base.universal_data_loader_base import AnalysisConfig, UniversalDataLoader

_ANALYSIS_KEY = "championship_standings_demo"
_API_ENDPOINT = "/api/v2/analysis/execute"
_FUNCTION_ID_STANDINGS = 97
_FUNCTION_ID_CALENDAR = 99


class _ChampionshipStandingsApiWorker(QThread):
    """Background worker responsible for fetching standings and calendar data via REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(
        self,
        base_url: str,
        year: int,
        *,
        round_hint: Optional[str] = None,
        include_constructors: bool = True,
        include_drivers: bool = True,
        force_refresh: bool = False,
        timeout: float = 90.0,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.base_url = base_url.rstrip("/") or "http://localhost:8000"
        self.year = int(year)
        self.round_hint = round_hint
        self.include_constructors = include_constructors
        self.include_drivers = include_drivers
        self.force_refresh = force_refresh
        self.timeout = timeout

    def run(self) -> None:  # pragma: no cover - network interaction
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            standings_payload = self._request_standings()
            # ✅ 中斷檢查點 2: standings 請求後
            if self.isInterruptionRequested():
                return
            self.progress.emit(60)
            calendar_payload = self._request_calendar()
            # ✅ 中斷檢查點 3: calendar 請求後
            if self.isInterruptionRequested():
                return
            self.progress.emit(90)
            self.success.emit({
                "standings": standings_payload,
                "calendar": calendar_payload,
            })
        except Exception as exc:  # pragma: no cover - defensive
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            self.failure.emit(str(exc))
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)

    def _request_standings(self) -> Dict[str, Any]:
        endpoint = f"{self.base_url}{_API_ENDPOINT}"
        params: Dict[str, Any] = {
            "function_id": _FUNCTION_ID_STANDINGS,
            "year": self.year,
        }
        if self.round_hint:
            params["round"] = self.round_hint
        if not self.include_constructors:
            params["include_constructors"] = False
        if not self.include_drivers:
            params["include_drivers"] = False
        if self.force_refresh:
            params["force_refresh"] = True

        start_ts = time.perf_counter()
        response = requests.post(
            endpoint,
            params=params,
            timeout=self.timeout,
            headers={"Accept": "application/json"},
            verify=certifi.where()  # ✅ SSL證書（EXE必須）
        )
        latency_ms = (time.perf_counter() - start_ts) * 1000.0
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("API response for standings must be a JSON object")
        if not payload.get("success", False):
            raise RuntimeError(payload.get("message", "API returned success=False"))
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("API standings response missing 'data' dictionary")
        metadata = payload.get("metadata") or payload.get("function_spec") or {}
        return {
            "payload": payload,
            "data": data,
            "meta": {
                "execution_time": payload.get("execution_time"),
                "source": payload.get("source", "api"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "function_spec": payload.get("function_spec"),
                "metadata": metadata,
            },
        }

    def _request_calendar(self) -> Dict[str, Any]:
        endpoint = f"{self.base_url}{_API_ENDPOINT}"
        params: Dict[str, Any] = {
            "function_id": _FUNCTION_ID_CALENDAR,
            "year": self.year,
        }
        if self.force_refresh:
            params["force_refresh"] = True

        start_ts = time.perf_counter()
        response = requests.post(
            endpoint,
            params=params,
            timeout=self.timeout,
            headers={"Accept": "application/json"},
            verify=certifi.where()  # ✅ SSL證書（EXE必須）
        )
        latency_ms = (time.perf_counter() - start_ts) * 1000.0
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("API response for calendar must be a JSON object")
        if not payload.get("success", False):
            raise RuntimeError(payload.get("message", "Calendar API returned success=False"))
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("API calendar response missing 'data' dictionary")
        return {
            "payload": payload,
            "data": data,
            "meta": {
                "execution_time": payload.get("execution_time"),
                "source": payload.get("source", "api"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "function_spec": payload.get("function_spec"),
            },
        }


class ChampionshipStandingsDataLoader(UniversalDataLoader):
    """UniversalDataLoader integration that fetches championship standings via API."""

    def __init__(
        self,
        *,
        year: Optional[int] = None,
        round_hint: Optional[str] = None,
        parent: Optional[QObject] = None,
        include_constructors: bool = True,
        include_drivers: bool = True,
        force_refresh: bool = False,
    ) -> None:
        self._ensure_analysis_config()
        super().__init__(_ANALYSIS_KEY, parent)
        self.year = int(year) if year is not None else None
        self.round_hint = round_hint
        self.include_constructors = include_constructors
        self.include_drivers = include_drivers
        self.force_refresh = force_refresh
        self._api_worker: Optional[_ChampionshipStandingsApiWorker] = None
        self._pending_params: Dict[str, Any] = {}
        self._api_base_url = resolve_api_base_url(event_logger=self._debug)
        self._allow_local_fallback = False
        self._debug("本地 JSON 後備已停用 (API-ONLY 模式)")

    # ------------------------------------------------------------------
    # UniversalDataLoader overrides
    # ------------------------------------------------------------------
    def load_data(self, **kwargs: Any) -> bool:
        if self._is_loading:
            self._debug("已有一個載入請求執行中，忽略新的請求")
            return False

        merged_params = self._prepare_params(kwargs)
        if not self._validate_load_parameters(merged_params):
            self._error("載入參數驗證失敗")
            self.load_error.emit(tr("standings_invalid_params", "載入參數不正確"))
            return False

        self._is_loading = True
        self._pending_params = merged_params
        self._api_base_url = resolve_api_base_url(event_logger=self._debug)

        self.load_progress.emit(5)
        self.status_changed.emit(tr("standings_status_fetching", "正在向 API 取得積分資料"))

        self._api_worker = _ChampionshipStandingsApiWorker(
            self._api_base_url,
            year=merged_params["year"],
            round_hint=merged_params.get("round_hint"),
            include_constructors=self.include_constructors,
            include_drivers=self.include_drivers,
            force_refresh=self.force_refresh or merged_params.get("force_refresh", False),
        )
        self._api_worker.progress.connect(self.load_progress.emit)
        self._api_worker.success.connect(self._handle_api_success)
        self._api_worker.failure.connect(self._handle_api_failure)
        self._api_worker.finished.connect(self._reset_worker_state)
        self._api_worker.start()
        return True

    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        try:
            year = params.get("year")
            if year is None:
                return False
            year_int = int(year)
            if year_int < 1950 or year_int > 2100:
                return False
            round_hint = params.get("round_hint")
            if round_hint is not None and not str(round_hint).strip():
                return False
            return True
        except Exception:
            return False

    def _build_filename_patterns(self, **kwargs: Any) -> List[str]:
        year = kwargs.get("year", self.year)
        patterns: List[str] = []
        if year:
            patterns.append(f"championship_standings_{year}_*.json")
        patterns.append("championship_standings_*.json")
        return patterns

    def _validate_data_format(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, dict):
            return False
        required_keys = {"drivers", "constructors", "summary", "metadata"}
        return required_keys.issubset(raw_data.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(kwargs)
        if "year" not in merged or merged["year"] is None:
            if self.year is not None:
                merged["year"] = self.year
        if "round_hint" not in merged and self.round_hint:
            merged["round_hint"] = self.round_hint
        if "force_refresh" not in merged:
            merged["force_refresh"] = self.force_refresh
        return merged

    def _reset_worker_state(self) -> None:
        self._api_worker = None
        self._is_loading = False

    def _handle_api_success(self, payload: Dict[str, Any]) -> None:
        try:
            processed = self._process_payload(payload)
            if not self._validate_data_format(processed):
                raise ValueError("API 回傳資料缺少必要欄位")
            self._current_data = processed
            self.data_loaded.emit(processed)
            self.status_changed.emit(tr("standings_status_ready", "積分資料載入完成"))
        except Exception as exc:
            self._error(f"資料處理失敗: {exc}")
            self.load_error.emit(str(exc))
        finally:
            self._reset_worker_state()

    def _handle_api_failure(self, message: str) -> None:
        self._error(f"API 請求失敗: {message}")
        self.load_error.emit(message)
        self._reset_worker_state()

    def _process_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        standings_block = payload.get("standings", {})
        calendar_block = payload.get("calendar", {})

        standings_payload = standings_block.get("payload", {})
        standings_data = standings_block.get("data", {})
        calendar_data = calendar_block.get("data", {})

        drivers = standings_data.get("drivers", [])
        constructors = standings_data.get("constructors", [])
        metadata = standings_payload.get("metadata", {})
        summary = standings_payload.get("summary") or standings_data.get("summary") or {}

        if not isinstance(drivers, list):
            raise ValueError("drivers 欄位格式錯誤")
        if not isinstance(constructors, list):
            raise ValueError("constructors 欄位格式錯誤")

        transformed_drivers = [self._transform_driver_row(row) for row in drivers]
        transformed_constructors = [self._transform_constructor_row(row) for row in constructors]
        season_context = self._build_season_context(calendar_data, metadata)

        return {
            "drivers": transformed_drivers,
            "constructors": transformed_constructors,
            "metadata": metadata,
            "summary": summary,
            "season": season_context,
            "raw": {
                "standings": standings_payload,
                "calendar": calendar_block.get("payload"),
                "api_meta": {
                    "standings": standings_block.get("meta"),
                    "calendar": calendar_block.get("meta"),
                },
            },
        }

    def _transform_driver_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        driver_info = row.get("driver", {}) if isinstance(row, dict) else {}
        constructors = row.get("constructors", []) if isinstance(row, dict) else []
        team_names = [team.get("name") for team in constructors if isinstance(team, dict) and team.get("name")]
        return {
            "position": row.get("position"),
            "position_text": row.get("position_text"),
            "points": row.get("points"),
            "wins": row.get("wins"),
            "points_delta": row.get("points_delta"),
            "driver_code": driver_info.get("code"),
            "driver_number": driver_info.get("number"),
            "driver_name": driver_info.get("full_name") or self._compose_name(driver_info),
            "nationality": driver_info.get("nationality"),
            "team_names": team_names,
        }

    def _transform_constructor_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        constructor_info = row.get("constructor", {}) if isinstance(row, dict) else {}
        return {
            "position": row.get("position"),
            "position_text": row.get("position_text"),
            "points": row.get("points"),
            "wins": row.get("wins"),
            "points_delta": row.get("points_delta"),
            "constructor_name": constructor_info.get("name"),
            "constructor_nationality": constructor_info.get("nationality"),
        }

    def _build_season_context(self, calendar_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        year = metadata.get("season_year")
        if year is None:
            try:
                year = self._pending_params.get("year")
            except Exception:
                year = None
        events: List[Dict[str, Any]] = []
        if isinstance(calendar_data, dict) and year is not None:
            year_key = str(year)
            events = calendar_data.get(year_key, []) if isinstance(calendar_data.get(year_key), list) else []

        total_events = len(events)
        completed_events = sum(1 for event in events if event.get("is_completed"))
        upcoming_events = max(total_events - completed_events, 0)

        next_event = self._find_next_event(events)
        latest_event = self._find_latest_completed_event(events)

        summary_text = self._compose_season_summary(year, total_events, completed_events, upcoming_events, next_event)

        return {
            "year": year,
            "total_events": total_events,
            "completed_events": completed_events,
            "upcoming_events": upcoming_events,
            "next_event": next_event,
            "latest_event": latest_event,
            "summary_text": summary_text,
        }

    def _find_next_event(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for event in events:
            if not event.get("is_completed"):
                return self._simplify_event(event)
        return None

    def _find_latest_completed_event(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for event in reversed(events):
            if event.get("is_completed"):
                return self._simplify_event(event)
        return None

    def _simplify_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        race_date = self._format_date(event.get("race_date_local") or event.get("race_date_utc"))
        return {
            "round": event.get("round"),
            "event_name": event.get("event_name"),
            "country": event.get("country"),
            "location": event.get("location"),
            "race_date": race_date,
            "days_until_race": event.get("days_until_race"),
        }

    def _compose_season_summary(
        self,
        year: Optional[int],
        total_events: int,
        completed_events: int,
        upcoming_events: int,
        next_event: Optional[Dict[str, Any]],
    ) -> str:
        if year is None:
            year_text = tr("standings_unknown_year", "未知賽季")
        else:
            year_text = f"{year}"

        base_text = tr(
            "standings_season_summary_base",
            "{year} 年度共 {total} 場賽事，已完成 {completed} 場，剩餘 {upcoming} 場。",
        ).format(year=year_text, total=total_events, completed=completed_events, upcoming=upcoming_events)

        if next_event:
            name = next_event.get("event_name") or tr("standings_unknown_event", "待定賽事")
            race_date = next_event.get("race_date") or tr("standings_unknown_date", "日期待定")
            country = next_event.get("country") or ""
            details_text = tr(
                "standings_next_event_detail",
                "下一場賽事：{name}（{country}），比賽日期 {date}",
            ).format(name=name, country=country, date=race_date)
            return f"{base_text} {details_text}"

        return base_text

    def _format_date(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value)).date().isoformat()
        except Exception:
            return None

    def _compose_name(self, info: Dict[str, Any]) -> Optional[str]:
        given = (info.get("given_name") or info.get("givenName") or "").strip()
        family = (info.get("family_name") or info.get("familyName") or "").strip()
        parts = [part for part in (given, family) if part]
        return " ".join(parts) if parts else None

    @staticmethod
    def _ensure_analysis_config() -> None:
        if _ANALYSIS_KEY in UniversalDataLoader.ANALYSIS_TYPES:
            return
        config = AnalysisConfig(
            display_name=tr("championship_standings_title", "賽季積分概覽"),
            debug_prefix="STANDINGS",
            data_source="api",
            cli_function=str(_FUNCTION_ID_STANDINGS),
            file_patterns=["championship_standings_*.json"],
            api_endpoint=_API_ENDPOINT,
            api_function_id=_FUNCTION_ID_STANDINGS,
            cache_patterns=["championship_standings"],
        )
        UniversalDataLoader.register_analysis_type(_ANALYSIS_KEY, config)
