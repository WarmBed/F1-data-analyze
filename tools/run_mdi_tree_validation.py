#!/usr/bin/env python3
"""Trigger MDI tree leaves and validate data loading for a target race/session."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("F1T_RUNTIME_MODE", "local")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox, QTableWidget, QTreeWidgetItem, QWidget

from windows.widgets.custom_mdi_area import CustomMdiArea
import f1t_gui_main


LOG_DIR = ROOT / "logs"

FAIL_TEXT = (
    "no data",
    "load failed",
    "api request failed",
    "analysis failed",
    "waiting for data",
    "api unavailable",
    "failed",
)


def _process(duration: float = 0.15) -> None:
    end_at = time.time() + max(duration, 0.0)
    while time.time() < end_at:
        QCoreApplication.processEvents()
        time.sleep(0.01)


def _patch_message_boxes() -> None:
    def _stub(*_args: Any, **_kwargs: Any) -> int:
        return QMessageBox.Ok

    QMessageBox.information = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.warning = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.critical = staticmethod(_stub)  # type: ignore[method-assign]
    QMessageBox.question = staticmethod(_stub)  # type: ignore[method-assign]


def _select_combo(combo: QComboBox, matcher) -> str:
    for idx in range(combo.count()):
        text = combo.itemText(idx)
        if matcher(text):
            combo.setCurrentIndex(idx)
            _process(0.5)
            return text
    return combo.currentText()


def _ensure_analysis_tab(main_window: Any) -> CustomMdiArea | None:
    current = main_window.tab_widget.currentWidget()
    if isinstance(current, CustomMdiArea):
        return current
    for child in current.findChildren(CustomMdiArea) if current else []:
        return child

    if hasattr(main_window, "add_new_tab"):
        main_window.add_new_tab()
        _process(0.6)
        current = main_window.tab_widget.currentWidget()
        if isinstance(current, CustomMdiArea):
            return current
        for child in current.findChildren(CustomMdiArea) if current else []:
            return child
    return None


def _all_mdi_areas(main_window: Any) -> List[CustomMdiArea]:
    areas: List[CustomMdiArea] = []
    tab_widget = getattr(main_window, "tab_widget", None)
    if tab_widget is None:
        return areas
    for i in range(tab_widget.count()):
        tab = tab_widget.widget(i)
        if isinstance(tab, CustomMdiArea):
            areas.append(tab)
            continue
        for child in tab.findChildren(CustomMdiArea) if tab else []:
            areas.append(child)
    return areas


def _all_subwindows(main_window: Any) -> List[Any]:
    windows: List[Any] = []
    for area in _all_mdi_areas(main_window):
        windows.extend(area.subWindowList())
    return windows


def _collect_leaves(root: QTreeWidgetItem) -> List[QTreeWidgetItem]:
    leaves: List[QTreeWidgetItem] = []
    for i in range(root.childCount()):
        item = root.child(i)
        if item.childCount() == 0:
            leaves.append(item)
        else:
            leaves.extend(_collect_leaves(item))
    return leaves


def _extract_texts(widget: QWidget, limit: int = 200) -> List[str]:
    texts: List[str] = []
    for child in widget.findChildren(QWidget):
        try:
            if not child.isVisible():
                continue
        except Exception:
            pass
        if hasattr(child, "text"):
            try:
                value = str(child.text()).strip()
            except Exception:
                value = ""
            if value:
                texts.append(value)
        if len(texts) >= limit:
            break
    return texts


def _check_data_loaded(widget: QWidget) -> Tuple[bool, Dict[str, Any]]:
    info: Dict[str, Any] = {
        "table_rows": [],
        "failure_texts": [],
        "data_attrs": {},
        "plot_signals": [],
    }

    loaded = False
    for table in widget.findChildren(QTableWidget):
        rows = int(table.rowCount())
        info["table_rows"].append(rows)
        if rows > 0:
            loaded = True

    texts = _extract_texts(widget)
    failures = [t for t in texts if any(k in t.lower() for k in FAIL_TEXT)]
    info["failure_texts"] = failures[:12]
    has_failure_text = bool(failures)

    targets = [
        "_is_data_loaded",
        "_data_loaded",
        "_current_data",
        "current_data",
        "analysis_data",
        "loaded_data",
        "data",
    ]
    for name in targets:
        if hasattr(widget, name):
            try:
                value = getattr(widget, name)
                if isinstance(value, dict):
                    non_empty = bool(value)
                    info["data_attrs"][name] = {"type": "dict", "non_empty": non_empty}
                    loaded = loaded or non_empty
                elif isinstance(value, (list, tuple, set)):
                    non_empty = bool(value)
                    info["data_attrs"][name] = {"type": type(value).__name__, "non_empty": non_empty}
                    loaded = loaded or non_empty
                elif isinstance(value, bool):
                    info["data_attrs"][name] = {"type": "bool", "value": value}
                    loaded = loaded or value
            except Exception:
                pass

    chart_data_attrs = [
        "lap_data",
        "air_temp_data",
        "track_temp_data",
        "wind_speed_data",
        "pressure_data",
        "all_drivers_stint_data",
        "stint_data",
        "position_data",
        "track_data",
        "heatmap_data",
        "traffic_data",
        "lap_times",
        "throttle_data",
        "pedal_data",
        "sector_data",
    ]
    for child in [widget, *widget.findChildren(QWidget)]:
        child_name = type(child).__name__
        for attr in chart_data_attrs:
            if not hasattr(child, attr):
                continue
            try:
                value = getattr(child, attr)
                if isinstance(value, dict):
                    size = len(value)
                    info["data_attrs"][f"{child_name}.{attr}"] = {"type": "dict", "size": size}
                    loaded = loaded or size > 0
                elif isinstance(value, (list, tuple, set)):
                    size = len(value)
                    info["data_attrs"][f"{child_name}.{attr}"] = {"type": type(value).__name__, "size": size}
                    loaded = loaded or size > 0
            except Exception:
                continue

    # Matplotlib-based modules often have no tables; detect real plotted data.
    for child in widget.findChildren(QWidget):
        fig = getattr(child, "figure", None)
        if fig is None:
            continue
        try:
            axes = list(getattr(fig, "axes", []) or [])
            axis_signal = {"axes": len(axes), "lines": 0, "collections": 0, "images": 0}
            has_plot_data = False
            for ax in axes:
                lines = list(getattr(ax, "lines", []) or [])
                cols = list(getattr(ax, "collections", []) or [])
                imgs = list(getattr(ax, "images", []) or [])
                axis_signal["lines"] += len(lines)
                axis_signal["collections"] += len(cols)
                axis_signal["images"] += len(imgs)

                for ln in lines:
                    try:
                        x = ln.get_xdata()
                        y = ln.get_ydata()
                        if len(x) > 0 and len(y) > 0:
                            has_plot_data = True
                            break
                    except Exception:
                        continue
                if not has_plot_data and (len(cols) > 0 or len(imgs) > 0):
                    has_plot_data = True
            info["plot_signals"].append(axis_signal)
            loaded = loaded or has_plot_data
        except Exception:
            continue

    return (loaded and not has_failure_text), info


def _run_api_check(year: int, race: str, session: str) -> Dict[str, Any]:
    from core.local_analysis_client import execute_analysis_sync

    results: List[Dict[str, Any]] = []
    ok = 0
    total = 37
    for function_id in range(1, total + 1):
        params: Dict[str, Any] = {"year": year, "race": race, "session": session}
        if function_id in {8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21}:
            params.update({"driver1": "VER", "driver2": "NOR", "lap1": 1, "lap2": 1})
        if function_id in {35, 36, 37}:
            params.update({"team": "Red Bull Racing"})
        if function_id in {26, 27, 28, 29, 30, 31, 32, 33, 34}:
            params.update({"driver1": "VER", "driver2": "NOR", "lap": 1})
        try:
            payload = execute_analysis_sync(function_id, **params)
            success = bool(payload.get("success"))
            data = payload.get("data")
            non_empty = isinstance(data, dict) and bool(data)
            if success and non_empty:
                ok += 1
            results.append(
                {
                    "function_id": function_id,
                    "success": success,
                    "data_non_empty": non_empty,
                    "source": payload.get("source"),
                    "message": payload.get("message"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "function_id": function_id,
                    "success": False,
                    "data_non_empty": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return {"ok_count": ok, "total": total, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--race-keyword", default="Japan")
    parser.add_argument("--session", default="R")
    parser.add_argument("--scope", choices=["historical", "all"], default="all")
    parser.add_argument("--per-item-timeout", type=float, default=8.0)
    parser.add_argument("--report", type=Path, default=LOG_DIR / "mdi_tree_validation_2026_japan_report.json")
    parser.add_argument("--screenshot", type=Path, default=LOG_DIR / "mdi_tree_validation_2026_japan.png")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _patch_message_boxes()

    app = QApplication.instance() or QApplication([])
    main_window = f1t_gui_main.StyleHMainWindow()
    main_window.show()
    _process(1.2)

    selected_year = _select_combo(main_window.year_combo, lambda t: t.strip() == str(args.year))
    _process(1.2)
    selected_race = _select_combo(main_window.race_combo, lambda t: args.race_keyword.lower() in t.lower())
    selected_session = _select_combo(main_window.session_combo, lambda t: t.strip().upper() == args.session.upper())
    _process(1.0)

    if _ensure_analysis_tab(main_window) is None:
        report = {
            "ok": False,
            "error": "No MDI area found",
            "selected_year": selected_year,
            "selected_race": selected_race,
            "selected_session": selected_session,
        }
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    leaves = _collect_leaves(main_window.function_tree.invisibleRootItem())
    if args.scope == "historical":
        filtered: List[QTreeWidgetItem] = []
        for item in leaves:
            p = item.parent()
            names: List[str] = []
            while p is not None:
                names.append(p.text(0))
                p = p.parent()
            if any("Historical Analysis" in n or "歷史分析" in n for n in names):
                filtered.append(item)
        leaves = filtered

    results: List[Dict[str, Any]] = []
    opened_windows: Dict[int, Any] = {}
    for idx, item in enumerate(leaves, start=1):
        label = item.text(0).strip()
        before = {id(sw): sw for sw in _all_subwindows(main_window)}
        started = time.time()
        try:
            main_window.function_tree.analyze_function(label, batch_mode=True)
        except Exception as exc:
            results.append(
                {
                    "index": idx,
                    "label": label,
                    "ok": False,
                    "error": f"trigger failed: {type(exc).__name__}: {exc}",
                    "elapsed_seconds": round(time.time() - started, 3),
                }
            )
            continue

        found_new = []
        while time.time() - started < args.per_item_timeout:
            _process(0.15)
            now = _all_subwindows(main_window)
            found_new = [sw for sw in now if id(sw) not in before]
            if found_new:
                break

        if not found_new:
            results.append(
                {
                    "index": idx,
                    "label": label,
                    "ok": False,
                    "new_windows": 0,
                    "inspected": [],
                    "error": "no new subwindow created",
                    "elapsed_seconds": round(time.time() - started, 3),
                }
            )
            continue

        window_ids: List[int] = []
        titles: List[str] = []
        for sw in found_new:
            sid = id(sw)
            opened_windows[sid] = sw
            window_ids.append(sid)
            titles.append(sw.windowTitle())

        results.append(
            {
                "index": idx,
                "label": label,
                "ok": False,
                "new_windows": len(found_new),
                "inspected": [],
                "window_ids": window_ids,
                "window_titles": titles,
                "elapsed_seconds": round(time.time() - started, 3),
            }
        )

    try:
        main_window.on_race_parameters_changed()
    except Exception:
        pass
    try:
        main_window.update_all_lap_analysis()
    except Exception:
        pass
    _process(10.0)

    for item in results:
        if item.get("new_windows", 0) <= 0:
            continue
        inspected = []
        for sid in item.get("window_ids", []):
            sw = opened_windows.get(sid)
            if sw is None:
                inspected.append({"title": "<closed>", "ok": False, "info": {"error": "window closed"}})
                continue
            widget = sw.widget()
            if widget is None:
                inspected.append({"title": sw.windowTitle(), "ok": False, "info": {"error": "no widget"}})
                continue
            ok, info = _check_data_loaded(widget)
            inspected.append({"title": sw.windowTitle(), "ok": ok, "info": info})
        item["inspected"] = inspected
        item["ok"] = any(x.get("ok") for x in inspected)

    ok_count = sum(1 for r in results if r.get("ok"))
    fail_count = len(results) - ok_count

    api_check = _run_api_check(args.year, args.race_keyword, args.session)

    screen = app.primaryScreen()
    if screen:
        shot = screen.grabWindow(main_window.winId())
        shot.save(str(args.screenshot))

    report = {
        "ok": fail_count == 0,
        "scope": args.scope,
        "selected_year": selected_year,
        "selected_race": selected_race,
        "selected_session": selected_session,
        "total_items": len(results),
        "ok_count": ok_count,
        "fail_count": fail_count,
        "results": results,
        "api_check": api_check,
        "screenshot": str(args.screenshot),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    main_window.close()
    _process(0.4)
    app.quit()
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
