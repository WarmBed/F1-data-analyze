#!/usr/bin/env python3
"""
Utilities for exporting F1 team and driver colour palettes.

This module reads the FastF1 plotting season constants to build a canonical
colour table for teams (and, optionally, drivers) for a target season.  The
result mirrors the structure used by season_calendar_analysis so it can be
consumed by both the CLI and the API bridge.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

from fastf1.ergast import Ergast
from fastf1.plotting._constants import Constants as SEASON_CONSTANTS


__all__ = ["generate_team_color_report", "check_color_freshness"]

JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")
SUPPORTED_SEASONS = sorted(int(year) for year in SEASON_CONSTANTS.keys())
DEFAULT_COLORMAP = "fastf1"
COLOR_REFRESH_HOURS = 168  # 7 天 (平時維護模式) - 顏色配置整季不變


def _ensure_json_dir() -> Path:
    path = Path(JSON_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def check_color_freshness(year: int, colormap: str = "fastf1") -> Dict[str, Any]:
    """
    檢查顏色配置 JSON 的新鮮度
    
    Args:
        year: 賽季年份
        colormap: 顏色映射類型 ("fastf1" 或 "official")
        
    Returns:
        包含檢查結果的字典：
        - exists: 檔案是否存在
        - path: 檔案路徑（如果存在）
        - age_hours: 檔案年齡（小時）
        - is_fresh: 是否新鮮（< COLOR_REFRESH_HOURS）
        - age_formatted: 格式化的年齡字串
    """
    
    json_dir = Path(JSON_OUTPUT_DIR)
    if not json_dir.exists():
        return {
            "exists": False,
            "path": None,
            "age_hours": None,
            "is_fresh": False,
            "age_formatted": None,
        }
    
    # 搜尋匹配的檔案（最新的）
    pattern = f"team_colors_{year}_{colormap}_*.json"
    matching_files = sorted(json_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not matching_files:
        return {
            "exists": False,
            "path": None,
            "age_hours": None,
            "is_fresh": False,
            "age_formatted": None,
        }
    
    latest_file = matching_files[0]
    file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age = now - file_mtime
    age_hours = age.total_seconds() / 3600
    
    # 格式化年齡顯示
    if age_hours < 1:
        age_formatted = f"{int(age.total_seconds() / 60)} 分鐘"
    elif age_hours < 24:
        age_formatted = f"{age_hours:.1f} 小時"
    else:
        age_formatted = f"{age_hours / 24:.1f} 天"
    
    return {
        "exists": True,
        "path": str(latest_file),
        "age_hours": age_hours,
        "is_fresh": age_hours < COLOR_REFRESH_HOURS,
        "age_formatted": age_formatted,
    }


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid hex colour '{value}'")
    return tuple(int(value[i : i + 2], 16) for i in range(0, 6, 2))


def _resolve_season(year: Optional[int]) -> int:
    if year is None:
        year = datetime.now().year
    candidates = [season for season in SUPPORTED_SEASONS if season <= year]
    if not candidates:
        return SUPPORTED_SEASONS[-1]
    return candidates[-1]


def _normalise_team_key(name: str) -> str:
    return (
        name.replace("grand prix", "")
        .replace("formula one team", "")
        .replace("f1 team", "")
        .replace("team", "")
        .replace("racing", "")
        .replace("scuderia", "")
        .replace("factory", "")
        .replace("stake", "")
        .strip()
        .lower()
    )


def _build_team_alias_map(season_teams: Dict[str, Any]) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    extra_aliases = {
        "visa cash app rb": "racing bulls",
        "visa cash app rb formula one": "racing bulls",
        "rb": "racing bulls",
        "alphatauri": "racing bulls",
        "alpha tauri": "racing bulls",
        "stake f1 kick sauber": "kick sauber",
        "sauber": "kick sauber",
        "kick sauber": "kick sauber",
        "aston martin aramco": "aston martin",
        "mercedes amg": "mercedes",
        "mercedes-amg": "mercedes",
        "red bull racing": "red bull",
        "red bull racing honda rbpt": "red bull",
    }

    for slug, team in season_teams.items():
        slug_norm = _normalise_team_key(slug)
        aliases[slug_norm] = slug

        short_name = getattr(team, "ShortName", "")
        if short_name:
            aliases[_normalise_team_key(short_name)] = slug

    for alias, target in extra_aliases.items():
        aliases[alias] = target

    return aliases


def _resolve_team_slug(name: str, alias_map: Dict[str, str]) -> Optional[str]:
    key = _normalise_team_key(name)
    if key in alias_map:
        return alias_map[key]

    # try progressive truncation (e.g. "aston martin aramco f1" -> "aston martin")
    parts = key.split()
    while len(parts) > 1:
        parts.pop()
        joined = " ".join(parts)
        if joined in alias_map:
            return alias_map[joined]

    return None


def _fetch_driver_mapping(year: int, alias_map: Dict[str, str]) -> Tuple[Optional[int], Dict[str, Dict[str, str]]]:
    earliest = SUPPORTED_SEASONS[0]
    candidate_years: Iterable[int] = range(year, earliest - 1, -1)
    ergast = Ergast()

    for candidate in candidate_years:
        try:
            response = ergast.get_driver_standings(season=candidate, round="last")
        except Exception:
            continue

        content = getattr(response, "content", None)
        if not content:
            continue

        standings = content[0]
        if standings.empty:
            continue

        mapping: Dict[str, Dict[str, str]] = {}
        for _, row in standings.iterrows():
            constructor_list = row.get("constructorNames")
            if isinstance(constructor_list, (list, tuple)) and constructor_list:
                constructor = constructor_list[0]
            else:
                constructor = constructor_list

            if not constructor:
                continue

            slug = _resolve_team_slug(str(constructor), alias_map)
            if not slug:
                continue

            driver_code = row.get("driverCode")
            if not isinstance(driver_code, str) or not driver_code.strip():
                family = str(row.get("familyName", "")).strip()
                driver_code = (family[:3] or "UNK").upper()
            else:
                driver_code = driver_code.strip().upper()

            given = str(row.get("givenName", "")).strip()
            family = str(row.get("familyName", "")).strip()
            full_name = " ".join(part for part in (given, family) if part)

            mapping[driver_code] = {
                "team_slug": slug,
                "full_name": full_name or driver_code,
                "driver_id": str(row.get("driverId", driver_code)),
            }

        if mapping:
            return candidate, mapping

    return None, {}


def generate_team_color_report(
    year: Optional[int] = None,
    *,
    colormap: str = DEFAULT_COLORMAP,
    save_json: bool = True,
    include_drivers: bool = True,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Build a colour table for the requested season.

    Args:
        year: Target season. Falls back to the latest supported season if the
            requested year is not available in FastF1 constants.
        colormap: ``"fastf1"`` (default) or ``"official"``. Controls which hex
            code is exposed as the primary value.
        save_json: When True (default) the result is persisted under
            ``JSON_OUTPUT_DIR`` with a timestamped filename.
        include_drivers: When True (default) driver colours are included by
            mapping the latest available driver standings from Ergast onto the
            season team palette.
        force: When True, force regeneration regardless of file freshness.

    Returns:
        Dictionary containing success flag, metadata and colour tables.
    """

    colormap = (colormap or DEFAULT_COLORMAP).lower()
    if colormap not in {"fastf1", "official"}:
        raise ValueError(f"Unsupported colormap '{colormap}' (expected 'fastf1' or 'official')")

    season_year = _resolve_season(year)
    
    # 檢查現有檔案的新鮮度（除非強制執行）
    if not force:
        freshness = check_color_freshness(season_year, colormap)
        
        if freshness["is_fresh"]:
            print(f"\n{'='*80}")
            print(f"✅ 顏色配置檢查")
            print(f"{'='*80}")
            print(f"📄 找到最新的配置檔案:")
            print(f"   路徑: {freshness['path']}")
            print(f"   年齡: {freshness['age_formatted']} ({freshness['age_hours']:.1f} 小時)")
            print(f"   狀態: ✅ 新鮮（< {COLOR_REFRESH_HOURS} 小時）")
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
                    existing_data["message"] = f"{season_year} 顏色配置（使用現有檔案，{freshness['age_formatted']}）"
                    return existing_data
            except Exception as exc:
                print(f"⚠️  讀取現有檔案失敗: {exc}，將重新生成")
        else:
            print(f"\n{'='*80}")
            print(f"⏰ 顏色配置需要更新")
            print(f"{'='*80}")
            if freshness["exists"]:
                print(f"📄 現有檔案:")
                print(f"   路徑: {freshness['path']}")
                print(f"   年齡: {freshness['age_formatted']} ({freshness['age_hours']:.1f} 小時)")
                print(f"   狀態: ⚠️  過期（> {COLOR_REFRESH_HOURS} 小時）")
            else:
                print(f"📄 狀態: 找不到現有檔案")
            print(f"\n🔄 開始重新生成配置...")
            print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print(f"🔄 強制重新生成模式")
        print(f"{'='*80}\n")

    season_constants = SEASON_CONSTANTS[str(season_year)]
    season_teams = season_constants.Teams
    alias_map = _build_team_alias_map(season_teams)

    team_payload: Dict[str, Dict[str, Any]] = {}
    for slug, team in season_teams.items():
        fastf1_hex = str(team.TeamColor.FastF1).upper()
        official_hex = str(team.TeamColor.Official).upper()

        team_payload[slug] = {
            "team_name": team.ShortName,
            "selected_hex": fastf1_hex if colormap == "fastf1" else official_hex,
            "fastf1_hex": fastf1_hex,
            "official_hex": official_hex,
            "fastf1_rgb": _hex_to_rgb(fastf1_hex),
            "official_rgb": _hex_to_rgb(official_hex),
        }

    driver_payload: Dict[str, Dict[str, Any]] = {}
    driver_source_year: Optional[int] = None

    if include_drivers:
        driver_source_year, mapping = _fetch_driver_mapping(season_year, alias_map)
        for code, info in mapping.items():
            team_slug = info["team_slug"]
            team_info = team_payload.get(team_slug)
            if not team_info:
                continue

            selected_hex = team_info["selected_hex"]
            driver_payload[code] = {
                "full_name": info["full_name"],
                "driver_id": info["driver_id"],
                "team_slug": team_slug,
                "team_name": team_info["team_name"],
                "hex": selected_hex,
                "rgb": _hex_to_rgb(selected_hex),
            }

    timestamp = datetime.now(timezone.utc).isoformat()

    result: Dict[str, Any] = {
        "success": True,
        "message": f"{season_year} 顏色配置生成完成",
        "metadata": {
            "requested_year": year,
            "season_year": season_year,
            "colormap": colormap,
            "generated_at": timestamp,
            "teams_count": len(team_payload),
            "drivers_included": include_drivers and bool(driver_payload),
            "driver_source_year": driver_source_year,
            "refresh_interval_hours": COLOR_REFRESH_HOURS,
            "force_regenerated": force,
        },
        "data": {
            "teams": team_payload,
            "drivers": driver_payload,
        },
        "summary": {
            "teams": list(team_payload.keys()),
            "drivers": sorted(driver_payload.keys()),
        },
    }

    if save_json:
        try:
            json_dir = _ensure_json_dir()
            filename = (
                json_dir
                / f"team_colors_{season_year}_{colormap}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
            )
            with filename.open("w", encoding="utf-8") as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2)
            result["metadata"]["output_file"] = str(filename)
        except Exception as exc:  # pragma: no cover - best effort only
            result.setdefault("warnings", []).append(f"JSON export failed: {exc}")

    return result
