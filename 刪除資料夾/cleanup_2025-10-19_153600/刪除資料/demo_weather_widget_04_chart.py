#!/usr/bin/env python3
"""
Race Weather Widget Demo 4: Chart Style
圖表式布局 - 溫度與降雨趨勢圖表

Author: F1T Team
Date: 2025-10-13
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QApplication, QFrame
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QBrush, QLinearGradient
from datetime import datetime


class WeatherChartWidget(QWidget):
    """天氣圖表小部件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.forecast_data: List[Dict[str, Any]] = []
        self.historical_data: List[Dict[str, Any]] = []
        self.setMinimumHeight(300)
        
    def set_data(self, forecast: List[Dict[str, Any]], historical: List[Dict[str, Any]]):
        """設置數據"""
        self.forecast_data = forecast
        self.historical_data = historical
        self.update()
        
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.forecast_data:
            return
            
        # 計算繪圖區域
        margin = 40
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        # 背景
        painter.fillRect(0, 0, self.width(), self.height(), QColor("#ffffff"))
        
        # 繪製網格
        self._draw_grid(painter, margin, width, height)
        
        # 繪製歷史數據 (虛線)
        if self.historical_data:
            self._draw_historical_lines(painter, margin, width, height)
            
        # 繪製預報溫度曲線
        self._draw_temperature_line(painter, margin, width, height)
        
        # 繪製降雨柱狀圖
        self._draw_precipitation_bars(painter, margin, width, height)
        
        # 繪製圖例
        self._draw_legend(painter)
        
    def _draw_grid(self, painter: QPainter, margin: int, width: int, height: int):
        """繪製網格"""
        painter.setPen(QPen(QColor("#e9ecef"), 1, Qt.DashLine))
        
        # 水平網格線 (溫度刻度)
        for i in range(5):
            y = margin + (height * i / 4)
            painter.drawLine(margin, int(y), margin + width, int(y))
            
    def _draw_historical_lines(self, painter: QPainter, margin: int, width: int, height: int):
        """繪製歷史數據虛線"""
        if len(self.historical_data) < 2:
            return
            
        # 收集所有溫度數據以確定範圍
        all_temps = []
        for day in self.forecast_data:
            summary = day.get("summary", {})
            temp_max = summary.get("temperature_max")
            if temp_max is not None:
                all_temps.append(temp_max)
                
        for year_group in self.historical_data:
            for entry in year_group.get("entries", []):
                summary = entry.get("summary", {})
                temp_max = summary.get("temperature_max")
                if temp_max is not None:
                    all_temps.append(temp_max)
                
        if not all_temps:
            return
            
        min_temp = min(all_temps) - 5
        max_temp = max(all_temps) + 5
        temp_range = max_temp - min_temp
        
        # 繪製 2024 和 2023
        colors = {"2024": QColor("#adb5bd"), "2023": QColor("#ced4da")}
        
        for year_group in self.historical_data:
            year = year_group.get("year")
            if year not in colors:
                continue
                
            year_entries = year_group.get("entries", [])
            if len(year_entries) < 2:
                continue
                
            painter.setPen(QPen(colors[year], 2, Qt.DashLine))
            
            # 只繪製前3個點 (對應預報的3天)
            points = []
            for i, entry in enumerate(year_entries[:3]):
                summary = entry.get("summary", {})
                temp_max = summary.get("temperature_max")
                if temp_max is None:
                    continue
                    
                x = margin + (width * i / 2)
                y = margin + height - ((temp_max - min_temp) / temp_range * height)
                points.append(QPointF(x, y))
                
            # 繪製線條
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
                
    def _draw_temperature_line(self, painter: QPainter, margin: int, width: int, height: int):
        """繪製溫度曲線"""
        # 收集溫度數據
        temps = []
        for day in self.forecast_data:
            summary = day.get("summary", {})
            temp_max = summary.get("temperature_max")
            if temp_max is not None:
                temps.append(temp_max)
                
        if not temps:
            return
            
        # 包含歷史數據以確定溫度範圍
        all_temps = temps.copy()
        for year_group in self.historical_data:
            for entry in year_group.get("entries", []):
                summary = entry.get("summary", {})
                temp_max = summary.get("temperature_max")
                if temp_max is not None:
                    all_temps.append(temp_max)
                
        min_temp = min(all_temps) - 5
        max_temp = max(all_temps) + 5
        temp_range = max_temp - min_temp
        
        # 計算點位置
        points = []
        for i, temp in enumerate(temps):
            x = margin + (width * i / (len(temps) - 1))
            y = margin + height - ((temp - min_temp) / temp_range * height)
            points.append(QPointF(x, y))
            
        # 繪製漸變填充區域
        if len(points) >= 2:
            gradient = QLinearGradient(0, margin, 0, margin + height)
            gradient.setColorAt(0, QColor("#4da6ff"))
            gradient.setColorAt(1, QColor("#ffffff"))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            
            # 創建填充多邊形
            from PyQt5.QtGui import QPolygonF
            polygon = QPolygonF()
            for point in points:
                polygon.append(point)
            polygon.append(QPointF(margin + width, margin + height))
            polygon.append(QPointF(margin, margin + height))
            painter.drawPolygon(polygon)
            
        # 繪製溫度線
        painter.setPen(QPen(QColor("#0066cc"), 3))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
        # 繪製數據點
        painter.setBrush(QBrush(QColor("#0066cc")))
        for i, point in enumerate(points):
            painter.drawEllipse(point, 5, 5)
            
            # 繪製溫度標籤
            painter.setPen(QPen(QColor("#000000")))
            font = QFont()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            
            temp = temps[i]
            day = self.forecast_data[i] if i < len(self.forecast_data) else {}
            label = day.get("label", "")
            
            # 比賽日用紅色
            if label == "race_day":
                painter.setPen(QPen(QColor("#dc3545")))
                
            painter.drawText(
                int(point.x() - 20),
                int(point.y() - 10),
                40,
                20,
                Qt.AlignCenter,
                f"{temp:.1f}°C"
            )
            painter.setPen(QPen(QColor("#0066cc"), 3))
            
    def _draw_precipitation_bars(self, painter: QPainter, margin: int, width: int, height: int):
        """繪製降雨柱狀圖"""
        # 收集降雨數據
        precips = []
        for day in self.forecast_data:
            summary = day.get("summary", {})
            precip = summary.get("precipitation_sum", 0)
            precips.append(precip)
            
        if not precips or max(precips) == 0:
            return
            
        max_precip = max(precips) * 1.2  # 留出頂部空間
        
        # 繪製柱狀圖
        bar_width = width / (len(precips) * 3)
        
        for i, precip in enumerate(precips):
            bar_height = (precip / max_precip) * (height * 0.4)  # 最多佔40%高度
            
            x = margin + (width * i / (len(precips) - 1 if len(precips) > 1 else 1)) - bar_width / 2
            y = margin + height - bar_height
            
            # 降雨柱 (半透明藍色)
            painter.setBrush(QBrush(QColor(100, 149, 237, 100)))
            painter.setPen(QPen(QColor("#6495ed"), 1))
            painter.drawRect(int(x), int(y), int(bar_width), int(bar_height))
            
            # 降雨量標籤
            if precip > 0:
                painter.setPen(QPen(QColor("#6495ed")))
                font = QFont()
                font.setPixelSize(10)
                painter.setFont(font)
                painter.drawText(
                    int(x),
                    int(y - 15),
                    int(bar_width),
                    15,
                    Qt.AlignCenter,
                    f"{precip:.1f}mm"
                )
                
    def _draw_legend(self, painter: QPainter):
        """繪製圖例"""
        x = self.width() - 180
        y = 10
        
        painter.setFont(QFont("Arial", 10))
        
        # 2025 預報
        painter.setPen(QPen(QColor("#0066cc"), 3))
        painter.drawLine(x, y + 5, x + 30, y + 5)
        painter.setPen(QPen(QColor("#000000")))
        painter.drawText(x + 35, y, 100, 15, Qt.AlignLeft | Qt.AlignVCenter, "2025 預報")
        
        y += 20
        
        # 降雨
        painter.setBrush(QBrush(QColor(100, 149, 237, 100)))
        painter.setPen(QPen(QColor("#6495ed"), 1))
        painter.drawRect(x, y, 30, 10)
        painter.setPen(QPen(QColor("#000000")))
        painter.drawText(x + 35, y - 3, 100, 15, Qt.AlignLeft | Qt.AlignVCenter, "降雨量")
        
        y += 20
        
        # 2024 歷史
        painter.setPen(QPen(QColor("#adb5bd"), 2, Qt.DashLine))
        painter.drawLine(x, y + 5, x + 30, y + 5)
        painter.setPen(QPen(QColor("#000000")))
        painter.drawText(x + 35, y, 100, 15, Qt.AlignLeft | Qt.AlignVCenter, "2024 歷史")
        
        y += 20
        
        # 2023 歷史
        painter.setPen(QPen(QColor("#ced4da"), 2, Qt.DashLine))
        painter.drawLine(x, y + 5, x + 30, y + 5)
        painter.setPen(QPen(QColor("#000000")))
        painter.drawText(x + 35, y, 100, 15, Qt.AlignLeft | Qt.AlignVCenter, "2023 歷史")


