#!/usr/bin/env python3
"""
Demo 2: Rounded Card Heatmap (圓角卡片熱力圖)
==============================================

視覺風格：Material Design - 圓角矩形 + 柔和陰影
特點：
- ✅ 圓角卡片設計
- ✅ 陰影效果（3D 感）
- ✅ 柔和漸層色彩
- ✅ 車手名稱顯示
- ✅ 懸停放大效果

作者: F1T Team
日期: 2025-10-11
"""

import sys
import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, QPoint, QRect, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QLinearGradient, QRadialGradient
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QToolTip, QLabel, QPushButton, QHBoxLayout
)


class RoundedCardHeatmapWidget(QWidget):
    """圓角卡片熱力圖 Widget"""
    
    cell_clicked = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據存儲
        self.drivers = []
        self.sector_data = {}
        self.sector_stats = {}
        
        # 佈局參數
        self.margin_left = 120
        self.margin_right = 200
        self.margin_top = 100
        self.margin_bottom = 120
        
        self.card_width = 100
        self.card_height = 80
        self.card_padding = 8
        self.corner_radius = 12
        
        # 色彩配置（柔和配色）
        self.color_fast = QColor(102, 187, 106)    # 柔和綠
        self.color_medium = QColor(255, 202, 40)   # 柔和黃
        self.color_slow = QColor(239, 83, 80)      # 柔和紅
        
        # 互動狀態
        self.hover_cell = None
        self.setMouseTracking(True)
        self.setMinimumSize(900, 500)
    
    def load_json_data(self, json_path: str):
        """從 JSON 載入數據"""
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
                'name': entry.get('driver_name', driver),
                'team': entry.get('team', 'Unknown')
            }
        
        # 計算統計
        sectors = ['S1', 'S2', 'S3']
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
        
        self.update()
    
    def paintEvent(self, event):
        """核心繪圖方法"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # 漸層背景
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor(250, 250, 252))
            gradient.setColorAt(1.0, QColor(238, 240, 245))
            painter.fillRect(self.rect(), QBrush(gradient))
            
            if not self.drivers:
                self._draw_no_data(painter)
                return
            
            self._draw_title(painter)
            self._draw_cards(painter)
            self._draw_axes(painter)
            self._draw_legend(painter)
        
        finally:
            painter.end()
    
    def _draw_no_data(self, painter):
        """繪製無數據提示"""
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        font = QFont('Segoe UI', 14)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter,
                        "No data loaded\nClick 'Load Data' to begin")
    
    def _draw_title(self, painter):
        """繪製標題"""
        painter.setPen(QPen(QColor(33, 33, 33), 1))
        font = QFont('Segoe UI', 18, QFont.Bold)
        painter.setFont(font)
        
        title = "Ideal Lap Sector Performance - Rounded Card View"
        title_rect = QRect(0, 20, self.width(), 40)
        painter.drawText(title_rect, Qt.AlignCenter, title)
        
        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)
        subtitle = f"{len(self.drivers)} Drivers | Material Design Style"
        subtitle_rect = QRect(0, 55, self.width(), 25)
        painter.drawText(subtitle_rect, Qt.AlignCenter, subtitle)
    
    def _draw_cards(self, painter):
        """繪製圓角卡片"""
        sectors = ['S1', 'S2', 'S3']
        
        for row_idx, sector in enumerate(sectors):
            for col_idx, driver in enumerate(self.drivers):
                value = self.sector_data[driver][sector]
                
                x = self.margin_left + col_idx * (self.card_width + self.card_padding)
                y = self.margin_top + row_idx * (self.card_height + self.card_padding)
                rect = QRectF(x, y, self.card_width, self.card_height)
                
                # 懸停放大效果
                is_hover = self.hover_cell == (driver, sector)
                if is_hover:
                    scale = 1.05
                    rect = QRectF(
                        rect.x() - rect.width() * 0.025,
                        rect.y() - rect.height() * 0.025,
                        rect.width() * scale,
                        rect.height() * scale
                    )
                
                self._draw_card(painter, rect, driver, sector, value, is_hover)
    
    def _draw_card(self, painter, rect, driver, sector, value, is_hover):
        """繪製單個卡片"""
        # 陰影效果
        shadow_offset = 5 if not is_hover else 8
        shadow_rect = rect.adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset)
        painter.setBrush(QBrush(QColor(0, 0, 0, 40 if is_hover else 25)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, self.corner_radius, self.corner_radius)
        
        # 卡片背景（漸層）
        if math.isnan(value):
            bg_color = QColor(240, 240, 240)
        else:
            bg_color = self._value_to_color(sector, value)
        
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, bg_color.lighter(110))
        gradient.setColorAt(1.0, bg_color.darker(105))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # 繪製數值
        if math.isnan(value):
            text = "N/A"
            font_size = 12
        else:
            text = f"{value:.3f}"
            font_size = 13
        
        text_color = self._get_text_color(bg_color)
        painter.setPen(QPen(text_color, 1))
        font = QFont('Segoe UI', font_size, QFont.Bold)
        painter.setFont(font)
        
        text_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.25,
                          rect.width(), rect.height() * 0.5)
        painter.drawText(text_rect, Qt.AlignCenter, text)
        
        # 繪製分段標籤（小字）
        font.setPointSize(9)
        painter.setFont(font)
        label_rect = QRectF(rect.x(), rect.y() + 5, rect.width(), 20)
        painter.drawText(label_rect, Qt.AlignCenter, sector)
        
        # 繪製高亮標記
        if self.sector_stats.get(sector, {}).get('fastest_driver') == driver:
            self._draw_badge(painter, rect, "⭐", QColor(255, 215, 0))
    
    def _draw_badge(self, painter, rect, text, color):
        """繪製角標"""
        badge_size = 24
        badge_rect = QRectF(
            rect.right() - badge_size - 5,
            rect.top() + 5,
            badge_size,
            badge_size
        )
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawEllipse(badge_rect)
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont('Segoe UI', 12)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignCenter, text)
    
    def _draw_axes(self, painter):
        """繪製座標軸標籤"""
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        font = QFont('Segoe UI', 11)
        painter.setFont(font)
        
        # X 軸（車手）
        for col_idx, driver in enumerate(self.drivers):
            x = self.margin_left + col_idx * (self.card_width + self.card_padding)
            y = self.margin_top + 3 * (self.card_height + self.card_padding) + 20
            
            label_rect = QRect(int(x), int(y), self.card_width, 30)
            painter.drawText(label_rect, Qt.AlignCenter | Qt.AlignTop, driver)
    
    def _draw_legend(self, painter):
        """繪製色彩圖例"""
        legend_x = self.width() - self.margin_right + 40
        legend_y = self.margin_top
        legend_width = 60
        legend_height = 3 * (self.card_height + self.card_padding) - self.card_padding
        
        # 漸層
        gradient = QLinearGradient(legend_x, legend_y, legend_x, legend_y + legend_height)
        gradient.setColorAt(0.0, self.color_fast)
        gradient.setColorAt(0.5, self.color_medium)
        gradient.setColorAt(1.0, self.color_slow)
        
        rect = QRectF(legend_x, legend_y, legend_width, legend_height)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        painter.drawRoundedRect(rect, 8, 8)
        
        # 標籤
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        font = QFont('Segoe UI', 10)
        painter.setFont(font)
        
        painter.drawText(int(legend_x + legend_width + 12), int(legend_y + 15), "Fast")
        painter.drawText(int(legend_x + legend_width + 12), int(legend_y + legend_height - 5), "Slow")
    
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
        return QColor(255, 255, 255) if luminance < 140 else QColor(33, 33, 33)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        if not self.drivers:
            return
        
        pos = event.pos()
        sectors = ['S1', 'S2', 'S3']
        
        for row_idx, sector in enumerate(sectors):
            for col_idx, driver in enumerate(self.drivers):
                x = self.margin_left + col_idx * (self.card_width + self.card_padding)
                y = self.margin_top + row_idx * (self.card_height + self.card_padding)
                rect = QRectF(x, y, self.card_width, self.card_height)
                
                if rect.contains(pos):
                    self.hover_cell = (driver, sector)
                    
                    value = self.sector_data[driver][sector]
                    name = self.sector_data[driver]['name']
                    team = self.sector_data[driver]['team']
                    
                    if not math.isnan(value):
                        tooltip = f"{name} ({driver})\nSector: {sector}\nTime: {value:.3f}s\nTeam: {team}"
                        QToolTip.showText(event.globalPos(), tooltip, self)
                    
                    self.update()
                    return
        
        if self.hover_cell:
            self.hover_cell = None
            QToolTip.hideText()
            self.update()
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.hover_cell = None
        QToolTip.hideText()
        self.update()


class Demo2Window(QMainWindow):
    """Demo 2 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo 2: Rounded Card Heatmap")
        self.resize(1600, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        title = QLabel("Demo 2: 圓角卡片熱力圖 (Material Design)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("載入 JSON 數據")
        btn_load.setStyleSheet("padding: 8px 16px; font-size: 12pt;")
        btn_load.clicked.connect(self.load_data)
        btn_layout.addWidget(btn_load)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.heatmap = RoundedCardHeatmapWidget()
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Demo2Window()
    window.show()
    sys.exit(app.exec_())
