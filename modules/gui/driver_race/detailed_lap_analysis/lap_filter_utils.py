"""Utility helpers for filtering caution laps in detailed lap analysis views."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Set

CAUTION_INCIDENT_TYPES = {
    "yellow_flag",
    "double_yellow",
    "double-yellow",
    "safety_car",
    "virtual_safety_car",
    "virtual-safety-car",
    "vsc",
    "full_course_yellow",
    "full-course-yellow",
    "full_course_caution",
    "code60",
}

CAUTION_FLAG_VALUES = {
    "yellow",
    "double yellow",
    "yellow flag",
    "yellow_flag",
    "double-yellow",
    "yellow-flag",
    "full course yellow",
    "fcy",
}

CAUTION_STATUS_DIGITS = {"2", "3", "4", "5", "6", "7"}

CAUTION_SUMMARY_KEYS: Iterable[str] = (
    "incident_lap_numbers",
    "yellow_flag_lap_numbers",
    "caution_lap_numbers",
    "safety_car_lap_numbers",
    "vsc_lap_numbers",
)


def normalize_lap_number(value: Any) -> Optional[int]:
    """Convert a lap number to an int when possible."""
    if isinstance(value, bool):  # bool is subclass of int; guard against accidental bools
        return int(value) if value else None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value:  # NaN check
            return None
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.isdigit():
            return int(stripped)
        try:
            return int(float(stripped))
        except (TypeError, ValueError):
            return None
    return None


def extract_caution_laps(driver_data: Dict[str, Any]) -> Set[int]:
    """Gather lap numbers flagged as caution from summary data."""
    caution_laps: Set[int] = set()

    summary = driver_data.get("smart_markers_summary", {})
    safety_summary = summary.get("accident_safety_detection", {})
    if not isinstance(safety_summary, dict):
        return caution_laps

    for key in CAUTION_SUMMARY_KEYS:
        laps = safety_summary.get(key)
        if isinstance(laps, (list, tuple, set)):
            for lap in laps:
                lap_int = normalize_lap_number(lap)
                if lap_int is not None:
                    caution_laps.add(lap_int)
    return caution_laps


def _extract_safety_marker(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    if "smart_markers" in data:
        smart_markers = data.get("smart_markers", {})
    else:
        smart_markers = data

    if isinstance(smart_markers, dict):
        safety_marker = smart_markers.get("accident_safety_detection", {})
        if isinstance(safety_marker, dict):
            return safety_marker
    return {}


def _track_status_indicates_caution(code: Any) -> bool:
    if code is None:
        return False
    text = str(code).strip()
    if not text:
        return False
    return any(ch in CAUTION_STATUS_DIGITS for ch in text if ch.isdigit())


def is_caution_lap(lap_or_markers: Dict[str, Any]) -> bool:
    """Determine whether a lap contains a caution (yellow/SC/VSC) condition."""
    safety_marker = _extract_safety_marker(lap_or_markers)
    if not safety_marker:
        return False

    incident_type = str(safety_marker.get("incident_type", "")).strip().lower()
    if incident_type in CAUTION_INCIDENT_TYPES:
        return True

    flag_value = str(safety_marker.get("flag", "") or safety_marker.get("flag_color", "")).strip().lower()
    if flag_value in CAUTION_FLAG_VALUES:
        return True

    track_status = safety_marker.get("track_status_code") or safety_marker.get("track_status")
    if _track_status_indicates_caution(track_status):
        return True

    description = str(safety_marker.get("description", "")).lower()
    if any(keyword in description for keyword in ("yellow", "safety car", "vsc", "full course")):
        return True

    return False


def lap_is_under_caution(
    lap_number: Any,
    lap_info: Dict[str, Any],
    caution_laps: Optional[Set[int]] = None,
) -> bool:
    """Check if a lap should be treated as caution using summary sets and detailed markers."""
    lap_int = normalize_lap_number(lap_number)
    if lap_int is not None and caution_laps and lap_int in caution_laps:
        return True
    return is_caution_lap(lap_info)


def lap_is_pit_stop(
    lap_info: Dict[str, Any],
    smart_markers_summary: Optional[Dict[str, Any]] = None,
) -> bool:
    """Determine whether the provided lap data corresponds to a pit stop lap."""

    if not isinstance(lap_info, dict):
        return False

    lap_raw = lap_info.get("lap_number")
    lap_int = normalize_lap_number(lap_raw)

    summary = smart_markers_summary
    if summary is None and isinstance(lap_info.get("smart_markers_summary"), dict):
        summary = lap_info.get("smart_markers_summary")
    if not isinstance(summary, dict):
        summary = {}

    pit_summary = summary.get("pit_stop_detection", {})

    def _collection_contains(collection: Any) -> bool:
        if not isinstance(collection, (list, tuple, set)):
            return False
        if lap_int is not None:
            return any(normalize_lap_number(value) == lap_int for value in collection)
        return lap_raw in collection

    if _collection_contains(pit_summary.get("pit_lap_numbers")):
        return True

    smart_markers = lap_info.get("smart_markers", {})
    if isinstance(smart_markers, dict):
        pit_detail = smart_markers.get("pit_stop_detection", {})
        if isinstance(pit_detail, dict) and pit_detail.get("is_pit_lap", False):
            return True

    return False
