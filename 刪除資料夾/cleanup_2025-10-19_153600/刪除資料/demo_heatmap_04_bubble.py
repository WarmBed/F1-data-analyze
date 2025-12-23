#!/usr/bin/env python3
"""
Demo 4: Bubble Heatmap (氣泡熱力圖)
===================================

視覺風格：散點圖風格 - 圓圈大小和顏色代表時間
特點：
- ✅ 圓圈大小 = 時間（越大越慢）
- ✅ 圓圈顏色 = 時間（綠→黃→紅）
- ✅ 視覺吸引力高
- ✅ 適合展示差異
- ✅ 懸停放大

作者: F1T Team
日期: 2025-10-11
"""

import sys
import json
import math
from pathlib import Path

from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QRadialGradient
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QToolTip, QLabel, QPushButton
)


class BubbleHeatmapWidget(QWidget):
    """氣泡熱力圖 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.drivers = []
        self.sector_data = {}
        self.sector_stats = {}
        
        self.margin_left = 120
        self.margin_right = 120
        self.margin_top = 100
        self.margin_bottom = 100
        
        self.cell_width = 100
        self.cell_height = 100
        
        self.min_bubble_size = 15
        self.max_bubble_size = 45
        
        self.hover_cell = None
        self.setMouseTracking(True)
        self.setMinimumSize(1000, 600)
    
    def load_json_data(self, json_path: str):
        """載入數據"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ranking = data.get('analysis_result', {}).get('ranking', [])[:12]
        
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
                    'max': max(times)
                }
        
        self.update()
    
    def paintEvent(self, event):
        """繪圖"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 深色背景
            painter.fillRect(self.rect(), QColor(30, 30, 40))
            
            if not self.drivers:
                self._draw_no_data(painter)
                return
            
            self._draw_title(painter)
            self._draw_grid(painter)
            self._draw_bubbles(painter)
            self._draw_axes(painter)
        
        finally:
            painter.end()
    
    def _draw_no_data(self, painter):
        """無數據提示"""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        font = QFont('Arial', 14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "No data loaded")
    
    def _draw_title(self, painter):
        """標題"""
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont('Arial', 18, QFont.Bold)
        painter.setFont(font)
        
        painter.drawText(0, 30, self.width(), 40, int(Qt.AlignCenter),
                        "Sector Performance - Bubble View")
        
        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(0, 60, self.width(), 25, int(Qt.AlignCenter),
                        "Bubble Size & Color = Sector Time")
    
    def _draw_grid(self, painter):
        """繪製網格"""
        painter.setPen(QPen(QColor(60, 60, 70), 1))
        
        # 垂直線
        for col_idx in range(len(self.drivers) + 1):
            x = self.margin_left + col_idx * self.cell_width
            painter.drawLine(x, self.margin_top,
                           x, self.margin_top + 3 * self.cell_height)
        
        # 水平線
        for row_idx in range(4):
            y = self.margin_top + row_idx * self.cell_height
            painter.drawLine(self.margin_left, y,
                           self.margin_left + len(self.drivers) * self.cell_width, y)
    
    def _draw_bubbles(self, painter):
        """繪製氣泡"""
        sectors = ['S1', 'S2', 'S3']
        
        for row_idx, sector in enumerate(sectors):
            stats = self.sector_stats.get(sector, {})
            vmin = stats.get('min', 0)
            vmax = stats.get('max', 1)
            
            for col_idx, driver in enumerate(self.drivers):
                value = self.sector_data[driver][sector]
                
                if math.isnan(value):
                    continue
                
                # 計算氣泡中心
                cx = self.margin_left + (col_idx + 0.5) * self.cell_width
                cy = self.margin_top + (row_idx + 0.5) * self.cell_height
                center = QPointF(cx, cy)
                
                # 計算氣泡大小（時間越大，氣泡越大）
                if vmax > vmin:
                    ratio = (value - vmin) / (vmax - vmin)
                else:
                    ratio = 0.5
                
                radius = self.min_bubble_size + ratio * (self.max_bubble_size - self.min_bubble_size)
                
                # 懸停放大
                if self.hover_cell == (driver, sector):
                    radius *= 1.2
                
                # 計算顏色
                color = self._value_to_color(ratio)
                
                # 繪製漸層氣泡
                gradient = QRadialGradient(center, radius)
                gradient.setColorAt(0.0, color.lighter(130))
                gradient.setColorAt(0.7, color)
                gradient.setColorAt(1.0, color.darker(120))
                
                painter.setBrush(QBrush(gradient))
                painter.setPen(QPen(color.darker(150), 2))
                painter.drawEllipse(center, radius, radius)
                
                # 繪製數值
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                font = QFont('Arial', 9, QFont.Bold)
                painter.setFont(font)
                
                text_rect = painter.boundingRect(int(cx - radius), int(cy - 10),
                                                 int(radius * 2), 20,
                                                 int(Qt.AlignCenter), f"{value:.3f}")
                painter.drawText(text_rect, int(Qt.AlignCenter), f"{value:.3f}")
    
    def _draw_axes(self, painter):
        """座標軸"""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        font = QFont('Arial', 11, QFont.Bold)
        painter.setFont(font)
        
        # Y 軸
        sectors = ['S1', 'S2', 'S3']
        for row_idx, sector in enumerate(sectors):
            y = self.margin_top + (row_idx + 0.5) * self.cell_height
            painter.drawText(20, int(y - 10), self.margin_left - 30, 20,
                           int(Qt.AlignRight | Qt.AlignVCenter), sector)
        
        # X 軸
        for col_idx, driver in enumerate(self.drivers):
            x = self.margin_left + (col_idx + 0.5) * self.cell_width
            y = self.margin_top + 3 * self.cell_height + 20
            painter.drawText(int(x - 40), int(y), 80, 30,
                           int(Qt.AlignCenter), driver)
    
    def _value_to_color(self, ratio):
        """比例轉顏色"""
        if ratio < 0.5:
            t = ratio * 2
            r = int(102 * (1 - t) + 255 * t)
            g = int(204 * (1 - t) + 235 * t)
            b = int(102 * (1 - t) + 59 * t)
        else:
            t = (ratio - 0.5) * 2
            r = int(255 * (1 - t) + 231 * t)
            g = int(235 * (1 - t) + 76 * t)
            b = int(59 * (1 - t) + 60 * t)
        
        return QColor(r, g, b)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動"""
        if not self.drivers:
            return
        
        pos = event.pos()
        sectors = ['S1', 'S2', 'S3']
        
        for row_idx, sector in enumerate(sectors):
            for col_idx, driver in enumerate(self.drivers):
                cx = self.margin_left + (col_idx + 0.5) * self.cell_width
                cy = self.margin_top + (row_idx + 0.5) * self.cell_height
                
                dist = math.sqrt((pos.x() - cx)**2 + (pos.y() - cy)**2)
                
                if dist <= self.max_bubble_size:
                    self.hover_cell = (driver, sector)
                    
                    value = self.sector_data[driver][sector]
                    if not math.isnan(value):
                        tooltip = f"{driver} - {sector}\n{value:.3f}s"
                        QToolTip.showText(event.globalPos(), tooltip, self)
                    
                    self.update()
                    return
        
        if self.hover_cell:
            self.hover_cell = None
            QToolTip.hideText()
            self.update()
    
    def leaveEvent(self, event):
        """滑鼠離開"""
        self.hover_cell = None
        QToolTip.hideText()
        self.update()


class Demo4Window(QMainWindow):
    """Demo 4 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 4: Bubble Heatmap")
        self.resize(1500, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        title = QLabel("Demo 4: 氣泡熱力圖")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        btn_load = QPushButton("載入 JSON 數據")
        btn_load.clicked.connect(self.load_data)
        layout.addWidget(btn_load)
        
        self.heatmap = BubbleHeatmapWidget()
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
    window = Demo4Window()
    window.show()
    sys.exit(app.exec_())
