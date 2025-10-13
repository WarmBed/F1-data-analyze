#!/usr/bin/env python3
"""
Driver Standings Table Widget

Displays driver championship standings with color-coded teams

Author: F1T Team
Date: 2025-10-12
Version: 1.0.0
"""

import sys
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QAbstractItemView, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush

from core.gui_i18n import tr
from modules.gui.themes.color_palette_provider import color_palette_provider


class DriverStandingsWidget(QWidget):
    """
    Driver Standings Table Widget
    
    Display driver championship standings including:
    - Position, driver code, driver name
    - Team (with color-coded background)
    - Points, wins, points delta
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.standings_data: List[Dict[str, Any]] = []
        self.season_year: int = 2024
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # 標題
        self.title_label = QLabel(tr("driver_standings_title", "車手積分榜"), self)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # 表格
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
    
    def populate_table(self, data: Dict[str, Any]):
        """
        填充表格資料
        
        Args:
            data: 轉換後的積分資料（來自 DataLoader）
        """
        # 🔍 調試：輸出接收到的數據結構
        print(f"[DRIVER_WIDGET] 📥 接收到的數據 keys: {list(data.keys())}")
        print(f"[DRIVER_WIDGET] 📥 season_year={data.get('season_year')}, round={data.get('round')}")
        print(f"[DRIVER_WIDGET] 📥 standings 數量: {len(data.get('standings', []))}")
        
        self.standings_data = data.get("standings", [])
        self.season_year = data.get("season_year", 2024)
        round_num = data.get("round", 0)
        
        print(f"[DRIVER_WIDGET] 📊 解析後: season_year={self.season_year}, round={round_num}")
        
        # 更新標題
        title = tr("driver_standings_title_with_round", "車手積分榜 - {year} 第 {round} 站").format(
            year=self.season_year,
            round=round_num
        )
        self.title_label.setText(title)
        print(f"[DRIVER_WIDGET] 📝 標題已設置: {title}")
        
        # 初始化顏色系統
        try:
            color_palette_provider.ensure_loaded(year=self.season_year)
            print(f"[DRIVER_WIDGET] 顏色系統已載入 (year={self.season_year})")
        except Exception as e:
            print(f"[DRIVER_WIDGET] ⚠️  顏色載入失敗: {e}")
        
        # 填充表格
        self.table.setRowCount(len(self.standings_data))
        
        for row_idx, entry in enumerate(self.standings_data):
            # 0. 名次
            self._set_item(row_idx, 0, entry.get("position"))
            
            # 1. 車手代碼（帶顏色背景）
            driver_code = entry.get("driver_code", "")
            driver_color = color_palette_provider.get_driver_color(driver_code, fallback=True)
            driver_code_item = self._create_colored_item(driver_code, driver_color)
            self.table.setItem(row_idx, 1, driver_code_item)
            
            # 2. 車手姓名（帶顏色背景）
            driver_name = entry.get("driver_name", "")
            driver_name_item = self._create_colored_item(driver_name, driver_color)
            self.table.setItem(row_idx, 2, driver_name_item)
            
            # 3. 車隊（帶顏色背景）
            team_name = entry.get("team", "Unknown")
            team_color = color_palette_provider.get_driver_color(driver_code, fallback=True)
            team_item = self._create_colored_item(team_name, team_color)
            self.table.setItem(row_idx, 3, team_item)
            
            # 4. 積分
            self._set_item(row_idx, 4, entry.get("points"))
            
            # 5. 勝場
            self._set_item(row_idx, 5, entry.get("wins"))
            
            # 6. 落後差距 (只顯示數字，不顯示符號)
            delta = entry.get("points_delta")
            delta_text = f"{delta:.1f}" if delta and delta > 0 else ""
            self._set_item(row_idx, 6, delta_text)
        
        self.table.resizeColumnsToContents()
        print(f"[DRIVER_WIDGET] Table populated ({len(self.standings_data)} drivers)")
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """
        創建帶背景色的表格項目，自動選擇文字顏色
        
        Args:
            text: 顯示文字
            bg_color: 背景顏色
            
        Returns:
            QTableWidgetItem: 帶顏色的表格項目
        """
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(bg_color))
        
        # 根據背景色亮度決定文字顏色
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def _set_item(self, row: int, col: int, value: Any):
        """
        設置普通表格項目
        
        Args:
            row: 行號
            col: 列號
            value: 值
        """
        text = "" if value is None else str(value)
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)


# Test code
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test Widget
    widget = DriverStandingsWidget()
    widget.setWindowTitle(tr("test_window_title", "Driver Standings Test"))
    widget.resize(900, 600)
    
    # Test data (for UI testing only)
    test_data = {
        "standings": [
            {
                "position": 1,
                "driver_code": "VER",
                "driver_name": "Max Verstappen",
                "team": "Red Bull Racing",
                "points": 393.0,
                "wins": 9,
                "points_delta": 0.0
            },
            {
                "position": 2,
                "driver_code": "NOR",
                "driver_name": "Lando Norris",
                "team": "McLaren",
                "points": 331.0,
                "wins": 3,
                "points_delta": 62.0
            }
        ],
        "season_year": 2024,
        "round": 24
    }
    
    widget.populate_table(test_data)
    widget.show()
    
    sys.exit(app.exec_())
