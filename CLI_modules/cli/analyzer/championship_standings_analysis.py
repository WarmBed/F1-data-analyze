#!/usr/bin/env python3
"""Championship standings utilities backed by FastF1/Ergast."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastf1.ergast import Ergast

__all__ = [
    "generate_championship_standings",
    "check_standings_freshness",
    "ChampionshipStandingsResult",
]

JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")
STANDINGS_REFRESH_HOURS = 120  # 5 天 (平時維護模式)

ChampionshipStandingsResult = Dict[str, Any]


def _ensure_json_dir() -> Path:
    path = Path(JSON_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _format_timedelta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds} 秒前"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes} 分鐘前"
    hours = minutes // 60
    if hours < 24:
        remaining_minutes = minutes % 60
        return f"{hours} 小時 {remaining_minutes} 分鐘前"
    days = hours // 24
    remaining_hours = hours % 24
    return f"{days} 天 {remaining_hours} 小時前"


def check_standings_freshness(year: int) -> Dict[str, Any]:
    json_dir = Path(JSON_OUTPUT_DIR)
    if not json_dir.exists():
        return {
            "exists": False,
            "path": None,
            "age_hours": None,
            "is_fresh": False,
            "age_formatted": None,
            "should_regenerate": True,
            "reason": "JSON 目錄不存在",
        }

    pattern = f"championship_standings_{year}_*.json"
    candidates = sorted(
        json_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not candidates:
        return {
            "exists": False,
            "path": None,
            "age_hours": None,
            "is_fresh": False,
            "age_formatted": None,
            "should_regenerate": True,
            "reason": "找不到現有積分檔案",
        }

    latest_file = candidates[0]
    file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age = now - file_mtime
    age_hours = age.total_seconds() / 3600
    is_fresh = age_hours < STANDINGS_REFRESH_HOURS

    return {
        "exists": True,
        "path": str(latest_file),
        "age_hours": round(age_hours, 2),
        "age_formatted": _format_timedelta(age),
        "is_fresh": is_fresh,
        "should_regenerate": not is_fresh,
        "reason": "檔案仍在有效期內" if is_fresh else "檔案已過期",
    }


def _normalise_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _isoformat(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        if value.tzinfo is None:
            return value.tz_localize(timezone.utc).isoformat()
        return value.isoformat()
    return str(value)


def _serialize_driver_row(row: pd.Series) -> Dict[str, Any]:
    constructors = []
    ids = _normalise_list(row.get("constructorIds"))
    names = _normalise_list(row.get("constructorNames"))
    urls = _normalise_list(row.get("constructorUrls"))
    nationalities = _normalise_list(row.get("constructorNationalities"))

    for idx, constructor_id in enumerate(ids):
        constructors.append(
            {
                "constructor_id": constructor_id or None,
                "name": names[idx] if idx < len(names) else None,
                "url": urls[idx] if idx < len(urls) else None,
                "nationality": nationalities[idx] if idx < len(nationalities) else None,
            }
        )

    given = str(row.get("givenName") or "").strip()
    family = str(row.get("familyName") or "").strip()
    full_name = " ".join(part for part in (given, family) if part)

    return {
        "position": int(row.get("position") or 0),
        "position_text": str(row.get("positionText") or ""),
        "points": float(row.get("points") or 0.0),
        "wins": int(row.get("wins") or 0),
        "driver": {
            "driver_id": str(row.get("driverId") or ""),
            "code": str(row.get("driverCode") or "").upper(),
            "number": int(row.get("driverNumber")) if pd.notna(row.get("driverNumber")) else None,
            "given_name": given,
            "family_name": family,
            "full_name": full_name or None,
            "nationality": row.get("driverNationality"),
            "date_of_birth": _isoformat(row.get("dateOfBirth")),
            "url": row.get("driverUrl"),
        },
        "constructors": constructors,
    }


def _serialize_constructor_row(row: pd.Series) -> Dict[str, Any]:
    return {
        "position": int(row.get("position") or 0),
        "position_text": str(row.get("positionText") or ""),
        "points": float(row.get("points") or 0.0),
        "wins": int(row.get("wins") or 0),
        "constructor": {
            "constructor_id": row.get("constructorId"),
            "name": row.get("constructorName"),
            "nationality": row.get("constructorNationality"),
            "url": row.get("constructorUrl"),
        },
    }


def _append_deltas(entries: List[Dict[str, Any]]) -> None:
    if not entries:
        return
    leader_points = entries[0].get("points", 0.0)
    for entry in entries:
        entry["points_delta"] = round(leader_points - entry.get("points", 0.0), 3)


def generate_championship_standings(
    year: Optional[int] = None,
    *,
    round_hint: Optional[str] = "last",
    save_json: bool = True,
    include_constructors: bool = True,
    include_drivers: bool = True,
    force: bool = False,
) -> ChampionshipStandingsResult:
    target_year = int(year or datetime.now(timezone.utc).year)

    if not include_constructors and not include_drivers:
        raise ValueError("至少需要啟用車手或車隊其中一種積分")

    if not force:
        freshness = check_standings_freshness(target_year)
        if freshness.get("is_fresh"):
            print("===============================")
            print("積分資料仍在有效期內，使用既有 JSON")
            print(f"路徑: {freshness['path']}")
            print(f"年齡: {freshness['age_formatted']} ({freshness['age_hours']} 小時)")
            print("===============================")
            try:
                with open(freshness["path"], "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                metadata = payload.setdefault("metadata", {})
                metadata["last_freshness_check"] = datetime.now(timezone.utc).isoformat()
                metadata["file_age_hours"] = freshness["age_hours"]
                metadata["is_fresh"] = True
                payload["message"] = payload.get("message", "使用既有積分資料")
                return payload
            except Exception as exc:
                print(f"[STANDINGS] 讀取既有 JSON 失敗: {exc}，改為重新生成")

    client = Ergast()
    now = datetime.now(timezone.utc)

    driver_entries: List[Dict[str, Any]] = []
    constructor_entries: List[Dict[str, Any]] = []
    driver_round = None
    constructor_round = None

    if include_drivers:
        try:
            driver_resp = client.get_driver_standings(season=target_year, round=round_hint)
            if driver_resp and driver_resp.content:
                driver_df = driver_resp.content[0]
                driver_entries = [_serialize_driver_row(row) for _, row in driver_df.iterrows()]
                _append_deltas(driver_entries)
                if not driver_resp.description.empty:
                    driver_round = int(driver_resp.description.iloc[0].get("round", 0) or 0)
        except Exception as exc:
            return {
                "success": False,
                "message": f"車手積分取得失敗: {exc}",
                "data": None,
                "function_id": "97",
            }

    if include_constructors:
        try:
            constructor_resp = client.get_constructor_standings(season=target_year, round=round_hint)
            if constructor_resp and constructor_resp.content:
                constructor_df = constructor_resp.content[0]
                constructor_entries = [_serialize_constructor_row(row) for _, row in constructor_df.iterrows()]
                _append_deltas(constructor_entries)
                if not constructor_resp.description.empty:
                    constructor_round = int(constructor_resp.description.iloc[0].get("round", 0) or 0)
        except Exception as exc:
            return {
                "success": False,
                "message": f"車隊積分取得失敗: {exc}",
                "data": None,
                "function_id": "97",
            }

    if include_drivers and not driver_entries:
        return {
            "success": False,
            "message": "未取得任何車手積分資料",
            "data": None,
            "function_id": "97",
        }

    if include_constructors and not constructor_entries:
        return {
            "success": False,
            "message": "未取得任何車隊積分資料",
            "data": None,
            "function_id": "97",
        }

    resolved_round = driver_round or constructor_round or 0

    summary: Dict[str, Any] = {}
    if driver_entries:
        leader = driver_entries[0]
        driver_info = leader.get("driver", {})
        summary["top_driver"] = {
            "full_name": driver_info.get("full_name") or driver_info.get("code"),
            "points": leader.get("points"),
            "wins": leader.get("wins"),
            "constructor": leader.get("constructors", [{}])[0].get("name") if leader.get("constructors") else None,
        }
        summary["drivers_count"] = len(driver_entries)

    if constructor_entries:
        leader = constructor_entries[0]
        constructor_info = leader.get("constructor", {})
        summary["top_constructor"] = {
            "name": constructor_info.get("name"),
            "points": leader.get("points"),
            "wins": leader.get("wins"),
        }
        summary["constructors_count"] = len(constructor_entries)

    payload: ChampionshipStandingsResult = {
        "success": True,
        "message": f"{target_year} 年積分查詢完成",
        "metadata": {
            "season_year": target_year,
            "requested_round": round_hint,
            "resolved_round": resolved_round,
            "generated_at": now.isoformat(),
            "refresh_interval_hours": STANDINGS_REFRESH_HOURS,
            "include_drivers": include_drivers,
            "include_constructors": include_constructors,
            "force_regenerated": force,
        },
        "data": {
            "drivers": driver_entries,
            "constructors": constructor_entries,
        },
        "summary": summary,
    }

    if save_json:
        try:
            json_dir = _ensure_json_dir()
            round_tag = f"R{resolved_round:02d}" if resolved_round else str(round_hint or "latest")
            timestamp = now.strftime("%Y%m%dT%H%M%SZ")
            filename = json_dir / f"championship_standings_{target_year}_{round_tag}_{timestamp}.json"
            with filename.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            payload["metadata"]["output_file"] = str(filename)
        except Exception as exc:
            payload.setdefault("warnings", []).append(f"JSON export failed: {exc}")

    return payload
