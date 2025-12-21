#!/usr/bin/env python3
"""
車手比賽排名分析表格元件
Driver Position Analysis Widget

負責顯示車手比賽排名變化，包含起始排名、結束排名、最佳/最差排名和位置變化
支援排序、顏色編碼、三角形符號標示

作者: F1T Team
日期: 2025-10-28
版本: 1.0.0
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush
from typing import Dict, List, Any, Optional

from core.gui_i18n import tr, get_team_name_text
from modules.gui.themes.color_palette_provider import color_palette_provider

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger("gui.driver_position_analysis_widget", component="gui")


class NumericSortTableWidgetItem(QTableWidgetItem):
    """
    支援數值排序的 QTableWidgetItem 子類別
    
    解決 QTableWidget 預設按字串排序的問題（1, 10, 11, 2...）
    使用 UserRole 儲存數值，重寫 __lt__ 方法進行數值比較
    """
    def __lt__(self, other):
        """重寫小於比較，使用 UserRole 的數值進行排序"""
        my_value = self.data(Qt.UserRole)
        other_value = other.data(Qt.UserRole)
        
        # 確保兩者都是數值
        if my_value is not None and other_value is not None:
            return my_value < other_value
        elif my_value is None:
            return False  # None 排在最後
        else:
            return True


class DriverPositionAnalysisWidget(QWidget):
    """
    車手比賽排名分析表格元件
    
    顯示所有車手的排名變化，包含：
    - 8 欄位表格（隱藏排名、車手、車隊、起始排名、結束排名、最佳排名、最差排名、位置變化）
    - 車隊顏色編碼
    - 位置變化三角形符號（▲進步/▼退步/━持平）
    - 排序功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 資料快取
        self._current_data = None
        self._position_data = []
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI 佈局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 創建主表格
        self.table = self._create_table()
        layout.addWidget(self.table, 1)  # 給予彈性空間
    
    def _create_table(self) -> QTableWidget:
        """創建主表格"""
        table = QTableWidget()
        
        # 設置欄位
        columns = [
            tr('table_header_position', '排名'),                  # 0: position (隱藏)
            tr('table_header_driver', '車手'),                    # 1: driver
            tr('table_header_team', '車隊'),                      # 2: team
            tr('table_header_starting_position', '起始排名'),     # 3: starting_position
            tr('table_header_finishing_position', '結束排名'),    # 4: finishing_position
            tr('table_header_best_position', '最佳排名'),         # 5: best_position
            tr('table_header_worst_position', '最差排名'),        # 6: worst_position
            tr('table_header_position_change', '位置變化'),       # 7: position_change
        ]
        
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 設置表格屬性
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 設置欄位寬度（8 欄）
        table.setColumnWidth(0, 60)   # 排名（隱藏）
        table.setColumnWidth(1, 80)   # 車手
        table.setColumnWidth(2, 150)  # 車隊
        table.setColumnWidth(3, 120)  # 起始排名
        table.setColumnWidth(4, 120)  # 結束排名
        table.setColumnWidth(5, 100)  # 最佳排名
        table.setColumnWidth(6, 100)  # 最差排名
        table.setColumnWidth(7, 120)  # 位置變化
        
        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)  # 最後一欄自動伸展
        
        # 隱藏排名欄位（第 0 欄）
        table.setColumnHidden(0, True)
        
        return table
    
    # ========== 公開方法 ==========
    
    def populate_table(self, position_data: List[Dict[str, Any]]):
        """
        填充表格資料
        
        Args:
            position_data: 車手排名資料列表
        """
        try:
            self._position_data = position_data
            row_count = len(position_data)
            
            self.table.setSortingEnabled(False)  # 暫時禁用排序以提高效能
            self.table.setRowCount(row_count)
            
            for row, driver_data in enumerate(position_data):
                self._set_row_data(row, driver_data)
            
            self.table.setSortingEnabled(True)  # 重新啟用排序
            logger.info("[POSITION_WIDGET] 已載入 %d 位車手", row_count)
            
        except Exception as e:
            logger.exception("[POSITION_WIDGET] 填充表格失敗")
    
    def clear_table(self):
        """清空表格"""
        self.table.setRowCount(0)
        self._position_data = []
        logger.info("[POSITION_WIDGET] 表格已清空")
    
    # ========== 私有方法 ==========
    
    def _set_row_data(self, row: int, driver_data: Dict[str, Any]):
        """
        設置單行資料
        
        Args:
            row: 行號
            driver_data: 車手資料字典
        """
        try:
            driver_code = driver_data.get("driver", tr('na', 'N/A'))
            team = driver_data.get("team", tr('unknown_team', 'Unknown'))
            starting_pos = driver_data.get("starting_position")
            finishing_pos = driver_data.get("finishing_position")
            best_pos = driver_data.get("best_position")
            worst_pos = driver_data.get("worst_position")
            
            # 計算位置變化（起始 - 結束，正數為進步）
            # DNF 車手無法計算位置變化，設為 None
            if starting_pos is not None and finishing_pos is not None:
                if finishing_pos == "DNF":
                    position_change = None  # DNF 無法計算變化
                else:
                    position_change = starting_pos - finishing_pos
            else:
                position_change = None
            
            # 獲取車手顏色
            driver_color = self._get_driver_color(driver_code)
            team_translated = get_team_name_text(team)
            
            # 0. 排名（隱藏，用於排序）
            pos_item = QTableWidgetItem()
            pos_item.setData(Qt.DisplayRole, finishing_pos if finishing_pos else 999)
            pos_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, pos_item)
            
            # 1. 車手（套用車隊顏色）
            driver_item = self._create_colored_item(driver_code, driver_color)
            self.table.setItem(row, 1, driver_item)
            
            # 2. 車隊（套用車隊顏色）
            team_item = self._create_colored_item(team_translated, driver_color)
            self.table.setItem(row, 2, team_item)
            
            # 3. 起始排名
            starting_item = self._create_position_item(starting_pos)
            self.table.setItem(row, 3, starting_item)
            
            # 4. 結束排名
            finishing_item = self._create_position_item(finishing_pos)
            self.table.setItem(row, 4, finishing_item)
            
            # 5. 最佳排名
            best_item = self._create_position_item(best_pos)
            self.table.setItem(row, 5, best_item)
            
            # 6. 最差排名
            worst_item = self._create_position_item(worst_pos)
            self.table.setItem(row, 6, worst_item)
            
            # 7. 位置變化（三角形符號 + 顏色背景）
            change_item = self._create_position_change_item(position_change)
            self.table.setItem(row, 7, change_item)
            
        except Exception as e:
            logger.exception("[POSITION_WIDGET] 設置行資料失敗 (row %d)", row)
    
    def _create_position_item(self, position) -> QTableWidgetItem:
        """
        創建排名欄位項目（支援數值排序）
        
        Args:
            position: 排名數字 (int) 或 DNF 狀態 (str "DNF")
            
        Returns:
            NumericSortTableWidgetItem: 支援數值排序的表格項目
        """
        item = NumericSortTableWidgetItem()  # 使用自定義類別
        if position is not None:
            # 檢查是否為 DNF
            if isinstance(position, str) and position == "DNF":
                item.setText("DNF")
                item.setData(Qt.UserRole, 998)  # 排序值：DNF 排倒數第二
            else:
                # 正常位置：顯示 "P1" 但按數值 1 排序
                item.setText(f"P{position}")
                item.setData(Qt.UserRole, int(position))  # 排序值：使用數值
        else:
            item.setText(tr('na', 'N/A'))
            item.setData(Qt.UserRole, 999)  # 排序值：N/A 排最後
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def _create_position_change_item(self, change) -> QTableWidgetItem:
        """
        創建位置變化項目（帶三角形符號和顏色，支援數值排序）
        
        Args:
            change: 位置變化（正數為進步，負數為退步，None 為無法計算如 DNF）
            
        Returns:
            NumericSortTableWidgetItem: 支援數值排序的表格項目
        """
        item = NumericSortTableWidgetItem()  # 使用自定義類別
        
        # 設置字體（8pt，與 Ideal Lap Ranking Table 統一）
        font = QFont()
        font.setPointSize(8)
        # ✅ 移除粗體
        item.setFont(font)
        
        # 處理 None 值（DNF 或無數據）
        if change is None:
            item.setText(tr('na', 'N/A'))
            item.setData(Qt.UserRole, 1000)  # 排序值：排在最後
            item.setBackground(QColor(230, 230, 230))  # 淺灰色
            item.setForeground(QColor(100, 100, 100))  # 深灰色文字
            item.setTextAlignment(Qt.AlignCenter)
            return item
        
        item.setData(Qt.UserRole, change)  # 用於排序
        
        if change > 0:
            # 進步：綠色背景 + ▲ 符號
            item.setText(f"{change} ▲")
            item.setBackground(QColor(200, 255, 200))  # 淺綠色
            item.setForeground(QColor(0, 120, 0))      # 深綠色文字
        elif change < 0:
            # 退步：紅色背景 + ▼ 符號
            item.setText(f"{change} ▼")
            item.setBackground(QColor(255, 200, 200))  # 淺紅色
            item.setForeground(QColor(180, 0, 0))      # 深紅色文字
        else:
            # 持平：灰色背景 + ━ 符號
            item.setText("0 ━")
            item.setBackground(QColor(230, 230, 230))  # 淺灰色
            item.setForeground(QColor(100, 100, 100))  # 深灰色文字
        
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def _create_colored_item(self, text: str, color: QColor) -> QTableWidgetItem:
        """
        創建帶顏色背景的表格項目（自動選擇文字顏色）
        
        Args:
            text: 顯示文字
            color: 背景顏色
            
        Returns:
            QTableWidgetItem: 表格項目
        """
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        
        # 設置背景色
        item.setBackground(QBrush(color))
        
        # 自動選擇文字顏色（黑或白）
        text_color = self._get_contrasting_text_color(color)
        item.setForeground(QBrush(text_color))
        
        # 設置字體（8pt，與 Ideal Lap Ranking Table 統一）
        font = QFont()
        # ✅ 移除粗體
        font.setPointSize(8)
        item.setFont(font)
        
        return item
    
    def _get_driver_color(self, driver_code: str) -> QColor:
        """
        獲取車手的車隊顏色
        
        Args:
            driver_code: 車手代碼（如 'VER', 'LEC'）
            
        Returns:
            QColor: 車隊顏色
        """
        try:
            hex_color = color_palette_provider.get_driver_color(driver_code)
            return QColor(hex_color)
        except Exception:
            return QColor("#CCCCCC")  # 預設灰色
    
    def _get_contrasting_text_color(self, bg_color: QColor) -> QColor:
        """
        根據背景色自動選擇對比文字顏色（黑或白）
        
        Args:
            bg_color: 背景顏色
            
        Returns:
            QColor: 文字顏色（黑或白）
        """
        # 計算亮度（使用 YIQ 公式）
        r, g, b, _ = bg_color.getRgb()
        yiq = (r * 299 + g * 587 + b * 114) / 1000
        
        # 亮度 > 128 使用黑色文字，否則使用白色
        return QColor(0, 0, 0) if yiq >= 128 else QColor(255, 255, 255)
