#!/usr/bin/env python3
"""
Ideal Lap Sector Heatmap Widget
===============================

PyQt5 widget that renders a sector heatmap (S1/S2/S3/Total across drivers)
using native QPainter for high-performance rendering.

作者: F1T Team
日期: 2025-10-11
版本: 2.0.0 (QPainter 重構版 + 動態佈局)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd

from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QLinearGradient, QPolygonF
)
from PyQt5.QtWidgets import QWidget

from core.gui_i18n import tr


class IdealLapSectorHeatmapWidget(QWidget):
    """Ideal Lap Sector Heatmap Widget - QPainter 原生渲染"""
    
    cell_clicked = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據存儲
        self.drivers = []
        self.sector_data = {}  # {driver: {S1: time, S2: time, S3: time}}
        self.sector_stats = {}  # {S1: {fastest: driver, ...}}
        self.driver_best = {}  # {driver: best_sector}
        
        # ✅ 動態佈局參數（根據視窗大小計算）
        self.drivers_per_row = 10  # 每排顯示 10 位車手
        
        # 色彩配置
        self.color_fast = QColor(46, 204, 113)    # 綠色（快）
        self.color_medium = QColor(241, 196, 15)  # 黃色（中）
        self.color_slow = QColor(231, 76, 60)     # 紅色（慢）
        
        # 取消互動狀態
        self.hover_cell = None
        self.setMouseTracking(False)  # 禁用滑鼠追蹤
        self.setMinimumSize(800, 400)
        
        # 顯示選項（已禁用標記）
        self.show_global_fastest = False
        self.show_personal_best = False
    
    def _calculate_layout(self):
        """根據視窗大小動態計算佈局參數"""
        widget_width = self.width()
        widget_height = self.height()
        
        # 動態邊距（佔視窗的百分比）
        self.margin_left = max(60, int(widget_width * 0.05))
        self.margin_right = max(150, int(widget_width * 0.12))
        self.margin_top = max(40, int(widget_height * 0.08))
        self.margin_bottom = max(30, int(widget_height * 0.05))
        
        # 計算可用空間
        available_width = widget_width - self.margin_left - self.margin_right
        available_height = widget_height - self.margin_top - self.margin_bottom
        
        # 動態計算儲存格尺寸
        # 每排 10 位車手，每位車手佔一列
        self.cell_width = max(50, int(available_width / self.drivers_per_row))
        
        # ✅ 修正：考慮車手名稱標籤的空間
        # 2 排，每排 4 個分段 (S1/S2/S3/Total)，加上排間距和標籤空間
        rows_count = 2
        sectors_per_driver = 4
        
        # 先粗估 cell_height 來計算間距
        estimated_cell_height = available_height / (rows_count * sectors_per_driver + 2)
        
        # 計算間距（基於粗估值）
        self.row_gap = max(30, int(estimated_cell_height * 1.2))
        self.label_height = max(18, int(estimated_cell_height * 0.7))
        self.label_gap = max(3, int(estimated_cell_height * 0.15))
        
        # 計算實際可用於熱力圖的高度
        space_for_labels = (self.label_height + self.label_gap) * rows_count
        space_for_heatmap = available_height - self.row_gap - space_for_labels
        
        # 根據實際可用高度計算最終 cell_height
        self.cell_height = max(24, int(space_for_heatmap / (rows_count * sectors_per_driver)))
        
        # 根據最終 cell_height 重新調整間距（可選，確保比例一致）
        self.row_gap = max(30, int(self.cell_height * 1.2))
        self.label_height = max(18, int(self.cell_height * 0.7))
        self.label_gap = max(3, int(self.cell_height * 0.15))
        
        # ✅ 動態字體大小
        self.font_size = max(7, min(10, int(self.cell_height * 0.35)))
        self.label_font_size = max(8, min(11, int(self.cell_height * 0.4)))
    
    def paintEvent(self, event):
        """核心繪圖方法"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(245, 245, 245))
            
            if not self.drivers:
                self._draw_no_data(painter)
                return
            
            # ✅ 每次繪製前重新計算佈局
            self._calculate_layout()
            
            # 繪製標題（已移除）
            # self._draw_title(painter)
            
            # 繪製熱力圖
            self._draw_heatmap(painter)
            
            # 繪製座標軸
            self._draw_axes(painter)
            
            # 繪製色彩圖例
            self._draw_legend(painter)
        
        finally:
            painter.end()
    
    def _draw_no_data(self, painter):
        """繪製無數據提示"""
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        font = QFont('Arial', 14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter,
                        tr("no_data_loaded_click_load", "No data loaded\nClick 'Load Data' to begin"))
    
    def _draw_title(self, painter):
        """繪製標題 - 已取消顯示"""
        # 不再顯示任何標題
        pass
    
    def _draw_heatmap(self, painter):
        """繪製熱力圖儲存格 - 上下兩排顯示"""
        sectors = ['S1', 'S2', 'S3', 'Total']
        
        for driver_idx, driver in enumerate(self.drivers):
            # 判斷是第一排還是第二排
            if driver_idx < self.drivers_per_row:
                # 第一排（前 10 位）
                col_idx = driver_idx
                base_y = self.margin_top
            else:
                # 第二排（後 10 位）
                col_idx = driver_idx - self.drivers_per_row
                base_y = self.margin_top + len(sectors) * self.cell_height + self.row_gap
            
            # 繪製該車手的所有分段
            for row_idx, sector in enumerate(sectors):
                value = self.sector_data[driver][sector]
                
                # 計算儲存格位置
                x = self.margin_left + col_idx * self.cell_width
                y = base_y + row_idx * self.cell_height
                rect = QRectF(x, y, self.cell_width, self.cell_height)
                
                # 繪製儲存格
                self._draw_cell(painter, rect, driver, sector, value)
    
    def _draw_cell(self, painter, rect, driver, sector, value):
        """繪製單個儲存格"""
        # 取得背景顏色
        if math.isnan(value):
            bg_color = QColor(230, 230, 230)
            text = "N/A"
        else:
            bg_color = self._value_to_color(sector, value)
            text = f"{value:.3f}"
        
        # 填充背景
        painter.fillRect(rect, bg_color)
        
        # 繪製網格線
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRect(rect)
        
        # 繪製數值
        text_color = self._get_text_color(bg_color)
        painter.setPen(QPen(text_color, 1))
        font = QFont()
        font.setPointSize(self.font_size)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, text)
    
    def _draw_axes(self, painter):
        """繪製座標軸標籤 - 上下兩排"""
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont()
        font.setPointSize(self.label_font_size)
        font.setBold(False)  # 取消粗體
        painter.setFont(font)
        
        sectors = ['S1', 'S2', 'S3', 'Total']
        
        # Y 軸標籤 - 第一排
        for row_idx, sector in enumerate(sectors):
            y = self.margin_top + row_idx * self.cell_height
            label_rect = QRect(10, y, self.margin_left - 20, self.cell_height)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, sector)
        
        # Y 軸標籤 - 第二排
        base_y_row2 = self.margin_top + len(sectors) * self.cell_height + self.row_gap
        for row_idx, sector in enumerate(sectors):
            y = base_y_row2 + row_idx * self.cell_height
            label_rect = QRect(10, y, self.margin_left - 20, self.cell_height)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, sector)
        
        # X 軸標籤 - 第一排（前 10 位車手）
        # ✅ 使用 _calculate_layout() 中已計算的值
        for i in range(min(self.drivers_per_row, len(self.drivers))):
            driver = self.drivers[i]
            x = self.margin_left + i * self.cell_width
            y = self.margin_top + len(sectors) * self.cell_height + self.label_gap
            label_rect = QRect(x, y, self.cell_width, self.label_height)
            painter.drawText(label_rect, Qt.AlignCenter | Qt.AlignTop, driver)
        
        # X 軸標籤 - 第二排（後 10 位車手）
        for i in range(self.drivers_per_row, len(self.drivers)):
            driver = self.drivers[i]
            col_idx = i - self.drivers_per_row
            x = self.margin_left + col_idx * self.cell_width
            y = base_y_row2 + len(sectors) * self.cell_height + self.label_gap
            label_rect = QRect(x, y, self.cell_width, self.label_height)
            painter.drawText(label_rect, Qt.AlignCenter | Qt.AlignTop, driver)
    
    def _draw_legend(self, painter):
        """繪製色彩圖例 - 固定在熱力圖右側"""
        sectors = ['S1', 'S2', 'S3', 'Total']
        
        # 計算圖例高度：覆蓋上下兩排
        legend_height = (len(sectors) * self.cell_height * 2) + self.row_gap
        
        # 固定位置：熱力圖右側（不隨視窗寬度變化）
        heatmap_right = self.margin_left + self.drivers_per_row * self.cell_width
        legend_x = heatmap_right + 30  # 熱力圖右邊 30px
        legend_y = self.margin_top
        legend_width = 50
        
        # 繪製漸層
        gradient = QLinearGradient(legend_x, legend_y, legend_x, legend_y + legend_height)
        gradient.setColorAt(0.0, self.color_fast)
        gradient.setColorAt(0.5, self.color_medium)
        gradient.setColorAt(1.0, self.color_slow)
        
        rect = QRectF(legend_x, legend_y, legend_width, legend_height)
        painter.fillRect(rect, QBrush(gradient))
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(rect)
        
        # 標籤 - 取消粗體
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont()
        font.setPointSize(self.label_font_size)
        font.setBold(False)  # 取消粗體
        painter.setFont(font)
        
        painter.drawText(legend_x + legend_width + 10, legend_y + 10, tr("fast", "Fast"))
        painter.drawText(legend_x + legend_width + 10, legend_y + legend_height - 5, tr("slow", "Slow"))
        
        # 圖例標題 - 取消粗體
        painter.drawText(legend_x - 10, legend_y - 15, tr("sector_time", "Sector Time"))
    
    def _draw_star(self, painter, center, size, color):
        """繪製五角星"""
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            radius = size if i % 2 == 0 else size // 2
            x = center.x() + radius * math.cos(angle)
            y = center.y() - radius * math.sin(angle)
            points.append(QPointF(x, y))
        
        polygon = QPolygonF(points)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(184, 153, 0), 2))
        painter.drawPolygon(polygon)
    
    def _draw_circle(self, painter, center, radius, color):
        """繪製圓圈"""
        painter.setPen(QPen(color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius, radius)
    
    def _value_to_color(self, sector, value):
        """數值轉色彩"""
        if math.isnan(value):
            return QColor(230, 230, 230)
        
        stats = self.sector_stats.get(sector, {})
        vmin = stats.get('fastest_time', value)
        vmax = stats.get('slowest_time', value)
        
        if vmax == vmin:
            ratio = 0.5
        else:
            ratio = (value - vmin) / (vmax - vmin)
        
        ratio = max(0.0, min(1.0, ratio))
        
        if ratio < 0.5:
            t = ratio * 2
            r = int(self.color_fast.red() * (1 - t) + self.color_medium.red() * t)
            g = int(self.color_fast.green() * (1 - t) + self.color_medium.green() * t)
            b = int(self.color_fast.blue() * (1 - t) + self.color_medium.blue() * t)
        else:
            t = (ratio - 0.5) * 2
            r = int(self.color_medium.red() * (1 - t) + self.color_slow.red() * t)
            g = int(self.color_medium.green() * (1 - t) + self.color_slow.green() * t)
            b = int(self.color_medium.blue() * (1 - t) + self.color_slow.blue() * t)
        
        return QColor(r, g, b)
    
    def _get_text_color(self, bg_color):
        """根據背景決定文字顏色"""
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        return QColor(255, 255, 255) if luminance < 140 else QColor(0, 0, 0)
    
    # ------------------------------------------------------------------ #
    # Public API Methods (兼容 MDI 介面)
    # ------------------------------------------------------------------ #
    def set_data(self, payload: Dict[str, Any]) -> None:
        """
        接收來自 data loader 的數據並重繪圖表
        
        Args:
            payload: 包含以下鍵的字典
                - driver_order: List[str] - 車手代碼列表
                - sector_matrix: pd.DataFrame - 分段時間矩陣  
                - sector_summary: Dict[str, Dict] - 分段統計
                - cell_details: Dict - 儲存格詳細資訊
                - driver_best_map: Dict[str, str] - {driver: best_sector}
        """
        self.drivers = payload.get("driver_order", [])
        
        # 從 pandas DataFrame 轉換數據格式
        df = payload.get("sector_matrix")
        if df is None or not isinstance(df, pd.DataFrame):
            self.clear_data()
            return
        
        self.sector_data = {}
        
        # DataFrame 格式: index=['S1', 'S2', 'S3'], columns=[drivers]
        for driver in self.drivers:
            if driver not in df.columns:
                continue
                
            driver_col = df[driver]
            s1 = driver_col.get('S1', float('nan'))
            s2 = driver_col.get('S2', float('nan'))
            s3 = driver_col.get('S3', float('nan'))
            
            # 計算 Total
            total = float('nan')
            if not (math.isnan(s1) or math.isnan(s2) or math.isnan(s3)):
                total = s1 + s2 + s3
            
            self.sector_data[driver] = {
                'S1': s1,
                'S2': s2,
                'S3': s3,
                'Total': total
            }
        
        # 從 sector_summary 提取統計資訊
        sector_summary = payload.get("sector_summary", {})
        self.sector_stats = {}
        
        for sector in ['S1', 'S2', 'S3']:
            summary = sector_summary.get(sector, {})
            if summary:
                self.sector_stats[sector] = {
                    'fastest_driver': summary.get('fastest_driver'),
                    'fastest_time': summary.get('fastest_time', float('nan')),
                    'slowest_time': summary.get('slowest_time', float('nan'))
                }
        
        # 計算 Total 的統計
        total_times = []
        for driver in self.drivers:
            total = self.sector_data.get(driver, {}).get('Total', float('nan'))
            if not math.isnan(total):
                total_times.append((driver, total))
        
        if total_times:
            total_times.sort(key=lambda x: x[1])
            self.sector_stats['Total'] = {
                'fastest_driver': total_times[0][0],
                'fastest_time': total_times[0][1],
                'slowest_time': total_times[-1][1]
            }
        
        # 計算每位車手的最佳分段
        self.driver_best = payload.get("driver_best_map", {})
        
        self.update()
    
    def render_heatmap(self, driver_order: Optional[List[str]] = None) -> None:
        """
        重新排序車手並重繪圖表
        
        Args:
            driver_order: 車手代碼列表（排序後）
        """
        if driver_order:
            # 更新車手順序
            self.drivers = [d for d in driver_order if d in self.sector_data]
        self.update()
    
    def clear_data(self) -> None:
        """清除所有數據"""
        self.drivers = []
        self.sector_data = {}
        self.sector_stats = {}
        self.driver_best = {}
        self.update()
    
    def set_highlight_options(
        self, 
        *,
        show_global_fastest: Optional[bool] = None, 
        show_personal_best: Optional[bool] = None
    ) -> None:
        """設置高亮選項（目前已禁用）"""
        if show_global_fastest is not None:
            self.show_global_fastest = show_global_fastest
        if show_personal_best is not None:
            self.show_personal_best = show_personal_best
        self.update()
    
    def get_current_data(self) -> Dict[str, Any]:
        """返回當前數據用於導出"""
        return {
            "sector_matrix": self.sector_data,
            "sector_summary": self.sector_stats,
            "driver_order": self.drivers,
            "highlight_options": {
                "show_global_fastest": self.show_global_fastest,
                "show_personal_best": self.show_personal_best
            }
        }
    
    def save_plot(self, file_path: str) -> bool:
        """保存當前圖表為圖片"""
        try:
            pixmap = self.grab()
            return pixmap.save(file_path)
        except Exception as exc:
            print(f"[SECTOR_HEATMAP_WIDGET] Failed to save plot: {exc}")
            return False

