#!/usr/bin/env python3
"""
Race Weather Widget Demo 1: Card Style Layout
卡片式布局 - 三天預報卡片並排顯示

Author: F1T Team
Date: 2025-10-13
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QApplication, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class WeatherCardWidget(QFrame):
    """單日天氣卡片"""
    
    def __init__(self, day_label: str, parent=None):
        super().__init__(parent)
        self.day_label = day_label
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # 日期標籤
        self.date_label = QLabel(self.day_label, self)
        self.date_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0066cc;")
        self.date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.date_label)
        
        # 天氣圖示 (使用文字符號)
        self.weather_icon = QLabel("☀️", self)
        font = QFont()
        font.setPointSize(32)
        self.weather_icon.setFont(font)
        self.weather_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.weather_icon)
        
        # 溫度範圍
        self.temp_label = QLabel("--°C ~ --°C", self)
        self.temp_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.temp_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.temp_label)
        
        # 降雨機率
        self.rain_label = QLabel("降雨: --%", self)
        self.rain_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        self.rain_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.rain_label)
        
        # 風速風向
        self.wind_label = QLabel("風速: -- km/h", self)
        self.wind_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        self.wind_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.wind_label)
        
    def populate_data(self, day_data: Dict[str, Any]):
        """填充天氣數據"""
        summary = day_data.get("summary", {})
        
        # 日期
        date_str = day_data.get("date", "")
        self.date_label.setText(date_str)
        
        # 溫度
        temp_max = summary.get("temperature_max")
        temp_min = summary.get("temperature_min")
        if temp_max is not None and temp_min is not None:
            self.temp_label.setText(f"{temp_min:.1f}°C ~ {temp_max:.1f}°C")
        
        # 降雨量
        precip_sum = summary.get("precipitation_sum", 0)
        cloud_cover = summary.get("cloudcover_mean", 0)
        
        # 根據降雨量和雲量決定圖示
        if precip_sum > 5:
            self.weather_icon.setText("🌧️")
        elif precip_sum > 0:
            self.weather_icon.setText("🌦️")
        elif cloud_cover > 50:
            self.weather_icon.setText("☁️")
        elif cloud_cover > 20:
            self.weather_icon.setText("⛅")
        else:
            self.weather_icon.setText("☀️")
            
        self.rain_label.setText(f"降雨: {precip_sum:.1f} mm")
        
        # 風速風向
        wind_speed = summary.get("windspeed_max")
        wind_dir = summary.get("winddirection_cardinal", "")
        if wind_speed is not None:
            self.wind_label.setText(f"風速: {wind_speed:.1f} km/h ({wind_dir})")


class RaceWeatherDemo1CardStyle(QWidget):
    """
    Demo 1: 卡片式天氣預報
    
    特點：
    - 三天預報卡片並排顯示
    - 大字體溫度顯示
    - 天氣圖示直觀
    - 適合快速瀏覽
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
        title_label = QLabel("比賽週末天氣預報", self)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 三天預報卡片容器
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        
        # 創建三張卡片
        self.card_minus_2 = WeatherCardWidget("比賽前2天", self)
        self.card_minus_1 = WeatherCardWidget("比賽前1天", self)
        self.card_race_day = WeatherCardWidget("比賽當天", self)
        
        cards_layout.addWidget(self.card_minus_2)
        cards_layout.addWidget(self.card_minus_1)
        cards_layout.addWidget(self.card_race_day)
        
        layout.addLayout(cards_layout)
        
        # 歷史天氣對比
        self.history_label = QLabel("", self)
        self.history_label.setStyleSheet("font-size: 12px; color: #6c757d; margin-top: 8px;")
        layout.addWidget(self.history_label)
        
    def load_weather_data(self, json_path: str):
        """從 JSON 檔案載入天氣數據"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.weather_data = json.load(f)
            
            if self.weather_data.get("success"):
                self.populate_forecast()
                self.populate_history()
            else:
                print(f"Weather data load failed: {self.weather_data.get('message')}")
        except Exception as e:
            print(f"Error loading weather data: {e}")
            
    def populate_forecast(self):
        """填充預報數據"""
        if not self.weather_data:
            return
            
        forecast_days = self.weather_data.get("data", {}).get("forecast", {}).get("days", [])
        
        if len(forecast_days) >= 3:
            self.card_minus_2.populate_data(forecast_days[0])
            self.card_minus_1.populate_data(forecast_days[1])
            self.card_race_day.populate_data(forecast_days[2])
            
    def populate_history(self):
        """填充歷史天氣對比"""
        if not self.weather_data:
            return
            
        historical = self.weather_data.get("data", {}).get("historical", {}).get("entries", {})
        
        # 獲取去年和前年比賽當天的天氣
        last_year_data = historical.get("2024_race_minus_0", {}).get("summary", {})
        two_years_ago_data = historical.get("2023_race_minus_0", {}).get("summary", {})
        
        history_text = "歷史天氣對比: "
        
        if last_year_data:
            temp_max_2024 = last_year_data.get("temperature_max")
            precip_2024 = last_year_data.get("precipitation_sum", 0)
            if temp_max_2024:
                history_text += f"2024年: {temp_max_2024:.1f}°C, {precip_2024:.1f}mm | "
                
        if two_years_ago_data:
            temp_max_2023 = two_years_ago_data.get("temperature_max")
            precip_2023 = two_years_ago_data.get("precipitation_sum", 0)
            if temp_max_2023:
                history_text += f"2023年: {temp_max_2023:.1f}°C, {precip_2023:.1f}mm"
                
        self.history_label.setText(history_text)


# Demo 主程式
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = RaceWeatherDemo1CardStyle()
    widget.setWindowTitle("Demo 1: 卡片式天氣預報")
    widget.resize(800, 400)
    
    # 載入測試數據
    json_path = "json/weather/race_weather_forecast_2025_united_states_grand_prix_20251013T031246Z.json"
    if Path(json_path).exists():
        widget.load_weather_data(json_path)
    
    widget.show()
    sys.exit(app.exec_())
