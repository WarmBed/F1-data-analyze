#!/usr/bin/env python3
"""
全車手最高速度分析表格元件
All Drivers Max Speed Table Widget

顯示 F121 API 返回的全車手最高速度統計數據
- 車手欄位使用車隊顏色
- Accel Performance 使用棒狀圖視覺化（與 All Drivers Speed & Acceleration 一致）

作者: F1T Team
日期: 2025-12-14
版本: 1.1.0
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QBrush, QFont, QPainter, QPen
from typing import Dict, List, Any, Optional

# 導入翻譯和配色
from core.gui_i18n import tr
from modules.gui.themes.color_palette_provider import (
    color_palette_provider,
    DEFAULT_DRIVER_MAP
)

from core.logger import get_logger
logger = get_logger("all_drivers_max_speed_table", component="gui")


class AccelerationBarDelegate(QStyledItemDelegate):
    """
    加速時間棒狀圖委託
    
    視覺化邏輯：
    - 棒狀圖長度 = 基於加速時間（100-300 km/h）
    - 時間越短 = 棒狀圖越短 = 性能越好
    - 使用相對時間範圍計算，使差異更明顯
    """
    
    def __init__(self, min_time: float = 0.0, max_time: float = 10.0, parent=None):
        super().__init__(parent)
        self.min_time = min_time  # 最快車手的時間
        self.max_time = max_time  # 最慢車手的時間
        self.time_range = max_time - min_time  # 時間範圍
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """繪製加速視覺化圖表"""
        # 獲取加速時間數據
        accel_time = index.data(Qt.UserRole)  # 加速時間（排序和繪圖依據）
        
        # 檢查數據有效性
        if accel_time is None or accel_time == 9999 or accel_time <= 0:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # 繪製背景（選中狀態）
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, QBrush(QColor(255, 255, 255)))
        
        # 計算關鍵位置（使用相對時間比例）
        base_x = option.rect.x() + 10
        base_y = option.rect.y() + 10
        
        # 文字和棒狀圖佈局
        text_reserved_width = 80  # 預留文字寬度
        left_margin = 10  # 左邊距
        text_margin = 10  # 棒狀圖與文字的間距
        
        # 計算棒狀圖最大可用寬度
        total_width = option.rect.width()
        bar_max_width = total_width - left_margin - text_reserved_width
        bar_height = 20
        
        # 使用相對時間計算棒狀圖長度
        if self.time_range > 0:
            relative_ratio = (accel_time - self.min_time) / self.time_range
        else:
            relative_ratio = 0.0
        
        # 棒狀圖寬度（按比例縮放）
        bar_width = min(bar_max_width * relative_ratio, bar_max_width)
        
        # 繪製加速棒（深藍色實心棒）
        bar_rect = QRectF(base_x, base_y, bar_width, bar_height)
        painter.fillRect(bar_rect, QBrush(QColor(50, 100, 180)))  # 深藍色實心
        painter.setPen(QPen(QColor(30, 70, 140), 2))  # 深藍邊框
        painter.drawRect(bar_rect)
        
        # 繪製時間標籤（固定位置）
        text_x = int(base_x + bar_max_width + text_margin)
        
        # 顯示加速時間
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QPen(QColor(50, 100, 180)))  # 深藍色
        text_y = int(base_y + 15)
        painter.drawText(text_x, text_y, f"{accel_time:.3f} s")
        
        painter.restore()
    
    def sizeHint(self, option: QStyleOptionViewItem, index):
        """設定單元格大小"""
        return super().sizeHint(option, index)


class AllDriversMaxSpeedTableWidget(QWidget):
    """
    全車手最高速度分析表格元件
    
    欄位:
    - Driver: 車手代碼（車隊背景色）
    - Team: 車隊名稱（車隊背景色）
    - Max Speed (km/h): 絕對最高速度
    - Median Speed (km/h): 速度中位數
    - Speed StdDev: 速度標準差
    - Accel 100-300 (s): 加速時間（熱力圖背景）
    - Time to Max (s): 到達最高速度時間
    
    排序: 預設按 Max Speed 降序
    """
    
    # 欄位定義
    COLUMNS = [
        ("driver", "Driver"),
        ("team", "Team"),
        ("max_speed", "Max Speed (km/h)"),
        ("median_speed", "Median Speed (km/h)"),
        ("speed_std", "Speed StdDev"),
        ("time_to_max", "Time to Max (s)"),
        ("accel_100_300", "Accel 100-300 (s)"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據
        self._drivers_data: List[Dict[str, Any]] = []
        
        # 加速時間範圍（用於棒狀圖委託）
        self._min_accel_time = 0.0
        self._max_accel_time = 10.0
        
        # 初始化 UI
        self._init_ui()
        
        logger.info("[MAX_SPEED_TABLE] 表格元件初始化完成")
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 創建表格（移除資訊標籤）
        self.table = self._create_table()
        layout.addWidget(self.table)
    
    def _create_table(self) -> QTableWidget:
        """創建表格"""
        table = QTableWidget()
        table.setColumnCount(len(self.COLUMNS))
        
        # 設定表頭
        headers = [tr(f"max_speed_col_{col[0]}", col[1]) for col in self.COLUMNS]
        table.setHorizontalHeaderLabels(headers)
        
        # 表格屬性
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setSortingEnabled(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        
        # 欄位寬度
        column_widths = {
            "driver": 80,
            "team": 150,
            "max_speed": 140,
            "median_speed": 150,
            "speed_std": 100,
            "accel_100_300": 140,
            "time_to_max": 130,
        }
        
        for idx, (col_key, _) in enumerate(self.COLUMNS):
            width = column_widths.get(col_key, 100)
            table.setColumnWidth(idx, width)
        
        # 行高
        table.verticalHeader().setDefaultSectionSize(40)
        
        # 最後一欄拉伸
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        return table
    
    def set_data(self, data: Dict[str, Any]):
        """
        設置數據並填充表格
        
        Args:
            data: API 返回的數據，包含 drivers 陣列
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[MAX_SPEED_TABLE] 無效的數據格式")
                return
            
            # 提取 drivers 數據
            drivers = data.get("drivers", [])
            if not drivers:
                # 嘗試其他可能的 key
                drivers = data.get("data", {}).get("drivers", [])
            
            if not drivers:
                logger.warning("[MAX_SPEED_TABLE] 無 drivers 數據")
                return
            
            logger.info(f"[MAX_SPEED_TABLE] 設定數據: {len(drivers)} 位車手")
            
            # 按 absolute_max_speed_kmh 降序排列
            sorted_drivers = sorted(
                drivers,
                key=lambda x: x.get("absolute_max_speed_kmh", 0) or 0,
                reverse=True
            )
            
            # 計算熱力圖範圍
            self._calculate_accel_range(sorted_drivers)
            
            # 確保顏色數據已載入
            try:
                color_palette_provider.ensure_loaded()
            except Exception as e:
                logger.warning(f"[MAX_SPEED_TABLE] 顏色載入失敗: {e}")
            
            # 填充表格
            self._populate_table(sorted_drivers)
            
        except Exception as e:
            logger.exception(f"[MAX_SPEED_TABLE] 設定數據失敗: {e}")
    
    def _calculate_accel_range(self, drivers: List[Dict[str, Any]]):
        """計算加速時間範圍用於棒狀圖委託"""
        accel_times = []
        for d in drivers:
            accel_stats = d.get("acceleration_100_300_stats", {})
            median = accel_stats.get("median")
            if median is not None and median > 0:
                accel_times.append(median)
        
        if accel_times:
            self._min_accel_time = min(accel_times)
            self._max_accel_time = max(accel_times)
        else:
            self._min_accel_time = 5.0
            self._max_accel_time = 8.0
    
    def _get_team_name(self, driver_code: str) -> str:
        """
        從 ColorPaletteProvider 獲取車隊名稱
        
        Args:
            driver_code: 車手代碼（如 VER, HAM）
            
        Returns:
            車隊名稱（如 Red Bull Racing, Mercedes）
        """
        # 使用 ColorPaletteProvider 統一獲取車隊名稱 (2025-12-14 更新)
        return color_palette_provider.get_driver_team(driver_code, fallback=True)
    
    def _populate_table(self, drivers: List[Dict[str, Any]]):
        """填充表格"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(drivers))
        
        for row, driver_data in enumerate(drivers):
            driver_code = driver_data.get("driver", "N/A")
            team = self._get_team_name(driver_code)  # 使用 DEFAULT_DRIVER_MAP
            
            # 提取數據
            absolute_max_speed = driver_data.get("absolute_max_speed_kmh")
            
            speed_stats = driver_data.get("speed_stats", {})
            median_speed = speed_stats.get("median")
            std_dev = speed_stats.get("std_dev")
            
            accel_stats = driver_data.get("acceleration_100_300_stats", {})
            accel_median = accel_stats.get("median")
            
            time_stats = driver_data.get("time_to_max_speed_stats", {})
            time_to_max = time_stats.get("median")
            
            # 獲取車手顏色
            driver_color = color_palette_provider.get_driver_color(driver_code, fallback=True)
            if not isinstance(driver_color, QColor):
                driver_color = QColor(100, 100, 100)
            
            # 計算文字顏色（根據背景亮度）
            luminance = (0.299 * driver_color.red() + 0.587 * driver_color.green() + 0.114 * driver_color.blue())
            text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
            
            # 0. Driver
            driver_item = QTableWidgetItem(driver_code)
            driver_item.setTextAlignment(Qt.AlignCenter)
            driver_item.setFont(QFont("Arial", 10, QFont.Bold))
            driver_item.setBackground(driver_color)
            driver_item.setForeground(QBrush(text_color))
            self.table.setItem(row, 0, driver_item)
            
            # 1. Team
            team_item = QTableWidgetItem(team)
            team_item.setTextAlignment(Qt.AlignCenter)
            team_item.setFont(QFont("Arial", 9))
            team_item.setBackground(driver_color)
            team_item.setForeground(QBrush(text_color))
            self.table.setItem(row, 1, team_item)
            
            # 2. Max Speed (無小數點，置中)
            max_speed_item = self._create_number_item(absolute_max_speed, "{:.0f}", align=Qt.AlignCenter)
            self.table.setItem(row, 2, max_speed_item)
            
            # 3. Median Speed (無小數點，置中)
            median_item = self._create_number_item(median_speed, "{:.0f}", align=Qt.AlignCenter)
            self.table.setItem(row, 3, median_item)
            
            # 4. Speed StdDev (置中)
            std_item = self._create_number_item(std_dev, "{:.2f}", align=Qt.AlignCenter)
            self.table.setItem(row, 4, std_item)
            
            # 5. Time to Max (置中)
            time_item = self._create_number_item(time_to_max, "{:.3f}", align=Qt.AlignCenter)
            self.table.setItem(row, 5, time_item)
            
            # 6. Accel 100-300 (使用棒狀圖委託)
            accel_item = QTableWidgetItem("")  # 空文字，由委託繪製
            if accel_median is not None and accel_median > 0:
                accel_item.setData(Qt.UserRole, accel_median)  # 用於排序和繪圖
            else:
                accel_item.setData(Qt.UserRole, 9999)  # N/A 標記
                accel_item.setText("N/A")
                accel_item.setForeground(QBrush(QColor(150, 150, 150)))
            accel_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, accel_item)
        
        # 設置 Accel 100-300 欄位的棒狀圖委託
        bar_delegate = AccelerationBarDelegate(self._min_accel_time, self._max_accel_time, self.table)
        self.table.setItemDelegateForColumn(6, bar_delegate)
        
        # 預設按 Max Speed 降序排列
        self.table.sortItems(2, Qt.DescendingOrder)
        self.table.setSortingEnabled(True)
        
        logger.info(f"[MAX_SPEED_TABLE] 表格填充完成: {len(drivers)} 行")
    
    def _create_number_item(
        self,
        value: Optional[float],
        format_str: str,
        align: int = Qt.AlignRight
    ) -> QTableWidgetItem:
        """
        創建數值表格項目
        
        Args:
            value: 數值
            format_str: 格式化字串
            align: 對齊方式
            
        Returns:
            QTableWidgetItem
        """
        if value is not None:
            text = format_str.format(value)
            item = QTableWidgetItem(text)
            item.setData(Qt.UserRole, value)  # 用於排序
        else:
            item = QTableWidgetItem("N/A")
            item.setData(Qt.UserRole, -9999)  # N/A 排序時放最後
            item.setForeground(QBrush(QColor(150, 150, 150)))
        
        item.setTextAlignment(align | Qt.AlignVCenter)
        item.setFont(QFont("Arial", 9))
        return item
    
    def clear(self):
        """清空表格"""
        self.table.setRowCount(0)
        self._drivers_data = []
