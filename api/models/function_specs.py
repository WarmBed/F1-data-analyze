#!/usr/bin/env python3
"""Function specifications and helpers for the API bridge."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Tuple, Union


NumberLike = Union[str, int, float]


@dataclass(frozen=True)
class FunctionSpec:
    """Metadata describing a CLI analysis function."""

    function_id: str
    name: str
    description: str
    required_params: List[str]
    optional_params: List[str] = field(default_factory=list)
    cli_flag_map: Dict[str, str] = field(default_factory=dict)
    cache_patterns: List[str] = field(default_factory=list)
    notes: str = ""
    aliases: List[str] = field(default_factory=list)


_ID_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")


def normalize_function_id(value: NumberLike | FunctionSpec) -> str:
    """Normalize function IDs to a canonical string form.

    Examples::

        normalize_function_id(6) -> "6"
        normalize_function_id("F14.2") -> "14.2"
        normalize_function_id("function_03") -> "3"
    """

    if isinstance(value, FunctionSpec):
        raw_value = value.function_id
    else:
        raw_value = value

    if raw_value is None:
        raise ValueError("function_id is required")

    text = str(raw_value).strip()
    if not text:
        raise ValueError("function_id is empty")

    lowered = text.lower()
    for prefix in ("function", "func", "mode", "id"):
        if lowered.startswith(prefix):
            text = text[len(prefix):]
            lowered = text.lower()
            break

    text = text.replace("_", ".").replace("-", ".").replace(" ", "")
    if text.lower().startswith("f"):
        text = text[1:]

    match = _ID_PATTERN.search(text)
    if not match:
        raise ValueError(f"無法解析 function_id: {raw_value}")

    canonical = match.group(1)
    major, dot, minor = canonical.partition(".")
    major_int = int(major)

    if not dot:
        return str(major_int)

    minor_trimmed = minor.rstrip("0")
    if not minor_trimmed:
        return str(major_int)

    # remove leading zeros but keep a single zero if needed
    minor_trimmed = minor_trimmed.lstrip("0") or "0"
    return f"{major_int}.{minor_trimmed}"


def function_id_sort_key(value: NumberLike | FunctionSpec) -> Tuple[int, Tuple[int, ...], str]:
    """Sorting helper ensuring 14.1 appears after 14 but before 15."""

    normalized = normalize_function_id(value)
    major_str, dot, minor_str = normalized.partition(".")
    major = int(major_str)
    if dot:
        minor_parts = tuple(int(part) for part in minor_str.split(".") if part != "")
    else:
        minor_parts = ()
    return major, minor_parts, normalized


def _make_spec(
    function_id: NumberLike,
    *,
    name: str,
    description: str,
    required_params: Iterable[str],
    optional_params: Iterable[str] | None = None,
    cli_flag_map: Dict[str, str] | None = None,
    cache_patterns: Iterable[str] | None = None,
    notes: str = "",
    aliases: Iterable[NumberLike] | None = None,
) -> FunctionSpec:
    canonical_id = normalize_function_id(function_id)
    alias_list = []
    for alias in aliases or []:
        normalized_alias = normalize_function_id(alias)
        if normalized_alias != canonical_id and normalized_alias not in alias_list:
            alias_list.append(normalized_alias)

    return FunctionSpec(
        function_id=canonical_id,
        name=name,
        description=description,
        required_params=list(required_params),
        optional_params=list(optional_params or []),
        cli_flag_map=dict(cli_flag_map or {}),
        cache_patterns=list(cache_patterns or []),
        notes=notes,
        aliases=alias_list,
    )


_FUNCTION_SPEC_LIST = [
    _make_spec(
        "1",
        name="Rain Analysis",
        description="Generates weather timeline and rain intensity metrics for a race session.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["rain_intensity_analysis", "rain_analysis"],
        notes="Used by GUI rain analysis panels; output JSON consumed directly.",
    ),
    _make_spec(
        "2",
        name="Track Analysis",
        description="Generates track map and position data JSON for a race session.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["track_path_analysis", "track_position"],
        notes="Feeds track overview widgets including map visualisations.",
    ),
    _make_spec(
        "3",
        name="Driver Fastest Pitstop Ranking",
        description="Generates a leaderboard of the quickest pit stops per driver for the selected session.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["driver_fastest_pitstop_ranking", "fastest_pitstop"],
        notes="Outputs JSON used by pit stop summary widgets.",
    ),
    _make_spec(
        "4",
        name="Team Pitstop Ranking",
        description="Ranks teams by cumulative or best pit stop performance for a session.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["team_pitstop_ranking", "pitstop_ranking"],
        notes="Provides team-level pit stop insights for dashboards.",
    ),
    _make_spec(
        "5",
        name="Driver Pitstop Records",
        description="Produces detailed pit stop logs for each driver including timings and tyre usage.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["driver_detailed_pitstop_records", "detailed_pitstop", "pitstop_records"],
        notes="Feeds GUI pit stop tables and audit exports.",
    ),
    _make_spec(
        "6",
        name="Accident Statistics Summary",
        description="Summarises accident categories, counts and severities for the selected session.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["accident_statistics_summary", "accident_statistics"],
        notes="Primary data source for GUI accident summary panels.",
    ),
    _make_spec(
        "7",
        name="Incident Severity Distribution",
        description="Calculates severity distribution histograms for each incident type.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["severity_distribution_analysis", "severity_analysis", "incident_severity"],
        notes="Feeds severity charts and comparative widgets.",
    ),
    _make_spec(
        "8",
        name="All Incidents Summary",
        description="Aggregates all incidents for the race session including penalties and safety car notes.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["all_incidents_summary", "incidents_summary"],
        notes="Used by incident review interfaces and reporting exports.",
    ),
    _make_spec(
        "9",
        name="Special Incident Reports",
        description="Highlights special incidents such as red flags, mechanical failures and retirements.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["special_incident_reports", "special_incidents", "notable_incidents"],
        notes="Used by detailed accident review dashboards.",
    ),
    _make_spec(
        "10",
        name="Key Events Summary",
        description="Captures key race events such as lead changes, safety cars and strategy pivots.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["key_events_summary", "key_events", "race_key_events"],
        notes="Feeds headline event timelines for the GUI dashboard.",
    ),
    _make_spec(
        "12",
        name="All Drivers Telemetry",
        description="Exports telemetry statistics for every driver in the session (or selected driver if provided).",
        required_params=["year", "race", "session"],
        optional_params=["driver1"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "driver1": "-d"},
        cache_patterns=["all_drivers_telemetry", "telemetry_analysis", "single_driver_telemetry"],
        notes="Generates the all-drivers telemetry JSON consumed by GUI tables.",
    ),
    _make_spec(
        "13",
        name="Telemetry Comparison",
        description="Produces telemetry comparison JSON for two drivers in the same session.",
        required_params=["year", "race", "session", "driver1", "driver2"],
        optional_params=["lap", "lap1", "lap2"],
        cli_flag_map={
            "year": "-y",
            "race": "-r",
            "session": "-s",
            "driver1": "-d",
            "driver2": "-d2",
            "lap": "--lap",
            "lap1": "--lap1",
            "lap2": "--lap2",
        },
        cache_patterns=["comparison_telemetry", "driver_comparison", "telemetry_comparison"],
        notes="GUI uses this for dual-driver telemetry charts.",
    ),
    _make_spec(
        "14",
        name="Race Position Changes",
        description="Tracks race position changes lap-by-lap for all drivers.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["race_position_changes", "position_changes"],
        notes="Feeds summary position charts within the race analysis GUI.",
    ),
    _make_spec(
        "14.1",
        name="Driver Statistics Overview",
        description="Summarises key performance statistics for a selected driver.",
        required_params=["year", "race", "session", "driver1"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "driver1": "-d"},
        cache_patterns=["driver_statistics_overview", "driver_summary"],
        notes="Provides driver snapshot data for the driver analysis module.",
    ),
    _make_spec(
        "14.2",
        name="Driver Telemetry Statistics",
        description="Computes aggregated telemetry statistics for a selected driver.",
        required_params=["year", "race", "session", "driver1"],
        optional_params=["driver2"],
        cli_flag_map={
            "year": "-y",
            "race": "-r",
            "session": "-s",
            "driver1": "-d",
            "driver2": "-d2",
        },
        cache_patterns=["driver_telemetry_statistics", "telemetry_statistics"],
        notes="Feeds the driver telemetry comparison panels; driver2 optional for contextual metrics.",
    ),
    _make_spec(
        "14.3",
        name="Driver Overtaking Analysis",
        description="Breaks down overtakes performed and defended by the selected driver.",
        required_params=["year", "race", "session", "driver1"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "driver1": "-d"},
        cache_patterns=["driver_overtaking_analysis", "overtaking_analysis"],
        notes="Used by the overtake deep-dive tab in the driver analysis module.",
    ),
    _make_spec(
        "14.4",
        name="Driver Fastest Lap Ranking",
        description="Provides fastest lap rankings and deltas for the selected context.",
        required_params=["year", "race", "session"],
        optional_params=["driver1"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "driver1": "-d"},
        cache_patterns=["driver_fastest_lap_ranking", "fastest_lap_report"],
        notes="Supports fastest lap comparisons for both single-driver and global views.",
    ),
    _make_spec(
        "14.9",
        name="All Drivers Comprehensive Report",
        description="Compiles an extended report covering all drivers' race metrics.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["all_drivers_comprehensive", "driver_comprehensive_full"],
        notes="Feeds in-depth PDF/GUI reports for post-race debriefs.",
    ),
    _make_spec(
        "25",
        name="Driver Race Position Analysis",
        description="Analyzes race position changes for a single driver or all drivers, including starting/finishing positions, lap-by-lap position tracking, and position statistics.",
        required_params=["year", "race", "session"],
        optional_params=["driver1"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "driver1": "-d"},
        cache_patterns=[
            "position_analysis_*_all_drivers",
            "position_analysis_*",
            "single_driver_position_analysis"
        ],
        notes="Driver parameter optional – when omitted analyzes all drivers. Provides starting position, finishing position, best/worst positions, lap-by-lap changes, and position statistics (average, median, time in top 5/10).",
    ),
    _make_spec(
        "29",
        name="FIA Parts Changes Analysis V2.0",
        description="Analyzes FIA technical document part changes with V2.0 classifier including confidence scoring and noise filtering. Provides comprehensive statistics on team upgrades, repairs, and modifications.",
        required_params=["year"],
        optional_params=["team", "driver", "race", "change_type", "min_confidence", "exclude_noise"],
        cli_flag_map={
            "year": "-y",
            "team": "--team",
            "driver": "-d",
            "race": "-r",
            "change_type": "--change-type",
            "min_confidence": "--min-confidence",
            "exclude_noise": "--include-noise"
        },
        cache_patterns=["fia_parts_analysis"],
        notes="Simplified parser with 15 main categories + 61 sub-categories, dynamic confidence scoring (0.60-0.95+), automatic noise filtering (default: exclude_noise=True). No FastF1 data required - reads from classified JSON files.",
    ),
    _make_spec(
        "26",
        name="Tire Strategy Analysis",
        description="Generates tire strategy timelines leveraging FastF1 cache data.",
        required_params=["year", "race", "session"],
        optional_params=["driver1"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "driver1": "-d"},
        cache_patterns=["driver_tire_strategy", "tire_strategy"],
        notes="Driver parameter optional – when omitted the analysis covers all drivers.",
    ),
    _make_spec(
        "28",
        name="Detailed Lap Analysis",
        description="Outputs per-lap timing breakdowns including markers and telemetry aggregates.",
        required_params=["year", "race", "session"],
        optional_params=["driver1"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "driver1": "-d"},
        cache_patterns=[
            "detailed_laptime_analysis",
            "detailed_driver_laptime",
            "driver_lap_time_analysis",
        ],
        notes="GUI detailed lap view consumes the JSON; driver optional for single-driver runs.",
    ),
_make_spec(
        "34",
        name="All Drivers Brake Performance",
        description="Analyzes brake performance for all drivers including maximum deceleration, brake distance and brake time.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["brake_performance", "all_drivers_brake_performance"],
        notes="Provides brake zone analysis data for GUI brake performance widgets. Calculates deceleration from hardcoded brake endpoints to earliest Brake=1 point.",
    ),
    _make_spec(
        "47",
        name="All Drivers Corner Performance Analysis",
        description="Analyzes cornering performance for all drivers across selected corners (low/mid/high-speed). Provides entry speed, apex speed, exit speed metrics with corner classification.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["all_drivers_cornering_analysis", "corner_performance", "cornering"],
        notes="CLI function -f 47. Outputs all_drivers_cornering_analysis_{year}_{race}_{session}.json with fastest_lap_analysis and selected_corners data for low/mid/high-speed corner visualizations.",
    ),
    _make_spec(
        "48",
        name="All Drivers Straight-Line Speed",
        description="Calculates the maximum straight-line speed achieved by every driver in the session.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["all_drivers_straight_line_speed", "straight_line_speed"],
        notes="Feeds the global straight-line speed chart for lap analysis modules.",
    ),
    _make_spec(
        "53",
        name="Ideal Lap Analysis (All Drivers)",
        description="Builds per-driver ideal lap from fastest sector times and provides rankings and comparisons.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["ideal_lap_ranking", "ideal_lap"],
        notes="CLI function -f 53. Outputs ideal_lap_ranking_{year}_{race}_{session}.json",
    ),
    _make_spec(
        "54",
        name="Throttle Box Plot Analysis",
        description="Generates box plot data for full-throttle duration per driver with outlier filtering.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["throttle_ratio", "throttle_box_plot", "lap_throttle_ratio"],
        notes="Provides per-driver full-throttle duration statistics for GUI box plot visualization.",
    ),
    _make_spec(
        "96",
        name="Race Weather Forecast",
        description="Returns 3-day weather forecast for the specified F1 race, including historical data from previous 2 years. Uses Open-Meteo API with automatic caching.",
        required_params=["year", "race"],
        optional_params=["force_refresh"],
        cli_flag_map={"year": "-y", "race": "-r"},
        cache_patterns=["race_weather_forecast"],
        notes="CLI function -f 96 generates weather forecast JSON for race events. Requires race parameter (e.g., 'Singapore', 'Japan').",
    ),
    _make_spec(
        "97",
        name="Championship Standings",
        description="Returns driver and constructor standings along with season summary statistics for the selected year.",
        required_params=["year"],
        optional_params=["force_refresh"],
        cli_flag_map={"year": "-y"},
        cache_patterns=["championship_standings"],
        notes="CLI function -f 97 exposes standings JSON consumed by GUI demos.",
    ),
    _make_spec(
        "98",
        name="Team Colour Export",
        description="Returns FastF1 team and driver colour mappings for the selected season.",
        required_params=[],
        optional_params=["year", "colormap"],
        cli_flag_map={"year": "-y", "colormap": "--colormap"},
        cache_patterns=["team_colors", "driver_colors"],
        notes="CLI function -f 98 exposes this colour palette for GUI/API consumption.",
    ),
    _make_spec(
        "73",
        name="v3.8 Batch Trainer (Qualifying Prediction Model Training)",
        description="Trains XGBoost qualifying prediction models using v3.8 feature set (17 features). Supports single track or all-track batch training with Optuna hyperparameter optimization.",
        required_params=[],
        optional_params=["trials", "cv_folds", "workers", "track"],
        cli_flag_map={
            "trials": "--trials",
            "cv_folds": "--cv-folds",
            "workers": "--workers",
            "track": "--track"
        },
        cache_patterns=["v3.8_training_results", "track_specific_v3.8"],
        notes="CLI function -f 73 trains qualifying prediction models. Returns training metrics (R², MAE, CV scores). Used by GUI qualifying prediction module to check model availability and quality.",
    ),
    _make_spec(
        "74",
        name="Qualifying Prediction Generator (v3.10 FP3→Q)",
        description="Generates qualifying predictions using trained v3.10 models. Loads FP3 data, extracts features, predicts Q times, and outputs JSON file to json/qualifying_prediction_{year}_{race}.json",
        required_params=["year", "race"],
        optional_params=[],
        cli_flag_map={
            "year": "-y",
            "race": "-r"
        },
        cache_patterns=["qualifying_prediction"],
        notes="CLI function -f 74 generates FP3→Q predictions JSON. Session is fixed to 'Q'. Requires pre-trained v3.10 model for the specified track (run -f 73 first). GUI module reads the generated JSON for display.",
    ),
    _make_spec(
        "75",
        name="FP2→Q Batch Trainer (XGBoost Model Training)",
        description="Trains XGBoost qualifying prediction models using FP2 data (v3.10 architecture, 16 features). Predicts qualifying results based on Friday FP2 practice sessions. Supports single track or all-track batch training.",
        required_params=[],
        optional_params=["trials", "cv_folds", "workers", "track", "start_year", "end_year"],
        cli_flag_map={
            "trials": "--trials",
            "cv_folds": "--cv-folds",
            "workers": "--workers",
            "track": "--track",
            "start_year": "--start-year",
            "end_year": "--end-year"
        },
        cache_patterns=["fp2_q_v3.10_training_results", "fp2_q_specific_v3.10"],
        notes="CLI function -f 75 trains FP2→Q prediction models. Expected accuracy is 5-10% lower than FP3→Q due to earlier prediction time. Returns training metrics (R², MAE, CV scores). Models saved to models/fp2_q_specific_v3.10/",
    ),
    _make_spec(
        "76",
        name="FP2→Q Qualifying Prediction Generator",
        description="Generates early qualifying predictions using FP2 data and trained v3.10 FP2→Q models. Provides Friday evening predictions before FP3. Outputs JSON file to json/fp2_qualifying_prediction_{year}_{race}.json",
        required_params=["year", "race"],
        optional_params=[],
        cli_flag_map={
            "year": "-y",
            "race": "-r"
        },
        cache_patterns=["fp2_qualifying_prediction"],
        notes="CLI function -f 76 generates FP2→Q predictions JSON. Requires pre-trained FP2→Q model for the specified track (run -f 75 first). Useful for early predictions on Friday evening before FP3 and qualifying.",
    ),
    _make_spec(
        "80",
        name="Dynamic Team Rating Analysis",
        description="Analyzes team performance using dynamic rating system based on 2023-2024 historical data with 2025 race updates. Generates JSON with team rankings, driver mappings, and rating changes for Q->R prediction.",
        required_params=[],
        optional_params=["year", "race"],
        cli_flag_map={
            "year": "-y",
            "race": "-r"
        },
        cache_patterns=["dynamic_team_rating"],
        notes="CLI function -f 80 generates dynamic team rating JSON to json/prediction/dynamic_team_rating_{timestamp}.json. Used by GUI Race Prediction module (Q->R) to predict race results based on qualifying positions and team ratings.",
    ),
    _make_spec(
        "99",
        name="Season Calendar Overview",
        description="Returns completed and upcoming events for the selected season using FastF1 schedule data. Supports multi-year mode with --all-years flag.",
        required_params=[],
        optional_params=["year"],
        cli_flag_map={"year": "-y"},
        cache_patterns=["season_calendar"],
        notes="CLI function -f 99 exposes this calendar for GUI/API consumption. Use --all-years for 2020-2025 batch query with smart refresh.",
    ),
    _make_spec(
        "100",
        name="Historical Flags Analysis",
        description="Analyzes historical flag events (Yellow, Double Yellow, Red, Safety Car) across multiple seasons (2022-2025) for a specific race track. Provides yearly statistics, corner-by-corner analysis, and detailed position records with track coordinates and elevation data.",
        required_params=["race"],
        optional_params=["year", "session", "start_year", "end_year"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s", "start_year": "--start-year", "end_year": "--end-year"},
        cache_patterns=["historical_flags_{race}"],
        notes="CLI function -f 100. Outputs historical_flags_{race}_{start_year}-{end_year}.json (FIXED FILENAME, no timestamp). Only requires race parameter. Year range defaults to 2022-2025, session defaults to 'R' (Race). Used by GUI Historical Track Map module for multi-season flag visualization. Simplified API: -f 100 -r [race]",
    ),
    _make_spec(
        "101",
        name="Season Start Reaction Analysis",
        description="Analyzes start reaction performance across all races in a season. Provides 0-50 km/h acceleration time distribution for all drivers, P1 (pole sitter) position retention statistics at end of Lap 2. Returns t50_distribution with quartiles, p1_lap2_position_unchanged count, and p1_lap2_position_changed count with race details.",
        required_params=[],
        optional_params=["year"],
        cli_flag_map={"year": "-y"},
        cache_patterns=["F101_season_start_reaction_{year}"],
        notes="CLI function -f 101. Outputs F101_season_start_reaction_{year}.json (FIXED FILENAME, no timestamp). Uses Live Timing data (CarData.json, SessionData.json, LapSeries.json). GUI uses t50_distribution for box plot chart and p1 stats for summary table. No race/session parameter needed - analyzes entire season.",
    ),
    _make_spec(
        "120",
        name="Corner All Laps Analysis",
        description="Analyzes all drivers' cornering performance across all laps with dual mode analysis (unified + grouped). Includes entry/apex/exit speeds with median-based outlier filtering. Returns entry_filtered and exit_filtered flags for GUI purple marker visualization.",
        required_params=["year", "race", "session"],
        optional_params=[],
        cli_flag_map={
            "year": "-y",
            "race": "-r",
            "session": "-s"
        },
        cache_patterns=["F120_corner_all_laps_analysis"],
        notes="CLI function -f 120. Outputs F120_corner_all_laps_analysis_{year}_{race}_{session}.json. Replaces deprecated function 47 for GUI corner analysis modules. Contains mode_a_unified (all laps) and mode_b_grouped (long_run/quali_sim). GUI uses entry_filtered/exit_filtered boolean flags to display filtered data points in purple (#D8BFD8).",
    ),
    _make_spec(
        "121",
        name="Straight Line All Laps Analysis",
        description="Analyzes all drivers' straight line speed performance across all valid laps using official API car_data. Replicates F48 acceleration logic (100→300 km/h + linear extrapolation to max speed) with unified analysis mode. Supports all session types (FP1/FP2/FP3/Q/R). Provides comprehensive statistics (median/mean/std_dev/min/max/q1/q3/iqr/cv) for speed, acceleration, and time-to-max calculations.",
        required_params=["year", "race", "session"],
        optional_params=[],
        cli_flag_map={
            "year": "-y",
            "race": "-r",
            "session": "-s"
        },
        cache_patterns=["fp2_straight_line_all_laps_analysis"],
        notes="CLI function -f 121. Outputs fp2_straight_line_all_laps_analysis_{year}_{race}_{session}.json. Unified analysis mode (Mode B removed 2025-12-14). Each driver entry includes: speed_stats, acceleration_100_300_stats, time_to_max_speed_stats, absolute_max_speed_kmh, absolute_max_speed_lap, speeds_raw, acceleration_times_raw, times_to_max_raw. Uses official API to avoid FastF1 interpolation issues.",
    ),
    _make_spec(
        "122",
        name="All Drivers Brake All Laps Analysis",
        description="Analyzes brake zone deceleration performance for all drivers across all valid laps. Uses voting-based brake zone detection to identify the main brake zone, then calculates per-driver max deceleration statistics (median/mean/std_dev/min/max/cv). Supports all session types (FP1/FP2/FP3/Q/R). Provides outlier detection and per-lap raw deceleration trends.",
        required_params=["year", "race", "session"],
        optional_params=[],
        cli_flag_map={
            "year": "-y",
            "race": "-r",
            "session": "-s"
        },
        cache_patterns=["brake_all_laps_analysis"],
        notes="CLI function -f 122. Outputs brake_all_laps_analysis_{year}_{race}_{session}.json. Each driver entry includes: brake_decel_stats (median/mean/std_dev/cv/min/max), raw_decel_trend (per-lap max_decel), valid_laps_count, outlier_count. Also includes main_brake_zone info (distance/avg_max_decel/detection_threshold/voter_count).",
    ),
    _make_spec(
        "126",
        name="Live Timing Weather Analysis",
        description="Fetches per-lap weather data from F1 official Live Timing API (WeatherData.jsonStream). Provides air temperature, track temperature, humidity, pressure, wind speed/direction, and rainfall status for each lap. Compatible with temp_analysis GUI module.",
        required_params=["year", "race", "session"],
        optional_params=[],
        cli_flag_map={
            "year": "-y",
            "race": "-r",
            "session": "-s"
        },
        cache_patterns=["live_timing_weather"],
        notes="CLI function -f 126. Outputs live_timing_weather_{year}_{race}_{session}.json. Uses F1 official Live Timing API (not FastF1 or OpenF1). Each lap entry includes: lap, air_temp, track_temp, humidity, pressure, wind_speed, wind_direction, rainfall. GUI-compatible format for temp_analysis module.",
    ),
    _make_spec(
        "127",
        name="Live Timing Traffic Distance Analysis",
        description="Analyzes traffic status (clean air / dirty air) for each driver per lap using distance-based thresholds. Excludes SC/VSC laps entirely. Provides timeline visualization data showing when each driver was in traffic or had clean air.",
        required_params=["year", "race", "session"],
        optional_params=[],
        cli_flag_map={
            "year": "-y",
            "race": "-r",
            "session": "-s"
        },
        cache_patterns=["live_timing_traffic_distance"],
        notes="CLI function -f 127. Outputs live_timing_traffic_distance_{year}_{race}_{session}.json. Uses F1 official Live Timing API. Each driver entry includes per-lap traffic status (clean/traffic/excluded), total laps count, clean air percentage, traffic percentage. GUI-compatible format for traffic_timeline module.",
    ),
    _make_spec(
        "143",
        name="FIA Season Statistics",
        description="Downloads and parses FIA official documents (Power Unit elements allocation & Parts changes) from fia.com. Returns per-driver PU element usage counts (ICE/TC/MGU-H/MGU-K/ES/CE) and all parts change records for the specified season. Supports seasons 2023-2025. PU limits: ICE/TC/MGU-H=4, MGU-K/ES/CE=3 per season.",
        required_params=["year"],
        optional_params=[],
        cli_flag_map={
            "year": "-y"
        },
        cache_patterns=["fia_season_stats"],
        notes="CLI function -f 143. Outputs fia_season_stats_{year}.json. Downloads PDF documents from FIA website, parses tables to extract driver-level PU usage and parts change history. GUI displays color-coded status: green (normal), orange (at limit), red (exceeded).",
    ),
]


FUNCTION_SPECS: Dict[str, FunctionSpec] = {}
_FUNCTION_ALIAS_INDEX: Dict[str, str] = {}

for spec in _FUNCTION_SPEC_LIST:
    if spec.function_id in FUNCTION_SPECS:
        raise ValueError(f"Duplicate function_id detected: {spec.function_id}")
    FUNCTION_SPECS[spec.function_id] = spec
    for alias in spec.aliases:
        if alias in _FUNCTION_ALIAS_INDEX and _FUNCTION_ALIAS_INDEX[alias] != spec.function_id:
            raise ValueError(f"Alias {alias} already registered for {_FUNCTION_ALIAS_INDEX[alias]}")
        _FUNCTION_ALIAS_INDEX[alias] = spec.function_id


def get_function_spec(function_id: NumberLike | FunctionSpec) -> FunctionSpec:
    """Return the specification for the requested function ID."""

    normalized = normalize_function_id(function_id)
    if normalized in FUNCTION_SPECS:
        return FUNCTION_SPECS[normalized]

    alias_target = _FUNCTION_ALIAS_INDEX.get(normalized)
    if alias_target:
        return FUNCTION_SPECS[alias_target]

    raise KeyError(f"Unsupported function_id: {function_id}")


def iter_function_specs() -> Iterator[FunctionSpec]:
    """Iterate over function specs sorted by canonical ID."""

    for function_id in sorted(FUNCTION_SPECS.keys(), key=function_id_sort_key):
        yield FUNCTION_SPECS[function_id]


__all__ = [
    "FunctionSpec",
    "FUNCTION_SPECS",
    "normalize_function_id",
    "function_id_sort_key",
    "get_function_spec",
    "iter_function_specs",
]
