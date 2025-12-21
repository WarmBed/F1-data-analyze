#!/usr/bin/env python3
"""
Ideal Lap Sector Heatmap Data Loader
====================================

Transforms CLI Function 53 output into a matrix structure that can be rendered
as a sector heatmap (S1/S2/S3 across all drivers).

The loader prefers cached JSON (API-ONLY mode) and never triggers CLI execution.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from modules.gui.base.universal_data_loader_base import UniversalDataLoader


class IdealLapSectorHeatmapDataLoader(UniversalDataLoader):
    """
    Data loader dedicated to the ideal lap sector heatmap view.

    Expected JSON structure (excerpt):
        {
          "analysis_result": {
            "ranking": [...],
            "sector_comparison": {...}
          }
        }
    """

    CLI_FUNCTION = 53
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    ANALYSIS_TYPE = "ideal_lap_sector_heatmap"

    def __init__(self, year: str, race: str, session: str, parent=None):
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)

        self.year = str(year)
        self.race = race
        self.session = session

        # ✅ API-ONLY 模式：禁止本地 JSON 後備和 CLI 調用
        self._allow_local_fallback = False

        self._debug(
            f"[SECTOR_HEATMAP_LOADER] Initialised loader for {self.year} {self.race} {self.session}"
        )
        self._debug("⚠️  [API-ONLY MODE] Local JSON fallback disabled")

    # --------------------------------------------------------------------- #
    # Validation / processing hooks
    # --------------------------------------------------------------------- #
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """Ensure year / race / session are provided."""
        try:
            year = int(params.get("year", self.year))
            race = params.get("race", self.race)
            session = params.get("session", self.session)

            if year < 2018 or year > 2026:
                self._debug("[VALIDATE] Year outside supported bounds")
                return False
            if not race:
                self._debug("[VALIDATE] Missing race name")
                return False
            if session not in {"FP1", "FP2", "FP3", "Q", "R", "S"}:
                self._debug(f"[VALIDATE] Unsupported session value: {session}")
                return False
            return True
        except Exception as exc:
            self._debug(f"[VALIDATE] Parameter validation failed: {exc}")
            return False

    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """Construct file search patterns for cached JSON."""
        year = kwargs.get("year", self.year)
        race = kwargs.get("race", self.race)
        session = kwargs.get("session", self.session)

        patterns = [
            self.JSON_PATTERN.format(year=year, race=race, session=session),
            f"ideal_lap_ranking_{year}_{race}_*.json",
            f"ideal_lap_ranking_{year}_*.json",
        ]
        return patterns

    def _validate_data_format(self, data: Any) -> bool:
        """Check ranking/sector payload before attempting to transform."""
        if not isinstance(data, dict):
            self._debug("[VALIDATE] Root payload is not a dict")
            return False

        analysis = data.get("analysis_result")
        if not isinstance(analysis, dict):
            self._debug("[VALIDATE] Missing 'analysis_result' block")
            return False

        ranking = analysis.get("ranking")
        sector_comp = analysis.get("sector_comparison")

        if not isinstance(ranking, list) or not ranking:
            self._debug("[VALIDATE] 'ranking' must be a non-empty list")
            return False

        first_driver = ranking[0]
        required_fields = ("driver", "ideal_lap_detail", "sector_breakdown")
        missing = [field for field in required_fields if field not in first_driver]
        if missing:
            self._debug(f"[VALIDATE] ranking entry missing fields: {missing}")
            return False

        ideal_detail = first_driver["ideal_lap_detail"]
        if "sector_sources" not in ideal_detail:
            self._debug("[VALIDATE] ideal_lap_detail missing sector_sources")
            return False

        if not isinstance(sector_comp, dict):
            self._debug("[VALIDATE] 'sector_comparison' must be a dict")
            return False

        self._debug(
            f"[VALIDATE] Payload validated successfully ({len(ranking)} drivers)"
        )
        return True

    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        Convert raw JSON into the enriched structure consumed by the heatmap UI.
        """
        try:
            transformed = self._transform_data_for_display(raw_data)
            transformed["raw_data"] = raw_data
            transformed.setdefault("success", True)
            return transformed
        except Exception as exc:
            self._error(f"[PROCESS] Data transformation failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "raw_data": raw_data,
            }

    # ------------------------------------------------------------------ #
    # Transformation helpers
    # ------------------------------------------------------------------ #
    def _transform_data_for_display(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the sector matrix, annotations, and metadata required by the widget.
        """
        analysis = data["analysis_result"]
        ranking: List[Dict[str, Any]] = analysis.get("ranking", [])
        sector_comp: Dict[str, Dict[str, Any]] = analysis.get(
            "sector_comparison", {}
        )

        driver_order: List[str] = []
        matrix_rows: List[Dict[str, Any]] = []
        cell_details: Dict[Tuple[str, str], Dict[str, Any]] = {}
        driver_metadata: Dict[str, Dict[str, Any]] = {}

        for driver_entry in ranking:
            driver_code = driver_entry.get("driver", "UNK")
            driver_order.append(driver_code)

            driver_metadata[driver_code] = {
                "code": driver_code,
                "name": driver_entry.get("driver_name"),
                "team": driver_entry.get("team"),
                "position": driver_entry.get("position"),
            }

            sector_sources = (
                driver_entry.get("ideal_lap_detail", {}).get("sector_sources", {})
            )

            row_record = {"driver": driver_code}

            for idx, sector_label in enumerate(("S1", "S2", "S3"), start=1):
                source_key = f"s{idx}"
                source_info = sector_sources.get(source_key, {}) or {}
                time_value = source_info.get("time")
                lap_number = source_info.get("lap")

                # Normalise missing values to NaN for pandas / numpy compatibility.
                numeric_time = (
                    float(time_value)
                    if self._is_number(time_value)
                    else float("nan")
                )

                row_record[sector_label] = numeric_time

                cell_details[(sector_label, driver_code)] = {
                    "driver": driver_code,
                    "sector": sector_label,
                    "time": numeric_time,
                    "lap": lap_number,
                    "team": driver_entry.get("team"),
                    "position": driver_entry.get("position"),
                    "source": source_info,
                }

            matrix_rows.append(row_record)

        if matrix_rows:
            df = pd.DataFrame(matrix_rows).set_index("driver").transpose()
        else:
            df = pd.DataFrame(columns=driver_order, index=["S1", "S2", "S3"])

        # Ensure row ordering is S1 -> S3 and columns follow ranking order.
        df = df.reindex(index=["S1", "S2", "S3"])
        df = df.loc[:, driver_order] if driver_order else df

        sector_summary = self._build_sector_summary(sector_comp)
        sector_rankings = self._calculate_sector_rankings(df)
        driver_best_map = self._calculate_driver_best_map(df)

        # Enrich cell details with ranking + delta information.
        for sector_label, rankings in sector_rankings.items():
            if not rankings:
                continue
            fastest_driver = rankings[0][0]
            fastest_time = rankings[0][1]

            for position, (driver_code, driver_time) in enumerate(rankings, start=1):
                details = cell_details.get((sector_label, driver_code))
                if not details:
                    continue

                delta = (
                    None
                    if math.isnan(driver_time) or math.isnan(fastest_time)
                    else driver_time - fastest_time
                )

                details.update(
                    {
                        "sector_rank": position,
                        "delta_to_fastest": delta,
                        "is_global_fastest": driver_code == fastest_driver,
                    }
                )

        # Append delta / ranking info to sector summary as well.
        for sector_label, summary in sector_summary.items():
            rankings = sector_rankings.get(sector_label, [])
            summary["total_classified"] = len(rankings)

        return {
            "success": True,
            "analysis_type": self.ANALYSIS_TYPE,
            "sector_matrix": df,
            "sector_summary": sector_summary,
            "sector_rankings": sector_rankings,
            "driver_best_map": driver_best_map,
            "driver_order": driver_order,
            "driver_metadata": driver_metadata,
            "cell_details": cell_details,
        }

    # ------------------------------------------------------------------ #
    # Helper computations
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_number(value: Any) -> bool:
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    def _build_sector_summary(
        self, sector_comp: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Normalise sector comparison block into S1/S2/S3 keyed dict.
        """
        summary: Dict[str, Dict[str, Any]] = {}

        for idx, sector_label in enumerate(("S1", "S2", "S3"), start=1):
            comp_key = f"sector_{idx}"
            info = sector_comp.get(comp_key, {}) or {}

            fastest_time = info.get("fastest_time")
            slowest_time = info.get("slowest_time")

            gap_range = None
            if self._is_number(fastest_time) and self._is_number(slowest_time):
                gap_range = float(slowest_time) - float(fastest_time)

            percentage_range = None
            if self._is_number(fastest_time) and gap_range is not None:
                fastest_val = float(fastest_time)
                if fastest_val > 0:
                    percentage_range = (gap_range / fastest_val) * 100.0

            summary[sector_label] = {
                "fastest_driver": info.get("fastest_driver"),
                "fastest_time": float(fastest_time)
                if self._is_number(fastest_time)
                else None,
                "slowest_driver": info.get("slowest_driver"),
                "slowest_time": float(slowest_time)
                if self._is_number(slowest_time)
                else None,
                "average_time": float(info.get("average_time"))
                if self._is_number(info.get("average_time"))
                else None,
                "range": gap_range,
                "range_percentage": percentage_range,
            }

        return summary

    def _calculate_sector_rankings(
        self, df: pd.DataFrame
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Produce sorted driver lists per sector (fastest -> slowest).
        """
        rankings: Dict[str, List[Tuple[str, float]]] = {}

        for sector_label, row in df.iterrows():
            valid_series = row.dropna().sort_values(ascending=True)
            rankings[sector_label] = list(valid_series.items())

        return rankings

    def _calculate_driver_best_map(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Identify which sector represents the driver's strongest contribution.
        """
        best_map: Dict[str, str] = {}

        for driver_code in df.columns:
            column = df[driver_code].dropna()
            if column.empty:
                continue
            best_sector = column.idxmin()
            best_map[driver_code] = best_sector

        return best_map

    # ------------------------------------------------------------------ #
    # Disabled CLI hook (API-ONLY)
    # ------------------------------------------------------------------ #
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        Explicitly disable CLI generation; API JSON is the single source of truth.
        """
        self._debug("[API-ONLY] CLI generation is disabled for sector heatmap")
        return False
