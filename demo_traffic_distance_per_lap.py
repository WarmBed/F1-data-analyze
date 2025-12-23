#!/usr/bin/env python3
"""
Traffic Distance Per-Lap DEMO
==============================

獨立 DEMO：顯示每位車手「每一圈」的 traffic 詳細狀態。

執行方式：
    python demo_traffic_distance_per_lap.py

預設載入：json/live_timing_traffic_distance_2025_Abu_Dhabi_R.json

Author: F1T Team
Date: 2025-12-23
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 確保專案根目錄在 Python path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QLabel, QComboBox, QFrame,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush


class PerLapTableWidget(QWidget):
    """Per-Lap Traffic 詳細表格 Widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._all_rows: List[Dict[str, Any]] = []
        self._driver_list: List[str] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #1a1a1a;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)

        self._label_title = QLabel("Traffic Distance - Per Lap Details")
        self._label_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(self._label_title)

        self._label_meta = QLabel("No data loaded")
        self._label_meta.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        header_layout.addWidget(self._label_meta)

        layout.addWidget(header)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        filter_label = QLabel("Filter by Driver:")
        filter_label.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        filter_row.addWidget(filter_label)

        self._driver_combo = QComboBox()
        self._driver_combo.setMinimumWidth(120)
        self._driver_combo.addItem("All Drivers")
        self._driver_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self._driver_combo)

        filter_row.addStretch()

        self._label_stats = QLabel("")
        self._label_stats.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        filter_row.addWidget(self._label_stats)

        layout.addLayout(filter_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Driver", "Team", "Lap", "Total Time (s)", "Traffic Time (s)",
            "Traffic %", "In Traffic?", "SC/VSC Excluded?"
        ])
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(22)
        self._table.horizontalHeader().setStretchLastSection(True)

        # 設置表格樣式
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #FFFFFF;
                gridline-color: #333333;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #333333;
            }
        """)

        layout.addWidget(self._table)

    def load_from_file(self, file_path: Path) -> bool:
        try:
            if not file_path.exists():
                self._label_meta.setText(f"File not found: {file_path}")
                return False

            with file_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            self._parse_data(payload)
            self._update_driver_combo()
            self._populate_table()
            return True

        except Exception as e:
            self._label_meta.setText(f"Error: {e}")
            return False

    def _parse_data(self, root: Dict[str, Any]):
        data = root.get("data") or {}
        metadata = data.get("metadata") or {}
        drivers = data.get("drivers") or {}

        year = metadata.get("year")
        race = metadata.get("race")
        session = metadata.get("session")

        self._label_meta.setText(f"Loaded: {year} {race} {session}")

        self._all_rows = []
        self._driver_list = []

        for driver_number, d in drivers.items():
            if not isinstance(d, dict):
                continue

            driver_tla = str(d.get("driver_tla") or driver_number)
            team = str(d.get("team") or "")
            per_lap = d.get("per_lap") or []

            if driver_tla not in self._driver_list:
                self._driver_list.append(driver_tla)

            for lap_data in per_lap:
                if not isinstance(lap_data, dict):
                    continue

                self._all_rows.append({
                    "driver_tla": driver_tla,
                    "team": team,
                    "lap": int(lap_data.get("lap") or 0),
                    "total_time_s": float(lap_data.get("total_time_s") or 0.0),
                    "traffic_time_s": float(lap_data.get("traffic_time_s") or 0.0),
                    "traffic_ratio": float(lap_data.get("traffic_ratio") or 0.0),
                    "lap_in_traffic": bool(lap_data.get("lap_in_traffic")),
                    "excluded_sc_vsc": bool(lap_data.get("excluded_sc_vsc")),
                })

        self._driver_list.sort()

    def _update_driver_combo(self):
        self._driver_combo.blockSignals(True)
        self._driver_combo.clear()
        self._driver_combo.addItem("All Drivers")
        for driver in self._driver_list:
            self._driver_combo.addItem(driver)
        self._driver_combo.blockSignals(False)

    def _on_filter_changed(self, text: str):
        self._populate_table()

    def _populate_table(self):
        filter_driver = self._driver_combo.currentText()
        show_all = (filter_driver == "All Drivers")

        # Filter rows
        if show_all:
            rows = self._all_rows
        else:
            rows = [r for r in self._all_rows if r["driver_tla"] == filter_driver]

        # Sort by driver then lap
        rows = sorted(rows, key=lambda r: (r["driver_tla"], r["lap"]))

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(rows))

        traffic_count = 0
        excluded_count = 0

        for row_idx, row in enumerate(rows):
            # Driver
            item_driver = QTableWidgetItem(row["driver_tla"])
            item_driver.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row_idx, 0, item_driver)

            # Team
            item_team = QTableWidgetItem(row["team"])
            self._table.setItem(row_idx, 1, item_team)

            # Lap
            item_lap = QTableWidgetItem(str(row["lap"]))
            item_lap.setTextAlignment(Qt.AlignCenter)
            item_lap.setData(Qt.UserRole, row["lap"])  # For sorting
            self._table.setItem(row_idx, 2, item_lap)

            # Total Time
            item_total = QTableWidgetItem(f"{row['total_time_s']:.2f}")
            item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_total.setData(Qt.UserRole, row["total_time_s"])
            self._table.setItem(row_idx, 3, item_total)

            # Traffic Time
            item_traffic = QTableWidgetItem(f"{row['traffic_time_s']:.2f}")
            item_traffic.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_traffic.setData(Qt.UserRole, row["traffic_time_s"])
            self._table.setItem(row_idx, 4, item_traffic)

            # Traffic %
            pct = row["traffic_ratio"] * 100
            item_pct = QTableWidgetItem(f"{pct:.1f}%")
            item_pct.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_pct.setData(Qt.UserRole, row["traffic_ratio"])
            self._table.setItem(row_idx, 5, item_pct)

            # In Traffic?
            in_traffic = row["lap_in_traffic"]
            item_in_traffic = QTableWidgetItem("YES" if in_traffic else "no")
            item_in_traffic.setTextAlignment(Qt.AlignCenter)
            if in_traffic:
                item_in_traffic.setForeground(QBrush(QColor("#FF6B6B")))  # Red
                traffic_count += 1
            else:
                item_in_traffic.setForeground(QBrush(QColor("#90EE90")))  # Green
            self._table.setItem(row_idx, 6, item_in_traffic)

            # SC/VSC Excluded?
            excluded = row["excluded_sc_vsc"]
            item_excluded = QTableWidgetItem("YES" if excluded else "no")
            item_excluded.setTextAlignment(Qt.AlignCenter)
            if excluded:
                item_excluded.setForeground(QBrush(QColor("#FFA500")))  # Orange
                excluded_count += 1
            else:
                item_excluded.setForeground(QBrush(QColor("#888888")))  # Gray
            self._table.setItem(row_idx, 7, item_excluded)

        self._table.setSortingEnabled(True)
        self._table.resizeColumnsToContents()

        # Update stats
        total = len(rows)
        self._label_stats.setText(
            f"Total: {total} laps | In Traffic: {traffic_count} | SC/VSC Excluded: {excluded_count}"
        )


class DemoPerLapWindow(QMainWindow):
    """Traffic Distance Per-Lap DEMO 主視窗"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traffic Distance Per-Lap DEMO (F127)")
        self.setMinimumSize(900, 600)

        # 中央 Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Per-Lap Widget
        self._widget = PerLapTableWidget()
        layout.addWidget(self._widget)

        # 設置深色背景
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")

        # 載入預設 JSON
        self._load_default_json()

    def _load_default_json(self):
        default_file = PROJECT_ROOT / "json" / "live_timing_traffic_distance_2025_Abu_Dhabi_R.json"
        if default_file.exists():
            self._widget.load_from_file(default_file)
            print(f"[DEMO] Loaded: {default_file}")
        else:
            print(f"[DEMO] File not found: {default_file}")
            print("[DEMO] Run CLI first: python f1_analysis_modular_main.py -f 127 -y 2025 -r Abu_Dhabi -s R")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = DemoPerLapWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
