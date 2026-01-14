#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lap Throttle Ratio Analysis (Function 54).

Computes per-lap throttle usage metrics for every driver in a loaded
FastF1 session. The output is saved as structured JSON so that GUI
modules operating under the API-ONLY policy can consume identical data.

Key metrics (per lap):
    - full_throttle_duration_s  - total seconds with throttle >= threshold.
    - full_throttle_ratio       - share of lap spent above threshold.
    - average_throttle          - time-weighted average throttle (0-1).
    - throttle_variability      - weighted standard deviation (0-1).
    - coasting_duration_s       - total seconds with throttle <= coast threshold.
    - drs_usage_ratio           - share of lap with DRS active (if data exists).
    - speed_avg_kmh / top_speed_kmh - from telemetry Speed channel when present.

The analyser returns a dictionary that matches the CLI unified response
format used across the project and persists JSON to ``json/``.
"""

from __future__ import annotations

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
import os
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


# 抑制 FastF1 的 FutureWarning (pick_driver 棄用警告)
warnings.filterwarnings('ignore', category=FutureWarning, module='fastf1')

DEFAULT_FULL_THROTTLE_THRESHOLD = 0.9
DEFAULT_COAST_THRESHOLD = 0.2
_JSON_DIR = "json"


@dataclass
class LapComputationResult:
    """Container for per-lap throttle metrics."""

    lap_number: int
    lap_time_seconds: Optional[float]
    full_throttle_duration_s: Optional[float]
    full_throttle_ratio: Optional[float]
    average_throttle: Optional[float]
    throttle_variability: Optional[float]
    coasting_duration_s: Optional[float]
    drs_usage_ratio: Optional[float]
    ers_deploy_ratio: Optional[float]
    speed_avg_kmh: Optional[float]
    top_speed_kmh: Optional[float]
    telemetry_sample_count: int
    data_status: str
    notes: Optional[str] = None
    
    # 新增：互斥踏板狀態（加總 = 100%）
    throttle_only_ratio: Optional[float] = None   # 純油門（油門 > 0，剎車 = 0）
    brake_only_ratio: Optional[float] = None      # 純剎車（油門 = 0，剎車 = 1）
    trail_braking_ratio: Optional[float] = None   # 左腳剎車（油門 > 0，剎車 = 1）
    coasting_ratio: Optional[float] = None        # 滑行（油門 = 0，剎車 = 0）

    def as_payload(self, extra_fields: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "lap_number": self.lap_number,
            "lap_time_seconds": self.lap_time_seconds,
            "full_throttle_duration_s": self.full_throttle_duration_s,
            "full_throttle_ratio": self.full_throttle_ratio,
            "average_throttle": self.average_throttle,
            "throttle_variability": self.throttle_variability,
            "coasting_duration_s": self.coasting_duration_s,
            "drs_usage_ratio": self.drs_usage_ratio,
            "ers_deploy_ratio": self.ers_deploy_ratio,
            "speed_avg_kmh": self.speed_avg_kmh,
            "top_speed_kmh": self.top_speed_kmh,
            "telemetry_sample_count": self.telemetry_sample_count,
            "data_status": self.data_status,
            # 新增：互斥踏板狀態
            "pedal_states": {
                "throttle_only_ratio": self.throttle_only_ratio,
                "brake_only_ratio": self.brake_only_ratio,
                "trail_braking_ratio": self.trail_braking_ratio,
                "coasting_ratio": self.coasting_ratio,
            },
        }
        if self.notes:
            payload["notes"] = self.notes
        payload.update(extra_fields)
        return payload

def run_driver_throttle_ratio_analysis(
    data_loader: Any,
    threshold: float = DEFAULT_FULL_THROTTLE_THRESHOLD,
    coast_threshold: float = DEFAULT_COAST_THRESHOLD,
    show_summary: bool = True,
    save_json: bool = True,
) -> Dict[str, Any]:
    """Entry point for Function 54.

    Parameters
    ----------
    data_loader : Any
        The compatible FastF1 data loader with ``session`` and ``laps``.
    threshold : float, default 0.9
        Minimum throttle (0-1) to consider full throttle.
    coast_threshold : float, default 0.2
        Maximum throttle (0-1) indicating coasting.
    show_summary : bool, default True
        Whether to print a compact summary per driver to stdout.
    save_json : bool, default True
        (已廢棄) 此參數保留以維持 API 相容性，但 JSON 保存由 function_mapper 統一處理
    """
    print("[INFO] 啟動 Function 54 - 全車手每圈油門比例分析")
    _validate_loader(data_loader)

    laps = getattr(data_loader, "laps", None)
    if laps is None or len(laps) == 0:
        raise ValueError("數據載入器缺少 laps 資料，請先載入 FastF1 會話")

    drivers = _extract_drivers(laps)
    if not drivers:
        raise ValueError("找不到任何車手資料，可用車手列表為空")

    print(f"📦 已載入 {len(drivers)} 位車手，準備計算油門指標 (門檻: ≥{threshold:.2f}, 滑行 ≤{coast_threshold:.2f})")

    driver_payloads: List[Dict[str, Any]] = []
    all_lap_summaries: List[Dict[str, float]] = []

    for index, driver_code in enumerate(drivers, start=1):
        print(f"  ↳ [{index}/{len(drivers)}] 分析車手 {driver_code} 的每圈油門數據…")
        driver_laps = _pick_driver_laps(laps, driver_code)
        driver_payload, driver_stats = _analyze_driver_laps(
            data_loader,
            driver_code,
            driver_laps,
            threshold,
            coast_threshold,
        )
        driver_payloads.append(driver_payload)
        if driver_stats:
            all_lap_summaries.extend(driver_stats)

        if show_summary:
            _print_driver_summary(driver_payload)

    metadata = _build_metadata(data_loader, threshold, coast_threshold)
    analysis_payload = {
        "drivers": driver_payloads,
        "summary": _aggregate_global_summary(all_lap_summaries),
    }
    
    # 返回標準格式，由 function_mapper 統一處理 JSON 保存（與 F34/F47/F48 一致）
    result = {
        "success": True,
        "message": f"Function 54 分析完成，共 {len(driver_payloads)} 位車手",
        "function_id": "54",
        "data": {
            "metadata": metadata,
            "analysis": analysis_payload,
            "total_drivers": len(driver_payloads),
        },
    }

    return result


def _validate_loader(data_loader: Any) -> None:
    if data_loader is None:
        raise ValueError("數據載入器未初始化")
    if not getattr(data_loader, "session_loaded", False):
        raise ValueError("數據載入器尚未載入會話資料")
    if not hasattr(data_loader, "session") or data_loader.session is None:
        raise ValueError("FastF1 會話不存在，請確認 load_race_data 已成功執行")


def _extract_drivers(laps: Any) -> List[str]:
    drivers = []
    if hasattr(laps, "drivers"):
        try:
            drivers = list(laps.drivers)
        except Exception:
            drivers = []
    if not drivers:
        try:
            driver_series = None
            if isinstance(laps, pd.DataFrame):
                driver_series = laps.get("Driver")
            else:
                driver_series = laps["Driver"] if "Driver" in laps.columns else None  # type: ignore[attr-defined]
            if driver_series is not None:
                drivers = list(pd.unique(driver_series.dropna()))
        except Exception:
            drivers = []
    return [d for d in drivers if isinstance(d, str) and d.strip()]


def _pick_driver_laps(laps: Any, driver: str) -> pd.DataFrame:
    if hasattr(laps, "pick_driver"):
        try:
            selected = laps.pick_driver(driver)
            if selected is not None and len(selected) > 0:
                return selected
        except Exception:
            pass
    # fallback to boolean filtering
    try:
        return laps[laps["Driver"] == driver]
    except Exception as err:  # pragma: no cover - defensive path
        raise RuntimeError(f"無法獲取車手 {driver} 的圈數資料: {err}")


def _analyze_driver_laps(
    data_loader: Any,
    driver_code: str,
    driver_laps: pd.DataFrame,
    threshold: float,
    coast_threshold: float,
) -> Tuple[Dict[str, Any], List[Dict[str, float]]]:
    laps_payload: List[Dict[str, Any]] = []
    stats_records: List[Dict[str, float]] = []

    team_name = _extract_team_name(driver_laps)

    for _, lap in driver_laps.iterrows():
        lap_number = int(lap.get("LapNumber", 0) or 0)
        lap_time_seconds = _timedelta_to_seconds(lap.get("LapTime"))

        telemetry = _safe_get_telemetry(lap)
        lap_payload: Dict[str, Any]
        if telemetry is None or telemetry.empty or "Throttle" not in telemetry.columns:
            lap_result = LapComputationResult(
                lap_number=lap_number,
                lap_time_seconds=lap_time_seconds,
                full_throttle_duration_s=None,
                full_throttle_ratio=None,
                average_throttle=None,
                throttle_variability=None,
                coasting_duration_s=None,
                drs_usage_ratio=None,
                ers_deploy_ratio=None,
                speed_avg_kmh=None,
                top_speed_kmh=None,
                telemetry_sample_count=int(0),
                data_status="insufficient",
                notes="Telemetry 不完整或缺少 Throttle 欄位",
            )
        else:
            lap_result = _calculate_lap_metrics_from_telemetry(
                telemetry,
                lap_time_seconds,
                threshold,
                coast_threshold,
                lap_number=lap_number,
            )

        extra_fields = _collect_extra_lap_fields(lap)
        lap_payload = lap_result.as_payload(extra_fields)
        laps_payload.append(lap_payload)

        if lap_result.data_status == "ok":
            stats_records.append(
                {
                    "driver": driver_code,
                    "lap_number": lap_number,
                    "full_throttle_duration_s": lap_result.full_throttle_duration_s or 0.0,
                    "full_throttle_ratio": lap_result.full_throttle_ratio or 0.0,
                    "lap_time_seconds": lap_result.lap_time_seconds or 0.0,
                }
            )

    driver_payload = {
        "driver_code": driver_code,
        "team": team_name,
        "laps": laps_payload,
        "summary": _build_driver_summary(stats_records),
    }
    return driver_payload, stats_records


def _extract_team_name(driver_laps: pd.DataFrame) -> Optional[str]:
    if driver_laps is None or len(driver_laps) == 0:
        return None
    possible_cols = ["Team", "TeamName", "Constructor"]
    for col in possible_cols:
        if col in driver_laps.columns:
            value = driver_laps[col].dropna().unique()
            if len(value) > 0:
                return str(value[0])
    return None


def _timedelta_to_seconds(value: Any) -> Optional[float]:
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "total_seconds"):
        return float(value.total_seconds())
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_get_telemetry(lap: pd.Series) -> Optional[pd.DataFrame]:
    try:
        telemetry = lap.get_telemetry()
        if telemetry is None:
            return None
        if "Time" not in telemetry.columns:
            return None
        # 確保依時間排序並移除重複索引
        telemetry = telemetry.dropna(subset=["Time", "Throttle"], how="any")
        telemetry = telemetry.sort_values("Time").reset_index(drop=True)
        return telemetry
    except Exception as exc:
        print(f"[WARNING] 無法取得第 {lap.get('LapNumber', '?')} 圈遙測資料: {exc}")
        return None


def _calculate_lap_metrics_from_telemetry(
    telemetry: pd.DataFrame,
    lap_time_seconds: Optional[float],
    threshold: float,
    coast_threshold: float,
    lap_number: Optional[int] = None,
) -> LapComputationResult:
    """Compute lap-level throttle metrics from telemetry."""

    telemetry = telemetry.copy()
    telemetry["Throttle"] = telemetry["Throttle"].astype(float)
    # FastF1 提供的油門為 0-100，若已是 0-1 則不需縮放
    if telemetry["Throttle"].max() > 1.0:
        throttle = telemetry["Throttle"] / 100.0
    else:
        throttle = telemetry["Throttle"].clip(0.0, 1.0)

    resolved_lap_number = _resolve_lap_number_from_telemetry(telemetry, lap_number)

    time_seconds = _telemetry_time_to_seconds(telemetry["Time"])
    if len(time_seconds) < 2:
        return LapComputationResult(
            lap_number=resolved_lap_number,
            lap_time_seconds=lap_time_seconds,
            full_throttle_duration_s=None,
            full_throttle_ratio=None,
            average_throttle=None,
            throttle_variability=None,
            coasting_duration_s=None,
            drs_usage_ratio=None,
            ers_deploy_ratio=None,
            speed_avg_kmh=None,
            top_speed_kmh=None,
            telemetry_sample_count=int(len(telemetry)),
            data_status="insufficient",
            notes="Telemetry 長度不足以計算時間差",
        )

    delta_t = np.diff(time_seconds)
    delta_t = np.where(delta_t < 0, 0, delta_t)  # 防止負時間

    # 使用左端點樣本代表該區間，確保與 delta_t 對齊
    throttle_left = throttle[:-1]

    total_duration = float(np.sum(delta_t)) if np.sum(delta_t) > 0 else (lap_time_seconds or None)
    if total_duration is None or total_duration <= 0:
        total_duration = float(time_seconds[-1] - time_seconds[0])

    full_mask = throttle_left >= threshold
    coast_mask = throttle_left <= coast_threshold

    full_duration = float(np.sum(delta_t[full_mask])) if total_duration else None
    coast_duration = float(np.sum(delta_t[coast_mask])) if total_duration else None

    avg_throttle = (
        float(np.sum(throttle_left * delta_t) / np.sum(delta_t)) if np.sum(delta_t) > 0 else None
    )
    variability = _weighted_std(throttle_left, delta_t) if np.sum(delta_t) > 0 else None

    drs_ratio = None
    if "DRS" in telemetry.columns:
        drs_values = telemetry["DRS"].astype(float).to_numpy()[:-1]
        drs_active = drs_values > 0.0
        drs_ratio = float(np.sum(delta_t[drs_active]) / total_duration) if total_duration else None

    ers_ratio = None
    if "ERSDeployMode" in telemetry.columns:
        ers_values = telemetry["ERSDeployMode"].astype(float).to_numpy()[:-1]
        ers_active = ers_values > 0.0
        ers_ratio = float(np.sum(delta_t[ers_active]) / total_duration) if total_duration else None

    speed_avg = None
    top_speed = None
    if "Speed" in telemetry.columns:
        speed = telemetry["Speed"].astype(float)
        speed_left = speed[:-1]
        speed_avg = float(np.sum(speed_left * delta_t) / np.sum(delta_t)) if np.sum(delta_t) > 0 else None
        top_speed = float(np.nanmax(speed)) if len(speed) > 0 else None

    # ===== 新增：互斥踏板狀態計算 =====
    # 剎車數據：0 或 1（二進制）
    throttle_only_ratio = None
    brake_only_ratio = None
    trail_braking_ratio = None
    coasting_ratio = None
    
    if "Brake" in telemetry.columns and total_duration and total_duration > 0:
        brake = telemetry["Brake"].astype(float).to_numpy()
        brake_left = brake[:-1]
        
        # 將油門轉換為 numpy array
        throttle_arr = throttle.to_numpy() if hasattr(throttle, 'to_numpy') else np.array(throttle)
        throttle_left_arr = throttle_arr[:-1]
        
        # 定義互斥狀態
        # 油門 > 0 視為「有油門」
        has_throttle = throttle_left_arr > 0
        has_brake = brake_left == 1  # 剎車是二進制的
        
        # 四種互斥狀態
        throttle_only_mask = has_throttle & ~has_brake    # 純油門
        brake_only_mask = ~has_throttle & has_brake       # 純剎車
        trail_braking_mask = has_throttle & has_brake     # 左腳剎車（同時踩）
        coasting_mask = ~has_throttle & ~has_brake        # 滑行
        
        # 計算每種狀態的時間佔比
        throttle_only_ratio = float(np.sum(delta_t[throttle_only_mask]) / total_duration)
        brake_only_ratio = float(np.sum(delta_t[brake_only_mask]) / total_duration)
        trail_braking_ratio = float(np.sum(delta_t[trail_braking_mask]) / total_duration)
        coasting_ratio = float(np.sum(delta_t[coasting_mask]) / total_duration)

    return LapComputationResult(
        lap_number=resolved_lap_number,
        lap_time_seconds=lap_time_seconds,
        full_throttle_duration_s=full_duration if total_duration else None,
        full_throttle_ratio=(full_duration / total_duration) if (full_duration is not None and total_duration) else None,
        average_throttle=avg_throttle,
        throttle_variability=variability,
        coasting_duration_s=coast_duration,
        drs_usage_ratio=drs_ratio,
        ers_deploy_ratio=ers_ratio,
        speed_avg_kmh=speed_avg,
        top_speed_kmh=top_speed,
        telemetry_sample_count=int(len(telemetry)),
        data_status="ok",
        # 新增：互斥踏板狀態
        throttle_only_ratio=throttle_only_ratio,
        brake_only_ratio=brake_only_ratio,
        trail_braking_ratio=trail_braking_ratio,
        coasting_ratio=coasting_ratio,
    )


def _resolve_lap_number_from_telemetry(telemetry: pd.DataFrame, fallback: Optional[int]) -> int:
    if fallback is not None:
        try:
            return int(fallback)
        except (TypeError, ValueError):
            pass

    if "LapNumber" in telemetry.columns:
        series = telemetry["LapNumber"].dropna()
        if not series.empty:
            try:
                return int(series.iloc[-1])
            except (TypeError, ValueError):
                pass

    return 0


def _collect_extra_lap_fields(lap: pd.Series) -> Dict[str, Any]:
    # 判斷是否為進站圈（有 pit_in_time 表示該圈進站）
    pit_in_time = _timedelta_to_seconds(lap.get("PitInTime"))
    pit_out_time = _timedelta_to_seconds(lap.get("PitOutTime"))
    is_pit_lap = pit_in_time is not None  # 有進站時間 = 進站圈
    
    fields = {
        "compound": _safe_get(lap, "Compound"),
        "tire_compound": _safe_get(lap, "Compound"),  # 別名，供 Stint Selector 使用
        "tyre_life": _safe_int(lap, "TyreLife"),
        "stint": _safe_int(lap, "Stint"),
        "sector1_time": _timedelta_to_seconds(lap.get("Sector1Time")),
        "sector2_time": _timedelta_to_seconds(lap.get("Sector2Time")),
        "sector3_time": _timedelta_to_seconds(lap.get("Sector3Time")),
        "is_accurate": bool(lap.get("IsAccurate", False)),
        "pit_out_time": pit_out_time,
        "pit_in_time": pit_in_time,
        "pit_status": _safe_get(lap, "PitOut"),
        "track_status": _safe_get(lap, "TrackStatus"),
        "lap_time_formatted": _format_lap_time(lap.get("LapTime")),
        # 新增：進站標記（供 Stint Selection 使用）
        "is_pit_lap": is_pit_lap,
        "smart_markers": {
            "pit_stop_detection": {
                "is_pit_lap": is_pit_lap,
            }
        },
    }
    if "DriverNumber" in lap:
        fields["driver_number"] = _safe_get(lap, "DriverNumber")
    return fields


def _weighted_std(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) == 0 or np.sum(weights) == 0:
        return 0.0
    average = np.sum(values * weights) / np.sum(weights)
    variance = np.sum(weights * (values - average) ** 2) / np.sum(weights)
    return float(np.sqrt(variance))


def _telemetry_time_to_seconds(time_series: pd.Series) -> np.ndarray:
    if hasattr(time_series, "dt"):
        return time_series.dt.total_seconds().to_numpy(dtype=float)
    return time_series.astype(float).to_numpy()


def _safe_get(obj: Any, key: str) -> Optional[Any]:
    try:
        value = obj.get(key)
    except AttributeError:
        value = getattr(obj, key, None)
    if pd.isna(value):
        return None
    return value


def _safe_int(obj: Any, key: str) -> Optional[int]:
    value = _safe_get(obj, key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_lap_time(value: Any) -> Optional[str]:
    seconds = _timedelta_to_seconds(value)
    if seconds is None:
        return None
    minutes, sec = divmod(seconds, 60)
    return f"{int(minutes):02d}:{sec:06.3f}"


def _build_driver_summary(records: List[Dict[str, float]]) -> Optional[Dict[str, Any]]:
    if not records:
        return None
    durations = np.array([r["full_throttle_duration_s"] for r in records], dtype=float)
    ratios = np.array([r["full_throttle_ratio"] for r in records], dtype=float)
    lap_times = np.array([r["lap_time_seconds"] for r in records], dtype=float)

    return {
        "valid_laps": int(len(records)),
        "avg_full_throttle_duration_s": float(np.mean(durations)),
        "median_full_throttle_duration_s": float(np.median(durations)),
        "max_full_throttle_duration_s": float(np.max(durations)),
        "min_full_throttle_duration_s": float(np.min(durations)),
        "avg_full_throttle_ratio": float(np.mean(ratios)),
        "avg_lap_time_seconds": float(np.mean(lap_times)),
    }


def _aggregate_global_summary(stats: List[Dict[str, float]]) -> Optional[Dict[str, Any]]:
    if not stats:
        return None
    durations = np.array([s["full_throttle_duration_s"] for s in stats], dtype=float)
    ratios = np.array([s["full_throttle_ratio"] for s in stats], dtype=float)
    return {
        "total_laps": int(len(stats)),
        "mean_full_throttle_duration_s": float(np.mean(durations)),
        "median_full_throttle_duration_s": float(np.median(durations)),
        "std_full_throttle_duration_s": float(np.std(durations)),
        "mean_full_throttle_ratio": float(np.mean(ratios)),
        "max_full_throttle_ratio": float(np.max(ratios)),
    }


def _build_metadata(data_loader: Any, threshold: float, coast_threshold: float) -> Dict[str, Any]:
    session = getattr(data_loader, "session", None)
    event = getattr(session, "event", {}) if session is not None else {}

    year = getattr(data_loader, "year", None) or event.get("year")
    race = getattr(data_loader, "race_name", None) or event.get("EventName")
    session_type = getattr(data_loader, "session_type", None) or event.get("SessionName")

    return {
        "function_id": 54,
        "function_name": "Lap Throttle Ratio Per Driver",
        "year": year,
        "race": race,
        "session": session_type,
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "thresholds": {
            "full_throttle": threshold,
            "coast": coast_threshold,
        },
        "driver_filter": None,
        "data_version": "1.0.0",
    }


def _save_analysis_json(metadata: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """
    [已廢棄] 此函數已不再使用，JSON 保存由 function_mapper._export_to_json() 統一處理
    保留此函數僅供單元測試使用
    """
    path = _build_output_path(metadata.get("year"), metadata.get("race"), metadata.get("session"))

    with open(path, "w", encoding="utf-8") as fp:
        json.dump({"metadata": metadata, "analysis": analysis}, fp, ensure_ascii=False, indent=2)
    return os.path.abspath(path)


def _slugify(value: Optional[str]) -> str:
    if not value:
        return "unknown"
    return (
        str(value)
        .strip()
        .replace(" ", "_")
        .replace("/", "-")
        .replace("__", "_")
        .lower()
    )


def _extract_session_identifiers(data_loader: Any) -> Tuple[Any, Any, Any]:
    session = getattr(data_loader, "session", None)
    event = getattr(session, "event", {}) if session is not None else {}

    year = getattr(data_loader, "year", None) or event.get("year")
    race = getattr(data_loader, "race_name", None) or event.get("EventName")
    session_type = getattr(data_loader, "session_type", None) or event.get("SessionName")
    return year, race, session_type


def _build_output_path(year: Any, race: Any, session_type: Any) -> str:
    os.makedirs(_JSON_DIR, exist_ok=True)
    year_part = str(year) if year is not None else "unknown"
    race_part = _slugify(race if race is not None else "unknown")
    session_part = str(session_type) if session_type else "Unknown"
    filename = f"throttle_ratio_{year_part}_{race_part}_{session_part}.json"
    return os.path.join(_JSON_DIR, filename)


def _load_existing_analysis(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception as exc:
        print(f"[WARNING] 無法載入既有分析 JSON ({path}): {exc}")
        return None


def _thresholds_match(payload: Dict[str, Any], threshold: float, coast_threshold: float) -> bool:
    metadata = payload.get("metadata", {})
    thresholds = metadata.get("thresholds", {}) if isinstance(metadata, dict) else {}
    full_value = thresholds.get("full_throttle")
    coast_value = thresholds.get("coast")
    try:
        full = float(full_value)
        coast = float(coast_value)
    except (TypeError, ValueError):
        return False
    return (
        math.isclose(full, float(threshold), rel_tol=1e-9, abs_tol=1e-9)
        and math.isclose(coast, float(coast_threshold), rel_tol=1e-9, abs_tol=1e-9)
    )


def _print_driver_summary(driver_payload: Dict[str, Any]) -> None:
    summary = driver_payload.get("summary") or {}
    if not summary:
        print(f"    ⚠️ 車手 {driver_payload.get('driver_code')} 沒有足夠的有效圈數")
        return
    print(
        "    ✅ 平均全油門秒數: "
        f"{summary.get('avg_full_throttle_duration_s', 0.0):.2f}s | "
        "平均占比: "
        f"{summary.get('avg_full_throttle_ratio', 0.0) * 100:.1f}% | "
        "有效圈: "
        f"{summary.get('valid_laps', 0)}"
    )


# --- Helper functions exposed for unit testing --- #


def calculate_throttle_metrics_from_telemetry(
    telemetry: pd.DataFrame,
    lap_time_seconds: Optional[float],
    threshold: float,
    coast_threshold: float,
    lap_number: Optional[int] = None,
) -> Dict[str, Any]:
    """Utility wrapper used in unit tests."""
    result = _calculate_lap_metrics_from_telemetry(
        telemetry,
        lap_time_seconds,
        threshold,
        coast_threshold,
        lap_number=lap_number,
    )
    return result.as_payload(extra_fields={})


def build_analysis_payload(
    metadata: Dict[str, Any], drivers: Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    """Helper to build final payload for tests."""
    return {"metadata": metadata, "analysis": {"drivers": list(drivers)}}


__all__ = [
    "run_driver_throttle_ratio_analysis",
    "calculate_throttle_metrics_from_telemetry",
    "build_analysis_payload",
]
