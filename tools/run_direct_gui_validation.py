#!/usr/bin/env python3
"""Validate selected GUI modules without importing the crashing main window."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("F1T_RUNTIME_MODE", "local")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidget, QWidget


LOG_DIR = ROOT / "logs"
FAIL_TEXT = (
    "load failed",
    "api request failed",
    "api 載入失敗",
    "api 隢",
    "failed",
    "under development",
    "waiting for data",
    "no data available",
)


def _process(duration: float = 0.2) -> None:
    end_at = time.time() + max(duration, 0.0)
    while time.time() < end_at:
        QCoreApplication.processEvents()
        time.sleep(0.01)


def _wait_until(predicate: Callable[[], bool], timeout: float = 20.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        _process(0.1)
        if predicate():
            return True
    return predicate()


def _patch_message_boxes() -> None:
    def _stub(*_args: Any, **_kwargs: Any) -> int:
        return QMessageBox.Ok

    QMessageBox.information = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.warning = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.critical = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.question = staticmethod(_stub)  # type: ignore[method-assign]


def _texts(widget: QWidget, limit: int = 300) -> List[str]:
    values: List[str] = []
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
                values.append(text)
        if len(values) >= limit:
            break
    return values


def _table_rows(widget: QWidget) -> List[int]:
    return [int(table.rowCount()) for table in widget.findChildren(QTableWidget)]


def _plot_signal(widget: QWidget) -> Dict[str, int]:
    signal = {"axes": 0, "lines": 0, "collections": 0, "images": 0, "non_empty_lines": 0}
    for child in [widget, *widget.findChildren(QWidget)]:
        fig = getattr(child, "figure", None)
        if fig is None:
            continue
        for ax in list(getattr(fig, "axes", []) or []):
            signal["axes"] += 1
            lines = list(getattr(ax, "lines", []) or [])
            cols = list(getattr(ax, "collections", []) or [])
            imgs = list(getattr(ax, "images", []) or [])
            signal["lines"] += len(lines)
            signal["collections"] += len(cols)
            signal["images"] += len(imgs)
            for line in lines:
                try:
                    if len(line.get_xdata()) > 0 and len(line.get_ydata()) > 0:
                        signal["non_empty_lines"] += 1
                except Exception:
                    pass
    return signal


def _snapshot(name: str, widget: QWidget, extras: Optional[List[Any]] = None) -> Dict[str, Any]:
    rows = _table_rows(widget)
    texts = _texts(widget)
    failures = [t for t in texts if any(token in t.lower() for token in FAIL_TEXT)]
    plot = _plot_signal(widget)
    data_attrs: Dict[str, Any] = {}
    objects: List[Any] = [widget, *widget.findChildren(QWidget)]
    for extra in extras or []:
        objects.extend([extra, getattr(extra, "data_manager", None), getattr(extra, "chart_widget", None)])
    for obj in [item for item in objects if item is not None]:
        obj_name = type(obj).__name__
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
            "speed_data",
            "track_data",
            "weather_data",
            "position_data",
        ):
            if not hasattr(obj, attr):
                continue
            try:
                value = getattr(obj, attr)
            except Exception:
                continue
            key = f"{obj_name}.{attr}"
            if isinstance(value, dict):
                data_attrs[key] = {"type": "dict", "size": len(value)}
            elif isinstance(value, (list, tuple, set)):
                data_attrs[key] = {"type": type(value).__name__, "size": len(value)}
            elif isinstance(value, bool):
                data_attrs[key] = {"type": "bool", "value": value}
    loaded = (
        any(row > 0 for row in rows)
        or plot["non_empty_lines"] > 0
        or plot["collections"] > 0
        or plot["images"] > 0
        or any(v.get("size", 0) > 0 for v in data_attrs.values() if isinstance(v, dict))
        or any(v.get("value") is True for v in data_attrs.values() if isinstance(v, dict))
    )
    return {
        "name": name,
        "ok": bool(loaded and not failures),
        "table_rows": rows,
        "plot": plot,
        "data_attrs": data_attrs,
        "failure_texts": failures[:20],
    }


def _as_widget(candidate: Any) -> QWidget:
    if isinstance(candidate, QWidget):
        return candidate
    if hasattr(candidate, "get_widget"):
        widget = candidate.get_widget()
        if isinstance(widget, QWidget):
            return widget
    raise TypeError(f"{type(candidate).__name__} is not a QWidget and has no QWidget get_widget()")


def _run_module(name: str, widget: Any, trigger: Callable[[], Any], wait: Callable[[], bool]) -> Dict[str, Any]:
    original = widget
    visible_widget = _as_widget(widget)
    visible_widget.resize(1000, 650)
    visible_widget.show()
    _process(0.5)
    error: Optional[str] = None
    try:
        trigger()
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    _wait_until(wait, timeout=25.0)
    _process(0.8)
    result = _snapshot(name, visible_widget, extras=[original])
    if error:
        result["ok"] = False
        result["error"] = error
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--race", default="Japan")
    parser.add_argument("--session", default="R")
    parser.add_argument("--report", type=Path, default=LOG_DIR / "direct_gui_validation_2026_japan.json")
    parser.add_argument("--screenshot", type=Path, default=LOG_DIR / "direct_gui_validation_2026_japan.png")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _patch_message_boxes()
    app = QApplication.instance() or QApplication([])

    results: List[Dict[str, Any]] = []

    from modules.gui.race_analysis.temp.temp_analysis_mdi import TempAnalysisUniversal
    from modules.gui.race_analysis.track.track_analysis_mdi import TrackAnalysisUniversal
    from modules.gui.race_analysis.pitstop.pitstop_analysis_mdi import PitstopAnalysisModule
    from modules.gui.race_analysis.accident.accident_analysis_mdi_simple import AccidentAnalysisModule
    from modules.gui.race_analysis.position.driver_position_analysis_mdi import DriverPositionAnalysisMDI
    from modules.gui.tire_analysis.tire_analysis_mdi import TireAnalysisUniversal
    from modules.gui.long_run_analysis.long_run_mdi_simple import LongRunAnalysis
    from modules.gui.multi_season.season_start_reaction.season_start_reaction_mdi import SeasonStartReactionAnalysis
    from modules.gui.multi_season.pole_defense.pole_defense_mdi import PoleDefenseAnalysis
    from modules.gui.multi_season.fia_season_stats.fia_season_stats_mdi import FiaSeasonStatsAnalysis

    temp = TempAnalysisUniversal()
    results.append(
        _run_module(
            "Temperature Analysis",
            temp,
            lambda: temp.update_lap_parameters(str(args.year), args.race, args.session),
            lambda: bool(getattr(temp.data_manager, "_current_data", None)),
        )
    )

    track = TrackAnalysisUniversal()
    results.append(
        _run_module(
            "Track Analysis",
            track,
            lambda: track.data_manager.load_data(year=args.year, race=args.race, session=args.session),
            lambda: bool(getattr(track.data_manager, "_current_data", None)),
        )
    )

    pitstop = PitstopAnalysisModule()
    pitstop.initialize_module()
    pitstop.update_parameters(args.year, args.race, args.session)
    pit_widget = pitstop.get_widget()
    results.append(
        _run_module(
            "Pitstop Analysis",
            pit_widget,
            lambda: pitstop.load_data(),
            lambda: any(row > 0 for row in _table_rows(pit_widget)),
        )
    )

    accident = AccidentAnalysisModule()
    accident.initialize_module()
    acc_widget = accident.get_widget()
    results.append(
        _run_module(
            "Accident Analysis",
            acc_widget,
            lambda: accident.update_parameters(args.year, args.race, args.session),
            lambda: any(row > 0 for row in _table_rows(acc_widget)),
        )
    )

    tire = TireAnalysisUniversal()
    results.append(
        _run_module(
            "Tire Strategy Analysis",
            tire,
            lambda: tire.update_lap_parameters(str(args.year), args.race, args.session),
            lambda: bool(getattr(tire.data_manager, "_current_data", None)),
        )
    )

    position = DriverPositionAnalysisMDI()
    position.current_year = str(args.year)
    position.current_race = args.race
    position.current_session = args.session
    position.initialize_module()
    results.append(
        _run_module(
            "Driver Race Position",
            position,
            lambda: position.update_parameters(args.year, args.race, args.session),
            lambda: bool(getattr(position, "_is_data_loaded", False)),
        )
    )

    long_run = LongRunAnalysis(args.year, args.race, args.session)
    results.append(
        _run_module(
            "Long Run & Degradation",
            long_run,
            lambda: long_run.refresh_data(),
            lambda: any(row > 0 for row in _table_rows(long_run)),
        )
    )

    season_start = SeasonStartReactionAnalysis(year=args.year)
    results.append(
        _run_module(
            "Season Start Reaction",
            season_start,
            lambda: season_start.update_lap_parameters(str(args.year)),
            lambda: bool(getattr(season_start.chart_widget, "driver_t50_data", None)),
        )
    )

    pole = PoleDefenseAnalysis(year=args.year)
    results.append(
        _run_module(
            "Pole Defense Statistics",
            pole,
            lambda: pole.update_lap_parameters(str(args.year)),
            lambda: bool(getattr(pole.chart_widget, "driver_pole_data", None)),
        )
    )

    fia = FiaSeasonStatsAnalysis(year=args.year)
    results.append(
        _run_module(
            "FIA Season Statistics",
            fia,
            lambda: fia.update_lap_parameters(str(args.year)),
            lambda: any(row > 0 for row in _table_rows(fia)),
        )
    )

    # Include all widgets in one screenshot area where possible.
    app.processEvents()
    if results:
        try:
            fia.grab().save(str(args.screenshot))
        except Exception:
            pass

    ok = all(item.get("ok") for item in results)
    report = {"ok": ok, "year": args.year, "race": args.race, "session": args.session, "results": results}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
