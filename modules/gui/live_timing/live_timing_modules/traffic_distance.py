"""
Live Timing Traffic Distance (JSON) Module
========================================

讀取 CLI Function 127 (live_timing_traffic_distance) 產生的 JSON，
以表格方式呈現每位車手的 traffic 統計結果。

限制：
- 僅讀取既有本地 JSON，不呼叫 CLI（API-ONLY 模式）。

Author: F1T Team
Date: 2025-12-23
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.gui_i18n import tr
from core.logger import get_logger
from ..core.base_live_mdi import BaseLiveTimingMDI


logger = get_logger("live_timing.traffic_distance", component="gui")


@dataclass(frozen=True)
class _TrafficRow:
    driver_tla: str
    team: str
    laps_analyzed: int
    laps_in_traffic: int
    time_in_traffic_ratio: float


class TrafficDistanceWidget(QWidget):
    """Traffic Distance 統計展示 Widget（讀取 JSON）"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._source_file: Optional[Path] = None

        self._label_title = QLabel(tr("live_timing_traffic_distance_title", "Traffic Distance"))
        self._label_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px;")

        self._label_meta = QLabel(tr("live_timing_traffic_distance_meta", "No data loaded"))
        self._label_meta.setStyleSheet("color: #CCCCCC; font-size: 12px;")

        self._label_params = QLabel("")
        self._label_params.setStyleSheet("color: #CCCCCC; font-size: 12px;")

        self._label_derived = QLabel("")
        self._label_derived.setStyleSheet("color: #CCCCCC; font-size: 12px;")

        self._table = QTableWidget()
        self._table.setProperty("is_live_timing_widget", True)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            [
                tr("driver", "Driver"),
                tr("team", "Team"),
                tr("laps_analyzed", "Laps"),
                tr("laps_in_traffic", "Traffic Laps"),
                tr("traffic_ratio", "Traffic %"),
            ]
        )
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(self._table.SelectRows)
        self._table.setSelectionMode(self._table.NoSelection)
        self._table.setAlternatingRowColors(False)
        self._table.setEditTriggers(self._table.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(22)
        self._table.horizontalHeader().setStretchLastSection(True)

        if self._table.viewport():
            self._table.viewport().setProperty("is_live_timing_widget", True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(6)

        header = QFrame()
        header.setStyleSheet("background-color: #1a1a1a;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(2)
        header_layout.addWidget(self._label_title)
        header_layout.addWidget(self._label_meta)
        header_layout.addWidget(self._label_params)
        header_layout.addWidget(self._label_derived)

        layout.addWidget(header)
        layout.addWidget(self._table)

    def load_from_file(self, file_path: Path) -> bool:
        try:
            if not file_path.exists():
                self._set_error(
                    tr("file_not_found", "File not found"),
                    str(file_path),
                )
                return False

            with file_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            self._source_file = file_path
            self._render(payload)
            return True

        except Exception as e:
            logger.exception("[TRAFFIC_DISTANCE] Failed to load JSON: %s", e)
            self._set_error(tr("error", "Error"), str(e))
            return False

    def _set_error(self, title: str, details: str) -> None:
        self._label_meta.setText(f"{title}: {details}")
        self._label_params.setText("")
        self._label_derived.setText("")
        self._table.setRowCount(0)

    def _render(self, root: Dict[str, Any]) -> None:
        data = root.get("data") or {}
        metadata = (data.get("metadata") or {}) if isinstance(data, dict) else {}
        parameters = (data.get("parameters") or {}) if isinstance(data, dict) else {}
        derived = (data.get("derived") or {}) if isinstance(data, dict) else {}
        drivers = (data.get("drivers") or {}) if isinstance(data, dict) else {}

        year = metadata.get("year")
        race = metadata.get("race")
        session = metadata.get("session")

        source_hint = str(self._source_file) if self._source_file else ""
        self._label_meta.setText(
            tr("live_timing_traffic_distance_loaded", "Loaded")
            + f": {year} {race} {session}"
            + (f" | {source_hint}" if source_hint else "")
        )

        distance_threshold = parameters.get("traffic_distance_threshold_m")
        lap_ratio_threshold = parameters.get("lap_traffic_ratio_threshold")
        exclude_codes = parameters.get("exclude_track_status_codes")

        self._label_params.setText(
            tr("live_timing_traffic_distance_params", "Params")
            + f": distance={distance_threshold}m, lap_ratio={lap_ratio_threshold}, exclude={exclude_codes}"
        )

        track_length = derived.get("track_length_est_m")
        xy_scale = derived.get("xy_scale") or {}
        meters_per_xy = None
        if isinstance(xy_scale, dict):
            meters_per_xy = xy_scale.get("meters_per_xy_unit")

        self._label_derived.setText(
            tr("live_timing_traffic_distance_derived", "Derived")
            + f": track_length_est_m={track_length}, meters_per_xy_unit={meters_per_xy}"
        )

        rows = self._build_rows(drivers)
        self._populate_table(rows)

    def _build_rows(self, drivers: Dict[str, Any]) -> List[_TrafficRow]:
        rows: List[_TrafficRow] = []
        if not isinstance(drivers, dict):
            return rows

        for driver_number, d in drivers.items():
            if not isinstance(d, dict):
                continue

            driver_tla = str(d.get("driver_tla") or driver_number)
            team = str(d.get("team") or "")
            laps_analyzed = int(d.get("laps_analyzed") or 0)
            laps_in_traffic = int(d.get("laps_in_traffic") or 0)
            ratio = float(d.get("time_in_traffic_ratio") or 0.0)

            rows.append(
                _TrafficRow(
                    driver_tla=driver_tla,
                    team=team,
                    laps_analyzed=laps_analyzed,
                    laps_in_traffic=laps_in_traffic,
                    time_in_traffic_ratio=ratio,
                )
            )

        rows.sort(key=lambda r: r.time_in_traffic_ratio, reverse=True)
        return rows

    def _populate_table(self, rows: List[_TrafficRow]) -> None:
        self._table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            items: List[Tuple[int, QTableWidgetItem]] = []

            items.append((0, QTableWidgetItem(row.driver_tla)))
            items.append((1, QTableWidgetItem(row.team)))
            items.append((2, QTableWidgetItem(str(row.laps_analyzed))))
            items.append((3, QTableWidgetItem(str(row.laps_in_traffic))))
            items.append((4, QTableWidgetItem(f"{row.time_in_traffic_ratio * 100:.1f}%")))

            for col, item in items:
                item.setTextAlignment(Qt.AlignVCenter | (Qt.AlignRight if col >= 2 else Qt.AlignLeft))
                self._table.setItem(row_idx, col, item)

        self._table.resizeColumnsToContents()


class TrafficDistanceMDI(BaseLiveTimingMDI):
    """Live Timing MDI 視窗：Traffic Distance（讀取 F127 JSON）"""

    _window_title_key = "traffic_distance"
    _default_title = "Traffic Distance"

    def __init__(self, parent=None, data_manager=None):
        self._widget: Optional[TrafficDistanceWidget] = None
        super().__init__(parent=parent, data_manager=data_manager)

    def _setup_ui(self):
        self.setWindowTitle(tr(self._window_title_key, self._default_title))
        self._widget = TrafficDistanceWidget(self)
        self._main_layout.addWidget(self._widget)

        # 預設 DEMO：Abu Dhabi 2025 R
        self._try_load_default_demo()

    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """當 Live Timing 載入不同賽事時，嘗試載入對應的 JSON。"""
        year = race_info.get("year")
        race = race_info.get("race")
        session = race_info.get("session")

        file_path = self._find_json_file(year=year, race=race, session=session)
        if file_path and self._widget:
            self._widget.load_from_file(file_path)

    def _on_race_unloaded(self):
        if self._widget:
            self._widget._set_error(tr("no_data", "No data"), tr("race_unloaded", "Race unloaded"))

    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        # 此模組為靜態 JSON 顯示，不需處理快照更新
        return

    def _try_load_default_demo(self) -> None:
        file_path = self._find_json_file(year=2025, race="Abu_Dhabi", session="R")
        if file_path and self._widget:
            self._widget.load_from_file(file_path)

    def _find_json_file(self, year: Any, race: Any, session: Any) -> Optional[Path]:
        try:
            if year is None or race is None or session is None:
                return None

            year_int = int(year)
            race_norm = self._normalize_race(str(race))
            session_norm = self._normalize_session_short(str(session))

            base_dir = self._get_json_dir()
            candidates = [
                base_dir / f"live_timing_traffic_distance_{year_int}_{race_norm}_{session_norm}.json",
                base_dir / f"live_timing_traffic_distance_{year_int}_{str(race)}_{session_norm}.json",
            ]

            for p in candidates:
                if p.exists():
                    return p

            return None

        except Exception:
            logger.exception("[TRAFFIC_DISTANCE] Failed to resolve JSON path")
            return None

    def _get_json_dir(self) -> Path:
        # EXE 模式：使用 EXE 所在目錄
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            exe_dir = Path(sys.executable).parent
            return exe_dir / "json"

        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        return project_root / "json"

    def _normalize_race(self, race: str) -> str:
        # 移除常見後綴，並統一空白為底線
        cleaned = (
            race.replace(" Grand Prix", "")
            .replace("_Grand_Prix", "")
            .replace("_Race", "")
            .replace(" Race", "")
        )
        return cleaned.replace(" ", "_")

    def _normalize_session_short(self, session: str) -> str:
        mapping = {
            "R": "R",
            "RACE": "R",
            "RACE ": "R",
            "Q": "Q",
            "QUALIFYING": "Q",
            "FP1": "FP1",
            "PRACTICE_1": "FP1",
            "PRACTICE 1": "FP1",
            "FP2": "FP2",
            "PRACTICE_2": "FP2",
            "PRACTICE 2": "FP2",
            "FP3": "FP3",
            "PRACTICE_3": "FP3",
            "PRACTICE 3": "FP3",
            "S": "S",
            "SPRINT": "S",
            "SQ": "SQ",
            "SPRINT_QUALIFYING": "SQ",
        }
        return mapping.get(session.upper(), session)
