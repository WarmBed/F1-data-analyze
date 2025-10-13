#!/usr/bin/env python3
"""
Demo 5: Compact Table Heatmap (緊湊表格熱力圖)
=============================================

視覺風格：緊湊表格 - 資訊密度高，適合顯示多車手
特點：
- ✅ 緊湊設計（小儲存格）
- ✅ 高資訊密度（可顯示 20+ 車手）
- ✅ 清晰的數值顯示
- ✅ 排名標記
- ✅ 適合數據分析

作者: F1T Team
日期: 2025-10-11
"""

import sys
import json
import math
from pathlib import Path

from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QToolTip, QLabel, QPushButton, QHBoxLayout
)


class CompactTableHeatmapWidget(QWidget):
    """緊湊表格熱力圖 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.drivers = []
        self.sector_data = {}
        self.sector_stats = {}
        self.sector_rankings = {}  # {sector: [(driver, time), ...]}
        
        self.margin_left = 80
        self.margin_right = 100
        self.margin_top = 120
        self.margin_bottom = 60
        
        self.cell_width = 65
        self.cell_height = 32
        
        self.hover_cell = None
        self.setMouseTracking(True)
        self.setMinimumSize(900, 500)
    
    def load_json_data(self, json_path: str):
        """載入數據"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ranking = data.get('analysis_result', {}).get('ranking', [])
        
        self.drivers = []
        self.sector_data = {}
        
        for entry in ranking:
            driver = entry['driver']
            self.drivers.append(driver)
            
            sector_breakdown = entry.get('sector_breakdown', {})
            self.sector_data[driver] = {
                'S1': sector_breakdown.get('sector_1', {}).get('time', float('nan')),
                'S2': sector_breakdown.get('sector_2', {}).get('time', float('nan')),
                'S3': sector_breakdown.get('sector_3', {}).get('time', float('nan')),
                'position': entry.get('position', 0)
            }
        
        # 計算統計和排名
        sectors = ['S1', 'S2', 'S3']
        self.sector_stats = {}
        self.sector_rankings = {}
        
        for sector in sectors:
            times = [(d, self.sector_data[d][sector]) for d in self.drivers 
                     if not math.isnan(self.sector_data[d][sector])]
            
            if times:
                times.sort(key=lambda x: x[1])
                self.sector_rankings[sector] = times
                
                self.sector_stats[sector] = {
                    'min': times[0][1],
                    'max': times[-1][1]
                }
        
        self.update()
    
    def paintEvent(self, event):
        """繪圖"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(255, 255, 255))
            
            if not self.drivers:
                self._draw_no_data(painter)
                return
            
            self._draw_title(painter)
            self._draw_table(painter)
            self._draw_headers(painter)
            self._draw_summary(painter)
        
        finally:
            painter.end()
    
    def _draw_no_data(self, painter):
        """無數據提示"""
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        font = QFont('Consolas', 14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "No data loaded")
    
    def _draw_title(self, painter):
        """標題"""
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont('Consolas', 16, QFont.Bold)
        painter.setFont(font)
        
        painter.drawText(0, 20, self.width(), 35, int(Qt.AlignCenter),
                        "Sector Performance - Compact Table View")
        
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(0, 50, self.width(), 25, int(Qt.AlignCenter),
                        f"{len(self.drivers)} Drivers | High Information Density")
    
    def _draw_headers(self, painter):
        """繪製表頭"""
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setBrush(QBrush(QColor(52, 73, 94)))
        font = QFont('Consolas', 10, QFont.Bold)
        painter.setFont(font)
        
        # 車手標頭（垂直）
        header_height = 80
        for col_idx, driver in enumerate(self.drivers):
            x = self.margin_left + col_idx * self.cell_width
            y = self.margin_top - header_height
            rect = QRectF(x, y, self.cell_width, header_height)
            
            painter.fillRect(rect, QColor(52, 73, 94))
            painter.drawRect(rect)
            
            # 垂直文字（簡化版：橫向顯示）
            painter.drawText(rect, int(Qt.AlignCenter), driver)
        
        # 分段標頭（橫向）
        sectors = ['S1', 'S2', 'S3']
        for row_idx, sector in enumerate(sectors):
            x = 10
            y = self.margin_top + row_idx * self.cell_height
            rect = QRectF(x, y, self.margin_left - 15, self.cell_height)
            
            painter.fillRect(rect, QColor(52, 73, 94))
            painter.drawRect(rect)
            painter.drawText(rect, int(Qt.AlignCenter), sector)
    
    def _draw_table(self, painter):
        """繪製表格"""
        sectors = ['S1', 'S2', 'S3']
        
        for row_idx, sector in enumerate(sectors):
            for col_idx, driver in enumerate(self.drivers):
                value = self.sector_data[driver][sector]
                
                x = self.margin_left + col_idx * self.cell_width
                y = self.margin_top + row_idx * self.cell_height
                rect = QRectF(x, y, self.cell_width, self.cell_height)
                
                self._draw_cell(painter, rect, driver, sector, value)
    
    def _draw_cell(self, painter, rect, driver, sector, value):
        """繪製單個儲存格"""
        # 背景顏色
        if math.isnan(value):
            bg_color = QColor(245, 245, 245)
            text = "—"
        else:
            bg_color = self._value_to_color(sector, value)
            text = f"{value:.3f}"
            
            # 如果是該分段最快，加深背景
            rankings = self.sector_rankings.get(sector, [])
            if rankings and rankings[0][0] == driver:
                bg_color = QColor(255, 215, 0).darker(110)
        
        painter.fillRect(rect, bg_color)
        
        # 邊框
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        painter.drawRect(rect)
        
        # 文字
        text_color = self._get_text_color(bg_color)
        painter.setPen(QPen(text_color, 1))
        font = QFont('Consolas', 9)
        painter.setFont(font)
        painter.drawText(rect, int(Qt.AlignCenter), text)
        
        # 排名標記（小字）
        if not math.isnan(value):
            rankings = self.sector_rankings.get(sector, [])
            rank = next((i + 1 for i, (d, _) in enumerate(rankings) if d == driver), None)
            
            if rank and rank <= 3:
                painter.setPen(QPen(QColor(255, 100, 100), 1))
                font.setPointSize(7)
                painter.setFont(font)
                
                rank_rect = QRectF(rect.right() - 15, rect.top() + 2, 12, 10)
                painter.drawText(rank_rect, int(Qt.AlignCenter), f"P{rank}")
    
    def _draw_summary(self, painter):
        """繪製統計摘要"""
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        font = QFont('Consolas', 9)
        painter.setFont(font)
        
        summary_y = self.margin_top + 3 * self.cell_height + 30
        
        painter.drawText(20, summary_y, "Sector Statistics:")
        
        y_offset = summary_y + 20
        for sector, stats in self.sector_stats.items():
            painter.drawText(30, y_offset,
                           f"{sector}: Min={stats['min']:.3f}s, Max={stats['max']:.3f}s, "
                           f"Δ={stats['max'] - stats['min']:.3f}s")
            y_offset += 18
    
    def _value_to_color(self, sector, value):
        """數值轉顏色（淡色系）"""
        if math.isnan(value):
            return QColor(245, 245, 245)
        
        stats = self.sector_stats.get(sector, {})
        vmin = stats.get('min', value)
        vmax = stats.get('max', value)
        
        if vmax == vmin:
            ratio = 0.5
        else:
            ratio = (value - vmin) / (vmax - vmin)
        
        ratio = max(0.0, min(1.0, ratio))
        
        # 淡色系漸層
        if ratio < 0.33:
            # 淺綠
            return QColor(200, 230, 201)
        elif ratio < 0.67:
            # 淺黃
            return QColor(255, 245, 157)
        else:
            # 淺紅
            return QColor(255, 205, 210)
    
    def _get_text_color(self, bg_color):
        """根據背景決定文字顏色"""
        return QColor(33, 33, 33)  # 統一深灰
    
    def mouseMoveEvent(self, event):
        """滑鼠移動"""
        if not self.drivers:
            return
        
        pos = event.pos()
        sectors = ['S1', 'S2', 'S3']
        
        col_idx = (pos.x() - self.margin_left) // self.cell_width
        row_idx = (pos.y() - self.margin_top) // self.cell_height
        
        if 0 <= col_idx < len(self.drivers) and 0 <= row_idx < 3:
            driver = self.drivers[col_idx]
            sector = sectors[row_idx]
            
            self.hover_cell = (driver, sector)
            
            value = self.sector_data[driver][sector]
            if not math.isnan(value):
                rankings = self.sector_rankings.get(sector, [])
                rank = next((i + 1 for i, (d, _) in enumerate(rankings) if d == driver), "N/A")
                
                tooltip = f"Driver: {driver}\nSector: {sector}\nTime: {value:.3f}s\nRank: P{rank}"
                QToolTip.showText(event.globalPos(), tooltip, self)
            
            self.update()
        else:
            if self.hover_cell:
                self.hover_cell = None
                QToolTip.hideText()
                self.update()
    
    def leaveEvent(self, event):
        """滑鼠離開"""
        self.hover_cell = None
        QToolTip.hideText()
        self.update()


class Demo5Window(QMainWindow):
    """Demo 5 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 5: Compact Table Heatmap")
        self.resize(1600, 900)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        title = QLabel("Demo 5: 緊湊表格熱力圖 (高資訊密度)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        btn_load = QPushButton("載入 JSON 數據")
        btn_load.clicked.connect(self.load_data)
        layout.addWidget(btn_load)
        
        self.heatmap = CompactTableHeatmapWidget()
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
    window = Demo5Window()
    window.show()
    sys.exit(app.exec_())
