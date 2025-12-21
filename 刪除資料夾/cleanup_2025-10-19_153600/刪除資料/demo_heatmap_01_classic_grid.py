#!/usr/bin/env python3
"""
Demo 1: Classic Grid Heatmap (經典格子熱力圖)
==============================================

視覺風格：傳統熱力圖 - 網格布局 + 色彩填充
特點：
- ✅ 清晰的網格線
- ✅ 數值置中顯示
- ✅ 色彩漸層（綠→黃→紅）
- ✅ 高亮標記（全局最快⭐、個人最佳🔵）
- ✅ 懸停 Tooltip

作者: F1T Team
日期: 2025-10-11
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
    """經典網格熱力圖 Widget"""
    
    cell_clicked = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據存儲
        self.drivers = []
        self.sector_data = {}  # {driver: {S1: time, S2: time, S3: time}}
        self.sector_stats = {}  # {S1: {fastest: driver, ...}}
        self.driver_best = {}  # {driver: best_sector}
        
        # 佈局參數 - 上下兩排顯示
        self.margin_left = 80
        self.margin_right = 180
        self.margin_top = 60
        self.margin_bottom = 50
        self.row_gap = 40  # 上下兩排之間的間距
        
        self.cell_width = 65
        self.cell_height = 32
        self.drivers_per_row = 10  # 每排顯示 10 位車手
        
        # 色彩配置
        self.color_fast = QColor(46, 204, 113)    # 綠色（快）
        self.color_medium = QColor(241, 196, 15)  # 黃色（中）
        self.color_slow = QColor(231, 76, 60)     # 紅色（慢）
        
        # 取消互動狀態
        self.hover_cell = None
        self.setMouseTracking(False)  # 禁用滑鼠追蹤
        self.setMinimumSize(800, 500)
        
        # 顯示選項（已禁用標記）
        self.show_global_fastest = False
        self.show_personal_best = False
    
    def load_json_data(self, json_path: str):
        """從 JSON 載入數據"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取排名數據
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
            
            # 計算總時間
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
        
        # 計算每個分段的統計（包含總時間）
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
        
        # 計算每位車手的最佳分段
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
        """核心繪圖方法"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(245, 245, 245))
            
            if not self.drivers:
                self._draw_no_data(painter)
                return
            
            # 繪製標題
            self._draw_title(painter)
            
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
                        "No data loaded\nClick 'Load Data' to begin")
    
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
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, text)
    
    def _draw_axes(self, painter):
        """繪製座標軸標籤 - 上下兩排"""
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont()
        font.setPointSize(8)
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
        for i in range(min(self.drivers_per_row, len(self.drivers))):
            driver = self.drivers[i]
            x = self.margin_left + i * self.cell_width
            y = self.margin_top + len(sectors) * self.cell_height + 5
            label_rect = QRect(x, y, self.cell_width, 25)
            painter.drawText(label_rect, Qt.AlignCenter | Qt.AlignTop, driver)
        
        # X 軸標籤 - 第二排（後 10 位車手）
        for i in range(self.drivers_per_row, len(self.drivers)):
            driver = self.drivers[i]
            col_idx = i - self.drivers_per_row
            x = self.margin_left + col_idx * self.cell_width
            y = base_y_row2 + len(sectors) * self.cell_height + 5
            label_rect = QRect(x, y, self.cell_width, 25)
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
        font.setPointSize(9)
        font.setBold(False)  # 取消粗體
        painter.setFont(font)
        
        painter.drawText(legend_x + legend_width + 10, legend_y + 10, "Fast")
        painter.drawText(legend_x + legend_width + 10, legend_y + legend_height - 5, "Slow")
        
        # 圖例標題 - 取消粗體
        painter.drawText(legend_x - 10, legend_y - 15, "Sector Time")
    
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


class Demo1Window(QMainWindow):
    """Demo 1 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 1: Classic Grid Heatmap")
        self.resize(1400, 700)
        
        # 主 Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 標題
        title = QLabel("Demo 1: 經典網格熱力圖")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 控制按鈕
        btn_layout = QHBoxLayout()
        
        btn_load = QPushButton("載入 JSON 數據")
        btn_load.clicked.connect(self.load_data)
        btn_layout.addWidget(btn_load)
        
        btn_toggle_global = QPushButton("切換全局最快")
        btn_toggle_global.clicked.connect(self.toggle_global)
        btn_layout.addWidget(btn_toggle_global)
        
        btn_toggle_personal = QPushButton("切換個人最佳")
        btn_toggle_personal.clicked.connect(self.toggle_personal)
        btn_layout.addWidget(btn_toggle_personal)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 熱力圖 Widget
        self.heatmap = ClassicGridHeatmapWidget()
        layout.addWidget(self.heatmap, stretch=1)
        
        self.statusBar().showMessage("就緒 - 點擊「載入 JSON 數據」開始")
    
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
    
    def toggle_global(self):
        """切換全局最快標記"""
        self.heatmap.show_global_fastest = not self.heatmap.show_global_fastest
        self.heatmap.update()
        status = "顯示" if self.heatmap.show_global_fastest else "隱藏"
        self.statusBar().showMessage(f"全局最快標記: {status}")
    
    def toggle_personal(self):
        """切換個人最佳標記"""
        self.heatmap.show_personal_best = not self.heatmap.show_personal_best
        self.heatmap.update()
        status = "顯示" if self.heatmap.show_personal_best else "隱藏"
        self.statusBar().showMessage(f"個人最佳標記: {status}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Demo1Window()
    window.show()
    sys.exit(app.exec_())
