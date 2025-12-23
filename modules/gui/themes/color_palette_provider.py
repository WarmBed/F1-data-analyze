#!/usr/bin/env python3
"""
Colour palette provider for GUI components.

The provider fetches team and driver colours through the REST API (Function 98)
and exposes helper methods returning `QColor`, hex, or RGB tuples.  When the
API is unavailable a small built-in palette is used so the GUI continues to
render charts with sensible defaults.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from PyQt5.QtGui import QColor

from core.api_base_url import resolve_api_base_url
from core.logger import get_logger

# ✅ 手動覆寫配置檔路徑（與 CLI 模組共用）
DRIVER_OVERRIDES_PATH = Path("config/driver_team_overrides.json")

API_ENDPOINT = "/api/v2/analysis/execute"
DEFAULT_TIMEOUT = 20.0

DEFAULT_TEAM_HEX: Dict[str, Tuple[str, str]] = {
    "red bull": ("Red Bull", "#0600EF"),
    "ferrari": ("Ferrari", "#E80020"),
    "mercedes": ("Mercedes", "#27F4D2"),
    "mclaren": ("McLaren", "#FF8000"),
    "aston martin": ("Aston Martin", "#00665F"),
    "alpine": ("Alpine", "#FF87BC"),
    "haas": ("Haas", "#B6BABD"),
    "rb": ("RB", "#364AA9"),
    "kick sauber": ("Kick Sauber", "#00E700"),
    "williams": ("Williams", "#00A0DD"),
}

DEFAULT_DRIVER_MAP: Dict[str, Tuple[str, str]] = {
    # Red Bull Racing
    "VER": ("red bull", "Max Verstappen"),
    "LAW": ("red bull", "Liam Lawson"),
    "PER": ("red bull", "Sergio Perez"),
    # Ferrari
    "LEC": ("ferrari", "Charles Leclerc"),
    "HAM": ("ferrari", "Lewis Hamilton"),
    # Mercedes
    "RUS": ("mercedes", "George Russell"),
    "ANT": ("mercedes", "Andrea Kimi Antonelli"),
    "KIM": ("mercedes", "Kimi Antonelli"),  # FastF1 別名（簡稱版本）
    # McLaren
    "NOR": ("mclaren", "Lando Norris"),
    "PIA": ("mclaren", "Oscar Piastri"),
    # Aston Martin
    "ALO": ("aston martin", "Fernando Alonso"),
    "STR": ("aston martin", "Lance Stroll"),
    # Alpine
    "GAS": ("alpine", "Pierre Gasly"),
    "COL": ("alpine", "Franco Colapinto"),
    "DOO": ("alpine", "Jack Doohan"),
    # Haas
    "OCO": ("haas", "Esteban Ocon"),
    "BEA": ("haas", "Oliver Bearman"),
    "MAG": ("haas", "Kevin Magnussen"),
    # Racing Bulls (RB)
    "TSU": ("rb", "Yuki Tsunoda"),
    "HAD": ("rb", "Isack Hadjar"),
    "RIC": ("rb", "Daniel Ricciardo"),
    # Kick Sauber / Audi
    "BOR": ("kick sauber", "Gabriel Bortoleto"),
    "HUL": ("kick sauber", "Nico Hülkenberg"),
    "BOT": ("kick sauber", "Valtteri Bottas"),
    "ZHO": ("kick sauber", "Zhou Guanyu"),
    # Williams
    "ALB": ("williams", "Alexander Albon"),
    "SAI": ("williams", "Carlos Sainz"),
    "SAR": ("williams", "Logan Sargeant"),
}

DEFAULT_HEX = "#808080"
DEFAULT_RGB = (128, 128, 128)


logger = get_logger(__name__)


class ColorPaletteError(RuntimeError):
    """Raised when the colour palette cannot be fetched from the API."""


class ColorPaletteProvider:
    """Fetches and caches colour information for teams and drivers."""

    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._base_url: Optional[str] = None
        self._team_palette: Dict[str, Dict[str, Any]] = {}
        self._driver_palette: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Any] = {}
        self._loaded_year: Optional[int] = None
        self._loaded_colormap: str = "fastf1"
        self._last_error: Optional[str] = None
        self._defaults_applied: bool = False
        self._allow_defaults: bool = self._resolve_fallback_policy()
        # 車手車隊映射緩存 (從 Driver Standings 或 CLI JSON 更新)
        self._driver_team_map: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ensure_loaded(
        self,
        *,
        year: Optional[int] = None,
        colormap: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """Ensure colour data is available for the requested season."""

        target_year = int(year or datetime.now(timezone.utc).year)
        colormap = (colormap or self._loaded_colormap or "fastf1").lower()

        if (
            not force
            and self._driver_palette
            and self._team_palette
            and self._loaded_year == target_year
            and self._loaded_colormap == colormap
        ):
            return

        try:
            payload = self._fetch_from_api(target_year)
            if payload is None:
                raise ColorPaletteError("API response is empty")
            self._apply_payload(payload, season_year=target_year, colormap=colormap)
            self._last_error = None
        except Exception as exc:  # pragma: no cover - defensive path
            self._last_error = str(exc)
            logger.exception("[COLOR] 顏色配置載入失敗: %s", exc)
            if not self._driver_palette or not self._team_palette:
                if self._allow_defaults:
                    self._apply_defaults(season_year=target_year, colormap=colormap)
                else:
                    raise ColorPaletteError("API 請求失敗且已禁用預設色票") from exc

    def get_driver_color(
        self,
        driver_code: str,
        *,
        format: str = "qcolor",
        fallback: bool = True,
    ) -> Optional[Any]:
        """Return the colour for the specified driver."""

        if not driver_code:
            return self._default_color(format) if fallback else None

        code = self._normalize_driver_code(driver_code)
        entry = self._driver_palette.get(code)

        if entry is None and fallback:
            # 嘗試從 DEFAULT_DRIVER_MAP 獲取車隊顏色
            if code in DEFAULT_DRIVER_MAP:
                team_slug, _ = DEFAULT_DRIVER_MAP[code]
                team_entry = self._team_palette.get(team_slug)
                if team_entry:
                    return self._format_entry(team_entry, format)
            
            # 最後嘗試用 driver_code 作為車隊名稱
            team_entry = self._team_palette.get(self._normalize_team_slug(driver_code))
            if team_entry:
                return self._format_entry(team_entry, format)
            
            return self._default_color(format)
        
        if entry is None:
            return None

        return self._format_entry(entry, format)

    def get_team_color(
        self,
        team_identifier: str,
        *,
        format: str = "qcolor",
        fallback: bool = True,
    ) -> Optional[Any]:
        """Return the colour for the specified team slug or display name."""

        if not team_identifier:
            return self._default_color(format) if fallback else None

        slug = self._normalize_team_slug(team_identifier)
        entry = self._team_palette.get(slug)
        if entry is None and fallback:
            return self._default_color(format)
        if entry is None:
            return None
        return self._format_entry(entry, format)

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about the currently loaded palette."""

        return dict(self._metadata)

    def last_error(self) -> Optional[str]:
        """Return the last error encountered while loading colours."""

        return self._last_error

    def allow_default_palette(self) -> bool:
        """Return whether the built-in fallback palette is permitted."""

        return self._allow_defaults

    def set_allow_default_palette(self, allowed: bool) -> None:
        """Enable or disable the built-in fallback palette at runtime."""

        self._allow_defaults = bool(allowed)

    # ------------------------------------------------------------------
    # Driver Team Mapping API (2025-12-14 新增)
    # ------------------------------------------------------------------
    def get_driver_team(self, driver_code: str, *, fallback: bool = True) -> Optional[str]:
        """
        返回車手所屬車隊的顯示名稱
        
        Args:
            driver_code: 車手代碼 (如 "VER", "TSU")
            fallback: 如果找不到是否返回預設值
            
        Returns:
            車隊顯示名稱 (如 "Red Bull Racing", "McLaren")
            如果找不到且 fallback=True 返回 "Unknown"
            如果找不到且 fallback=False 返回 None
        """
        if not driver_code:
            return "Unknown" if fallback else None
        
        code = self._normalize_driver_code(driver_code)
        
        # 優先級 1: 從動態映射獲取 (Driver Standings / CLI JSON)
        if code in self._driver_team_map:
            return self._driver_team_map[code]
        
        # 優先級 2: 從 DEFAULT_DRIVER_MAP 靜態映射獲取
        if code in DEFAULT_DRIVER_MAP:
            team_slug, _ = DEFAULT_DRIVER_MAP[code]
            # 轉換 slug 為顯示名稱
            team_display = DEFAULT_TEAM_HEX.get(team_slug, (team_slug.title(), "#808080"))[0]
            return team_display
        
        return "Unknown" if fallback else None
    
    def update_driver_teams_from_standings(self, standings_data: Dict[str, Any]) -> int:
        """
        從 Driver Standings JSON (F99) 更新車手車隊映射
        
        Args:
            standings_data: Driver Standings API 返回的數據
            格式: {"data": {"drivers": [{"driver": {"code": "VER"}, "constructors": [{"name": "Red Bull Racing"}]}]}}
            
        Returns:
            更新的車手數量
        """
        count = 0
        try:
            data = standings_data.get("data", standings_data)
            drivers = data.get("drivers", [])
            
            for entry in drivers:
                driver_info = entry.get("driver", {})
                code = driver_info.get("code")
                constructors = entry.get("constructors", [])
                
                if code and constructors:
                    # 取第一個 constructor 的名稱
                    team_name = constructors[0].get("name", "Unknown")
                    normalized_code = self._normalize_driver_code(code)
                    self._driver_team_map[normalized_code] = team_name
                    count += 1
            
            if count > 0:
                logger.info("[COLOR] 從 Driver Standings 更新 %d 位車手的車隊映射", count)
        except Exception as exc:
            logger.warning("[COLOR] 解析 Driver Standings 失敗: %s", exc)
        
        return count
    
    def update_driver_teams_from_json(self, json_data: Dict[str, Any]) -> int:
        """
        從 CLI JSON (F48/F121/F122 等) 更新車手車隊映射
        
        Args:
            json_data: CLI 分析結果 JSON
            格式: {"data": {"drivers": [{"driver": "VER", "team": "Red Bull Racing"}]}}
            或: {"data": {"driver_speeds": [{"driver": "VER", "team": "Red Bull Racing"}]}}
            
        Returns:
            更新的車手數量
        """
        count = 0
        try:
            data = json_data.get("data", json_data)
            
            # 嘗試多種可能的數據結構
            drivers_list = (
                data.get("drivers") or 
                data.get("driver_speeds") or 
                data.get("driver_data") or
                []
            )
            
            for entry in drivers_list:
                code = entry.get("driver")
                team = entry.get("team")
                
                if code and team:
                    normalized_code = self._normalize_driver_code(code)
                    self._driver_team_map[normalized_code] = team
                    count += 1
            
            if count > 0:
                logger.debug("[COLOR] 從 JSON 更新 %d 位車手的車隊映射", count)
        except Exception as exc:
            logger.warning("[COLOR] 解析 JSON 失敗: %s", exc)
        
        return count
    
    def get_driver_team_map(self) -> Dict[str, str]:
        """返回當前的車手車隊映射副本"""
        return dict(self._driver_team_map)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_from_api(self, year: int) -> Optional[Dict[str, Any]]:
        try:
            if self._base_url is None:
                self._base_url = resolve_api_base_url(
                    event_logger=lambda message: logger.info("[COLOR] %s", message)
                )

            # ✅ 修復: 使用 URL 參數（與其他模組一致）
            response = requests.post(
                f"{self._base_url}{API_ENDPOINT}",
                params={"function_id": 98, "year": int(year)},
                headers={"Accept": "application/json"},
                timeout=self._timeout,
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ColorPaletteError("API response is not a JSON object")
            if not payload.get("success", False):
                raise ColorPaletteError(payload.get("message", "API returned success=False"))
            return payload
        except Exception as exc:
            logger.exception("[COLOR] API 請求失敗: %s", exc)
            return None

    def _apply_payload(self, payload: Dict[str, Any], *, season_year: int, colormap: str) -> None:
        # ✅ 修復: API 返回嵌套結構 data.data.teams（而非 data.teams）
        outer_data = payload.get("data") or {}
        inner_data = outer_data.get("data") or outer_data  # 兼容舊格式
        teams = inner_data.get("teams") or {}
        drivers = inner_data.get("drivers") or {}

        # ✅ 調試日誌：顯示 API 回應摘要
        logger.info("[COLOR] 📋 API 回應摘要: teams=%s, drivers=%s", len(teams), len(drivers))
        if teams:
            logger.info(
                "[COLOR] 📋 車隊列表: %s%s",
                list(teams.keys())[:5],
                "..." if len(teams) > 5 else "",
            )
        if drivers:
            logger.info(
                "[COLOR] 📋 車手列表: %s%s",
                list(drivers.keys())[:10],
                "..." if len(drivers) > 10 else "",
            )

        team_palette: Dict[str, Dict[str, Any]] = {}
        for slug, info in teams.items():
            slug_norm = self._normalize_team_slug(slug)
            selected_hex = self._select_hex_value(info)
            if not selected_hex:
                continue
            rgb = self._ensure_rgb(info.get("selected_rgb"), selected_hex)
            qcolor = self._make_qcolor(selected_hex)
            team_palette[slug_norm] = {
                "hex": selected_hex,
                "rgb": rgb,
                "qcolor": qcolor,
                "team_slug": slug_norm,
                "team_name": info.get("team_name") or info.get("team_title") or slug.title(),
            }

        logger.info("[COLOR] 📋 車隊處理完成: team_palette=%s 個車隊", len(team_palette))

        driver_palette: Dict[str, Dict[str, Any]] = {}
        processed_count = 0
        skipped_count = 0
        
        for code, info in drivers.items():
            code_norm = self._normalize_driver_code(code)
            hex_value = str(info.get("hex") or "").strip()
            if not hex_value:
                # Fallback to team colour if hex missing
                team_slug = self._normalize_team_slug(info.get("team_slug"))
                team_entry = team_palette.get(team_slug)
                if team_entry:
                    hex_value = team_entry["hex"]
                    logger.info("[COLOR] 💡 車手 %s 使用車隊顏色: team_slug='%s' → %s", code, team_slug, hex_value)
                else:
                    logger.warning("[COLOR] ⚠️  車手 %s 跳過: team_slug='%s' 在 team_palette 中找不到", code, team_slug)
                    logger.info("[COLOR] 📋 可用車隊: %s", list(team_palette.keys())[:5])
                    skipped_count += 1
                    continue
            rgb = self._ensure_rgb(info.get("rgb"), hex_value)
            qcolor = self._make_qcolor(hex_value)
            team_slug = self._normalize_team_slug(info.get("team_slug"))
            team_name = info.get("team_name")
            if not team_name and team_slug in team_palette:
                team_name = team_palette[team_slug]["team_name"]

            driver_palette[code_norm] = {
                "hex": hex_value,
                "rgb": rgb,
                "qcolor": qcolor,
                "team_slug": team_slug,
                "team_name": team_name,
                "driver_id": info.get("driver_id"),
                "full_name": info.get("full_name") or code_norm,
            }
            processed_count += 1

        # ✅ 調試日誌：顯示處理結果
        logger.info(
            "[COLOR] 📊 車手處理完成: 成功=%s, 跳過=%s, driver_palette=%s",
            processed_count,
            skipped_count,
            len(driver_palette),
        )

        if not driver_palette:
            # ✅ 提供詳細的錯誤診斷資訊
            logger.error("[COLOR] ❌ driver_palette 為空！")
            logger.info("[COLOR] 📋 原始 teams 鍵: %s", list(teams.keys()))
            logger.info("[COLOR] 📋 原始 drivers 鍵: %s", list(drivers.keys()))
            logger.info("[COLOR] 📋 team_palette 鍵: %s", list(team_palette.keys()))
            raise ColorPaletteError("API payload did not contain driver colour information")

        self._team_palette = team_palette
        self._driver_palette = driver_palette
        self._metadata = dict(payload.get("metadata") or {})
        self._metadata.setdefault("season_year", season_year)
        self._metadata.setdefault("colormap", colormap)
        self._metadata.setdefault("source", "api")
        self._loaded_year = season_year
        self._loaded_colormap = colormap
        self._defaults_applied = False
        
        # ✅ 套用手動覆寫（最高優先級）
        self._apply_driver_overrides(season_year)

    def _apply_driver_overrides(self, season_year: int) -> None:
        """
        套用車手-車隊手動覆寫（GUI 版本）
        
        Args:
            season_year: 賽季年份
        """
        if not DRIVER_OVERRIDES_PATH.exists():
            return
        
        try:
            with open(DRIVER_OVERRIDES_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            year_str = str(season_year)
            year_overrides = config.get("overrides", {}).get(year_str, {})
            
            override_count = 0
            for code, data in year_overrides.items():
                if code.startswith("_"):  # 跳過註解欄位
                    continue
                
                if not isinstance(data, dict):
                    continue
                    
                if not data.get("enabled", False):
                    continue
                
                code_upper = self._normalize_driver_code(code)
                
                # ✅ 檢查車手是否存在於調色盤
                if code_upper not in self._driver_palette:
                    # 新增車手（季中替補）
                    team_slug = self._normalize_team_slug(data.get("team_slug", ""))
                    team_entry = self._team_palette.get(team_slug)
                    
                    if not team_entry:
                        logger.warning("[GUI_OVERRIDE] ⚠️  跳過 %s: 車隊 '%s' 不存在", code_upper, team_slug)
                        continue
                    
                    self._driver_palette[code_upper] = {
                        "hex": team_entry["hex"],
                        "rgb": team_entry["rgb"],
                        "qcolor": team_entry["qcolor"],
                        "team_slug": team_slug,
                        "team_name": data.get("team_name", team_entry["team_name"]),
                        "driver_id": data.get("driver_id", code_upper.lower()),
                        "full_name": data.get("full_name", code_upper),
                    }
                    logger.info(
                        "[GUI_OVERRIDE] ➕ 新增車手: %s → %s (%s)",
                        code_upper,
                        data.get('team_name'),
                        data.get('reason', 'N/A'),
                    )
                    override_count += 1
                else:
                    # 更新現有車手的車隊資訊
                    original_team = self._driver_palette[code_upper].get("team_name", "Unknown")
                    new_team_slug = self._normalize_team_slug(data.get("team_slug", ""))
                    new_team_entry = self._team_palette.get(new_team_slug)
                    
                    if not new_team_entry:
                        logger.warning("[GUI_OVERRIDE] ⚠️  跳過 %s: 車隊 '%s' 不存在", code_upper, new_team_slug)
                        continue
                    
                    self._driver_palette[code_upper].update({
                        "hex": new_team_entry["hex"],
                        "rgb": new_team_entry["rgb"],
                        "qcolor": new_team_entry["qcolor"],
                        "team_slug": new_team_slug,
                        "team_name": data.get("team_name", new_team_entry["team_name"]),
                    })
                    logger.info(
                        "[GUI_OVERRIDE] 🔄 更新車手: %s: %s → %s (%s)",
                        code_upper,
                        original_team,
                        data.get('team_name'),
                        data.get('reason', 'N/A'),
                    )
                    override_count += 1
            
            if override_count > 0:
                logger.info("[GUI_OVERRIDE] ✅ 共套用 %s 個車手覆寫（%s 賽季）", override_count, season_year)
                self._metadata["overrides_applied"] = override_count
                self._metadata["overrides_source"] = str(DRIVER_OVERRIDES_PATH)
            
        except Exception as e:
            logger.exception("[GUI_OVERRIDE] ⚠️  載入覆寫配置失敗: %s", e)
    
    def _apply_defaults(self, *, season_year: int, colormap: str) -> None:
        if not self._allow_defaults:
            raise ColorPaletteError("預設色票已被禁用，無法套用")
        team_palette: Dict[str, Dict[str, Any]] = {}
        for slug, (team_name, hex_value) in DEFAULT_TEAM_HEX.items():
            rgb = self._hex_to_rgb(hex_value)
            team_palette[slug] = {
                "hex": hex_value,
                "rgb": rgb,
                "qcolor": self._make_qcolor(hex_value),
                "team_slug": slug,
                "team_name": team_name,
            }

        driver_palette: Dict[str, Dict[str, Any]] = {}
        for code, (team_slug, driver_name) in DEFAULT_DRIVER_MAP.items():
            team_entry = team_palette.get(team_slug)
            if not team_entry:
                continue
            driver_palette[code] = {
                "hex": team_entry["hex"],
                "rgb": team_entry["rgb"],
                "qcolor": self._make_qcolor(team_entry["hex"]),
                "team_slug": team_slug,
                "team_name": team_entry["team_name"],
                "driver_id": None,
                "full_name": driver_name or code,
            }

        self._team_palette = team_palette
        self._driver_palette = driver_palette
        self._metadata = {
            "season_year": season_year,
            "colormap": colormap,
            "source": "defaults",
        }
        self._loaded_year = season_year
        self._loaded_colormap = colormap
        self._defaults_applied = True

    def _select_hex_value(self, info: Dict[str, Any]) -> Optional[str]:
        for key in ("selected_hex", "fastf1_hex", "official_hex"):
            value = info.get(key)
            if value:
                text = str(value).strip()
                if text:
                    if not text.startswith("#"):
                        text = f"#{text}"
                    return text.upper()
        return None

    def _ensure_rgb(self, candidate: Any, hex_value: str) -> Tuple[int, int, int]:
        if isinstance(candidate, (list, tuple)) and len(candidate) == 3:
            try:
                r, g, b = int(candidate[0]), int(candidate[1]), int(candidate[2])
                return (r, g, b)
            except (TypeError, ValueError):
                pass
        rgb = self._hex_to_rgb(hex_value)
        return rgb or DEFAULT_RGB

    @staticmethod
    def _hex_to_rgb(hex_value: str) -> Optional[Tuple[int, int, int]]:
        if not hex_value:
            return None
        text = hex_value.lstrip("#")
        if len(text) != 6:
            return None
        try:
            return tuple(int(text[i : i + 2], 16) for i in range(0, 6, 2))
        except ValueError:
            return None

    @staticmethod
    def _make_qcolor(hex_value: str) -> QColor:
        return QColor(hex_value) if hex_value else QColor(*DEFAULT_RGB)

    @staticmethod
    def _normalize_driver_code(code: str) -> str:
        return str(code or "").strip().upper()

    @staticmethod
    def _normalize_team_slug(identifier: str) -> str:
        """正規化車隊名稱為小寫 slug，移除常見後綴"""
        normalized = str(identifier or "").strip().lower()
        
        # 移除常見後綴
        suffixes_to_remove = [
            " f1 team",
            " racing",
            " f1",
        ]
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        return normalized

    def _format_entry(self, entry: Dict[str, Any], format: str) -> Any:
        fmt = (format or "qcolor").lower()
        if fmt == "hex":
            return entry.get("hex")
        if fmt == "rgb":
            return tuple(entry.get("rgb") or DEFAULT_RGB)
        if fmt == "qcolor":
            color = entry.get("qcolor")
            return QColor(color) if isinstance(color, QColor) else QColor(*DEFAULT_RGB)
        raise ValueError(f"Unsupported colour format '{format}'")

    def _default_color(self, format: str) -> Any:
        fmt = (format or "qcolor").lower()
        if fmt == "hex":
            return DEFAULT_HEX
        if fmt == "rgb":
            return DEFAULT_RGB
        if fmt == "qcolor":
            return QColor(*DEFAULT_RGB)
        raise ValueError(f"Unsupported colour format '{format}'")

    @staticmethod
    def _resolve_fallback_policy() -> bool:
        env_value = os.getenv("F1T_COLOR_PALETTE_ALLOW_FALLBACK")
        if env_value is None:
            return True
        normalized = str(env_value).strip().lower()
        return normalized in {"1", "true", "yes", "on"}


# Module-level singleton used by GUI components.
color_palette_provider = ColorPaletteProvider()

__all__ = ["ColorPaletteError", "ColorPaletteProvider", "color_palette_provider"]