class RaceWeatherDemo4Chart(QWidget):
    """
    Demo 4: 圖表式天氣預報
    
    特點：
    - 溫度趨勢曲線圖
    - 降雨柱狀圖
    - 歷史數據對比 (虛線)
    - 漸變填充效果
    - 適合視覺化分析
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.weather_data: Optional[Dict[str, Any]] = None
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 標題
        title_label = QLabel("比賽週末天氣趨勢分析", self)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 賽事資訊
        self.event_info_label = QLabel("", self)
        self.event_info_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(self.event_info_label)
        
        # 圖表
        self.chart = WeatherChartWidget(self)
        layout.addWidget(self.chart)
        
        # 日期標籤
        self.date_labels_layout = QHBoxLayout()
        self.date_labels_layout.setSpacing(20)
        layout.addLayout(self.date_labels_layout)
        
    def load_weather_data(self, json_path: str):
        """載入天氣數據"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.weather_data = json.load(f)
                
            if self.weather_data.get("success"):
                self.populate_chart()
        except Exception as e:
            print(f"Error loading weather data: {e}")
            
    def populate_chart(self):
        """填充圖表"""
        if not self.weather_data:
            return
            
        data = self.weather_data.get("data", {})
        
        # 賽事資訊
        calendar_event = data.get("calendar_event", {})
        year = calendar_event.get("year", "")
        event_name = calendar_event.get("EventName", "")
        location = data.get("circuit_info", {}).get("location", "")
        self.event_info_label.setText(
            f"{year} {event_name} - {location}"
        )
        
        # 預報數據
        forecast_days = data.get("forecast", {}).get("days", [])
        
        # 歷史數據 (轉換為列表)
        historical_dict = data.get("historical", {}).get("entries", {})
        historical_entries = []
        
        # 轉換歷史數據字典為列表
        for year in ["2024", "2023"]:
            year_data = {
                "year": year,
                "entries": []
            }
            for day_offset in ["race_minus_2", "race_minus_1", "race_minus_0"]:
                key = f"{year}_{day_offset}"
                if key in historical_dict:
                    entry = historical_dict[key].copy()
                    entry["year"] = year
                    entry["day_label"] = day_offset
                    year_data["entries"].append(entry)
            if year_data["entries"]:
                historical_entries.append(year_data)
        
        # 設置圖表數據
        self.chart.set_data(forecast_days, historical_entries)
        
        # 清除舊的日期標籤
        while self.date_labels_layout.count():
            item = self.date_labels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # 添加日期標籤
        self.date_labels_layout.addStretch()
        
        for day_data in forecast_days:
            date = day_data.get("date", "")
            label = day_data.get("label", "")
            
            # 日期標籤
            if label == "race_minus_2":
                date_text = f"前2天 ({date})"
            elif label == "race_minus_1":
                date_text = f"前1天 ({date})"
            else:
                date_text = f"比賽日 ({date})"
                
            date_label = QLabel(date_text, self)
            if label == "race_day":
                date_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #dc3545;")
            else:
                date_label.setStyleSheet("font-size: 12px; color: #495057;")
                
            self.date_labels_layout.addWidget(date_label)
            
        self.date_labels_layout.addStretch()


# Demo 主程式
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = RaceWeatherDemo4Chart()
    widget.setWindowTitle("Demo 4: 圖表式天氣預報")
    widget.resize(1000, 550)
    
    # 載入測試數據
    json_path = "json/weather/race_weather_forecast_2025_united_states_grand_prix_20251013T031246Z.json"
    if Path(json_path).exists():
        widget.load_weather_data(json_path)
    
    widget.show()
    sys.exit(app.exec_())
