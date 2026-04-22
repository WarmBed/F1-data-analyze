"""Requests-compatible local bridge for GUI analysis calls.

This module intentionally implements only the small subset of ``requests`` used
by GUI loaders. Calls to the local analysis endpoint are executed in-process via
the local executor. Other URLs are delegated to the real ``requests`` package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests as _real_requests

from core.local_analysis_client import execute_analysis_sync
from core.runtime_mode import is_local_first


exceptions = _real_requests.exceptions


@dataclass
class LocalResponse:
    payload: Dict[str, Any]
    status_code: int = 200
    url: str = "local://analysis"

    @property
    def text(self) -> str:
        return str(self.payload)

    def json(self) -> Dict[str, Any]:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise _real_requests.HTTPError(f"HTTP {self.status_code}: {self.url}")

    def close(self) -> None:
        return None


def _is_local_analysis_execute(url: str) -> bool:
    parsed = urlparse(str(url))
    return parsed.path.endswith("/api/v2/analysis/execute")


def _extract_function_id(params: Optional[Dict[str, Any]], json_body: Optional[Dict[str, Any]]) -> Any:
    source = params or json_body or {}
    function_id = source.get("function_id") or source.get("function") or source.get("f")
    if function_id in (None, ""):
        raise ValueError("function_id is required for local analysis execution")
    return function_id


def _extract_params(params: Optional[Dict[str, Any]], json_body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    if json_body:
        merged.update(json_body)
    if params:
        merged.update(params)
    merged.pop("function_id", None)
    merged.pop("function", None)
    merged.pop("f", None)
    nested_parameters = merged.pop("parameters", None)
    if isinstance(nested_parameters, dict):
        local_params = dict(nested_parameters)
        local_params.update(merged)
        return local_params
    return merged


def _fallback_color_payload(year: Any = None, colormap: str = "fastf1") -> Dict[str, Any]:
    teams = {
        "red bull": {"team_name": "Red Bull", "selected_hex": "#0600EF"},
        "ferrari": {"team_name": "Ferrari", "selected_hex": "#E80020"},
        "mercedes": {"team_name": "Mercedes", "selected_hex": "#27F4D2"},
        "mclaren": {"team_name": "McLaren", "selected_hex": "#FF8000"},
        "aston martin": {"team_name": "Aston Martin", "selected_hex": "#00665F"},
        "alpine": {"team_name": "Alpine", "selected_hex": "#FF87BC"},
        "haas": {"team_name": "Haas", "selected_hex": "#B6BABD"},
        "rb": {"team_name": "RB", "selected_hex": "#364AA9"},
        "kick sauber": {"team_name": "Kick Sauber", "selected_hex": "#00E700"},
        "williams": {"team_name": "Williams", "selected_hex": "#00A0DD"},
    }
    driver_to_team = {
        "VER": ("red bull", "Max Verstappen"),
        "LAW": ("red bull", "Liam Lawson"),
        "PER": ("red bull", "Sergio Perez"),
        "LEC": ("ferrari", "Charles Leclerc"),
        "HAM": ("ferrari", "Lewis Hamilton"),
        "RUS": ("mercedes", "George Russell"),
        "ANT": ("mercedes", "Andrea Kimi Antonelli"),
        "NOR": ("mclaren", "Lando Norris"),
        "PIA": ("mclaren", "Oscar Piastri"),
        "ALO": ("aston martin", "Fernando Alonso"),
        "STR": ("aston martin", "Lance Stroll"),
        "GAS": ("alpine", "Pierre Gasly"),
        "COL": ("alpine", "Franco Colapinto"),
        "DOO": ("alpine", "Jack Doohan"),
        "OCO": ("haas", "Esteban Ocon"),
        "BEA": ("haas", "Oliver Bearman"),
        "TSU": ("rb", "Yuki Tsunoda"),
        "HAD": ("rb", "Isack Hadjar"),
        "HUL": ("kick sauber", "Nico Hulkenberg"),
        "BOR": ("kick sauber", "Gabriel Bortoleto"),
        "ALB": ("williams", "Alexander Albon"),
        "SAI": ("williams", "Carlos Sainz"),
    }
    drivers = {}
    for code, (team_slug, name) in driver_to_team.items():
        team = teams.get(team_slug, {})
        drivers[code] = {
            "driver_name": name,
            "team_slug": team_slug,
            "hex": team.get("selected_hex", "#808080"),
        }

    return {
        "success": True,
        "message": "Local fallback colour palette",
        "source": "local_fallback",
        "data": {
            "data": {
                "teams": teams,
                "drivers": drivers,
                "metadata": {
                    "season_year": int(year or 2026),
                    "colormap": colormap,
                    "source": "local_fallback",
                },
            }
        },
    }


def post(url: str, *args: Any, **kwargs: Any) -> Any:
    """Handle local analysis POSTs in-process and proxy all other URLs."""

    params = kwargs.get("params")
    json_body = kwargs.get("json")

    if is_local_first() and _is_local_analysis_execute(url):
        try:
            function_id = _extract_function_id(params, json_body)
            local_params = _extract_params(params, json_body)
            payload = execute_analysis_sync(function_id, **local_params)
            if str(function_id) == "98" and not payload.get("success"):
                payload = _fallback_color_payload(
                    year=local_params.get("year"),
                    colormap=str(local_params.get("colormap") or "fastf1"),
                )
            return LocalResponse(payload=payload, status_code=200, url=str(url))
        except Exception as exc:
            return LocalResponse(
                payload={
                    "success": False,
                    "message": "Local analysis execution failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "source": "local_requests",
                },
                status_code=500,
                url=str(url),
            )

    return _real_requests.post(url, *args, **kwargs)


def get(url: str, *args: Any, **kwargs: Any) -> Any:
    """Return local health/status responses where possible; proxy otherwise."""

    parsed = urlparse(str(url))
    if is_local_first() and parsed.path.endswith("/api/v2/system/health"):
        return LocalResponse(
            payload={"success": True, "status": "local", "message": "Local runtime active"},
            status_code=200,
            url=str(url),
        )
    if is_local_first() and parsed.path.endswith("/api/v2/analysis/status"):
        try:
            state = execute_analysis_sync(99, year=2026).get("runtime", {})
        except Exception:
            state = {"busy": False, "active_tasks": []}
        return LocalResponse(
            payload={"success": True, "status": "local", "runtime": state},
            status_code=200,
            url=str(url),
        )

    return _real_requests.get(url, *args, **kwargs)


__all__ = ["exceptions", "get", "post", "LocalResponse"]
