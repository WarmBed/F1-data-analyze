#!/usr/bin/env python3
"""
Constructor Standings Table Widget

Displays constructor championship standings with color-coded teams

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

from core.logger import get_logger
logger = get_logger(__name__)



class ConstructorStandingsWidget(QWidget):
    """
    Constructor Standings Table Widget
    
    Display constructor championship standings including:
    - Position, constructor name (with color-coded background)
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
        self.title_label = QLabel(tr("constructor_standings_title", "車隊積分榜"), self)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # 表格
        self.table = QTableWidget(self)
        columns = [
            tr("standings_col_position", "名次"),
            tr("standings_col_constructor", "車隊"),
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
        self.standings_data = data.get("standings", [])
        self.season_year = data.get("season_year", 2024)
        round_num = data.get("round", 0)
        is_future_season = data.get("_is_future_season", False)
        
        # 更新標題
        if is_future_season or (round_num == 0 and not self.standings_data):
            # 未來賽季：顯示友善標題
            title = tr("constructor_standings_title", "車隊積分榜 - {year}").format(year=self.season_year)
        else:
            title = tr("constructor_standings_title_with_round", "車隊積分榜 - {year} 第 {round} 站").format(
                year=self.season_year,
                round=round_num
            )
        self.title_label.setText(title)
        
        # 未來賽季或空數據：顯示友善訊息
        if is_future_season or not self.standings_data:
            self.table.setRowCount(1)
            empty_item = QTableWidgetItem(tr("future_season_no_data", "賽季數據尚未發布"))
            empty_item.setTextAlignment(Qt.AlignCenter)
            empty_item.setForeground(QColor("#6c757d"))
            self.table.setItem(0, 0, empty_item)
            self.table.setSpan(0, 0, 1, self.table.columnCount())
            return
        
        # 初始化顏色系統
        try:
            color_palette_provider.ensure_loaded(year=self.season_year)
            logger.debug(f"[CONSTRUCTOR_WIDGET] 顏色系統已載入 (year={self.season_year})")
        except Exception as e:
            logger.warning(f"[CONSTRUCTOR_WIDGET] ⚠️  顏色載入失敗: {e}")
        
        # 填充表格
        self.table.setRowCount(len(self.standings_data))
        
        for row_idx, entry in enumerate(self.standings_data):
            # 0. Position
            self._set_item(row_idx, 0, entry.get("position"))
            
            # 1. Constructor name (with color background)
            team_name = entry.get("constructor_name", "Unknown")
            team_slug = entry.get("team_slug", team_name.lower())  # ✅ 獲取 team_slug
            team_color = color_palette_provider.get_team_color(team_slug)  # ✅ 使用 team_slug 查詢
            team_item = self._create_colored_item(team_name, team_color)
            self.table.setItem(row_idx, 1, team_item)
            
            # 2. Points
            self._set_item(row_idx, 2, entry.get("points"))
            
            # 3. Wins
            self._set_item(row_idx, 3, entry.get("wins"))
            
            # 4. Points delta (只顯示數字，不顯示符號)
            delta = entry.get("points_delta")
            delta_text = f"{delta:.1f}" if delta and delta > 0 else ""
            self._set_item(row_idx, 4, delta_text)
        
        self.table.resizeColumnsToContents()
        logger.debug(f"[CONSTRUCTOR_WIDGET] Table populated ({len(self.standings_data)} teams)")
    
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
    widget = ConstructorStandingsWidget()
    widget.setWindowTitle(tr("test_window_title", "Constructor Standings Test"))
    widget.resize(700, 400)
    
    # Test data (for UI testing only)
    test_data = {
        "standings": [
            {
                "position": 1,
                "constructor_name": "McLaren",
                "points": 640.0,
                "wins": 7,
                "points_delta": 0.0
            },
            {
                "position": 2,
                "constructor_name": "Ferrari",
                "points": 619.0,
                "wins": 5,
                "points_delta": 21.0
            }
        ],
        "season_year": 2024,
        "round": 24
    }
    
    widget.populate_table(test_data)
    widget.show()
    
    sys.exit(app.exec_())
