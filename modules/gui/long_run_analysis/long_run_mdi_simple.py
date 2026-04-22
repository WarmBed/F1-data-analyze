#!/usr/bin/env python3
"""Stable local Long Run & Degradation widget for MDI use."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class LongRunAnalysis(QWidget):
    """Local-only Long Run summary that avoids API workers and fragile MDI widgets."""

    analysis_type = "long_run"

    def __init__(self, year: int = 2025, race: str = "Japan", session: str = "FP2", parent=None):
        super().__init__(parent)
        self.year = int(year)
        self.race = self._normalise_race(race)
        self.session = str(session or "FP2").upper()
        self._data: Optional[Dict[str, Any]] = None
        self._source_path: Optional[Path] = None
        self._fallback_source_path: Optional[Path] = None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self.summary_label = QLabel()
        self.summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_data)
        header.addWidget(self.summary_label, 1)
        header.addWidget(refresh_button)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.driver_table = QTableWidget(0, 6)
        self.driver_table.setHorizontalHeaderLabels(
            ["Driver", "Laps", "Best", "Average", "Compounds", "Long run laps"]
        )
        self.tabs.addTab(self.driver_table, "Drivers")

        self.stint_table = QTableWidget(0, 5)
        self.stint_table.setHorizontalHeaderLabels(["Driver", "Compound", "Start lap", "End lap", "Laps"])
        self.tabs.addTab(self.stint_table, "Stints")

        self.status_label = QLabel()
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.status_label)

    def _load_data(self) -> None:
        self._source_path = None
        self._fallback_source_path = None
        self._data = None
        for path in self._candidate_paths():
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as handle:
                self._data = json.load(handle)
            self._source_path = path
            break
        if self._data is None:
            fallback = self._find_latest_available_file()
            if fallback is not None:
                with fallback.open("r", encoding="utf-8") as handle:
                    self._data = json.load(handle)
                self._source_path = fallback
                self._fallback_source_path = fallback
        self._populate()

    def _candidate_paths(self) -> List[Path]:
        race_values = []
        for value in (self.race, self.race.replace(" ", "_"), self.race.replace("_", " ")):
            if value and value not in race_values:
                race_values.append(value)
        roots = [Path.cwd()]
        module_root = Path(__file__).resolve()
        for parent in module_root.parents:
            if (parent / "f1t_gui_main.py").exists():
                roots.insert(0, parent)
                break
        paths: List[Path] = []
        for root in roots:
            for folder in ("json", "json_exports"):
                for race in race_values:
                    paths.append(
                        root
                        / folder
                        / f"detailed_laptime_analysis_{self.year}_{race}_{self.session}_all_drivers.json"
                    )
        return paths

    def _find_latest_available_file(self) -> Optional[Path]:
        roots = [Path.cwd()]
        module_root = Path(__file__).resolve()
        for parent in module_root.parents:
            if (parent / "f1t_gui_main.py").exists():
                roots.insert(0, parent)
                break

        candidates: List[Path] = []
        pattern = f"detailed_laptime_analysis_*_*_{self.session}_all_drivers.json"
        for root in roots:
            for folder in ("json", "json_exports"):
                base = root / folder
                if not base.exists():
                    continue
                candidates.extend(base.glob(pattern))

        if not candidates:
            return None
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0]

    def _populate(self) -> None:
        lap_data = self._extract_lap_data(self._data)
        self.driver_table.setRowCount(0)
        self.stint_table.setRowCount(0)

        if not lap_data:
            self.summary_label.setText(f"{self.year} {self.race} {self.session} - no local long-run data")
            searched = "\n".join(str(path) for path in self._candidate_paths())
            self.status_label.setText(f"Local JSON not found. Searched:\n{searched}")
            return

        total_laps = 0
        stint_rows: List[Tuple[str, str, int, int, int]] = []
        for driver, payload in sorted(lap_data.items()):
            cleaned = self._driver_laps(payload)
            total_laps += len(cleaned)
            compounds = sorted(
                {str(lap.get("Compound") or lap.get("compound") or lap.get("tire_compound") or "-") for lap in cleaned}
            )
            lap_times = [
                self._to_seconds(lap.get("LapTime") or lap.get("lap_time_seconds") or lap.get("lap_time"))
                for lap in cleaned
            ]
            lap_times = [value for value in lap_times if value is not None]
            long_run_laps = self._count_long_run_laps(cleaned)
            self._append_driver_row(driver, len(cleaned), lap_times, compounds, long_run_laps)
            stint_rows.extend(self._detect_stints(driver, cleaned))

        for row in stint_rows:
            self._append_stint_row(row)

        self.summary_label.setText(
            f"{self.year} {self.race} {self.session} - {len(lap_data)} drivers, {total_laps} laps"
        )
        source = str(self._source_path) if self._source_path else "unknown"
        if self._fallback_source_path is not None:
            self.status_label.setText(
                f"Loaded fallback local JSON (requested {self.year} {self.race} {self.session}): {source}"
            )
        else:
            self.status_label.setText(f"Loaded local JSON: {source}")

    def _append_driver_row(
        self, driver: str, lap_count: int, lap_times: List[float], compounds: List[str], long_run_laps: int
    ) -> None:
        row = self.driver_table.rowCount()
        self.driver_table.insertRow(row)
        best = min(lap_times) if lap_times else None
        avg = sum(lap_times) / len(lap_times) if lap_times else None
        values = [
            driver,
            str(lap_count),
            self._format_seconds(best),
            self._format_seconds(avg),
            ", ".join(compounds),
            str(long_run_laps),
        ]
        for col, value in enumerate(values):
            self.driver_table.setItem(row, col, QTableWidgetItem(value))

    def _append_stint_row(self, data: Tuple[str, str, int, int, int]) -> None:
        row = self.stint_table.rowCount()
        self.stint_table.insertRow(row)
        for col, value in enumerate(data):
            self.stint_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _extract_lap_data(self, data: Optional[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        if not isinstance(data, dict):
            return {}
        if isinstance(data.get("all_drivers_detailed_laptime"), dict):
            return data["all_drivers_detailed_laptime"]
        inner = data.get("data")
        if isinstance(inner, dict) and isinstance(inner.get("all_drivers_detailed_laptime"), dict):
            return inner["all_drivers_detailed_laptime"]
        return {}

    def _driver_laps(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [lap for lap in payload if isinstance(lap, dict)]
        if isinstance(payload, dict):
            laps = payload.get("detailed_lap_data") or payload.get("laps") or payload.get("lap_data") or []
            if isinstance(laps, list):
                return [lap for lap in laps if isinstance(lap, dict)]
        return []

    def _detect_stints(self, driver: str, laps: List[Dict[str, Any]]) -> List[Tuple[str, str, int, int, int]]:
        rows: List[Tuple[str, str, int, int, int]] = []
        current_compound = None
        start_lap = None
        end_lap = None
        for lap in laps:
            lap_number = int(lap.get("LapNumber") or lap.get("lap") or lap.get("lap_number") or 0)
            compound = str(lap.get("Compound") or lap.get("compound") or lap.get("tire_compound") or "-")
            if current_compound is None:
                current_compound = compound
                start_lap = lap_number
            elif compound != current_compound:
                if start_lap and end_lap and end_lap >= start_lap:
                    rows.append((driver, current_compound, start_lap, end_lap, end_lap - start_lap + 1))
                current_compound = compound
                start_lap = lap_number
            end_lap = lap_number
        if current_compound is not None and start_lap and end_lap and end_lap >= start_lap:
            rows.append((driver, current_compound, start_lap, end_lap, end_lap - start_lap + 1))
        return rows

    def _count_long_run_laps(self, laps: List[Dict[str, Any]]) -> int:
        return sum(length for _, _, _, _, length in self._detect_stints("-", laps) if length >= 5)

    @staticmethod
    def _to_seconds(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value)
        if "days" in text:
            text = text.rsplit(" ", 1)[-1]
        parts = text.split(":")
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _format_seconds(value: Optional[float]) -> str:
        if value is None:
            return "-"
        minutes = int(value // 60)
        seconds = value - minutes * 60
        return f"{minutes}:{seconds:06.3f}"

    @staticmethod
    def _normalise_race(race: str) -> str:
        text = str(race or "").strip()
        if "(" in text:
            text = text.split("(", 1)[0].strip()
        return text.replace("_", " ")

    def refresh_data(self) -> None:
        self._load_data()

    def update_parameters(self, year: int, race: str, session: str) -> bool:
        self.year = int(year)
        self.race = self._normalise_race(race)
        self.session = str(session or "FP2").upper()
        self._load_data()
        return True

    def get_widget(self) -> QWidget:
        return self

    def get_title(self) -> str:
        return f"Long Run_{self.year}_{self.race}_{self.session}"

    def get_window_title(self, year: int, race: str, session: str) -> str:
        return "Long Run & Degradation Analysis"

    def get_default_size(self) -> tuple:
        return (1100, 720)

    def set_parent_window(self, parent_window) -> None:
        self._parent_window = parent_window
