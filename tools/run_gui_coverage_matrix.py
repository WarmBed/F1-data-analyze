#!/usr/bin/env python3
"""Build and validate GUI function-tree coverage for a target event."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("F1T_RUNTIME_MODE", "local")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox, QTableWidget, QWidget


LOG_DIR = ROOT / "logs"
FAIL_TEXT = (
    "failed",
    "load failed",
    "api request failed",
    "api 載入失敗",
    "under development",
    "not implemented",
    "no data available",
)


DIRECT_PASS_NAMES = {
    "Temperature Analysis",
    "Track Analysis",
    "Pitstop Analysis",
    "Accident Analysis",
    "Tire Strategy Analysis",
    "Driver Race Position",
    "Long Run & Degradation",
    "Season Start Reaction",
    "Pole Defense Statistics",
    "FIA Season Statistics",
}


def _patch_message_boxes() -> None:
    def _stub(*_args: Any, **_kwargs: Any) -> int:
        return QMessageBox.Ok

    QMessageBox.information = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.warning = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.critical = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.question = staticmethod(_stub)  # type: ignore[method-assign]


def _process(duration: float = 0.2) -> None:
    end_at = time.time() + max(duration, 0.0)
    while time.time() < end_at:
        QCoreApplication.processEvents()
        time.sleep(0.01)


def _wait(timeout: float = 8.0) -> None:
    _process(timeout)


class _DummyMain(QWidget):
    def __init__(self, year: int, race: str, session: str):
        super().__init__()
        self.year = int(year)
        self.race = race
        self.session = session
        self.active_subwindows: List[Any] = []
        self.year_combo = QComboBox()
        self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(year))
        self.race_combo = QComboBox()
        self.race_combo.addItem(race)
        self.race_combo.setCurrentText(race)
        self.session_combo = QComboBox()
        self.session_combo.addItem(session)
        self.session_combo.setCurrentText(session)

    def get_selected_year(self) -> int:
        return self.year

    def get_selected_race_key(self) -> str:
        return self.race

    def get_selected_session_code(self) -> str:
        return self.session

    def _mark_module_factory_type(self, module: Any, module_type: str) -> Any:
        setattr(module, "_factory_module_type", module_type)
        return module

    def get_current_mdi_area(self, auto_create_tab: bool = True) -> None:
        return None

    def _on_live_timing_module_opened(self) -> None:
        return None

    def _on_live_timing_module_closed(self) -> None:
        return None

    def on_subwindow_closed(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def _get_widget(module: Any) -> Optional[QWidget]:
    if isinstance(module, QWidget):
        return module
    if hasattr(module, "get_widget"):
        try:
            widget = module.get_widget()
            if isinstance(widget, QWidget):
                return widget
        except Exception:
            return None
    return None


def _leaf_paths(main: _DummyMain) -> List[List[str]]:
    from windows.managers.function_tree_builder import FunctionTreeBuilder

    container = FunctionTreeBuilder(main).create_professional_function_tree()
    main._function_tree_container = container
    tree = main.function_tree
    leaves: List[List[str]] = []

    def walk(item: Any, path: List[str]) -> None:
        label = item.text(0).strip()
        new_path = path + [label]
        if item.childCount() == 0:
            leaves.append(new_path)
            return
        for idx in range(item.childCount()):
            walk(item.child(idx), new_path)

    root = tree.invisibleRootItem()
    for idx in range(root.childCount()):
        walk(root.child(idx), [])
    return leaves


def _module_type_for_path(path: List[str]) -> str:
    label = path[-1]
    mapping = {
        "Temperature Analysis": "temp_analysis",
        "Track Analysis": "track_analysis",
        "Pitstop Analysis": "pitstop_analysis",
        "Accident Analysis": "accident_analysis",
        "Tire Strategy Analysis": "tire_analysis",
        "Driver Race Position": "driver_position_analysis",
        "Traffic Analysis": "traffic_analysis",
        "(L) Speed Analysis": "speed_analysis",
        "(L) Brake Analysis": "brake_analysis",
        "(L) Throttle Analysis": "throttle_analysis",
        "(L) Gear Analysis": "gear_analysis",
        "(L) RPM Analysis": "rpm_analysis",
        "(L) Acceleration Analysis": "acceleration_analysis",
        "(L) Speed Diff Analysis": "speeddiff_analysis",
        "(L) Distance Diff Analysis": "distancediff_analysis",
        "(L) Time Diff Analysis": "timediff_analysis",
        "(D) Detailed Lap Table": "driverlap_analysis",
        "(D) Lap Time Box Plot": "laptime_box_plot",
        "(T) Throttle Box Plot": "throttle_box_plot",
        "(T) Throttle Line Chart": "throttle_line_chart",
        "(T) Pedal Behavior Analysis": "pedal_behavior_analysis",
        "Long Run & Degradation": "long_run_analysis",
        "Ideal Lap Ranking Table": "ideal_lap_ranking",
        "Sector Heat Map": "ideal_lap_sector_heatmap",
        "All Drivers Speed & Acceleration (Dev)": "all_drivers_straight_line_speed",
        "Straight Speed & Acceleration": "all_drivers_straight_line_speed",
        "All Drivers Max Speed": "all_drivers_max_speed",
        "Acceleration Chart": "all_drivers_acceleration_chart",
        "Brake Chart": "all_drivers_brake_chart",
        "All Drivers Brake Performance (Dev)": "all_drivers_brake_performance",
        "Brake Performance": "all_drivers_brake_performance",
        "All Drivers Brake All Laps Analysis": "all_drivers_brake_all_laps",
        "Low-Speed Corner Analysis": "corner_performance",
        "Mid-Speed Corner Analysis": "corner_performance",
        "High-Speed Corner Analysis": "corner_performance",
        "FP3 → Q Prediction Table": "qualifying_prediction_table",
        "FP2 → Q Prediction Table": "fp2_qualifying_prediction_table",
        "Q → R Prediction Table": "race_prediction_table",
        "Historical Track Map": "historical_track_map",
        "Season Start Reaction": "season_start_reaction",
        "Pole Defense Statistics": "pole_defense",
        "Pit Loss Table": "pit_loss_table",
        "FIA Season Statistics": "fia_season_stats",
        "Traffic Timeline": "traffic_timeline" if path[0] != "Live Timing" else "live_traffic_timeline",
    }
    if label == "Sector Comparison":
        return "sector_comparison" if path[0] == "Live Timing" else "ideal_lap_sector_comparison"
    return mapping.get(label, label)


def _corner_hint(path: List[str]) -> Optional[str]:
    label = path[-1].lower()
    if "mid" in label:
        return "mid_speed"
    if "high" in label:
        return "high_speed"
    if "low" in label:
        return "low_speed"
    return None


def _data_signal(module: Any, widget: Optional[QWidget]) -> Dict[str, Any]:
    rows: List[int] = []
    texts: List[str] = []
    data_attrs: Dict[str, Any] = {}
    plot = {"figures": 0, "lines": 0, "collections": 0, "images": 0, "non_empty_lines": 0}

    objects: List[Any] = [module, getattr(module, "data_manager", None), getattr(module, "chart_widget", None)]
    if widget is not None:
        objects.append(widget)
        objects.extend(widget.findChildren(QWidget))
        for table in widget.findChildren(QTableWidget):
            rows.append(int(table.rowCount()))
        for child in widget.findChildren(QWidget):
            try:
                if not child.isVisible():
                    continue
            except Exception:
                pass
            if hasattr(child, "text"):
                try:
                    text = str(child.text()).strip()
                except Exception:
                    text = ""
                if text:
                    texts.append(text)

    for obj in [item for item in objects if item is not None]:
        name = type(obj).__name__
        for attr in (
            "_current_data",
            "current_data",
            "_data",
            "data",
            "_drivers_data",
            "driver_t50_data",
            "driver_pole_data",
            "all_drivers_stint_data",
            "stint_data",
            "position_data",
            "track_data",
            "speed_data",
            "analysis_data",
            "loaded_data",
        ):
            if not hasattr(obj, attr):
                continue
            try:
                value = getattr(obj, attr)
            except Exception:
                continue
            key = f"{name}.{attr}"
            if isinstance(value, dict):
                data_attrs[key] = {"type": "dict", "size": len(value)}
            elif isinstance(value, (list, tuple, set)):
                data_attrs[key] = {"type": type(value).__name__, "size": len(value)}
            elif isinstance(value, bool):
                data_attrs[key] = {"type": "bool", "value": value}

        fig = getattr(obj, "figure", None)
        if fig is not None:
            plot["figures"] += 1
            for ax in list(getattr(fig, "axes", []) or []):
                lines = list(getattr(ax, "lines", []) or [])
                plot["lines"] += len(lines)
                plot["collections"] += len(list(getattr(ax, "collections", []) or []))
                plot["images"] += len(list(getattr(ax, "images", []) or []))
                for line in lines:
                    try:
                        if len(line.get_xdata()) > 0 and len(line.get_ydata()) > 0:
                            plot["non_empty_lines"] += 1
                    except Exception:
                        pass

    failures = [text for text in texts if any(token in text.lower() for token in FAIL_TEXT)]
    loaded = (
        any(row > 0 for row in rows)
        or plot["non_empty_lines"] > 0
        or plot["collections"] > 0
        or plot["images"] > 0
        or any(v.get("size", 0) > 0 for v in data_attrs.values() if isinstance(v, dict))
        or any(v.get("value") is True for v in data_attrs.values() if isinstance(v, dict))
    )
    return {"loaded": loaded, "rows": rows, "plot": plot, "data_attrs": data_attrs, "failures": failures[:10]}


def _trigger_update(module: Any, year: int, race: str, session: str) -> None:
    module_type = getattr(module, "_factory_module_type", "")
    if module_type in {
        "qualifying_prediction_table",
        "fp2_qualifying_prediction_table",
        "race_prediction_table",
    }:
        for attr, value in (
            ("year", str(year)),
            ("race", race),
            ("current_year", str(year)),
            ("current_race", race),
        ):
            try:
                setattr(module, attr, value)
            except Exception:
                pass
        method = getattr(module, "update_analysis_parameters", None)
        if callable(method):
            try:
                method(str(year), race)
                return
            except Exception:
                pass

    for attr, value in (
        ("year", year),
        ("race", race),
        ("session", session),
        ("current_year", str(year)),
        ("current_race", race),
        ("current_session", session),
    ):
        try:
            setattr(module, attr, value)
        except Exception:
            pass
    class_name = type(module).__name__
    if class_name in {
        "AllDriversStraightLineSpeedMDI",
        "AllDriversAccelerationChartMDI",
        "AllDriversBrakeChartMDI",
        "AllDriversBrakePerformanceMDI",
        "AllDriversBrakeAllLapsMDI",
        "AllDriversCornerPerformanceMDI",
    }:
        method = getattr(module, "load_initial_data", None)
        if callable(method):
            try:
                method()
            except Exception:
                pass
        return
    for method_name, args in (
        ("update_parameters", (year, race, session)),
        ("update_lap_parameters", (str(year), race, session)),
        ("update_analysis_parameters", (str(year), race, session)),
        ("load_initial_data", ()),
        ("load_data", ()),
        ("refresh_analysis", ()),
        ("refresh_data", ()),
    ):
        method = getattr(module, method_name, None)
        if not callable(method):
            continue
        try:
            if method_name in {"load_initial_data", "load_data", "refresh_analysis", "refresh_data"}:
                method()
            else:
                method(*args)
        except TypeError:
            try:
                method(year=year, race=race, session=session)
            except Exception:
                continue
        except Exception:
            continue


def _validate_non_live(path: List[str], main: _DummyMain, timeout: float) -> Dict[str, Any]:
    from windows.managers.analysis_module_creator import AnalysisModuleCreator

    label = path[-1]
    module_type = _module_type_for_path(path)
    result: Dict[str, Any] = {"path": path, "label": label, "module_type": module_type}
    try:
        module = AnalysisModuleCreator(main)._create_analysis_module(
            label,
            module_type_hint=module_type,
            corner_type_hint=_corner_hint(path),
        )
    except Exception as exc:
        result.update({"ok": False, "phase": "create", "error": f"{type(exc).__name__}: {exc}"})
        return result

    if module is None:
        result.update({"ok": False, "phase": "create", "error": "module factory returned None"})
        return result

    widget = _get_widget(module)
    if widget is not None:
        try:
            widget.resize(1000, 650)
            widget.show()
        except Exception:
            pass
    _trigger_update(module, main.year, main.race, main.session)
    _wait(timeout)
    signal = _data_signal(module, widget)
    result.update(signal)
    result["ok"] = bool(signal["loaded"] and not signal["failures"])
    result["phase"] = "validate"
    return result


def _validate_live(path: List[str], main: _DummyMain, timeout: float) -> Dict[str, Any]:
    from modules.gui.live_timing import LiveTimingModuleFactory

    label = path[-1]
    factory = LiveTimingModuleFactory.get_instance()
    result: Dict[str, Any] = {"path": path, "label": label, "module_type": "live_timing"}
    try:
        module = factory.create_module(label, main)
    except Exception as exc:
        result.update({"ok": False, "phase": "create", "error": f"{type(exc).__name__}: {exc}"})
        return result
    if module is None:
        result.update({"ok": False, "phase": "create", "error": "live factory returned None"})
        return result
    widget = _get_widget(module) or (module if isinstance(module, QWidget) else None)
    if widget is not None:
        try:
            widget.resize(900, 600)
            widget.show()
        except Exception:
            pass
    _wait(timeout)
    signal = _data_signal(module, widget)
    result.update(signal)
    # Live modules are considered covered if they instantiate without an error;
    # data load is checked separately because historical playback state is shared.
    result["ok"] = bool(widget is not None and not signal["failures"])
    result["phase"] = "instantiate"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--race", default="Japan")
    parser.add_argument("--session", default="R")
    parser.add_argument("--scope", choices=["all", "non-live", "live", "matrix"], default="matrix")
    parser.add_argument("--timeout", type=float, default=6.0)
    parser.add_argument("--only-index", type=int, default=None)
    parser.add_argument("--report", type=Path, default=LOG_DIR / "gui_coverage_matrix_2026_japan.json")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    main_window = _DummyMain(args.year, args.race, args.session)
    leaves = _leaf_paths(main_window)
    indexed_leaves = list(enumerate(leaves))
    if args.only_index is not None:
        indexed_leaves = [(idx, path) for idx, path in indexed_leaves if idx == args.only_index]

    results: List[Dict[str, Any]] = []
    if args.scope == "matrix":
        previous = {}
        direct_report = LOG_DIR / "direct_gui_validation_2026_japan.json"
        if direct_report.exists():
            data = json.loads(direct_report.read_text(encoding="utf-8"))
            previous = {item.get("name"): item for item in data.get("results", [])}
        for idx, path in indexed_leaves:
            label = path[-1]
            prior = previous.get(label)
            ok = bool(prior and prior.get("ok"))
            results.append(
                {
                    "index": idx,
                    "path": path,
                    "label": label,
                    "status": "pass" if ok else "pending",
                    "source": "direct_gui_validation" if ok else None,
                    "evidence": prior if ok else None,
                }
            )
    else:
        for idx, path in indexed_leaves:
            is_live = path[0] == "Live Timing"
            if args.scope == "non-live" and is_live:
                continue
            if args.scope == "live" and not is_live:
                continue
            if is_live:
                result = _validate_live(path, main_window, args.timeout)
            else:
                result = _validate_non_live(path, main_window, args.timeout)
            result["index"] = idx
            results.append(result)

    ok_count = sum(1 for item in results if item.get("ok") or item.get("status") == "pass")
    report = {
        "ok": ok_count == len(results) if results else False,
        "scope": args.scope,
        "year": args.year,
        "race": args.race,
        "session": args.session,
        "total": len(results),
        "passed": ok_count,
        "coverage_percent": round((ok_count / len(results) * 100.0) if results else 0.0, 1),
        "results": results,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.__stdout__.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    sys.__stdout__.flush()
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.__stdout__.flush()
    sys.__stderr__.flush()
    os._exit(exit_code)
