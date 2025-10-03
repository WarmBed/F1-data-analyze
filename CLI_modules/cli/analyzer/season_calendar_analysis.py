#!/usr/bin/env python3
"""Season calendar utilities backed by FastF1."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import fastf1
import pandas as pd

__all__ = ["generate_season_calendar", "SeasonCalendarResult"]

FASTF1_CACHE_DIR = os.getenv("F1_ANALYSIS_FASTF1_CACHE", "f1_analysis_cache")
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")

SeasonCalendarResult = Dict[str, Any]


def _enable_fastf1_cache() -> None:
    """Ensure FastF1 caching is enabled before accessing the API."""

    try:
        fastf1.Cache.enable_cache(FASTF1_CACHE_DIR)
    except Exception as exc:  # pragma: no cover - defensive safeguard
        print(f"[WARNING] FastF1 cache enable failed: {exc}")


def _to_datetime(value: Any) -> Optional[datetime]:
    """Convert FastF1/pandas timestamp values into timezone-aware datetimes."""

    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):  # type: ignore[call-arg]
            return None
        dt = value.to_pydatetime()
    elif isinstance(value, datetime):
        dt = value
    else:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _to_iso(value: Any) -> Optional[str]:
    dt = _to_datetime(value)
    return dt.isoformat() if dt is not None else None


def _normalise_round(value: Any) -> Optional[int]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_testing_event(event_name: Optional[str]) -> bool:
    if not event_name:
        return False
    lowered = event_name.lower()
    return "testing" in lowered or "pre-season" in lowered


def _days_until(target: Optional[datetime], *, reference: datetime) -> Optional[int]:
    if target is None:
        return None
    delta = target - reference
    if delta.total_seconds() < 0:
        return None
    return int(delta.total_seconds() // 86400)


def _ensure_json_dir() -> Path:
    path = Path(JSON_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _build_session_block(row: pd.Series) -> Dict[str, Optional[str]]:
    session_payload: Dict[str, Optional[str]] = {}
    for idx in range(1, 6):
        name_key = f"Session{idx}"
        local_key = f"Session{idx}Date"
        utc_key = f"Session{idx}DateUtc"
        session_payload[f"session{idx}_name"] = row.get(name_key)
        session_payload[f"session{idx}_local"] = _to_iso(row.get(local_key))
        session_payload[f"session{idx}_utc"] = _to_iso(row.get(utc_key))
    return session_payload


def _summarise_event(row: pd.Series, *, reference: datetime, cache_enabled: bool) -> Optional[Dict[str, Any]]:
    round_number = _normalise_round(row.get("RoundNumber"))
    event_name = row.get("EventName")

    if round_number is None or _is_testing_event(str(event_name) if event_name else None):
        return None

    race_dt_local = _to_datetime(row.get("Session5Date"))
    race_dt_utc = _to_datetime(row.get("Session5DateUtc"))

    is_completed = bool(race_dt_utc and race_dt_utc <= reference)

    return {
        "round": round_number,
        "event_name": event_name,
        "official_name": row.get("OfficialEventName"),
        "country": row.get("Country"),
        "location": row.get("Location"),
        "is_completed": is_completed,
        "race_date_local": race_dt_local.isoformat() if race_dt_local else None,
        "race_date_utc": race_dt_utc.isoformat() if race_dt_utc else None,
        "days_until_race": _days_until(race_dt_utc, reference=reference),
        "session_dates": _build_session_block(row),
        "cache_used": cache_enabled,
    }


def _create_summary(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}

    for event in reversed(events):
        if event.get("is_completed"):
            summary["last_completed_event"] = {
                "round": event.get("round"),
                "event_name": event.get("event_name"),
                "race_date_local": event.get("race_date_local"),
                "race_date_utc": event.get("race_date_utc"),
            }
            break

    for event in events:
        if not event.get("is_completed"):
            summary["next_event"] = {
                "round": event.get("round"),
                "event_name": event.get("event_name"),
                "race_date_local": event.get("race_date_local"),
                "race_date_utc": event.get("race_date_utc"),
                "days_until_race": event.get("days_until_race"),
            }
            break

    return summary


def _write_json(payload: Dict[str, Any], *, year: int) -> Optional[str]:
    try:
        json_dir = _ensure_json_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = json_dir / f"season_calendar_{year}_{timestamp}.json"
        with filename.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return str(filename)
    except Exception as exc:  # pragma: no cover - best effort only
        print(f"[WARNING] Season calendar JSON export failed: {exc}")
        return None


def generate_season_calendar(year: int, *, save_json: bool = True) -> SeasonCalendarResult:
    """Fetch and transform the FastF1 season schedule for the given year."""

    _enable_fastf1_cache()

    response: SeasonCalendarResult = {
        "success": False,
        "message": "賽程查詢尚未執行",
        "metadata": {
            "year": year,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_rounds": 0,
            "completed_rounds": 0,
            "upcoming_rounds": 0,
            "cache_enabled": not fastf1.Cache.disabled,
        },
        "data": [],
        "summary": {},
    }

    try:
        schedule = fastf1.get_event_schedule(year)
    except Exception as exc:
        response.update({
            "success": False,
            "message": f"FastF1 賽程取得失敗: {exc}",
        })
        return response

    reference_time = datetime.now(timezone.utc)
    cache_enabled = not fastf1.Cache.disabled

    events: List[Dict[str, Any]] = []
    for _, row in schedule.iterrows():
        event_payload = _summarise_event(row, reference=reference_time, cache_enabled=cache_enabled)
        if event_payload is None:
            continue
        events.append(event_payload)

    events.sort(key=lambda item: item.get("round", 0))

    completed = sum(1 for event in events if event.get("is_completed"))
    total = len(events)

    response.update({
        "success": True,
        "message": f"{year} 年賽季賽程查詢成功",
        "metadata": {
            **response["metadata"],
            "total_rounds": total,
            "completed_rounds": completed,
            "upcoming_rounds": max(total - completed, 0),
        },
        "data": events,
        "summary": _create_summary(events),
    })

    if save_json and events:
        exported_path = _write_json(response, year=year)
        if exported_path:
            response["metadata"]["output_file"] = exported_path

    return response