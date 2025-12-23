#!/usr/bin/env python3
"""
理想圈分段對比表格元件 - 表格版本
Ideal Lap Sector Comparison Table Widget

✅ 版本 3: QTableWidget 表格版本（與 Ranking Table UI 一致）
✅ 使用 QTableWidget + 自定義單元格繪製累積差異棒狀圖

作者: F1T Team
日期: 2025-10-10
版本: 3.0.0 (表格版本)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle, QApplication
)
from PyQt5.QtCore import Qt, QRect, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPen
from typing import Dict, List, Any, Optional

# 導入翻譯和配色
from core.gui_i18n import tr
# ✅ 導入共用顏色配置和通用顏色系統
from modules.gui.themes.color_palette_provider import color_palette_provider

from core.logger import get_logger
logger = get_logger(__name__)

try:
    from modules.gui.lap_analysis.ideal_lap.shared_colors import get_gap_color, get_cumulative_bar_color
except ImportError:
    from modules.gui.lap_analysis.ideal_lap.shared_colors import get_gap_color, get_cumulative_bar_color


class CumulativeBarDelegate(QStyledItemDelegate):
    """
    累積差異棒狀圖委託
    
    在表格單元格中繪製棒狀圖
    """
    
    def __init__(self, max_cumulative: float = 1.0, parent=None):
        super().__init__(parent)
        self.max_cumulative = max_cumulative
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """繪製棒狀圖"""
        # 獲取數值
        cumulative = index.data(Qt.UserRole)
        if cumulative is None:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # 繪製背景（選中狀態）
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, QBrush(QColor(255, 255, 255)))
        
        # 計算棒狀圖寬度
        bar_max_width = option.rect.width() - 100  # 預留文字空間
        
        if cumulative > 0 and self.max_cumulative > 0:
            percentage = cumulative / self.max_cumulative
            bar_width = percentage * bar_max_width
            
            # 顏色
            bar_color = self._get_cumulative_color(cumulative)
            
            # 繪製棒狀圖
            bar_rect = QRectF(
                option.rect.x() + 5,
                option.rect.y() + 5,
                bar_width,
                option.rect.height() - 10
            )
            painter.fillRect(bar_rect, QBrush(bar_color))
            
            # 邊框
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.drawRect(bar_rect)
            
            # 數值文字
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.setPen(QPen(QColor(200, 50, 50)))
            text_x = int(option.rect.x() + bar_width + 10)
            text_y = int(option.rect.y() + option.rect.height() // 2 + 4)
            painter.drawText(text_x, text_y, f"+{cumulative:.3f}s")
        else:
            # 完美圈
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.setPen(QPen(QColor(0, 150, 0)))
            text_x = int(option.rect.x() + 10)
            text_y = int(option.rect.y() + option.rect.height() // 2 + 4)
            painter.drawText(text_x, text_y, "0.000s ✓")
        
        painter.restore()
    
    def _get_cumulative_color(self, cumulative: float) -> QColor:
        """累積差異顏色（使用共用配置）"""
        return get_cumulative_bar_color(cumulative)
    
    def sizeHint(self, option: QStyleOptionViewItem, index):
        """設定單元格大小"""
        return super().sizeHint(option, index)


class IdealLapSectorComparisonTableWidget(QWidget):
    """
    理想圈分段對比表格元件 - 表格版本
    
    特點：
    - 使用 QTableWidget（與 Ranking Table 一致）
    - 車手欄位顯示車隊背景色
    - 分段差異使用顏色編碼
    - 累積差異使用棒狀圖（自定義委託）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據屬性
        self.comparison_data: List[Dict] = []
        self.max_cumulative = 0.0
        
        # ✅ 移除本地車隊顏色定義，使用共用配置
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 創建表格
        self.table = self._create_table()
        layout.addWidget(self.table)
    
    def _create_table(self) -> QTableWidget:
        """創建表格"""
        table = QTableWidget()
        
        # 設置欄位（使用多國語言）
        columns = [
            tr('sector_comparison_header_position', '排名'),
            tr('sector_comparison_header_driver', '車手'),
            tr('sector_comparison_header_s1_delta', 'S1 差異'),
            tr('sector_comparison_header_s2_delta', 'S2 差異'),
            tr('sector_comparison_header_s3_delta', 'S3 差異'),
            tr('sector_comparison_header_cumulative', '累積總差異')
        ]
        
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 設置表格屬性
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # ✅ 禁用選擇功能
        table.setSelectionMode(QAbstractItemView.NoSelection)
        
        # 設置欄位寬度
        table.setColumnWidth(0, 60)   # 排名
        table.setColumnWidth(1, 100)  # 車手
        table.setColumnWidth(2, 100)  # S1
        table.setColumnWidth(3, 100)  # S2
        table.setColumnWidth(4, 100)  # S3
        table.setColumnWidth(5, 300)  # 累積總差異（棒狀圖需要更寬）
        
        # 設置行高
        table.verticalHeader().setDefaultSectionSize(35)
        
        # 設置表頭
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # ✅ 隱藏排名欄位（第 0 欄）
        table.setColumnHidden(0, True)
        
        return table
    
    def update_data(self, data: Dict[str, Any]):
        """
        更新數據並填充表格
        
        Args:
            data: 包含 analysis_result.ranking 的字典
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[SECTOR_COMPARISON_TABLE] 無效的數據格式")
                return
            
            # 提取排名數據
            if 'analysis_result' in data:
                self.comparison_data = data['analysis_result'].get('ranking', [])
            else:
                self.comparison_data = data.get('comparison_data', [])
            
            if not self.comparison_data:
                return
            
            # 計算最大累積差異
            self._calculate_max_cumulative()
            
            # 填充表格
            self._populate_table()
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_TABLE] 更新數據失敗: {e}")
    
    def _calculate_max_cumulative(self):
        """計算最大累積差異"""
        max_delta = 0.0
        for driver_data in self.comparison_data:
            sector_breakdown = driver_data.get("sector_breakdown", {})
            
            delta_s1 = sector_breakdown.get("sector_1", {}).get("delta", 0) or 0
            delta_s2 = sector_breakdown.get("sector_2", {}).get("delta", 0) or 0
            delta_s3 = sector_breakdown.get("sector_3", {}).get("delta", 0) or 0
            
            cumulative = delta_s1 + delta_s2 + delta_s3
            max_delta = max(max_delta, cumulative)
        
        self.max_cumulative = max_delta
    
    def _populate_table(self):
        """填充表格數據"""
        row_count = len(self.comparison_data)
        
        self.table.setSortingEnabled(False)
        self.table.setRowCount(row_count)
        
        for row, driver_data in enumerate(self.comparison_data):
            self._populate_row(row, driver_data)
        
        # 設置累積差異欄位的委託
        bar_delegate = CumulativeBarDelegate(self.max_cumulative, self.table)
        self.table.setItemDelegateForColumn(5, bar_delegate)
        
        self.table.setSortingEnabled(True)
    
    def _populate_row(self, row: int, driver_data: Dict):
        """填充單行數據"""
        # 0. 排名
        position = driver_data.get("position", row + 1)
        pos_item = QTableWidgetItem(str(position))
        pos_item.setTextAlignment(Qt.AlignCenter)
        pos_item.setFont(QFont("Arial", 8))
        self.table.setItem(row, 0, pos_item)
        
        # 1. 車手（車手背景色，與 Ranking Table 保持一致）
        driver_code = driver_data.get("driver", "N/A")
        team = driver_data.get("team", "Unknown")
        driver_color = self._get_driver_color(driver_code)
        driver_item = self._create_colored_item(driver_code, driver_color)
        driver_item.setToolTip(f"{driver_code} - {team}")
        self.table.setItem(row, 1, driver_item)
        
        # 提取分段數據
        sector_breakdown = driver_data.get("sector_breakdown", {})
        
        # 2. S1 差異
        s1_delta = sector_breakdown.get("sector_1", {}).get("delta", 0) or 0
        s1_item = self._create_delta_item(s1_delta)
        self.table.setItem(row, 2, s1_item)
        
        # 3. S2 差異
        s2_delta = sector_breakdown.get("sector_2", {}).get("delta", 0) or 0
        s2_item = self._create_delta_item(s2_delta)
        self.table.setItem(row, 3, s2_item)
        
        # 4. S3 差異
        s3_delta = sector_breakdown.get("sector_3", {}).get("delta", 0) or 0
        s3_item = self._create_delta_item(s3_delta)
        self.table.setItem(row, 4, s3_item)
        
        # 5. 累積總差異（使用委託繪製棒狀圖）
        cumulative = s1_delta + s2_delta + s3_delta
        cumulative_item = QTableWidgetItem()
        # ✅ 同時設置 DisplayRole (用於排序) 和 UserRole (用於繪製)
        cumulative_item.setData(Qt.DisplayRole, cumulative)  # 排序用
        cumulative_item.setData(Qt.UserRole, cumulative)     # 委託繪製用
        cumulative_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, 5, cumulative_item)
    
    def _create_delta_item(self, delta: float) -> QTableWidgetItem:
        """
        創建分段差異單元格
        
        Args:
            delta: 差異值（秒）
            
        Returns:
            QTableWidgetItem: 格式化的單元格
        """
        # 格式化文字
        if abs(delta) < 0.001:
            text = "✓"
        else:
            text = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
        
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFont(QFont("Arial", 8))
        
        # 設置背景色
        bg_color = self._get_delta_color(delta)
        item.setBackground(bg_color)
        
        # 設置前景色（統一使用黑色）
        if abs(delta) < 0.001:
            item.setForeground(QBrush(QColor(0, 0, 0)))
            item.setFont(QFont("Arial", 8, QFont.Bold))
        else:
            item.setForeground(QBrush(QColor(50, 50, 50)))
        
        return item
    
    def _get_driver_color(self, driver_code: str) -> QColor:
        """
        獲取車手顏色（使用通用顏色系統，與 Ranking Table 保持一致）
        
        Args:
            driver_code: 車手代碼（例如: "VER", "HAM"）
            
        Returns:
            QColor: 車手顏色
        """
        return color_palette_provider.get_driver_color(driver_code, fallback=True)
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """
        創建帶背景色的表格項目，自動選擇文字顏色（與 Ranking Table 保持一致）
        
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
    
    def _get_delta_color(self, delta: float) -> QColor:
        """分段差異顏色（使用共用配置）"""
        return get_gap_color(delta)
