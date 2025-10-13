#!/usr/bin/env python3
"""Season calendar utilities backed by FastF1."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import fastf1
import pandas as pd

__all__ = ["generate_season_calendar", "SeasonCalendarResult", "check_calendar_freshness"]

FASTF1_CACHE_DIR = os.getenv("F1_ANALYSIS_FASTF1_CACHE", "f1_analysis_cache")
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")
CALENDAR_REFRESH_HOURS = 168  # 7 天 (平時維護模式) - 賽程固定除非有改期

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


def check_calendar_freshness(*, all_years: bool = True) -> Dict[str, Any]:
    """
    檢查賽季日曆 JSON 的新鮮度
    
    Args:
        all_years: 是否檢查批量日曆 (2020-2025)
        
    Returns:
        包含檢查結果的字典：
        - exists: 檔案是否存在
        - path: 檔案路徑（如果存在）
        - age_hours: 檔案年齡（小時）
        - is_fresh: 是否在刷新間隔內（<12小時）
        - should_regenerate: 是否應該重新生成
    """
    json_dir = Path(JSON_OUTPUT_DIR)
    if not json_dir.exists():
        return {
            "exists": False,
            "path": None,
            "age_hours": None,
            "is_fresh": False,
            "should_regenerate": True,
            "reason": "JSON 目錄不存在"
        }
    
    # 根據模式選擇搜尋模式
    if all_years:
        # 🔧 FIX: 更新搜尋模式以匹配新的檔案命名
        pattern = "season_calendar_multi_year_*.json"
    else:
        current_year = datetime.now().year
        pattern = f"season_calendar_{current_year}_*.json"
    
    # 尋找最新的檔案
    candidates = sorted(
        json_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not candidates:
        return {
            "exists": False,
            "path": None,
            "age_hours": None,
            "is_fresh": False,
            "should_regenerate": True,
            "reason": f"找不到匹配的 JSON 檔案 ({pattern})"
        }
    
    latest_file = candidates[0]
    file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age = now - file_mtime
    age_hours = age.total_seconds() / 3600
    
    is_fresh = age_hours < CALENDAR_REFRESH_HOURS
    
    return {
        "exists": True,
        "path": str(latest_file),
        "file_time": file_mtime.isoformat(),
        "current_time": now.isoformat(),
        "age_hours": round(age_hours, 2),
        "age_formatted": _format_age(age),
        "is_fresh": is_fresh,
        "should_regenerate": not is_fresh,
        "refresh_interval_hours": CALENDAR_REFRESH_HOURS,
        "reason": f"檔案{'新鮮' if is_fresh else '過期'}（{round(age_hours, 1)}小時前生成）"
    }


def _format_age(delta: timedelta) -> str:
    """格式化時間差為易讀字串"""
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


def generate_season_calendar(year: int = None, *, save_json: bool = True, all_years: bool = False, force: bool = False) -> SeasonCalendarResult:
    """
    Fetch and transform the FastF1 season schedule for the given year.
    
    Args:
        year: 單一年份，如果為 None 且 all_years=True，則查詢 2020-2025
        save_json: 是否儲存 JSON
        all_years: 是否查詢 2020-2025 所有年份
        force: 是否強制重新生成（忽略 12 小時智能刷新檢查）
    """

    _enable_fastf1_cache()

    # 如果啟用 all_years，查詢 2020-2025
    if all_years:
        return _generate_multi_year_calendar(save_json=save_json, force=force)
    
    # 單一年份查詢（原始邏輯）
    if year is None:
        year = datetime.now().year

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


def _generate_multi_year_calendar(*, save_json: bool = True, force: bool = False) -> SeasonCalendarResult:
    """
    查詢 2020-2025 所有年份的賽季賽程
    
    Args:
        save_json: 是否儲存 JSON
        force: 是否強制重新生成（忽略新鮮度檢查）
        
    Returns:
        包含所有年份數據的結果字典
    """
    
    # 檢查現有檔案的新鮮度（除非強制執行）
    if not force:
        freshness = check_calendar_freshness(all_years=True)
        
        if freshness["is_fresh"]:
            print(f"\n{'='*80}")
            print(f"✅ 賽季日曆檢查")
            print(f"{'='*80}")
            print(f"📄 找到最新的日曆檔案:")
            print(f"   路徑: {freshness['path']}")
            print(f"   年齡: {freshness['age_formatted']} ({freshness['age_hours']} 小時)")
            print(f"   狀態: ✅ 新鮮（< {CALENDAR_REFRESH_HOURS} 小時）")
            print(f"\n💡 提示: 檔案仍在有效期內，跳過重新生成")
            print(f"   如需強制更新，請設定 force=True")
            print(f"{'='*80}\n")
            
            # 讀取並返回現有檔案
            try:
                with open(freshness['path'], 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # 更新 metadata 中的檢查時間
                    existing_data["metadata"]["last_freshness_check"] = datetime.now(timezone.utc).isoformat()
                    existing_data["metadata"]["file_age_hours"] = freshness["age_hours"]
                    existing_data["metadata"]["is_fresh"] = True
                    existing_data["message"] = f"使用現有日曆檔案（{freshness['age_formatted']}）"
                    return existing_data
            except Exception as exc:
                print(f"⚠️  讀取現有檔案失敗: {exc}，將重新生成")
        else:
            print(f"\n{'='*80}")
            print(f"⏰ 賽季日曆需要更新")
            print(f"{'='*80}")
            if freshness["exists"]:
                print(f"📄 現有檔案:")
                print(f"   路徑: {freshness['path']}")
                print(f"   年齡: {freshness['age_formatted']} ({freshness['age_hours']} 小時)")
                print(f"   狀態: ⚠️  過期（> {CALENDAR_REFRESH_HOURS} 小時）")
            else:
                print(f"📄 狀態: 找不到現有檔案")
            print(f"\n🔄 開始重新生成日曆...")
            print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print(f"🔄 強制重新生成模式")
        print(f"{'='*80}\n")
    
    years = list(range(2020, 2026))  # 2020-2025
    all_seasons_data = {}
    total_events = 0
    total_completed = 0
    total_upcoming = 0
    
    print(f"🏎️  F1 賽季賽程批量查詢 (2020-2025)")
    print(f"{'='*80}\n")
    
    for year in years:
        try:
            print(f"📅 正在查詢 {year} 年賽季...")
            result = generate_season_calendar(year, save_json=False)
            
            if result["success"]:
                # 🔧 修復: 只存儲事件列表,避免雙層嵌套
                # 舊: all_seasons_data[str(year)] = result  ← 會導致 data['2024']['data']
                # 新: all_seasons_data[str(year)] = result["data"]  ← 直接存儲事件列表
                all_seasons_data[str(year)] = result["data"]
                total_events += result["metadata"]["total_rounds"]
                total_completed += result["metadata"]["completed_rounds"]
                total_upcoming += result["metadata"]["upcoming_rounds"]
                print(f"   ✅ 成功: {result['metadata']['total_rounds']} 場賽事 "
                      f"({result['metadata']['completed_rounds']} 已完成)")
            else:
                print(f"   ⚠️  失敗: {result['message']}")
                # 失敗時存儲空列表
                all_seasons_data[str(year)] = []
        except Exception as exc:
            print(f"   ❌ 錯誤: {exc}")
            # 錯誤時存儲空列表
            all_seasons_data[str(year)] = []
    
    # 建立總結報告
    response: SeasonCalendarResult = {
        "success": True,
        "message": f"2020-2025 年賽季賽程查詢完成",
        "metadata": {
            "years": years,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events_all_years": total_events,
            "completed_events_all_years": total_completed,
            "upcoming_events_all_years": total_upcoming,
            "cache_enabled": not fastf1.Cache.disabled,
            "refresh_interval_hours": CALENDAR_REFRESH_HOURS,
            "force_regenerated": force,
        },
        "data": all_seasons_data,
        "summary": {
            "years_covered": len(years),
            "total_events": total_events,
            "completed_events": total_completed,
            "upcoming_events": total_upcoming,
        }
    }
    
    # 儲存合併的 JSON
    if save_json:
        try:
            json_dir = _ensure_json_dir()
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            # 🔧 FIX: 移除年份範圍,避免 API 緩存匹配失敗
            # 舊: season_calendar_2020-2025_{timestamp}.json
            # 新: season_calendar_multi_year_{timestamp}.json
            filename = json_dir / f"season_calendar_multi_year_{timestamp}.json"
            with filename.open("w", encoding="utf-8") as handle:
                json.dump(response, handle, ensure_ascii=False, indent=2)
            response["metadata"]["output_file"] = str(filename)
            print(f"\n💾 JSON 已儲存: {filename}")
        except Exception as exc:
            print(f"\n⚠️  JSON 儲存失敗: {exc}")
    
    print(f"\n{'='*80}")
    print(f"📊 總結:")
    print(f"   • 總賽事數: {total_events}")
    print(f"   • 已完成: {total_completed}")
    print(f"   • 未來賽事: {total_upcoming}")
    print(f"{'='*80}\n")
    
    return response