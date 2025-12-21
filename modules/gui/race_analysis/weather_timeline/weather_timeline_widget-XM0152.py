#!/usr/bin/env python3
"""
Weather Timeline Widget

Displays race weather forecast in timeline format with historical comparison

Author: F1T Team
Date: 2025-10-13
Version: 1.0.0
"""

import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.gui_i18n import tr


class TimelineNode(QFrame):
    """時間軸節點"""
    
    def __init__(self, date: str, parent=None):
        super().__init__(parent)
        self.date = date
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 設定統一字體
        font = QFont()
        font.setPointSize(8)
        
        # 日期標籤
        self.date_label = QLabel(self.date, self)
        self.date_label.setFont(font)
        self.date_label.setStyleSheet("color: #495057;")
        self.date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.date_label)
        
        # 溫度
        self.temp_label = QLabel(tr("weather_temp_loading", "--"), self)
        self.temp_label.setFont(font)
        self.temp_label.setStyleSheet("font-weight: bold; color: #000000;")
        self.temp_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.temp_label)
        
        # 天氣圖示
        self.weather_label = QLabel(tr("weather_icon_loading", "..."), self)
        icon_font = QFont()
        icon_font.setPointSize(16)
        self.weather_label.setFont(icon_font)
        self.weather_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.weather_label)
        
        # 降雨
        self.rain_label = QLabel(tr("weather_rain_loading", "--"), self)
        self.rain_label.setFont(font)
        self.rain_label.setStyleSheet("color: #6c757d;")
        self.rain_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.rain_label)
        
        # 風向風速
        self.wind_label = QLabel(tr("weather_wind_loading", "--"), self)
        self.wind_label.setFont(font)
        self.wind_label.setStyleSheet("color: #6c757d;")
        self.wind_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.wind_label)
        
        self.setFixedWidth(120)
        
    def populate_data(self, day_data: Dict[str, Any]):
        """填充數據"""
        summary = day_data.get("summary", {})
        
        # 溫度 (顯示最高溫)
        temp_max = summary.get("temperature_max")
        if temp_max is not None:
            self.temp_label.setText(tr("weather_temp_celsius", "{temp:.1f}°C").format(temp=temp_max))
            
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
            icon = "🌤️"   # 晴朗（彩色太陽）
        self.weather_label.setText(icon)
        
        self.rain_label.setText(tr("weather_rain_mm", "{precip:.1f}mm").format(precip=precip))
        
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
            self.wind_label.setText(tr("weather_wind_kmh", "{arrow} {speed:.0f}km/h").format(arrow=arrow, speed=wind_speed))


