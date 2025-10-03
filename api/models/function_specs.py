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
        "48",
        name="All Drivers Straight-Line Speed",
        description="Calculates the maximum straight-line speed achieved by every driver in the session.",
        required_params=["year", "race", "session"],
        cli_flag_map={"year": "-y", "race": "-r", "session": "-s"},
        cache_patterns=["all_drivers_straight_line_speed", "straight_line_speed"],
        notes="Feeds the global straight-line speed chart for lap analysis modules.",
    ),
    _make_spec(
        "99",
        name="Season Calendar Overview",
        description="Returns completed and upcoming events for the selected season using FastF1 schedule data.",
        required_params=["year"],
        cli_flag_map={"year": "-y"},
        cache_patterns=["season_calendar"],
        notes="CLI function -f 99 exposes this calendar for GUI/API consumption.",
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
