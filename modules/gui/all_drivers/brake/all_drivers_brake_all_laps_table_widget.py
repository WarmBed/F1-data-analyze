#!/usr/bin/env python3
"""
全車手煞車全圈數分析表格元件
All Drivers Brake All Laps Table Widget

顯示全車手的煞車性能統計分析（全場比賽）
包含 10 個完整統計欄位 + 中位數減速度視覺化棒狀圖

欄位列表（選項 C: 完整統計欄位）:
1. driver - 車手
2. team - 車隊
3. median - 中位數 (m/s²)
4. mean - 平均值 (m/s²)
5. std_dev - 標準差 (m/s²)
6. min - 最小值 (m/s²)
7. max - 最大值 (m/s²)
8. cv - 變異係數 (%)
9. valid_laps - 有效圈數
10. outlier_count - 異常值

視覺化：使用中位數減速度繪製棒狀圖（選項 C）

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QStyledItemDelegate,
    QStyle, QAbstractItemView
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import (
    QFont, QColor, QBrush, QPainter, QPen, QLinearGradient
)

from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.themes.color_palette_provider import (
    color_palette_provider,
    DEFAULT_DRIVER_MAP
)

logger = get_logger(component="AllDriversBrakeAllLapsTableWidget")


class MedianDecelBarDelegate(QStyledItemDelegate):
    """
    中位數減速度棒狀圖委託
    
    繪製基於中位數減速度的視覺化棒狀圖（選項 C）
    減速度越大（絕對值越大）= 棒越長 = 煞車越強
    
    顏色編碼：
    - 綠色: > 40 m/s² (強煞車)
    - 橙色: 30-40 m/s² (中等煞車)
    - 紅色: < 30 m/s² (弱煞車)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 繪圖參數
        self.min_decel = 20.0   # 最小減速度（用於比例計算）
        self.max_decel = 50.0   # 最大減速度（用於比例計算）
        self.decel_range = self.max_decel - self.min_decel
    
    def update_range(self, min_decel: float, max_decel: float):
        """更新減速度範圍（根據實際數據調整）"""
        self.min_decel = min_decel
        self.max_decel = max_decel
        self.decel_range = max(self.max_decel - self.min_decel, 1.0)  # 避免除以零
    
    def paint(self, painter: QPainter, option, index):
        """繪製棒狀圖"""
        # 獲取中位數減速度（絕對值）
        median_decel = index.data(Qt.UserRole)
        if median_decel is None or median_decel == 0:
            # 沒有數據時顯示 N/A
            super().paint(painter, option, index)
            return
        
        # 確保使用絕對值（減速度通常是負數）
        decel_abs = abs(float(median_decel))
        
        # 計算棒狀圖參數
        rect = option.rect
        margin = 4
        bar_max_width = rect.width() - 2 * margin - 60  # 保留空間顯示數值
        bar_height = rect.height() - 2 * margin
        
        # 計算棒狀圖長度（基於減速度比例）
        relative_ratio = (decel_abs - self.min_decel) / self.decel_range
        relative_ratio = max(0.0, min(1.0, relative_ratio))  # 限制在 0-1 範圍
        bar_width = int(bar_max_width * relative_ratio)
        
        # 決定顏色（基於減速度閾值）
        if decel_abs > 40:
            bar_color = QColor(0, 150, 0)   # 綠色：強煞車
        elif decel_abs > 30:
            bar_color = QColor(255, 150, 0) # 橙色：中等煞車
        else:
            bar_color = QColor(200, 0, 0)   # 紅色：弱煞車
        
        # 繪製背景
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())
        else:
            painter.fillRect(rect, option.palette.base())
        
        # 繪製棒狀圖
        bar_rect = QRect(
            rect.left() + margin,
            rect.top() + margin,
            bar_width,
            bar_height
        )
        
        # 創建漸變效果
        gradient = QLinearGradient(bar_rect.left(), bar_rect.top(), bar_rect.right(), bar_rect.top())
        gradient.setColorAt(0, bar_color.lighter(120))
        gradient.setColorAt(1, bar_color)
        
        painter.fillRect(bar_rect, gradient)
        
        # 繪製邊框
        painter.setPen(QPen(bar_color.darker(120), 1))
        painter.drawRect(bar_rect)
        
        # 繪製數值文字
        text = f"{decel_abs:.1f}"
        text_rect = QRect(
            rect.left() + margin + bar_width + 5,
            rect.top(),
            55,
            rect.height()
        )
        painter.setPen(Qt.black if not (option.state & QStyle.State_Selected) else Qt.white)
        painter.setFont(QFont("Arial", 9))
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
        
        painter.restore()
    
    def sizeHint(self, option, index):
        """返回建議大小"""
        size = super().sizeHint(option, index)
        size.setWidth(max(size.width(), 200))  # 最小寬度
        return size