class WeatherTimelineWidget(QWidget):
    """
    Weather Timeline Summary Widget
    
    Displays race weekend weather forecast in timeline format:
    - 3-day forecast (race_minus_2, race_minus_1, race_day)
    - Visual weather icons
    - Temperature, precipitation, wind data
    - Historical comparison (2024 and 2023)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.weather_data: Optional[Dict[str, Any]] = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI 組件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # 標題 - 響應式字體
        self.title_label = QLabel(tr("weather_timeline_title", "比賽週末天氣時間軸"), self)
        self.title_label.setObjectName("weather_timeline_title")  # 用於響應式選擇器
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # 時間軸容器（固定大小，與 Season Progress 一致）
        timeline_container = QWidget(self)
        timeline_container_layout = QVBoxLayout(timeline_container)
        timeline_container_layout.setContentsMargins(0, 0, 0, 0)
        timeline_container_layout.setSpacing(0)
        
        # 時間軸內容
        timeline_widget = QWidget()
        self.timeline_layout = QHBoxLayout(timeline_widget)
        self.timeline_layout.setSpacing(0)
        self.timeline_layout.setContentsMargins(8, 4, 8, 8)
        
        timeline_container_layout.addWidget(timeline_widget)
        layout.addWidget(timeline_container)
        
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
        
        # 歷史數據標題 - 響應式字體
        self.history_title = QLabel(tr("weather_history_title", "歷史天氣對比"), self)
        self.history_title.setObjectName("weather_history_title")  # 用於響應式選擇器
        self.history_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #6c757d;")
        history_layout.addWidget(self.history_title)
        
        # 2024 和 2023 數據
        self.history_2024_label = QLabel("", self)
        self.history_2024_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        history_layout.addWidget(self.history_2024_label)
        
        self.history_2023_label = QLabel("", self)
        self.history_2023_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        history_layout.addWidget(self.history_2023_label)
        
        layout.addWidget(history_frame)
        
        # 添加彈性空間以防止內容被拉伸（與 Season Progress 一致）
        layout.addStretch(1)
    
    def populate_data(self, data: Dict[str, Any]):
        """
        Populate widget with weather data
        
        Args:
            data: Transformed weather data from DataLoader
        """
        self.weather_data = data
        self._populate_timeline()
        self._populate_historical_data()
        
    def _populate_timeline(self):
        """填充時間軸"""
        if not self.weather_data:
            return
            
        # 清除現有節點
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        forecast_days = self.weather_data.get("forecast_days", [])
        
        # 添加預報節點
        for i, day_data in enumerate(forecast_days):
            date = day_data.get("date", "")
            label = day_data.get("label", "")
            
            # 日期標籤
            if label == "race_minus_2":
                date_text = tr("weather_day_minus_2", "前2天\n{date}").format(date=date)
            elif label == "race_minus_1":
                date_text = tr("weather_day_minus_1", "前1天\n{date}").format(date=date)
            else:
                date_text = tr("weather_race_day", "比賽日\n{date}").format(date=date)
                
            node = TimelineNode(date_text, self)
            node.populate_data(day_data)
            
            self.timeline_layout.addWidget(node)
            
            # 添加連接線 (除了最後一個節點)
            if i < len(forecast_days) - 1:
                line = self._create_timeline_line()
                self.timeline_layout.addWidget(line)
                
        self.timeline_layout.addStretch()
        
    def _populate_historical_data(self):
        """填充歷史天氣數據"""
        if not self.weather_data:
            return
            
        historical_dict = self.weather_data.get("historical_entries", {})
        
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
                history_text_2024 = tr(
                    "weather_history_2024",
                    "2024 年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm"
                ).format(
                    date=date_2024,
                    icon=icon_2024,
                    temp_min=temp_min_2024,
                    temp_max=temp_max_2024,
                    precip=precip_2024
                )
                if wind_2024:
                    history_text_2024 += tr("weather_wind_speed", ", 風速 {speed:.0f}km/h").format(speed=wind_2024)
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
                history_text_2023 = tr(
                    "weather_history_2023",
                    "2023 年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm"
                ).format(
                    date=date_2023,
                    icon=icon_2023,
                    temp_min=temp_min_2023,
                    temp_max=temp_max_2023,
                    precip=precip_2023
                )
                if wind_2023:
                    history_text_2023 += tr("weather_wind_speed", ", 風速 {speed:.0f}km/h").format(speed=wind_2023)
                self.history_2023_label.setText(history_text_2023)
        
    def _create_timeline_line(self) -> QFrame:
        """創建時間軸連接線"""
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #dee2e6; margin: 60px 0px;")
        line.setFixedWidth(40)
        return line
    
    def resizeEvent(self, event):
        """響應視窗大小變化，自動調整字體大小"""
        super().resizeEvent(event)
        self._adjust_responsive_font()
    
    def _adjust_responsive_font(self):
        """根據視窗寬度調整字體大小"""
        width = self.width()
        
        # 定義響應式字體大小
        if width < 250:
            # 極小視窗: 主標題 12px, 次標題 9px, 內容 8px, 節點 7px
            title_size = 12
            subtitle_size = 9
            content_size = 8
            node_size = 7
            icon_size = 12
        elif width < 350:
            # 小視窗: 主標題 14px, 次標題 10px, 內容 9px, 節點 7px
            title_size = 14
            subtitle_size = 10
            content_size = 9
            node_size = 7
            icon_size = 14
        elif width < 450:
            # 中等視窗: 主標題 16px, 次標題 11px, 內容 10px, 節點 8px
            title_size = 16
            subtitle_size = 11
            content_size = 10
            node_size = 8
            icon_size = 15
        else:
            # 大視窗: 主標題 18px, 次標題 12px, 內容 11px, 節點 8px (預設)
            title_size = 18
            subtitle_size = 12
            content_size = 11
            node_size = 8
            icon_size = 16
        
        # 應用響應式樣式 - 主標題
        self.title_label.setStyleSheet(f"font-size: {title_size}px; font-weight: bold;")
        
        # 歷史標題
        self.history_title.setStyleSheet(f"font-size: {subtitle_size}px; font-weight: bold; color: #6c757d;")
        
        # 歷史內容
        self.history_2024_label.setStyleSheet(f"font-size: {content_size}px; color: #6c757d;")
        self.history_2023_label.setStyleSheet(f"font-size: {content_size}px; color: #6c757d;")
        
        # 更新時間軸節點字體
        for i in range(self.timeline_layout.count()):
            item = self.timeline_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, TimelineNode):
                # 更新節點內的標籤字體
                widget.date_label.setStyleSheet(f"font-size: {node_size}px; color: #495057;")
                widget.temp_label.setStyleSheet(f"font-size: {node_size}px; font-weight: bold; color: #000000;")
                widget.rain_label.setStyleSheet(f"font-size: {node_size}px; color: #6c757d;")
                widget.wind_label.setStyleSheet(f"font-size: {node_size}px; color: #6c757d;")
                
                # 調整天氣圖示大小
                icon_font = QFont()
                icon_font.setPointSize(icon_size)
                widget.weather_label.setFont(icon_font)


# Demo 測試
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = WeatherTimelineWidget()
    widget.setWindowTitle(tr("weather_test_window", "Weather Timeline Widget Test"))
    widget.resize(1000, 500)
    
    # 模擬數據
    test_data = {
        "forecast_days": [
            {
                "label": "race_minus_2",
                "date": "2025-10-17",
                "summary": {
                    "temperature_max": 22.5,
                    "temperature_min": 16.8,
                    "precipitation_sum": 2.3,
                    "cloudcover_mean": 65.5,
                    "windspeed_max": 28.5,
                    "winddirection_cardinal": "E"
                }
            },
            {
                "label": "race_minus_1",
                "date": "2025-10-18",
                "summary": {
                    "temperature_max": 19.2,
                    "temperature_min": 14.5,
                    "precipitation_sum": 8.7,
                    "cloudcover_mean": 85.2,
                    "windspeed_max": 35.8,
                    "winddirection_cardinal": "W"
                }
            },
            {
                "label": "race_day",
                "date": "2025-10-19",
                "summary": {
                    "temperature_max": 18.5,
                    "temperature_min": 13.2,
                    "precipitation_sum": 12.5,
                    "cloudcover_mean": 92.0,
                    "windspeed_max": 42.3,
                    "winddirection_cardinal": "NW"
                }
            }
        ],
        "historical_entries": {
            "2024_race_minus_0": {
                "date": "2024-10-20",
                "summary": {
                    "temperature_max": 30.2,
                    "temperature_min": 22.5,
                    "precipitation_sum": 0.5,
                    "cloudcover_mean": 25.5,
                    "windspeed_max": 18.7
                }
            },
            "2023_race_minus_0": {
                "date": "2023-10-22",
                "summary": {
                    "temperature_max": 24.2,
                    "temperature_min": 17.8,
                    "precipitation_sum": 5.5,
                    "cloudcover_mean": 75.2,
                    "windspeed_max": 32.5
                }
            }
        }
    }
    
    widget.populate_data(test_data)
    widget.show()
    sys.exit(app.exec_())
