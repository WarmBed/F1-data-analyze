#!/usr/bin/env python3
"""
Colour palette provider for GUI components.

The provider fetches team and driver colours through the REST API (Function 98)
and exposes helper methods returning `QColor`, hex, or RGB tuples.  When the
API is unavailable a small built-in palette is used so the GUI continues to
render charts with sensible defaults.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import requests
from PyQt5.QtGui import QColor

from core.api_base_url import resolve_api_base_url

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
    "racing bulls": ("Racing Bulls", "#FCD700"),
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
    # Racing Bulls
    "TSU": ("racing bulls", "Yuki Tsunoda"),
    "HAD": ("racing bulls", "Isack Hadjar"),
    "RIC": ("racing bulls", "Daniel Ricciardo"),
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
            print(f"[COLOR] 顏色配置載入失敗: {exc}")
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

        if entry is None:
            team_entry = self._team_palette.get(self._normalize_team_slug(driver_code))
            if team_entry:
                return self._format_entry(team_entry, format)
            return self._default_color(format) if fallback else None

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
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_from_api(self, year: int) -> Optional[Dict[str, Any]]:
        try:
            if self._base_url is None:
                self._base_url = resolve_api_base_url(
                    event_logger=lambda message: print(f"[COLOR] {message}")
                )

            response = requests.post(
                f"{self._base_url}{API_ENDPOINT}",
                params={"function_id": 98, "year": int(year)},
                headers={"Accept": "application/json"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ColorPaletteError("API response is not a JSON object")
            if not payload.get("success", False):
                raise ColorPaletteError(payload.get("message", "API returned success=False"))
            return payload
        except Exception as exc:
            print(f"[COLOR] API 請求失敗: {exc}")
            return None

    def _apply_payload(self, payload: Dict[str, Any], *, season_year: int, colormap: str) -> None:
        data = payload.get("data") or {}
        teams = data.get("teams") or {}
        drivers = data.get("drivers") or {}

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

        driver_palette: Dict[str, Dict[str, Any]] = {}
        for code, info in drivers.items():
            code_norm = self._normalize_driver_code(code)
            hex_value = str(info.get("hex") or "").strip()
            if not hex_value:
                # Fallback to team colour if hex missing
                team_slug = self._normalize_team_slug(info.get("team_slug"))
                team_entry = team_palette.get(team_slug)
                if team_entry:
                    hex_value = team_entry["hex"]
                else:
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

        if not driver_palette:
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
        return str(identifier or "").strip().lower()

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
