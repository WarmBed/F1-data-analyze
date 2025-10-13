#!/usr/bin/env python3
"""
Demo 3: Bar Chart Heatmap (條狀圖熱力圖)
========================================

視覺風格：橫向條狀圖 - 每個分段用條狀圖表示
特點：
- ✅ 橫向條狀圖（長度 = 時間）
- ✅ 數值標註在條內
- ✅ 最快的條最短（視覺直觀）
- ✅ 色彩編碼
- ✅ 分段統計顯示

作者: F1T Team
日期: 2025-10-11
"""

import sys
import json
import math
from pathlib import Path

from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QLinearGradient
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QToolTip, QLabel, QPushButton, QHBoxLayout
)


class BarChartHeatmapWidget(QWidget):
    """條狀圖熱力圖 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.drivers = []
        self.sector_data = {}
        self.sector_stats = {}
        
        self.margin_left = 120
        self.margin_right = 100
        self.margin_top = 100
        self.margin_bottom = 80
        
        self.row_height = 35
        self.bar_height = 28
        self.section_gap = 15
        
        self.hover_cell = None
        self.setMouseTracking(True)
        self.setMinimumSize(1000, 600)
    
    def load_json_data(self, json_path: str):
        """載入數據"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ranking = data.get('analysis_result', {}).get('ranking', [])[:10]  # 只取前 10 位
        
        self.drivers = []
        self.sector_data = {}
        
        for entry in ranking:
            driver = entry['driver']
            self.drivers.append(driver)
            
            sector_breakdown = entry.get('sector_breakdown', {})
            self.sector_data[driver] = {
                'S1': sector_breakdown.get('sector_1', {}).get('time', float('nan')),
                'S2': sector_breakdown.get('sector_2', {}).get('time', float('nan')),
                'S3': sector_breakdown.get('sector_3', {}).get('time', float('nan'))
            }
        
        # 計算統計
        sectors = ['S1', 'S2', 'S3']
        self.sector_stats = {}
        
        for sector in sectors:
            times = [self.sector_data[d][sector] for d in self.drivers 
                     if not math.isnan(self.sector_data[d][sector])]
            
            if times:
                self.sector_stats[sector] = {
                    'min': min(times),
                    'max': max(times),
                    'avg': sum(times) / len(times)
                }
        
        self.update()
    
    def paintEvent(self, event):
        """繪圖"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(252, 252, 252))
            
            if not self.drivers:
                self._draw_no_data(painter)
                return
            
            self._draw_title(painter)
            self._draw_bars(painter)
            self._draw_stats(painter)
        
        finally:
            painter.end()
    
    def _draw_no_data(self, painter):
        """無數據提示"""
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        font = QFont('Arial', 14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "No data loaded")
    
    def _draw_title(self, painter):
        """標題"""
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont('Arial', 18, QFont.Bold)
        painter.setFont(font)
        
        painter.drawText(QRectF(0, 15, self.width(), 40),
                        int(Qt.AlignCenter), "Sector Performance - Horizontal Bar Chart")
        
        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QRectF(0, 50, self.width(), 25),
                        int(Qt.AlignCenter), f"Top {len(self.drivers)} Drivers")
    
    def _draw_bars(self, painter):
        """繪製條狀圖"""
        sectors = ['S1', 'S2', 'S3']
        sector_colors = {
            'S1': QColor(52, 152, 219),   # 藍色
            'S2': QColor(155, 89, 182),   # 紫色
            'S3': QColor(230, 126, 34)    # 橙色
        }
        
        chart_width = self.width() - self.margin_left - self.margin_right
        
        y_offset = self.margin_top
        
        for sector_idx, sector in enumerate(sectors):
            # 分段標題
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            font = QFont('Arial', 13, QFont.Bold)
            painter.setFont(font)
            
            title_rect = QRectF(20, y_offset, self.margin_left - 30, 30)
            painter.drawText(title_rect, int(Qt.AlignRight | Qt.AlignVCenter), f"Sector {sector_idx + 1}")
            
            y_offset += 35
            
            # 繪製每位車手的條狀圖
            stats = self.sector_stats.get(sector, {})
            vmin = stats.get('min', 0)
            vmax = stats.get('max', 1)
            
            for driver_idx, driver in enumerate(self.drivers):
                value = self.sector_data[driver][sector]
                
                if not math.isnan(value):
                    # 計算條的寬度（反向：時間越短條越短）
                    if vmax > vmin:
                        ratio = (value - vmin) / (vmax - vmin)
                        bar_width = chart_width * (0.5 + 0.5 * (1 - ratio))  # 50%-100%
                    else:
                        bar_width = chart_width * 0.75
                    
                    # 繪製條
                    bar_x = self.margin_left
                    bar_y = y_offset + driver_idx * self.row_height
                    bar_rect = QRectF(bar_x, bar_y, bar_width, self.bar_height)
                    
                    # 漸層
                    gradient = QLinearGradient(bar_x, bar_y, bar_x + bar_width, bar_y)
                    color = sector_colors[sector]
                    gradient.setColorAt(0.0, color.lighter(120))
                    gradient.setColorAt(1.0, color)
                    
                    painter.setBrush(QBrush(gradient))
                    painter.setPen(QPen(color.darker(120), 1))
                    painter.drawRoundedRect(bar_rect, 4, 4)
                    
                    # 車手代碼（左側）
                    painter.setPen(QPen(QColor(60, 60, 60), 1))
                    font.setPointSize(10)
                    font.setBold(True)
                    painter.setFont(font)
                    
                    driver_rect = QRectF(20, bar_y, self.margin_left - 30, self.bar_height)
                    painter.drawText(driver_rect, int(Qt.AlignRight | Qt.AlignVCenter), driver)
                    
                    # 時間數值（條內）
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    font.setBold(False)
                    painter.setFont(font)
                    
                    time_rect = QRectF(bar_x + 10, bar_y, bar_width - 20, self.bar_height)
                    painter.drawText(time_rect, int(Qt.AlignLeft | Qt.AlignVCenter), f"{value:.3f}s")
            
            y_offset += len(self.drivers) * self.row_height + self.section_gap
    
    def _draw_stats(self, painter):
        """繪製統計資訊"""
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        font = QFont('Arial', 9)
        painter.setFont(font)
        
        stats_x = self.width() - self.margin_right + 20
        stats_y = self.margin_top
        
        painter.drawText(stats_x, stats_y, "Statistics:")
        stats_y += 25
        
        for sector, stats in self.sector_stats.items():
            painter.drawText(stats_x, stats_y, f"{sector}:")
            painter.drawText(stats_x + 10, stats_y + 15, f"Min: {stats['min']:.3f}s")
            painter.drawText(stats_x + 10, stats_y + 30, f"Max: {stats['max']:.3f}s")
            painter.drawText(stats_x + 10, stats_y + 45, f"Avg: {stats['avg']:.3f}s")
            stats_y += 70
    
    def mouseMoveEvent(self, event):
        """滑鼠移動"""
        # 簡化版：只顯示 Tooltip
        pass
    
    def leaveEvent(self, event):
        """滑鼠離開"""
        QToolTip.hideText()


class Demo3Window(QMainWindow):
    """Demo 3 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 3: Bar Chart Heatmap")
        self.resize(1400, 900)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        title = QLabel("Demo 3: 條狀圖熱力圖")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        btn_load = QPushButton("載入 JSON 數據")
        btn_load.clicked.connect(self.load_data)
        layout.addWidget(btn_load)
        
        self.heatmap = BarChartHeatmapWidget()
        layout.addWidget(self.heatmap, stretch=1)
        
        self.statusBar().showMessage("就緒")
    
    def load_data(self):
        """載入數據"""
        json_path = "json/ideal_lap_ranking_2025_Japan_R.json"
        
        if not Path(json_path).exists():
            self.statusBar().showMessage(f"❌ 找不到檔案: {json_path}")
            return
        
        try:
            self.heatmap.load_json_data(json_path)
            self.statusBar().showMessage(f"✅ 已載入: {json_path}")
        except Exception as e:
            self.statusBar().showMessage(f"❌ 載入失敗: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Demo3Window()
    window.show()
    sys.exit(app.exec_())
