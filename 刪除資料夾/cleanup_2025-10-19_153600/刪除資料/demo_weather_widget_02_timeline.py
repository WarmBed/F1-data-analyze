#!/usr/bin/env python3
"""
Race Weather Widget Demo 2: Timeline Style
時間軸式布局 - 橫向時間軸顯示天氣變化

Author: F1T Team
Date: 2025-10-13
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QApplication, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QPen, QColor


class TimelineNode(QFrame):
    """時間軸節點"""
    
    def __init__(self, date: str, is_race_day: bool = False, parent=None):
        super().__init__(parent)
        self.date = date
        self.is_race_day = is_race_day
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 日期標籤
        self.date_label = QLabel(self.date, self)
        font = QFont()
        font.setBold(self.is_race_day)
        self.date_label.setFont(font)
        self.date_label.setStyleSheet(
            f"color: {'#dc3545' if self.is_race_day else '#495057'}; font-size: 12px;"
        )
        self.date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.date_label)
        
        # 溫度（比賽日使用紅色）
        self.temp_label = QLabel("--°C", self)
        temp_color = '#dc3545' if self.is_race_day else '#000000'
        self.temp_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {temp_color};")
        self.temp_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.temp_label)
        
        # 天氣圖示
        self.weather_label = QLabel("☀️", self)
        self.weather_label.setStyleSheet("font-size: 20px;")
        self.weather_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.weather_label)
        
        # 降雨
        self.rain_label = QLabel("0mm", self)
        self.rain_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        self.rain_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.rain_label)
        
        # 風向風速
        self.wind_label = QLabel("↓ 10km/h", self)
        self.wind_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        self.wind_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.wind_label)
        
        self.setFixedWidth(120)
        
    def populate_data(self, day_data: Dict[str, Any]):
        """填充數據"""
        summary = day_data.get("summary", {})
        
        # 溫度 (顯示最高溫)
        temp_max = summary.get("temperature_max")
        if temp_max is not None:
            self.temp_label.setText(f"{temp_max:.1f}°C")
            
        # 降雨
        precip = summary.get("precipitation_sum", 0)
        cloud = summary.get("cloudcover_mean", 0)
        
        # 天氣圖示（使用彩色 emoji）
        if precip > 10:
            icon = "⛈️"  # 雷雨
        elif precip > 5:
            icon = "🌧️"  # 大雨
        elif precip > 0:
            icon = "🌦️"  # 陣雨
        elif cloud > 50:
            icon = "☁️"   # 多雲
        elif cloud > 20:
            icon = "⛅"   # 局部雲
        else:
            icon = "🌤️"   # 晴朗（有顏色的太陽）
        self.weather_label.setText(icon)
        
        self.rain_label.setText(f"{precip:.1f}mm")
        
        # 風向風速
        wind_speed = summary.get("windspeed_max")
        wind_dir = summary.get("winddirection_cardinal", "")
        if wind_speed:
            # 風向箭頭
            wind_arrows = {
                "N": "↓", "NE": "↙", "E": "←", "SE": "↖",
                "S": "↑", "SW": "↗", "W": "→", "NW": "↘"
            }
            arrow = wind_arrows.get(wind_dir, "•")
            self.wind_label.setText(f"{arrow} {wind_speed:.0f}km/h")


class RaceWeatherDemo2Timeline(QWidget):
    """
    Demo 2: 時間軸式天氣預報
    
    特點：
    - 橫向時間軸展示
    - 視覺化天氣變化趨勢
    - 比賽日突出顯示
    - 包含歷史對比節點
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
        title_label = QLabel("比賽週末天氣時間軸", self)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 時間軸容器 (可滾動)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(250)
        
        # 時間軸內容
        timeline_widget = QWidget()
        self.timeline_layout = QHBoxLayout(timeline_widget)
        self.timeline_layout.setSpacing(0)
        self.timeline_layout.setContentsMargins(20, 20, 20, 20)
        
        scroll.setWidget(timeline_widget)
        layout.addWidget(scroll)
        
        # 歷史數據區塊
        history_frame = QFrame(self)
        history_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(8, 8, 8, 8)
        history_layout.setSpacing(4)
        
        # 歷史數據標題
        history_title = QLabel("歷史天氣對比", self)
        history_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #6c757d;")
        history_layout.addWidget(history_title)
        
        # 2024 和 2023 數據
        self.history_2024_label = QLabel("", self)
        self.history_2024_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        history_layout.addWidget(self.history_2024_label)
        
        self.history_2023_label = QLabel("", self)
        self.history_2023_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        history_layout.addWidget(self.history_2023_label)
        
        layout.addWidget(history_frame)
        
        # 圖例
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(20)
        
        legend_race = QLabel("■ 比賽日（紅色標示）", self)
        legend_race.setStyleSheet("color: #dc3545; font-size: 12px;")
        legend_layout.addWidget(legend_race)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
    def load_weather_data(self, json_path: str):
        """載入天氣數據"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.weather_data = json.load(f)
                
            if self.weather_data.get("success"):
                self.populate_timeline()
        except Exception as e:
            print(f"Error loading weather data: {e}")
            
    def populate_timeline(self):
        """填充時間軸"""
        if not self.weather_data:
            return
            
        # 清除現有節點
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        forecast_days = self.weather_data.get("data", {}).get("forecast", {}).get("days", [])
        
        # 添加預報節點
        for i, day_data in enumerate(forecast_days):
            date = day_data.get("date", "")
            label = day_data.get("label", "")
            is_race_day = (label == "race_day")
            
            # 日期標籤
            if label == "race_minus_2":
                date_text = f"前2天\n{date}"
            elif label == "race_minus_1":
                date_text = f"前1天\n{date}"
            else:
                date_text = f"比賽日\n{date}"
                
            node = TimelineNode(date_text, is_race_day, self)
            node.populate_data(day_data)
            
            self.timeline_layout.addWidget(node)
            
            # 添加連接線 (除了最後一個節點)
            if i < len(forecast_days) - 1:
                line = self._create_timeline_line()
                self.timeline_layout.addWidget(line)
                
        self.timeline_layout.addStretch()
        
        # 填充歷史數據
        self._populate_historical_data()
        
    def _populate_historical_data(self):
        """填充歷史天氣數據"""
        if not self.weather_data:
            return
            
        historical_dict = self.weather_data.get("data", {}).get("historical", {}).get("entries", {})
        
        # 2024 年比賽日數據
        data_2024 = historical_dict.get("2024_race_minus_0", {})
        if data_2024:
            date_2024 = data_2024.get("date", "")
            summary_2024 = data_2024.get("summary", {})
            temp_max_2024 = summary_2024.get("temperature_max")
            temp_min_2024 = summary_2024.get("temperature_min")
            precip_2024 = summary_2024.get("precipitation_sum", 0)
            wind_2024 = summary_2024.get("windspeed_max")
            
            # 天氣圖示（使用彩色 emoji）
            cloud_2024 = summary_2024.get("cloudcover_mean", 0)
            if precip_2024 > 10:
                icon_2024 = "⛈️"
            elif precip_2024 > 5:
                icon_2024 = "🌧️"
            elif precip_2024 > 0:
                icon_2024 = "🌦️"
            elif cloud_2024 > 50:
                icon_2024 = "☁️"
            elif cloud_2024 > 20:
                icon_2024 = "⛅"
            else:
                icon_2024 = "🌤️"
                
            if temp_max_2024 is not None and temp_min_2024 is not None:
                history_text_2024 = (
                    f"2024 年 ({date_2024}): {icon_2024} "
                    f"{temp_min_2024:.1f}°C ~ {temp_max_2024:.1f}°C, "
                    f"降雨 {precip_2024:.1f}mm"
                )
                if wind_2024:
                    history_text_2024 += f", 風速 {wind_2024:.0f}km/h"
                self.history_2024_label.setText(history_text_2024)
        
        # 2023 年比賽日數據
        data_2023 = historical_dict.get("2023_race_minus_0", {})
        if data_2023:
            date_2023 = data_2023.get("date", "")
            summary_2023 = data_2023.get("summary", {})
            temp_max_2023 = summary_2023.get("temperature_max")
            temp_min_2023 = summary_2023.get("temperature_min")
            precip_2023 = summary_2023.get("precipitation_sum", 0)
            wind_2023 = summary_2023.get("windspeed_max")
            
            # 天氣圖示（使用彩色 emoji）
            cloud_2023 = summary_2023.get("cloudcover_mean", 0)
            if precip_2023 > 10:
                icon_2023 = "⛈️"
            elif precip_2023 > 5:
                icon_2023 = "🌧️"
            elif precip_2023 > 0:
                icon_2023 = "🌦️"
            elif cloud_2023 > 50:
                icon_2023 = "☁️"
            elif cloud_2023 > 20:
                icon_2023 = "⛅"
            else:
                icon_2023 = "🌤️"
                
            if temp_max_2023 is not None and temp_min_2023 is not None:
                history_text_2023 = (
                    f"2023 年 ({date_2023}): {icon_2023} "
                    f"{temp_min_2023:.1f}°C ~ {temp_max_2023:.1f}°C, "
                    f"降雨 {precip_2023:.1f}mm"
                )
                if wind_2023:
                    history_text_2023 += f", 風速 {wind_2023:.0f}km/h"
                self.history_2023_label.setText(history_text_2023)
        
    def _create_timeline_line(self) -> QFrame:
        """創建時間軸連接線"""
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #dee2e6; margin: 60px 0px;")
        line.setFixedWidth(40)
        return line


# Demo 主程式
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = RaceWeatherDemo2Timeline()
    widget.setWindowTitle("Demo 2: 時間軸式天氣預報")
    widget.resize(1000, 400)
    
    # 載入測試數據
    json_path = "json/weather/race_weather_forecast_2025_united_states_grand_prix_20251013T031246Z.json"
    if Path(json_path).exists():
        widget.load_weather_data(json_path)
    
    widget.show()
    sys.exit(app.exec_())
