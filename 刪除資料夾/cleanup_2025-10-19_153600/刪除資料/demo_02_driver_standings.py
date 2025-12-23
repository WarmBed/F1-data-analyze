#!/usr/bin/env python3
"""Demo 2: 車手積分表 - 直接讀取 JSON 並顯示"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
    QHeaderView,
    QLabel,
)

from core.gui_i18n import tr
from modules.gui.themes import color_palette_provider


class DriverStandingsTable(QWidget):
    """車手積分表 Widget"""

    def __init__(self, *, json_path: str, parent=None):
        super().__init__(parent)
        self.json_path = Path(json_path)
        self._init_ui()
        self._load_and_populate()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.title_label = QLabel(tr("driver_standings_title", "車手積分榜"), self)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        self.table = QTableWidget(self)
        columns = [
            tr("standings_col_position", "名次"),
            tr("standings_col_driver_code", "代碼"),
            tr("standings_col_driver", "車手"),
            tr("standings_col_team", "車隊"),
            tr("standings_col_points", "積分"),
            tr("standings_col_wins", "勝場"),
            tr("standings_col_delta", "落後差"),
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def _load_and_populate(self):
        if not self.json_path.exists():
            self.title_label.setText(
                tr("error_file_not_found", "錯誤：找不到檔案 {path}").format(path=str(self.json_path))
            )
            return

        with open(self.json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if not data.get("success"):
            self.title_label.setText(tr("error_data_invalid", "錯誤：資料無效"))
            return

        # 初始化顏色系統
        metadata = data.get("metadata", {})
        season_year = metadata.get("season_year", 2024)
        try:
            color_palette_provider.ensure_loaded(year=season_year)
            print(f"[DEMO2] 顏色系統已載入 (year={season_year})")
        except Exception as e:
            print(f"[DEMO2] 顏色系統載入失敗: {e}")

        drivers = data.get("data", {}).get("drivers", [])
        self.table.setRowCount(len(drivers))

        for row_idx, entry in enumerate(drivers):
            driver = entry.get("driver", {})
            driver_code = driver.get("code", "")
            driver_name = driver.get("full_name", "")
            
            # 獲取車手顏色（會自動 fallback 到車隊顏色）
            driver_color = color_palette_provider.get_driver_color(
                driver_code, format="qcolor", fallback=True
            )
            
            self._set_item(row_idx, 0, entry.get("position"))
            
            # 車手代碼加背景色
            code_item = self._create_colored_item(driver_code, driver_color)
            self.table.setItem(row_idx, 1, code_item)
            
            # 車手姓名加背景色
            name_item = self._create_colored_item(driver_name, driver_color)
            self.table.setItem(row_idx, 2, name_item)
            
            # 車隊名稱也加背景色
            constructors = entry.get("constructors", [])
            if constructors:
                team_name = constructors[0].get("name", "")
                
                # 移除 "F1 Team" 後綴以簡化顯示
                display_team_name = team_name.replace(" F1 Team", "").strip()
                
                team_color = color_palette_provider.get_team_color(
                    team_name, format="qcolor", fallback=True
                )
                # 使用簡化後的顯示名稱
                team_item = self._create_colored_item(display_team_name, team_color)
                self.table.setItem(row_idx, 3, team_item)
            else:
                self._set_item(row_idx, 3, "")
            
            self._set_item(row_idx, 4, entry.get("points"))
            self._set_item(row_idx, 5, entry.get("wins"))
            delta = entry.get("points_delta")
            delta_text = "0.0" if delta == 0.0 else f"+{delta}"
            self._set_item(row_idx, 6, delta_text)

        self.table.resizeColumnsToContents()

    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """創建帶背景色的表格項目，自動選擇文字顏色"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(bg_color))
        
        # 根據背景色亮度決定文字顏色
        # 使用相對亮度公式: Y = 0.299*R + 0.587*G + 0.114*B
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        
        # 亮度 < 128 使用白色文字，否則使用黑色
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def _set_item(self, row: int, col: int, value: Any):
        text = "" if value is None else str(value)
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, col, item)


def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("F1T Demo 2 - 車手積分表")

    json_file = "json/championship_standings_2024_R24_20251012T155237Z.json"
    widget = DriverStandingsTable(json_path=json_file, parent=window)
    window.setCentralWidget(widget)
    window.resize(1000, 700)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
