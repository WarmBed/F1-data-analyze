#!/usr/bin/env python3
"""Validate Live Timing modules against a loaded historical replay cache."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("F1T_RUNTIME_MODE", "local")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QLabel, QGridLayout, QTableWidget, QWidget

from tools.run_gui_coverage_matrix import _DummyMain, _data_signal, _get_widget, _leaf_paths


LOG_DIR = ROOT / "logs"
FAIL_TEXT = (
    "failed",
    "load failed",
    "api request failed",
    "under development",
    "not implemented",
    "no data available",
    "waiting for data",
)


def _process(duration: float = 0.2) -> None:
    end_at = time.time() + max(duration, 0.0)
    while time.time() < end_at:
        QCoreApplication.processEvents()
        time.sleep(0.01)


def _session_name(code: str) -> str:
    return {
        "R": "Race",
        "Q": "Qualifying",
        "S": "Sprint",
        "SQ": "Sprint Qualifying",
        "FP1": "Practice 1",
        "FP2": "Practice 2",
        "FP3": "Practice 3",
    }.get(code, code)


def _visible_text_samples(widget: QWidget, limit: int = 40) -> List[str]:
    samples: List[str] = []
    for label in widget.findChildren(QLabel):
        try:
            if not label.isVisible():
                continue
            text = label.text().strip()
        except Exception:
            continue
        if text and text not in samples:
            samples.append(text)
        if len(samples) >= limit:
            break
    return samples


def _table_samples(widget: QWidget, limit: int = 40) -> List[str]:
    samples: List[str] = []
    for table in widget.findChildren(QTableWidget):
        rows = min(table.rowCount(), 8)
        cols = min(table.columnCount(), 8)
        for row in range(rows):
            values: List[str] = []
            for col in range(cols):
                item = table.item(row, col)
                if item is not None:
                    value = item.text().strip()
                    if value:
                        values.append(value)
            if values:
                samples.append(" | ".join(values))
            if len(samples) >= limit:
                return samples
    return samples


def _has_numeric_sample(samples: List[str]) -> bool:
    return any(any(ch.isdigit() for ch in sample) for sample in samples)


def _module_passes(label: str, load_ok: bool, signal: Dict[str, Any], text_samples: List[str], table_samples: List[str]) -> bool:
    if not load_ok or signal.get("failures"):
        return False
    if signal.get("loaded") and (_has_numeric_sample(text_samples) or _has_numeric_sample(table_samples)):
        return True
    # Map/trace style widgets can be numeric-data backed without table text.
    numeric_optional = {
        "Track Map",
        "Circle Map",
        "Pit Window",
        "Tyre Strategy",
        "Lap Time Distribution",
        "Track & Weather",
        "Speed Trace",
        "Throttle Trace",
        "Brake Trace",
        "Gear Trace",
        "DRS Trace",
        "RPM Trace",
        "Pedal Behavior",
        "S1 Comparison",
        "S2 Comparison",
        "S3 Comparison",
    }
    return label in numeric_optional and not signal.get("failures")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--race", default="Miami")
    parser.add_argument("--session", default="R")
    parser.add_argument("--report", type=Path, default=LOG_DIR / "live_timing_data_validation_2026_miami.json")
    parser.add_argument("--screenshot", type=Path, default=LOG_DIR / "live_timing_data_validation_2026_miami.png")
    parser.add_argument("--screenshot-dir", type=Path, default=LOG_DIR / "live_timing_data_validation_2026_miami")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    args.screenshot_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])

    from modules.gui.live_timing import LiveTimingDataManager, LiveTimingModuleFactory

    dm = LiveTimingDataManager.instance()
    main_window = _DummyMain(args.year, args.race, args.session)
    factory = LiveTimingModuleFactory.get_instance()
    live_paths = [path for path in _leaf_paths(main_window) if path and path[0] == "Live Timing"]

    dashboard = QWidget()
    dashboard.setWindowTitle(f"Live Timing Validation - {args.year} {args.race} {args.session}")
    grid = QGridLayout(dashboard)
    grid.setContentsMargins(4, 4, 4, 4)
    grid.setSpacing(4)
    dashboard.resize(1800, 1000)

    modules: List[Dict[str, Any]] = []
    preview_count = 0
    preview_labels = {"Track Map", "Live Ranking", "Race Control Messages", "Track & Weather", "Traffic Timeline", "Pit Window"}

    for path in live_paths:
        label = path[-1]
        try:
            module = factory.create_module(label, main_window)
            widget = _get_widget(module) or (module if isinstance(module, QWidget) else None)
            if widget is not None:
                widget.resize(900, 560)
                widget.show()
                if label in preview_labels and preview_count < 6:
                    grid.addWidget(widget, preview_count // 2, preview_count % 2)
                    preview_count += 1
            _process(0.15)
        except Exception as exc:
            modules.append({"path": path, "label": label, "module": None, "widget": None, "create_error": f"{type(exc).__name__}: {exc}"})
            continue
        modules.append({"path": path, "label": label, "module": module, "widget": widget})

    progress: List[List[Any]] = []
    load_ok = dm.load_race(
        args.year,
        args.race,
        _session_name(args.session),
        source_type="api",
        progress_callback=lambda percent, message: progress.append([percent, message]),
    )
    _process(0.8)
    if load_ok:
        try:
            dm.seek_by_progress(0.5)
        except Exception:
            pass
        _process(1.2)

    results: List[Dict[str, Any]] = []
    for entry in modules:
        result: Dict[str, Any] = {"path": entry["path"], "label": entry["label"]}
        if entry.get("create_error"):
            result.update({"ok": False, "error": entry["create_error"]})
        else:
            signal = _data_signal(entry.get("module"), entry.get("widget"))
            widget = entry.get("widget")
            text_samples = _visible_text_samples(widget) if isinstance(widget, QWidget) else []
            table_samples = _table_samples(widget) if isinstance(widget, QWidget) else []
            result.update(signal)
            result["visible_text_samples"] = text_samples[:20]
            result["table_samples"] = table_samples[:20]
            result["has_numeric_sample"] = _has_numeric_sample(text_samples + table_samples)
            result["ok"] = _module_passes(entry["label"], load_ok, signal, text_samples, table_samples)
            if isinstance(widget, QWidget):
                try:
                    safe_name = "".join(ch if ch.isalnum() else "_" for ch in entry["label"]).strip("_").lower()
                    screenshot_path = args.screenshot_dir / f"{safe_name}.png"
                    widget.grab().save(str(screenshot_path))
                    result["screenshot"] = str(screenshot_path)
                except Exception as exc:
                    result["screenshot_error"] = f"{type(exc).__name__}: {exc}"
        results.append(result)

    _process(1.0)
    dashboard.show()
    _process(1.0)
    dashboard.grab().save(str(args.screenshot))

    race_info = dm.get_race_info() or {}
    report = {
        "ok": bool(load_ok and all(item.get("ok") for item in results)),
        "year": args.year,
        "race": args.race,
        "session": args.session,
        "load_ok": bool(load_ok),
        "snapshots": dm.get_total_snapshots(),
        "current_index": dm.get_current_index(),
        "race_info": {
            "year": race_info.get("year"),
            "race": race_info.get("race"),
            "session": race_info.get("session"),
            "total_snapshots": race_info.get("total_snapshots"),
            "total_laps": race_info.get("total_laps"),
            "driver_count": len(race_info.get("driver_info", {}) or {}),
            "pit_event_count": len(race_info.get("pit_events", []) or []),
        },
        "progress_tail": progress[-20:],
        "screenshot": str(args.screenshot),
        "screenshot_dir": str(args.screenshot_dir),
        "total_modules": len(results),
        "passed_modules": sum(1 for item in results if item.get("ok")),
        "results": results,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.__stdout__.write(json.dumps(report, ensure_ascii=False, indent=2))
    sys.__stdout__.write("\n")
    sys.__stdout__.flush()
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
