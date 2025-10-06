#!/usr/bin/env python3
"""All drivers straight-line speed analysis module."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


@dataclass
class DriverSpeedRecord:
    """Container representing the maximum speed details for a driver."""

    driver: str
    driver_number: Optional[int]
    team: Optional[str]
    full_name: Optional[str]
    max_speed_kmh: float
    lap_number: Optional[int]
    distance_m: Optional[float]
    session_time: Optional[str]
    throttle: Optional[float]
    drs: Optional[int]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "driver": self.driver,
            "driver_number": self.driver_number,
            "team": self.team,
            "full_name": self.full_name,
            "max_speed_kmh": round(float(self.max_speed_kmh), 3),
            "lap_number": self.lap_number,
            "distance_m": round(float(self.distance_m), 3) if self.distance_m is not None else None,
            "session_time": self.session_time,
            "throttle_percent": round(float(self.throttle), 2) if self.throttle is not None else None,
            "drs": self.drs,
        }


class AllDriversStraightLineSpeedAnalysis:
    """Analyse maximum straight-line speeds for every driver in a session."""

    def __init__(
        self,
        data_loader: Any,
        *,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
    ) -> None:
        self.data_loader = data_loader
        self.year = year or getattr(data_loader, "year", None)
        self.race = race or getattr(data_loader, "race_name", None)
        self.session = session or getattr(data_loader, "session_type", None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, *, top_n: Optional[int] = None, include_chart: bool = True) -> Dict[str, Any]:
        self._ensure_ready()

        records = self._collect_speed_records()
        if not records:
            return {
                "success": False,
                "function_id": "48",
                "message": "無法計算任何車手的直線最高速度 (缺少遙測資料)",
                "data": {
                    "metadata": self._build_metadata(),
                    "driver_speeds": [],
                },
            }

        records.sort(key=lambda item: item.max_speed_kmh, reverse=True)
        if top_n is not None and isinstance(top_n, int) and top_n > 0:
            sliced_records = records[:top_n]
        else:
            sliced_records = records

        data_payload = {
            "metadata": self._build_metadata(total_drivers=len(records)),
            "driver_speeds": [record.as_dict() for record in sliced_records],
            "summary": self._build_summary(records),
        }

        if include_chart:
            data_payload["chart_data"] = self._build_chart_data(records)

        return {
            "success": True,
            "function_id": "48",
            "message": "全部車手直線速度分析完成",
            "data": data_payload,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_ready(self) -> None:
        if not self.data_loader:
            raise ValueError("data_loader 尚未初始化")
        if not getattr(self.data_loader, "session_loaded", False):
            raise ValueError("尚未載入任何賽事資料，無法執行分析")

    def _collect_speed_records(self) -> List[DriverSpeedRecord]:
        records: List[DriverSpeedRecord] = []
        for driver_code in self._iter_drivers():
            record = self._compute_driver_record(driver_code)
            if record:
                records.append(record)
        return records

    # Driver iteration -------------------------------------------------

    def _iter_drivers(self) -> Iterable[str]:
        results = getattr(self.data_loader, "results", None)
        if isinstance(results, pd.DataFrame) and not results.empty:
            return results["Abbreviation"].dropna().unique()

        # fallback to synchronized data if available
        loaded = getattr(self.data_loader, "loaded_data", {}) or {}
        sync_map = loaded.get("synchronized_driver_data", {})
        if isinstance(sync_map, dict):
            return list(sync_map.keys())

        # final fallback: try laps dataframe columns
        laps = getattr(self.data_loader, "laps", None)
        if hasattr(laps, "drivers"):
            return list(laps.drivers)
        if isinstance(laps, pd.DataFrame) and "Driver" in laps.columns:
            return laps["Driver"].dropna().unique()

        return []

    # Single driver computation ---------------------------------------

    def _compute_driver_record(self, driver_code: str) -> Optional[DriverSpeedRecord]:
        driver_laps = self._pick_driver_laps(driver_code)
        if driver_laps is None or getattr(driver_laps, "empty", False):
            return None

        best: Optional[DriverSpeedRecord] = None
        for _, lap in self._iter_lap_rows(driver_laps):
            lap_number = self._extract_lap_number(lap)
            if lap_number is None:
                continue

            car_data = self._extract_car_data(lap)
            if car_data is None or "Speed" not in car_data.columns:
                continue

            speeds = pd.to_numeric(car_data["Speed"], errors="coerce").dropna()
            if speeds.empty:
                continue

            idx = speeds.idxmax()
            top_speed = float(speeds[idx])
            if not math.isfinite(top_speed):
                continue

            distance_m = self._safe_float(car_data, idx, "Distance")
            throttle = self._safe_float(car_data, idx, "Throttle")
            drs = self._safe_int(car_data, idx, "DRS")
            session_time = self._format_time(car_data, idx, "Time")

            record = DriverSpeedRecord(
                driver=driver_code,
                driver_number=self._lookup_driver_number(driver_code),
                team=self._lookup_driver_team(driver_code),
                full_name=self._lookup_driver_name(driver_code),
                max_speed_kmh=top_speed,
                lap_number=lap_number,
                distance_m=distance_m,
                session_time=session_time,
                throttle=throttle,
                drs=drs,
            )

            if best is None or record.max_speed_kmh > best.max_speed_kmh:
                best = record

        return best

    def _pick_driver_laps(self, driver_code: str) -> Any:
        laps = getattr(self.data_loader, "laps", None)
        if laps is None:
            return None
        if hasattr(laps, "pick_driver"):
            return laps.pick_driver(driver_code)
        return None

    def _iter_lap_rows(self, driver_laps: Any) -> Iterable[Tuple[Any, Any]]:
        if hasattr(driver_laps, "iterlaps"):
            yield from driver_laps.iterlaps()
        elif hasattr(driver_laps, "iterrows"):
            yield from driver_laps.iterrows()
        elif isinstance(driver_laps, list):
            for idx, lap in enumerate(driver_laps):
                yield idx, lap
        else:
            return []

    def _extract_lap_number(self, lap: Any) -> Optional[int]:
        for attr in ("LapNumber", "lap_number"):
            if hasattr(lap, attr):
                value = getattr(lap, attr)
                if value is not None:
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        return None
        if isinstance(lap, pd.Series) and "LapNumber" in lap:
            try:
                return int(lap["LapNumber"])
            except (TypeError, ValueError):
                return None
        return None

    def _extract_car_data(self, lap: Any) -> Optional[pd.DataFrame]:
        get_car_data = getattr(lap, "get_car_data", None)
        if not callable(get_car_data):
            return None

        try:
            car_data = get_car_data()
            if car_data is None:
                return None
            if hasattr(car_data, "add_distance"):
                try:
                    car_data = car_data.add_distance()
                except Exception:
                    pass
            return self._to_dataframe(car_data)
        except Exception:
            return None

    def _to_dataframe(self, telemetry: Any) -> Optional[pd.DataFrame]:
        if telemetry is None:
            return None
        if isinstance(telemetry, pd.DataFrame):
            return telemetry
        if hasattr(telemetry, "to_pandas"):
            return telemetry.to_pandas()
        if hasattr(telemetry, "data"):
            try:
                return pd.DataFrame(telemetry.data)
            except Exception:
                pass
        try:
            return pd.DataFrame(telemetry)
        except Exception:
            return None

    # Metadata lookups -----------------------------------------------

    def _lookup_driver_number(self, driver_code: str) -> Optional[int]:
        row = self._get_driver_row(driver_code)
        if row is not None and "DriverNumber" in row:
            value = row["DriverNumber"]
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        return None

    def _lookup_driver_team(self, driver_code: str) -> Optional[str]:
        row = self._get_driver_row(driver_code)
        if row is not None:
            for key in ("TeamName", "Team", "Constructor", "team_reconciled"):
                if key in row and pd.notna(row[key]):
                    return str(row[key])
        sync_data = self._get_sync_driver_data(driver_code)
        if sync_data:
            return sync_data.get("team_reconciled") or sync_data.get("team_fastf1") or sync_data.get("team_openf1")
        return None

    def _lookup_driver_name(self, driver_code: str) -> Optional[str]:
        row = self._get_driver_row(driver_code)
        if row is not None:
            for key in ("FullName", "Driver", "Name"):
                if key in row and pd.notna(row[key]):
                    return str(row[key])
        sync_data = self._get_sync_driver_data(driver_code)
        if sync_data:
            return sync_data.get("name")
        return None

    def _get_driver_row(self, driver_code: str) -> Optional[pd.Series]:
        results = getattr(self.data_loader, "results", None)
        if isinstance(results, pd.DataFrame) and not results.empty:
            matches = results[results["Abbreviation"] == driver_code]
            if not matches.empty:
                return matches.iloc[0]
        return None

    def _get_sync_driver_data(self, driver_code: str) -> Optional[Dict[str, Any]]:
        loaded = getattr(self.data_loader, "loaded_data", {}) or {}
        sync_map = loaded.get("synchronized_driver_data", {})
        if isinstance(sync_map, dict):
            entry = sync_map.get(driver_code)
            if isinstance(entry, dict):
                return entry.get("reconciled_data") or entry
        return None

    # Utility helpers -------------------------------------------------

    def _safe_float(self, df: pd.DataFrame, idx: Any, column: str) -> Optional[float]:
        if column in df.columns:
            value = df.loc[idx, column]
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return None

    def _safe_int(self, df: pd.DataFrame, idx: Any, column: str) -> Optional[int]:
        if column in df.columns:
            value = df.loc[idx, column]
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        return None

    def _format_time(self, df: pd.DataFrame, idx: Any, column: str) -> Optional[str]:
        if column not in df.columns:
            return None
        value = df.loc[idx, column]
        if pd.isna(value):
            return None
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        if isinstance(value, pd.Timedelta):
            return self._timedelta_to_string(value)
        return str(value)

    def _timedelta_to_string(self, td: pd.Timedelta) -> str:
        total_seconds = td.total_seconds()
        return f"{total_seconds:.3f}s"

    # Summary & chart -------------------------------------------------

    def _build_summary(self, records: List[DriverSpeedRecord]) -> Dict[str, Any]:
        speeds = [rec.max_speed_kmh for rec in records]
        highest = max(records, key=lambda rec: rec.max_speed_kmh)
        summary = {
            "fastest_driver": highest.driver,
            "fastest_driver_number": highest.driver_number,
            "fastest_speed_kmh": round(highest.max_speed_kmh, 3),
            "fastest_lap": highest.lap_number,
            "drivers_analysed": len(records),
            "average_speed_kmh": round(float(sum(speeds) / len(speeds)), 3),
            "max_minus_min_delta_kmh": round(float(max(speeds) - min(speeds)), 3),
        }
        if len(speeds) > 1:
            sorted_speeds = sorted(speeds)
            median = sorted_speeds[len(sorted_speeds) // 2]
            summary["median_speed_kmh"] = round(float(median), 3)
        return summary

    def _build_chart_data(self, records: List[DriverSpeedRecord]) -> Dict[str, Any]:
        return {
            "type": "bar",
            "x": [rec.driver for rec in records],
            "values": [round(float(rec.max_speed_kmh), 3) for rec in records],
            "unit": "km/h",
            "highlight": records[0].driver if records else None,
        }

    def _build_metadata(self, *, total_drivers: Optional[int] = None) -> Dict[str, Any]:
        return {
            "year": self.year,
            "race": self.race,
            "session": self.session,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "drivers_total": total_drivers,
        }


__all__ = [
    "AllDriversStraightLineSpeedAnalysis",
    "DriverSpeedRecord",
]
