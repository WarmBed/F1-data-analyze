#!/usr/bin/env python3
"""
Demo 1: Classic Grid Heatmap (蝬?澆??勗???
==============================================

閬死憸冽嚗蝯梁?? - 蝬脫撣? + ?脣蔗憛怠?
?寥?嚗?
- ??皜?雯?潛?
- ???詨潛蔭銝剝＊蝷?
- ???脣蔗瞍詨惜嚗?????嚗?
- ??擃漁璅?嚗撅?敹徉??犖?雿喫?蛛?
- ???詨? Tooltip

雿? F1T Team
?交?: 2025-10-11
"""

import sys
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, QPoint, QRect, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QLinearGradient, QPolygonF
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QToolTip, QLabel, QPushButton, QHBoxLayout
)


class ClassicGridHeatmapWidget(QWidget):
    """蝬蝬脫?勗???Widget"""
    
    cell_clicked = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ?豢?摮
        self.drivers = []
        self.sector_data = {}  # {driver: {S1: time, S2: time, S3: time}}
        self.sector_stats = {}  # {S1: {fastest: driver, ...}}
        self.driver_best = {}  # {driver: best_sector}
        
        # 雿?? - 銝??拇?憿舐內
        self.margin_left = 80
        self.margin_right = 180
        self.margin_top = 60
        self.margin_bottom = 50
        self.row_gap = 40  # 銝??拇?銋???頝?
        
        self.cell_width = 65
        self.cell_height = 32
        self.drivers_per_row = 10  # 瘥?憿舐內 10 雿???
        
        # ?脣蔗?蔭
        self.color_fast = QColor(46, 204, 113)    # 蝬嚗翰嚗?
        self.color_medium = QColor(241, 196, 15)  # 暺嚗葉嚗?
        self.color_slow = QColor(231, 76, 60)     # 蝝嚗嚗?
        
        # ??鈭????
        self.hover_cell = None
        self.setMouseTracking(False)  # 蝳皛?餈質馱
        self.setMinimumSize(800, 500)
        
        # 憿舐內?賊?嚗歇蝳璅?嚗?
        self.show_global_fastest = False
        self.show_personal_best = False
    
    def load_json_data(self, json_path: str):
        """敺?JSON 頛?豢?"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # ?????豢?
        ranking = data.get('analysis_result', {}).get('ranking', [])
        
        self.drivers = []
        self.sector_data = {}
        
        for entry in ranking:
            driver = entry['driver']
            self.drivers.append(driver)
            
            sector_breakdown = entry.get('sector_breakdown', {})
            s1 = sector_breakdown.get('sector_1', {}).get('time', float('nan'))
            s2 = sector_breakdown.get('sector_2', {}).get('time', float('nan'))
            s3 = sector_breakdown.get('sector_3', {}).get('time', float('nan'))
            
            # 閮?蝮賣???
            if not (math.isnan(s1) or math.isnan(s2) or math.isnan(s3)):
                total = s1 + s2 + s3
            else:
                total = float('nan')
            
            self.sector_data[driver] = {
                'S1': s1,
                'S2': s2,
                'S3': s3,
                'Total': total,
                'team': entry.get('team', 'Unknown')
            }
        
        # 閮?瘥?畾萇?蝯梯?嚗??怎蜇??嚗?
        sectors = ['S1', 'S2', 'S3', 'Total']
        self.sector_stats = {}
        
        for sector in sectors:
            times = [(d, self.sector_data[d][sector]) for d in self.drivers 
                     if not math.isnan(self.sector_data[d][sector])]
            
            if times:
                times.sort(key=lambda x: x[1])
                self.sector_stats[sector] = {
                    'fastest_driver': times[0][0],
                    'fastest_time': times[0][1],
                    'slowest_time': times[-1][1]
                }
        
        # 閮?瘥?頠???雿喳?畾?
        self.driver_best = {}
        for driver in self.drivers:
            s1 = self.sector_data[driver]['S1']
            s2 = self.sector_data[driver]['S2']
            s3 = self.sector_data[driver]['S3']
            
            valid_sectors = []
            if not math.isnan(s1):
                valid_sectors.append(('S1', s1))
            if not math.isnan(s2):
                valid_sectors.append(('S2', s2))
            if not math.isnan(s3):
                valid_sectors.append(('S3', s3))
            
            if valid_sectors:
                valid_sectors.sort(key=lambda x: x[1])
                self.driver_best[driver] = valid_sectors[0][0]
        
        self.update()
    
    def paintEvent(self, event):
        """?詨?蝜芸??寞?"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(245, 245, 245))
            
            if not self.drivers:
                self._draw_no_data(painter)
                return
            
            # 蝜芾ˊ璅?
            self._draw_title(painter)
            
            # 蝜芾ˊ?勗???
            self._draw_heatmap(painter)
            
            # 蝜芾ˊ摨扳?頠?
            self._draw_axes(painter)
            
            # 蝜芾ˊ?脣蔗??
            self._draw_legend(painter)
        
        finally:
            painter.end()
    
    def _draw_no_data(self, painter):
        """蝜芾ˊ?⊥??蝷?""
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        font = QFont('Arial', 14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter,
                        "No data loaded\nClick 'Load Data' to begin")
    
    def _draw_title(self, painter):
        """蝜芾ˊ璅? - 撌脣?瘨＊蝷?""
        # 銝?憿舐內隞颱?璅?
        pass
    
    def _draw_heatmap(self, painter):
        """蝜芾ˊ?勗??摮 - 銝??拇?憿舐內"""
        sectors = ['S1', 'S2', 'S3', 'Total']
        
        for driver_idx, driver in enumerate(self.drivers):
            # ?斗?舐洵銝???舐洵鈭?
            if driver_idx < self.drivers_per_row:
                # 蝚砌?????10 雿?
                col_idx = driver_idx
                base_y = self.margin_top
            else:
                # 蝚砌???敺?10 雿?
                col_idx = driver_idx - self.drivers_per_row
                base_y = self.margin_top + len(sectors) * self.cell_height + self.row_gap
            
            # 蝜芾ˊ閰脰??????畾?
            for row_idx, sector in enumerate(sectors):
                value = self.sector_data[driver][sector]
                
                # 閮??脣??潔?蝵?
                x = self.margin_left + col_idx * self.cell_width
                y = base_y + row_idx * self.cell_height
                rect = QRectF(x, y, self.cell_width, self.cell_height)
                
                # 蝜芾ˊ?脣???
                self._draw_cell(painter, rect, driver, sector, value)
    
    def _draw_cell(self, painter, rect, driver, sector, value):
        """蝜芾ˊ?桀摮"""
        # ???憿
        if math.isnan(value):
            bg_color = QColor(230, 230, 230)
            text = "N/A"
        else:
            bg_color = self._value_to_color(sector, value)
            text = f"{value:.3f}"
        
        # 憛怠??
        painter.fillRect(rect, bg_color)
        
        # 蝜芾ˊ蝬脫蝺?
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRect(rect)
        
        # 蝜芾ˊ?詨?
        text_color = self._get_text_color(bg_color)
        painter.setPen(QPen(text_color, 1))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, text)
    
    def _draw_axes(self, painter):
        """蝜芾ˊ摨扳?頠豢?蝐?- 銝??拇?"""
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont()
        font.setPointSize(8)
        font.setBold(False)  # ??蝎?
        painter.setFont(font)
        
        sectors = ['S1', 'S2', 'S3', 'Total']
        
        # Y 頠豢?蝐?- 蝚砌???
        for row_idx, sector in enumerate(sectors):
            y = self.margin_top + row_idx * self.cell_height
            label_rect = QRect(10, y, self.margin_left - 20, self.cell_height)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, sector)
        
        # Y 頠豢?蝐?- 蝚砌???
        base_y_row2 = self.margin_top + len(sectors) * self.cell_height + self.row_gap
        for row_idx, sector in enumerate(sectors):
            y = base_y_row2 + row_idx * self.cell_height
            label_rect = QRect(10, y, self.margin_left - 20, self.cell_height)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, sector)
        
        # X 頠豢?蝐?- 蝚砌?????10 雿???
        for i in range(min(self.drivers_per_row, len(self.drivers))):
            driver = self.drivers[i]
            x = self.margin_left + i * self.cell_width
            y = self.margin_top + len(sectors) * self.cell_height + 5
            label_rect = QRect(x, y, self.cell_width, 25)
            painter.drawText(label_rect, Qt.AlignCenter | Qt.AlignTop, driver)
        
        # X 頠豢?蝐?- 蝚砌???敺?10 雿???
        for i in range(self.drivers_per_row, len(self.drivers)):
            driver = self.drivers[i]
            col_idx = i - self.drivers_per_row
            x = self.margin_left + col_idx * self.cell_width
            y = base_y_row2 + len(sectors) * self.cell_height + 5
            label_rect = QRect(x, y, self.cell_width, 25)
            painter.drawText(label_rect, Qt.AlignCenter | Qt.AlignTop, driver)
    
    def _draw_legend(self, painter):
        """蝜芾ˊ?脣蔗?? - ?箏??函???喳"""
        sectors = ['S1', 'S2', 'S3', 'Total']
        
        # 閮???擃漲嚗???銝??
        legend_height = (len(sectors) * self.cell_height * 2) + self.row_gap
        
        # ?箏?雿蔭嚗???喳嚗??刻?蝒祝摨西???
        heatmap_right = self.margin_left + self.drivers_per_row * self.cell_width
        legend_x = heatmap_right + 30  # ?勗????30px
        legend_y = self.margin_top
        legend_width = 50
        
        # 蝜芾ˊ瞍詨惜
        gradient = QLinearGradient(legend_x, legend_y, legend_x, legend_y + legend_height)
        gradient.setColorAt(0.0, self.color_fast)
        gradient.setColorAt(0.5, self.color_medium)
        gradient.setColorAt(1.0, self.color_slow)
        
        rect = QRectF(legend_x, legend_y, legend_width, legend_height)
        painter.fillRect(rect, QBrush(gradient))
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(rect)
        
        # 璅惜 - ??蝎?
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont()
        font.setPointSize(9)
        font.setBold(False)  # ??蝎?
        painter.setFont(font)
        
        painter.drawText(legend_x + legend_width + 10, legend_y + 10, "Fast")
        painter.drawText(legend_x + legend_width + 10, legend_y + legend_height - 5, "Slow")
        
        # ??璅? - ??蝎?
        painter.drawText(legend_x - 10, legend_y - 15, "Sector Time")
    
    def _draw_star(self, painter, center, size, color):
        """蝜芾ˊ鈭???""
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
        """蝜芾ˊ??"""
        painter.setPen(QPen(color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius, radius)
    
    def _value_to_color(self, sector, value):
        """?詨潸??脣蔗"""
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
        """?寞??瘙箏???憿"""
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        return QColor(255, 255, 255) if luminance < 140 else QColor(0, 0, 0)


class Demo1Window(QMainWindow):
    """Demo 1 銝餉?蝒?""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 1: Classic Grid Heatmap")
        self.resize(1400, 700)
        
        # 銝?Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 璅?
        title = QLabel("Demo 1: 蝬蝬脫?勗???)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # ?批??
        btn_layout = QHBoxLayout()
        
        btn_load = QPushButton("頛 JSON ?豢?")
        btn_load.clicked.connect(self.load_data)
        btn_layout.addWidget(btn_load)
        
        btn_toggle_global = QPushButton("???典??敹?)
        btn_toggle_global.clicked.connect(self.toggle_global)
        btn_layout.addWidget(btn_toggle_global)
        
        btn_toggle_personal = QPushButton("???犖?雿?)
        btn_toggle_personal.clicked.connect(self.toggle_personal)
        btn_layout.addWidget(btn_toggle_personal)
        
