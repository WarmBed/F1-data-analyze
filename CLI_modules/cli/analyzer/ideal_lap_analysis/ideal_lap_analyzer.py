#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ideal Lap Analysis (Function 53) - All Drivers

模組化實現，依據文檔規格計算全車手理想圈資訊並輸出 JSON。
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd


@dataclass
class SectorTiming:
    time_seconds: float
    lap_number: int

    @property
    def formatted_time(self) -> str:
        minutes = int(self.time_seconds // 60)
        remainder = self.time_seconds % 60
        if minutes:
            return f"{minutes}:{remainder:06.3f}"
        return f"{remainder:.3f}s"


@dataclass
class LapRecord:
    lap_number: int
    lap_time_seconds: Optional[float]
    sector_times: Dict[str, Optional[float]]
    is_valid: bool

    @property
    def lap_time_formatted(self) -> str:
        if self.lap_time_seconds is None or math.isnan(self.lap_time_seconds):
            return "N/A"
        minutes = int(self.lap_time_seconds // 60)
        remainder = self.lap_time_seconds % 60
        return f"{minutes}:{remainder:06.3f}" if minutes else f"{remainder:.3f}s"


@dataclass
class IdealLapDetail:
    total_time: float
    sector_sources: Dict[str, Dict[str, float]]

    @property
    def formatted_time(self) -> str:
        minutes = int(self.total_time // 60)
        remainder = self.total_time % 60
        return f"{minutes}:{remainder:06.3f}" if minutes else f"{remainder:.3f}s"


@dataclass
class DriverIdealLap:
    driver: str
    driver_name: str
    team: str
    ideal_lap_time: float
    fastest_lap_time: Optional[float]
    time_gap: Optional[float]
    sector_breakdown: Dict[str, Dict[str, Any]]
    laps: List[LapRecord]
    ideal_lap_detail: IdealLapDetail
    driver_position: Optional[int] = None
    gap_to_leader: Optional[float] = None


class IdealLapAnalyzer:
    """核心分析類別"""

    def __init__(self, data_loader, debug: bool = True) -> None:
        self.data_loader = data_loader
        self.debug = debug
        self.session = None
        self.laps: Optional[pd.DataFrame] = None
        self.results: Optional[pd.DataFrame] = None

    def log(self, message: str) -> None:
        if self.debug:
            print(f"[F53] {message}")

    def load_data(self) -> bool:
        try:
            data = self.data_loader.get_loaded_data()
            self.session = data.get("session")
            self.laps = data.get("laps")
            self.results = data.get("results")
            if self.laps is None or self.laps.empty:
                self.log("圈速資料不存在或為空")
                return False
            if "Driver" not in self.laps.columns:
                self.log("圈速資料缺少 Driver 欄位")
                return False
            return True
        except Exception as exc:
            self.log(f"載入資料失敗: {exc}")
            return False

    @staticmethod
    def _to_seconds(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, pd.Timedelta):
            return float(value.total_seconds())
        if hasattr(value, "total_seconds"):
            return float(value.total_seconds())
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _collect_driver_laps(self, driver_code: str) -> pd.DataFrame:
        driver_laps = self.laps[self.laps["Driver"] == driver_code].copy()
        if driver_laps.empty:
            return driver_laps
        columns_needed = {
            "LapTime",
            "LapNumber",
            "IsAccurate",
            "Sector1Time",
            "Sector2Time",
            "Sector3Time",
        }
        missing = [col for col in columns_needed if col not in driver_laps.columns]
        for col in missing:
            driver_laps[col] = pd.NA
        return driver_laps

    def _build_lap_records(self, driver_laps: pd.DataFrame) -> List[LapRecord]:
        records: List[LapRecord] = []
        for _, row in driver_laps.iterrows():
            lap_number = int(row.get("LapNumber", 0))
            lap_time_sec = self._to_seconds(row.get("LapTime"))
            sector_times = {
                "s1": self._to_seconds(row.get("Sector1Time")),
                "s2": self._to_seconds(row.get("Sector2Time")),
                "s3": self._to_seconds(row.get("Sector3Time")),
            }
            is_valid = bool(row.get("IsAccurate", True)) and not pd.isna(lap_time_sec)
            records.append(
                LapRecord(
                    lap_number=lap_number,
                    lap_time_seconds=lap_time_sec,
                    sector_times=sector_times,
                    is_valid=is_valid,
                )
            )
        return records

    def _calculate_ideal_lap(self, driver_laps: pd.DataFrame) -> Optional[IdealLapDetail]:
        valid_laps = driver_laps.dropna(subset=["Sector1Time", "Sector2Time", "Sector3Time"], how="any")
        if valid_laps.empty:
            return None

        sectors = {}
        for idx, sector in enumerate(["Sector1Time", "Sector2Time", "Sector3Time"], start=1):
            fastest_idx = valid_laps[sector].idxmin()
            value = valid_laps.loc[fastest_idx, sector]
            lap_number = int(valid_laps.loc[fastest_idx, "LapNumber"])
            seconds = self._to_seconds(value)
            if seconds is None:
                return None
            sectors[f"s{idx}"] = {"lap": lap_number, "time": round(seconds, 3)}

        total_time = sum(s["time"] for s in sectors.values())
        return IdealLapDetail(total_time=round(total_time, 3), sector_sources=sectors)

    def _fastest_lap_info(self, driver_laps: pd.DataFrame) -> Dict[str, Any]:
        valid = driver_laps.dropna(subset=["LapTime"], how="any")
        if valid.empty:
            return {"lap_number": None, "total_time": None, "sectors": {}}
        idx = valid["LapTime"].idxmin()
        row = valid.loc[idx]
        total_time = self._to_seconds(row["LapTime"])
        lap_number = int(row.get("LapNumber", 0))
        sectors = {}
        # ✅ 修正：使用正確的鍵名 sector_1, sector_2, sector_3
        for key, sector_key in [("Sector1Time", "sector_1"), ("Sector2Time", "sector_2"), ("Sector3Time", "sector_3")]:
            sec = self._to_seconds(row.get(key))
            if sec is not None:
                sectors[sector_key] = {
                    "time": round(sec, 3),
                    "is_optimal_in_fastest": False,
                }
        return {
            "lap_number": lap_number,
            "total_time": round(total_time, 3) if total_time is not None else None,
            "sectors": sectors,
        }

    def analyze_driver(self, driver_code: str) -> Optional[DriverIdealLap]:
        driver_laps = self._collect_driver_laps(driver_code)
        if driver_laps.empty:
            self.log(f"車手 {driver_code} 無圈速資料")
            return None

        lap_records = self._build_lap_records(driver_laps)
        ideal_detail = self._calculate_ideal_lap(driver_laps)
        if ideal_detail is None:
            self.log(f"車手 {driver_code} 無法計算理想圈")
            return None

        fastest_info = self._fastest_lap_info(driver_laps)
        fastest_time = fastest_info["total_time"]
        time_gap = None
        if fastest_time is not None:
            time_gap = round(fastest_time - ideal_detail.total_time, 3)

        sector_breakdown: Dict[str, Dict[str, Any]] = {}
        for idx, sector_key in enumerate(["sector_1", "sector_2", "sector_3"], start=1):
            ideal_sector = ideal_detail.sector_sources[f"s{idx}"]["time"]
            fastest_sector = fastest_info["sectors"].get(sector_key, {}).get("time")
            is_optimal = False
            if fastest_sector is not None:
                is_optimal = abs(fastest_sector - ideal_sector) < 0.01
            
            # ✅ 同時輸出理想圈和最速圈的分段時間
            sector_breakdown[sector_key] = {
                "ideal_time": ideal_sector,  # 理想圈分段時間
                "fastest_time": fastest_sector,  # 最速圈分段時間
                "delta": round(fastest_sector - ideal_sector, 3) if fastest_sector is not None else None,  # 差異
                "is_optimal_in_fastest": is_optimal,
                # 向下相容：保留舊的 "time" 欄位（指向理想圈時間）
                "time": ideal_sector,
            }

        driver_name, team = self._resolve_driver_info(driver_code)

        return DriverIdealLap(
            driver=driver_code,
            driver_name=driver_name,
            team=team,
            ideal_lap_time=ideal_detail.total_time,
            fastest_lap_time=fastest_time,
            time_gap=time_gap,
            sector_breakdown=sector_breakdown,
            laps=lap_records,
            ideal_lap_detail=ideal_detail,
        )

    def _resolve_driver_info(self, driver_code: str) -> tuple[str, str]:
        if self.results is not None and not self.results.empty:
            match = self.results[self.results["Abbreviation"] == driver_code]
            if not match.empty:
                row = match.iloc[0]
                return str(row.get("FullName", driver_code)), str(row.get("TeamName", "Unknown Team"))
        return driver_code, "Unknown Team"

    def analyze_all_drivers(self) -> List[DriverIdealLap]:
        drivers = sorted(self.laps["Driver"].dropna().unique()) if self.laps is not None else []
        output: List[DriverIdealLap] = []
        for code in drivers:
            result = self.analyze_driver(code)
            if result:
                output.append(result)
        output.sort(key=lambda d: d.ideal_lap_time)
        leader_time = output[0].ideal_lap_time if output else None
        for idx, driver in enumerate(output, start=1):
            driver.driver_position = idx
            if leader_time is not None:
                driver.gap_to_leader = round(driver.ideal_lap_time - leader_time, 3)
        return output

    # ---------------- JSON BUILDERS -----------------

    @staticmethod
    def _serialize_lap_record(lap: LapRecord) -> Dict[str, Any]:
        return {
            "lap_number": lap.lap_number,
            "lap_time_seconds": None if lap.lap_time_seconds is None else round(lap.lap_time_seconds, 3),
            "lap_time_formatted": lap.lap_time_formatted,
            "sector_times": {
                key: None if value is None else round(value, 3)
                for key, value in lap.sector_times.items()
            },
            "is_valid": lap.is_valid,
        }

    def build_json(self, driver_results: List[DriverIdealLap]) -> Dict[str, Any]:
        if not driver_results:
            return {
                "success": False,
                "message": "無法生成理想圈資料",
            }

        year = getattr(self.data_loader, "year", None)
        race = getattr(self.data_loader, "race_name", None)
        session = getattr(self.data_loader, "session_type", None)

        # 找出全場最速實際圈
        session_fastest_lap = None
        session_fastest_driver = None
        session_fastest_lap_number = None
        
        for driver in driver_results:
            if driver.fastest_lap_time is not None:
                if session_fastest_lap is None or driver.fastest_lap_time < session_fastest_lap:
                    session_fastest_lap = driver.fastest_lap_time
                    session_fastest_driver = driver.driver
                    # 找出該車手最速圈的圈數
                    fastest_lap_info = self._fastest_lap_info(self._collect_driver_laps(driver.driver))
                    session_fastest_lap_number = fastest_lap_info.get("lap_number")
        
        # 找出最快理想圈的車手
        fastest_ideal_driver = driver_results[0].driver if driver_results else None

        summary = {
            "total_drivers": len(driver_results),
            # 理想圈統計
            "fastest_ideal_lap": {
                "time": round(driver_results[0].ideal_lap_time, 3),
                "driver": fastest_ideal_driver,
            } if driver_results else None,
            "slowest_ideal_lap": round(driver_results[-1].ideal_lap_time, 3),
            "average_ideal_lap": round(np.mean([d.ideal_lap_time for d in driver_results]), 3),
            "ideal_lap_range": {
                "range_seconds": round(driver_results[-1].ideal_lap_time - driver_results[0].ideal_lap_time, 3),
                "fastest": round(driver_results[0].ideal_lap_time, 3),
                "slowest": round(driver_results[-1].ideal_lap_time, 3),
            },
            # 全場最速實際圈
            "session_fastest_lap": session_fastest_lap,
            "session_fastest_driver": session_fastest_driver,
            "session_fastest_lap_number": session_fastest_lap_number,
            # 完美單圈達成率（理想圈 = 實際圈的車手數）
            "perfect_lap_count": sum(1 for d in driver_results if d.time_gap is not None and abs(d.time_gap) < 0.01),
            "perfect_lap_rate": f"{sum(1 for d in driver_results if d.time_gap is not None and abs(d.time_gap) < 0.01)}/{len(driver_results)}",
            # 平均差異
            "average_gap": round(np.mean([d.time_gap for d in driver_results if d.time_gap is not None]), 3),
        }

        ranking = []
        team_summary: Dict[str, Dict[str, Any]] = {}

        for driver in driver_results:
            # 計算與全場最速實際圈的差距（使用理想圈時間比較）
            # 意義：如果車手完美發揮，與全場最速圈的差距
            gap_to_session_fastest = None
            if session_fastest_lap is not None:
                gap_to_session_fastest = round(driver.ideal_lap_time - session_fastest_lap, 3)
            
            ranking.append({
                "position": driver.driver_position,
                "driver": driver.driver,
                "driver_name": driver.driver_name,
                "team": driver.team,
                "ideal_lap_time": round(driver.ideal_lap_time, 3),
                "fastest_lap_time": None if driver.fastest_lap_time is None else round(driver.fastest_lap_time, 3),
                "time_gap": driver.time_gap,
                "gap_to_leader": driver.gap_to_leader,
                "gap_to_session_fastest": gap_to_session_fastest,  # 理想圈 vs 全場最速
                "sector_breakdown": driver.sector_breakdown,
                "laps": [self._serialize_lap_record(l) for l in driver.laps],
                "ideal_lap_detail": {
                    "total_time": driver.ideal_lap_detail.total_time,
                    "formatted_time": driver.ideal_lap_detail.formatted_time,
                    "sector_sources": driver.ideal_lap_detail.sector_sources,
                },
            })

            team_entry = team_summary.setdefault(driver.team, {"drivers": [], "ideal_laps": []})
            team_entry["drivers"].append(driver.driver)
            team_entry["ideal_laps"].append(driver.ideal_lap_time)

        team_analysis = {}
        for team, info in team_summary.items():
            team_drivers = [d for d in driver_results if d.team == team]
            best_driver = min(team_drivers, key=lambda d: d.ideal_lap_time) if team_drivers else None
            team_analysis[team] = {
                "drivers": info["drivers"],
                "average_ideal_lap": round(float(np.mean(info["ideal_laps"])), 3),
                "best_driver": best_driver.driver if best_driver else None,
                "best_driver_ideal_lap": round(best_driver.ideal_lap_time, 3) if best_driver else None,
            }

        sector_times = {"sector_1": [], "sector_2": [], "sector_3": []}
        for driver in driver_results:
            for idx, key in enumerate(["sector_1", "sector_2", "sector_3"], start=1):
                sector_times[key].append(driver.ideal_lap_detail.sector_sources[f"s{idx}"]["time"])

        sector_comparison = {}
        for key, values in sector_times.items():
            sector_comparison[key] = {
                "fastest_time": round(min(values), 3),
                "slowest_time": round(max(values), 3),
                "average_time": round(float(np.mean(values)), 3),
                "spread": round(max(values) - min(values), 3),
                "fastest_driver": next(
                    driver.driver
                    for driver in driver_results
                    if driver.ideal_lap_detail.sector_sources[f"s{int(key[-1])}"]["time"] == min(values)
                ),
                "slowest_driver": next(
                    driver.driver
                    for driver in driver_results
                    if driver.ideal_lap_detail.sector_sources[f"s{int(key[-1])}"]["time"] == max(values)
                ),
            }

        return {
            "success": True,
            "metadata": {
                "function_id": 53,
                "function_name": "Ideal Lap Analysis - All Drivers",
                "year": year,
                "race": race,
                "session": session,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "api_source": "FastF1",
            },
            "analysis_result": {
                "summary": summary,
                "ranking": ranking,
                "team_analysis": team_analysis,
                "sector_comparison": sector_comparison,
            },
        }

    def save_json(self, payload: Dict[str, Any]) -> Optional[str]:
        if not payload.get("success"):
            return None
        year = payload["metadata"].get("year", "Unknown")
        race = payload["metadata"].get("race", "Unknown")
        session = payload["metadata"].get("session", "Unknown")
        filename = f"ideal_lap_ranking_{year}_{race}_{session}.json"
        json_dir = os.path.join(os.getcwd(), "json")
        os.makedirs(json_dir, exist_ok=True)
        path = os.path.join(json_dir, filename)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        self.log(f"JSON 已輸出: {path}")
        return path


__all__ = ["IdealLapAnalyzer", "DriverIdealLap"]