class AllDriversBrakeAllLapsTableWidget(QWidget):
    """
    全車手煞車全圈數分析表格元件
    
    顯示 10 個完整統計欄位 + 中位數減速度視覺化棒狀圖
    支援動態欄位可見性和 Qt 內建排序
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據存儲
        self.drivers_data: List[Dict[str, Any]] = []
        
        # 欄位定義（選項 C: 完整統計欄位）
        self.all_columns = [
            ('driver', tr('column_driver', 'Driver')),
            ('team', tr('column_team', 'Team')),
            ('median', tr('column_median_decel', 'Median (m/s²)')),
            ('mean', tr('column_mean_decel', 'Mean (m/s²)')),
            ('std_dev', tr('column_std_dev', 'Std Dev (m/s²)')),
            ('min', tr('column_min_decel', 'Peak (m/s²)')),  # Min = 最強煞車（絕對值最大）
            ('max', tr('column_max_decel', 'Weakest (m/s²)')),  # Max = 最弱煞車（絕對值最小）
            ('cv', tr('column_cv', 'CV (%)')),
            ('valid_laps', tr('column_valid_laps', 'Valid Laps')),
            ('outlier_count', tr('column_outlier_count', 'Outliers')),
            ('performance_bar', tr('column_performance_bar', 'Decel Visualization')),
        ]
        
        # 永遠可見的欄位
        self.always_visible = {'driver', 'team', 'median', 'performance_bar'}
        
        # 欄位索引映射
        self.column_indices: Dict[str, int] = {}
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI 組件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 創建表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSortingEnabled(True)  # 啟用排序
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止編輯
        
        # 設置表頭
        self._setup_table_columns()
        
        layout.addWidget(self.table)
    
    def _setup_table_columns(self):
        """設置表格欄位"""
        # 讀取欄位可見性設置
        visible_columns = self._get_visible_columns()
        
        # 設置表格列數
        self.table.setColumnCount(len(visible_columns))
        
        # 設置表頭
        headers = []
        self.column_indices.clear()
        
        for idx, (col_name, col_display) in enumerate(visible_columns):
            headers.append(col_display)
            self.column_indices[col_name] = idx
        
        self.table.setHorizontalHeaderLabels(headers)
        
        # 設置表頭樣式
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # 設置預設列寬
        default_widths = {
            'driver': 80,
            'team': 150,
            'median': 100,
            'mean': 100,
            'std_dev': 100,
            'min': 90,
            'max': 90,
            'cv': 80,
            'valid_laps': 90,
            'outlier_count': 80,
            'performance_bar': 200,
        }
        
        for col_name, width in default_widths.items():
            if col_name in self.column_indices:
                self.table.setColumnWidth(self.column_indices[col_name], width)
        
        # 設置棒狀圖委託
        if 'performance_bar' in self.column_indices:
            self.bar_delegate = MedianDecelBarDelegate(self)
            self.table.setItemDelegateForColumn(
                self.column_indices['performance_bar'],
                self.bar_delegate
            )
    
    def _get_visible_columns(self) -> List[tuple]:
        """獲取可見欄位列表（F122 顯示所有欄位）"""
        # F122 使用完整統計欄位，不需要動態可見性設定
        # 直接返回所有欄位
        return list(self.all_columns)
    
    def _get_column_index(self, column_name: str) -> Optional[int]:
        """獲取欄位索引"""
        return self.column_indices.get(column_name)
    
    def _set_item_at_column(self, row: int, column_name: str, item: QTableWidgetItem):
        """在指定欄位設置項目"""
        col_index = self._get_column_index(column_name)
        if col_index is not None:
            self.table.setItem(row, col_index, item)
    
    def update_data(self, data: Dict[str, Any]):
        """
        更新表格數據
        
        Args:
            data: F122 分析結果
                {
                    "drivers": [...],
                    "main_brake_zone": {...},
                    "metadata": {...}
                }
        """
        try:
            logger.info("[BRAKE_ALL_LAPS_TABLE] Updating data...")
            
            # 提取車手數據
            self.drivers_data = data.get("drivers", [])
            
            if not self.drivers_data:
                logger.warning("[BRAKE_ALL_LAPS_TABLE] No driver data")
                self.table.setRowCount(0)
                return
            
            # 計算減速度範圍（用於棒狀圖）
            self._calculate_decel_range()
            
            # 填充表格
            self._populate_table()
            
            logger.info("[BRAKE_ALL_LAPS_TABLE] Data updated, drivers: %d", len(self.drivers_data))
            
        except Exception as e:
            logger.exception("[BRAKE_ALL_LAPS_TABLE] Failed to update data", exc_info=e)
    
    def _calculate_decel_range(self):
        """計算減速度範圍（用於棒狀圖比例）"""
        medians = []
        for driver_data in self.drivers_data:
            stats = driver_data.get("brake_decel_stats", {})
            median = stats.get("median")
            if median is not None:
                medians.append(abs(float(median)))
        
        if medians:
            min_decel = min(medians) * 0.9  # 留一點邊距
            max_decel = max(medians) * 1.1
            
            if hasattr(self, 'bar_delegate'):
                self.bar_delegate.update_range(min_decel, max_decel)
            
            logger.debug("[BRAKE_ALL_LAPS_TABLE] Decel range: %.2f - %.2f", min_decel, max_decel)
    
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
    
    def _populate_table(self):
        """填充表格數據"""
        # 暫時禁用排序（避免填充時排序問題）
        self.table.setSortingEnabled(False)
        
        # 設置行數
        self.table.setRowCount(len(self.drivers_data))
        
        # 填充每一行
        for row, driver_data in enumerate(self.drivers_data):
            self._populate_row(row, driver_data)
        
        # 重新啟用排序
        self.table.setSortingEnabled(True)
        
        # 預設按中位數減速度排序（降序，絕對值大的在前）
        if 'median' in self.column_indices:
            self.table.sortByColumn(
                self.column_indices['median'],
                Qt.DescendingOrder
            )
    
    def _populate_row(self, row: int, driver_data: Dict):
        """填充單行數據"""
        driver = driver_data.get("driver", "")
        team = self._get_team_name(driver)  # 使用 DEFAULT_DRIVER_MAP 獲取車隊名稱
        
        # 提取統計數據
        stats = driver_data.get("brake_decel_stats", {})
        median = stats.get("median", 0)
        mean = stats.get("mean", 0)
        std_dev = stats.get("std_dev", 0)
        cv = stats.get("cv", 0)
        min_decel = stats.get("min", 0)
        max_decel = stats.get("max", 0)
        
        valid_laps = driver_data.get("valid_laps_count", 0)
        outlier_count = driver_data.get("outlier_count", 0)
        
        # 1. 車手（車隊背景色）
        driver_item = QTableWidgetItem(driver)
        driver_item.setTextAlignment(Qt.AlignCenter)
        driver_item.setFont(QFont("Arial", 10))
        
        # 設置車隊背景色
        driver_color = color_palette_provider.get_driver_color(driver, fallback=True)
        driver_item.setBackground(driver_color)
        
        # 根據背景色亮度決定文字顏色
        luminance = (0.299 * driver_color.red() + 0.587 * driver_color.green() + 0.114 * driver_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        driver_item.setForeground(QBrush(text_color))
        driver_item.setToolTip(tr("driver_tooltip", "{driver} - {team}").format(driver=driver, team=team))
        
        self._set_item_at_column(row, 'driver', driver_item)
        
        # 2. 車隊
        team_item = QTableWidgetItem(team)
        team_item.setTextAlignment(Qt.AlignCenter)
        team_item.setFont(QFont("Arial", 9))
        team_item.setBackground(driver_color)
        team_item.setForeground(QBrush(text_color))
        self._set_item_at_column(row, 'team', team_item)
        
        # 3. 中位數減速度（使用絕對值顯示，帶顏色編碼）
        median_abs = abs(float(median)) if median else 0
        median_item = QTableWidgetItem(f"{median_abs:.2f}")
        median_item.setTextAlignment(Qt.AlignCenter)
        median_item.setFont(QFont("Arial", 9, QFont.Bold))
        median_item.setData(Qt.DisplayRole, median_abs)  # 用於排序
        median_item.setData(Qt.UserRole, median_abs)
        
        # 顏色編碼
        median_color = self._get_decel_color(median_abs)
        median_item.setForeground(QBrush(median_color))
        
        self._set_item_at_column(row, 'median', median_item)
        
        # 4. 平均值
        mean_abs = abs(float(mean)) if mean else 0
        mean_item = QTableWidgetItem(f"{mean_abs:.2f}")
        mean_item.setTextAlignment(Qt.AlignCenter)
        mean_item.setData(Qt.DisplayRole, mean_abs)
        mean_item.setData(Qt.UserRole, mean_abs)
        self._set_item_at_column(row, 'mean', mean_item)
        
        # 5. 標準差（穩定性指標）
        std_val = float(std_dev) if std_dev else 0
        std_item = QTableWidgetItem(f"{std_val:.2f}")
        std_item.setTextAlignment(Qt.AlignCenter)
        std_item.setData(Qt.DisplayRole, std_val)
        std_item.setData(Qt.UserRole, std_val)
        
        # 標準差顏色編碼（越小越穩定）
        if std_val < 3:
            std_item.setForeground(QBrush(QColor(0, 150, 0)))  # 綠色
        elif std_val < 6:
            std_item.setForeground(QBrush(QColor(255, 150, 0)))  # 橙色
        else:
            std_item.setForeground(QBrush(QColor(200, 0, 0)))  # 紅色
        
        self._set_item_at_column(row, 'std_dev', std_item)
        
        # 6. 最小值
        min_abs = abs(float(min_decel)) if min_decel else 0
        min_item = QTableWidgetItem(f"{min_abs:.2f}")
        min_item.setTextAlignment(Qt.AlignCenter)
        min_item.setData(Qt.DisplayRole, min_abs)
        min_item.setData(Qt.UserRole, min_abs)
        self._set_item_at_column(row, 'min', min_item)
        
        # 7. 最大值
        max_abs = abs(float(max_decel)) if max_decel else 0
        max_item = QTableWidgetItem(f"{max_abs:.2f}")
        max_item.setTextAlignment(Qt.AlignCenter)
        max_item.setData(Qt.DisplayRole, max_abs)
        max_item.setData(Qt.UserRole, max_abs)
        self._set_item_at_column(row, 'max', max_item)
        
        # 8. 變異係數
        cv_val = float(cv) if cv else 0
        cv_item = QTableWidgetItem(f"{cv_val:.1f}")
        cv_item.setTextAlignment(Qt.AlignCenter)
        cv_item.setData(Qt.DisplayRole, cv_val)
        cv_item.setData(Qt.UserRole, cv_val)
        
        # CV 顏色編碼（越小越穩定）
        if cv_val < 10:
            cv_item.setForeground(QBrush(QColor(0, 150, 0)))
        elif cv_val < 20:
            cv_item.setForeground(QBrush(QColor(255, 150, 0)))
        else:
            cv_item.setForeground(QBrush(QColor(200, 0, 0)))
        
        self._set_item_at_column(row, 'cv', cv_item)
        
        # 9. 有效圈數
        laps_item = QTableWidgetItem(str(valid_laps))
        laps_item.setTextAlignment(Qt.AlignCenter)
        laps_item.setData(Qt.DisplayRole, valid_laps)
        laps_item.setData(Qt.UserRole, valid_laps)
        self._set_item_at_column(row, 'valid_laps', laps_item)
        
        # 10. 異常值數量
        outlier_item = QTableWidgetItem(str(outlier_count))
        outlier_item.setTextAlignment(Qt.AlignCenter)
        outlier_item.setData(Qt.DisplayRole, outlier_count)
        outlier_item.setData(Qt.UserRole, outlier_count)
        
        # 異常值顏色編碼（越少越好）
        if outlier_count <= 2:
            outlier_item.setForeground(QBrush(QColor(0, 150, 0)))
        elif outlier_count <= 5:
            outlier_item.setForeground(QBrush(QColor(255, 150, 0)))
        else:
            outlier_item.setForeground(QBrush(QColor(200, 0, 0)))
        
        self._set_item_at_column(row, 'outlier_count', outlier_item)
        
        # 11. 視覺化棒狀圖（使用中位數減速度）
        bar_item = QTableWidgetItem()
        bar_item.setData(Qt.DisplayRole, median_abs)  # 用於排序
        bar_item.setData(Qt.UserRole, median_abs)     # 用於繪圖
        self._set_item_at_column(row, 'performance_bar', bar_item)
        
        # 儲存完整數據到車手欄位（用於點擊詳情）
        driver_item.setData(Qt.UserRole + 100, {
            "driver": driver,
            "team": team,
            "stats": stats,
            "valid_laps_count": valid_laps,
            "outlier_count": outlier_count,
        })
    
    def _get_decel_color(self, decel_abs: float) -> QColor:
        """
        根據減速度絕對值返回顏色
        
        綠色: > 40 m/s² (強煞車)
        橙色: 30-40 m/s² (中等煞車)
        紅色: < 30 m/s² (弱煞車)
        """
        if decel_abs > 40:
            return QColor(0, 150, 0)  # 綠色
        elif decel_abs > 30:
            return QColor(255, 150, 0)  # 橙色
        else:
            return QColor(200, 0, 0)  # 紅色
