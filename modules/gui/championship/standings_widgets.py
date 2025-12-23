#!/usr/bin/env python3
"""
整合積分榜 Widget 模組
將 Demo 1 (車隊積分) 和 Demo 2 (車手積分) 整合為可嵌入主 GUI 的模組
"""

import sys
import json
from typing import Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QApplication, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush

from modules.gui.themes.color_palette_provider import color_palette_provider

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger(component="championship_standings")


def tr(key: str, fallback: str) -> str:
    """簡化的翻譯函數"""
    return fallback


class ConstructorStandingsWidget(QWidget):
    """車隊積分榜 Widget - 可嵌入主 GUI"""
    
    def __init__(self, json_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.json_path = json_path or "json/championship_standings_2024_R24_20251012T155237Z.json"
        self._init_ui()
        self._load_and_populate()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 標題
        self.title_label = QLabel(tr("constructor_standings", "🏆 2024 車隊積分榜"))
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                padding: 5px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            tr("position", "排名"),
            tr("team", "車隊"),
            tr("points", "積分"),
            tr("wins", "勝場"),
            tr("delta", "變化")
        ])
        
        # 表格樣式
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 5px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
    
    def _load_and_populate(self):
        """載入並填充數據"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            self.title_label.setText(f"❌ 錯誤：無法載入數據 ({e})")
            return
        
        if not data.get("success"):
            self.title_label.setText(tr("error_data_invalid", "❌ 錯誤：資料無效"))
            return
        
        # 初始化顏色系統
        metadata = data.get("metadata", {})
        season_year = metadata.get("season_year", 2024)
        try:
            color_palette_provider.ensure_loaded(year=season_year)
        except Exception as e:
            logger.exception("[CONSTRUCTOR_WIDGET] 顏色系統載入失敗", exc_info=e)
        
        constructors = data.get("data", {}).get("constructors", [])
        self.table.setRowCount(len(constructors))
        
        for row_idx, entry in enumerate(constructors):
            constructor = entry.get("constructor", {})
            constructor_name = constructor.get("name", "")
            
            # 移除 "F1 Team" 後綴以簡化顯示
            display_name = constructor_name.replace(" F1 Team", "").strip()
            
            # 獲取車隊顏色（使用原始名稱）
            team_color = color_palette_provider.get_team_color(
                constructor_name, format="qcolor", fallback=True
            )
            
            self._set_item(row_idx, 0, entry.get("position"))
            
            # 車隊名稱加背景色（使用簡化後的顯示名稱）
            name_item = self._create_colored_item(display_name, team_color)
            self.table.setItem(row_idx, 1, name_item)
            
            self._set_item(row_idx, 2, entry.get("points"))
            self._set_item(row_idx, 3, entry.get("wins"))
            delta = entry.get("points_delta")
            delta_text = "0.0" if delta == 0.0 else f"+{delta}"
            self._set_item(row_idx, 4, delta_text)
        
        self.table.resizeColumnsToContents()
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """創建帶背景色的表格項目，自動選擇文字顏色"""
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
        """設置普通表格項目"""
        text = "" if value is None else str(value)
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)


class DriverStandingsWidget(QWidget):
    """車手積分榜 Widget - 可嵌入主 GUI"""
    
    def __init__(self, json_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.json_path = json_path or "json/championship_standings_2024_R24_20251012T155237Z.json"
        self._init_ui()
        self._load_and_populate()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 標題
        self.title_label = QLabel(tr("driver_standings", "🏁 2024 車手積分榜"))
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                padding: 5px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            tr("position", "排名"),
            tr("code", "代碼"),
            tr("driver", "車手"),
            tr("team", "車隊"),
            tr("points", "積分"),
            tr("wins", "勝場"),
            tr("delta", "變化")
        ])
        
        # 表格樣式
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 5px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
    
    def _load_and_populate(self):
        """載入並填充數據"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            self.title_label.setText(f"❌ 錯誤：無法載入數據 ({e})")
            return
        
        if not data.get("success"):
            self.title_label.setText(tr("error_data_invalid", "❌ 錯誤：資料無效"))
            return
        
        # 初始化顏色系統
        metadata = data.get("metadata", {})
        season_year = metadata.get("season_year", 2024)
        try:
            color_palette_provider.ensure_loaded(year=season_year)
        except Exception as e:
            logger.exception("[DRIVER_WIDGET] 顏色系統載入失敗", exc_info=e)
        
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
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def _set_item(self, row: int, col: int, value: Any):
        """設置普通表格項目"""
        text = "" if value is None else str(value)
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)


# 測試代碼
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 測試車隊積分榜
    constructor_widget = ConstructorStandingsWidget()
    constructor_widget.setWindowTitle("車隊積分榜測試")
    constructor_widget.resize(700, 400)
    constructor_widget.show()
    
    # 測試車手積分榜
    driver_widget = DriverStandingsWidget()
    driver_widget.setWindowTitle("車手積分榜測試")
    driver_widget.resize(900, 600)
    driver_widget.show()
    
    sys.exit(app.exec_())
