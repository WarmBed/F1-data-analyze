#!/usr/bin/env python3
"""
Race Weather Widget Demo 5: Compact Style
緊湊式布局 - 最小化空間佔用的簡潔顯示

Author: F1T Team
Date: 2025-10-13
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QApplication, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class CompactWeatherRow(QFrame):
    """緊湊式天氣行"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # 日期 (固定寬度)
        self.date_label = QLabel("", self)
        self.date_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.date_label.setFixedWidth(70)
        layout.addWidget(self.date_label)
        
        # 天氣圖示
        self.icon_label = QLabel("☀️", self)
        self.icon_label.setStyleSheet("font-size: 16px;")
        self.icon_label.setFixedWidth(25)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # 溫度
        self.temp_label = QLabel("", self)
        self.temp_label.setStyleSheet("font-size: 11px;")
        self.temp_label.setFixedWidth(90)
        layout.addWidget(self.temp_label)
        
        # 降雨
        self.rain_label = QLabel("", self)
        self.rain_label.setStyleSheet("font-size: 11px; color: #6495ed;")
        self.rain_label.setFixedWidth(60)
        layout.addWidget(self.rain_label)
        
        # 風速
        self.wind_label = QLabel("", self)
        self.wind_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        self.wind_label.setFixedWidth(70)
        layout.addWidget(self.wind_label)
        
        layout.addStretch()
        
    def populate_data(self, date: str, day_data: Dict[str, Any], is_race_day: bool = False):
        """填充數據"""
        summary = day_data.get("summary", {})
        
        # 日期
        self.date_label.setText(date)
        if is_race_day:
            self.date_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #dc3545;")
            
        # 溫度
        temp_min = summary.get("temperature_min")
        temp_max = summary.get("temperature_max")
        if temp_min is not None and temp_max is not None:
            self.temp_label.setText(f"{temp_min:.0f}° ~ {temp_max:.0f}°C")
            
        # 降雨
        precip = summary.get("precipitation_sum", 0)
        cloud = summary.get("cloudcover_mean", 0)
        
        # 天氣圖示
        if precip > 5:
            icon = "🌧️"
        elif precip > 0:
            icon = "🌦️"
        elif cloud > 50:
            icon = "☁️"
        elif cloud > 20:
            icon = "⛅"
        else:
            icon = "☀️"
        self.icon_label.setText(icon)
        
        self.rain_label.setText(f"雨 {precip:.1f}mm")
        
        # 風速
        wind_speed = summary.get("windspeed_max")
        if wind_speed:
            self.wind_label.setText(f"風 {wind_speed:.0f}km/h")


class CollapsibleSection(QFrame):
    """可折疊區塊"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.is_expanded = True
        self._init_ui(title)
        
    def _init_ui(self, title: str):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 標題欄
        header = QFrame(self)
        header.setStyleSheet("""
            QFrame {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        header.setCursor(Qt.PointingHandCursor)
        header.mousePressEvent = self._on_header_clicked
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        # 展開/折疊圖示
        self.toggle_icon = QLabel("▼", header)
        self.toggle_icon.setStyleSheet("font-size: 10px; color: #6c757d;")
        self.toggle_icon.setFixedWidth(15)
        header_layout.addWidget(self.toggle_icon)
        
        # 標題
        title_label = QLabel(title, header)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #495057;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 內容容器
        self.content = QFrame(self)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(4)
        layout.addWidget(self.content)
        
    def _on_header_clicked(self, event):
        """標題點擊事件"""
        self.is_expanded = not self.is_expanded
        self.content.setVisible(self.is_expanded)
        self.toggle_icon.setText("▼" if self.is_expanded else "▶")
        self.toggled.emit(self.is_expanded)
        
    def add_row(self, widget: QWidget):
        """添加內容行"""
        self.content_layout.addWidget(widget)


class RaceWeatherDemo5Compact(QWidget):
    """
    Demo 5: 緊湊式天氣預報
    
    特點：
    - 最小化空間佔用
    - 單行顯示關鍵資訊
    - 可折疊區塊
    - 快速瀏覽模式
    - 適合空間受限的介面
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.weather_data: Optional[Dict[str, Any]] = None
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 標題欄
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("比賽週末天氣", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        self.event_info_label = QLabel("", self)
        self.event_info_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        header_layout.addWidget(self.event_info_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 預報區塊
        self.forecast_section = CollapsibleSection("2025 預報", self)
        layout.addWidget(self.forecast_section)
        
        # 歷史區塊
        self.history_section = CollapsibleSection("歷史數據", self)
        self.history_section.is_expanded = False
        self.history_section.content.setVisible(False)
        self.history_section.toggle_icon.setText("▶")
        layout.addWidget(self.history_section)
        
        layout.addStretch()
        
    def load_weather_data(self, json_path: str):
        """載入天氣數據"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.weather_data = json.load(f)
                
            if self.weather_data.get("success"):
                self.populate_compact_view()
        except Exception as e:
            print(f"Error loading weather data: {e}")
            
    def populate_compact_view(self):
        """填充緊湊視圖"""
        if not self.weather_data:
            return
            
        data = self.weather_data.get("data", {})
        
        # 賽事資訊
        calendar_event = data.get("calendar_event", {})
        event_name = calendar_event.get("EventName", "")
        self.event_info_label.setText(event_name)
        
        # 預報數據
        forecast_days = data.get("forecast", {}).get("days", [])
        
        for day_data in forecast_days:
            label = day_data.get("label", "")
            date = day_data.get("date", "")
            is_race_day = (label == "race_day")
            
            # 日期標籤
            if label == "race_minus_2":
                date_text = f"前2天"
            elif label == "race_minus_1":
                date_text = f"前1天"
            else:
                date_text = f"比賽日"
                
            row = CompactWeatherRow(self)
            row.populate_data(date_text, day_data, is_race_day)
            self.forecast_section.add_row(row)
            
        # 歷史數據 (轉換為列表)
        historical_dict = data.get("historical", {}).get("entries", {})
        
        for year in ["2024", "2023"]:
            for day_offset in ["race_minus_0"]:  # 只顯示比賽日
                key = f"{year}_{day_offset}"
                if key in historical_dict:
                    entry = historical_dict[key]
                    
                    row = CompactWeatherRow(self)
                    row.populate_data(f"{year}", entry, False)
                    
                    # 歷史數據使用較淡的顏色
                    row.setStyleSheet("""
                        QFrame {
                            background-color: #ffffff;
                            border: 1px solid #e9ecef;
                            border-radius: 4px;
                            padding: 4px;
                        }
                    """)
                    
                    self.history_section.add_row(row)


# Demo 主程式
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = RaceWeatherDemo5Compact()
    widget.setWindowTitle("Demo 5: 緊湊式天氣預報")
    widget.resize(500, 400)
    
    # 載入測試數據
    json_path = "json/weather/race_weather_forecast_2025_united_states_grand_prix_20251013T031246Z.json"
    if Path(json_path).exists():
        widget.load_weather_data(json_path)
    
    widget.show()
    sys.exit(app.exec_())
