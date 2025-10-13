#!/usr/bin/env python3
"""
Race Weather Widget Demo 3: Table Style
資料表式布局 - 詳細數據表格顯示

Author: F1T Team
Date: 2025-10-13
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QApplication, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class RaceWeatherDemo3Table(QWidget):
    """
    Demo 3: 資料表式天氣預報
    
    特點：
    - 傳統表格式布局
    - 完整數據展示
    - 包含歷史對比
    - 適合數據分析用戶
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
        title_label = QLabel("比賽週末天氣詳細數據", self)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 賽事資訊
        self.event_info_label = QLabel("", self)
        self.event_info_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(self.event_info_label)
        
        # 數據表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "類型", "日期", "天氣", "溫度範圍", "降雨", "雲量", "風速", "濕度"
        ])
        
        # 表格樣式
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e7f3ff;
                color: #000;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #0066cc;
                font-weight: bold;
                color: #495057;
            }
        """)
        
        # 表頭設置
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # 圖例
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(20)
        
        legend_forecast = QLabel("■ 2025年預報", self)
        legend_forecast.setStyleSheet("color: #0066cc; font-size: 12px;")
        legend_layout.addWidget(legend_forecast)
        
        legend_history = QLabel("■ 歷史數據", self)
        legend_history.setStyleSheet("color: #6c757d; font-size: 12px;")
        legend_layout.addWidget(legend_history)
        
        legend_race = QLabel("■ 比賽日", self)
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
                self.populate_table()
        except Exception as e:
            print(f"Error loading weather data: {e}")
            
    def populate_table(self):
        """填充表格"""
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
        
        # 按年份和天數組織歷史數據
        for year in ["2024", "2023"]:
            for day_offset in ["race_minus_2", "race_minus_1", "race_minus_0"]:
                key = f"{year}_{day_offset}"
                if key in historical_dict:
                    entry_data = historical_dict[key]
                    entry_data["year"] = year
                    entry_data["day_label"] = day_offset
                    historical_entries.append(entry_data)
        
        # 設置表格行數
        total_rows = len(forecast_days) + len(historical_entries)
        self.table.setRowCount(total_rows)
        
        row = 0
        
        # 填充預報數據
        for day_data in forecast_days:
            label = day_data.get("label", "")
            date = day_data.get("date", "")
            summary = day_data.get("summary", {})
            
            # 類型
            if label == "race_minus_2":
                type_text = "預報 (前2天)"
                color = QColor("#0066cc")
            elif label == "race_minus_1":
                type_text = "預報 (前1天)"
                color = QColor("#0066cc")
            else:
                type_text = "預報 (比賽日)"
                color = QColor("#dc3545")
                
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(color)
            font = QFont()
            font.setBold(label == "race_day")
            type_item.setFont(font)
            self.table.setItem(row, 0, type_item)
            
            # 日期
            self.table.setItem(row, 1, QTableWidgetItem(date))
            
            # 天氣圖示
            precip = summary.get("precipitation_sum", 0)
            cloud = summary.get("cloudcover_mean", 0)
            if precip > 5:
                icon = "🌧️ 降雨"
            elif precip > 0:
                icon = "🌦️ 陣雨"
            elif cloud > 50:
                icon = "☁️ 多雲"
            elif cloud > 20:
                icon = "⛅ 局部雲"
            else:
                icon = "☀️ 晴天"
            self.table.setItem(row, 2, QTableWidgetItem(icon))
            
            # 溫度範圍
            temp_min = summary.get("temperature_min")
            temp_max = summary.get("temperature_max")
            if temp_min is not None and temp_max is not None:
                temp_text = f"{temp_min:.1f}°C ~ {temp_max:.1f}°C"
            else:
                temp_text = "無數據"
            self.table.setItem(row, 3, QTableWidgetItem(temp_text))
            
            # 降雨
            rain_text = f"{precip:.1f} mm"
            self.table.setItem(row, 4, QTableWidgetItem(rain_text))
            
            # 雲量
            cloud_text = f"{cloud:.0f}%"
            self.table.setItem(row, 5, QTableWidgetItem(cloud_text))
            
            # 風速
            wind_speed = summary.get("windspeed_max")
            wind_dir = summary.get("winddirection_cardinal", "")
            if wind_speed:
                wind_text = f"{wind_dir} {wind_speed:.0f} km/h"
            else:
                wind_text = "無數據"
            self.table.setItem(row, 6, QTableWidgetItem(wind_text))
            
            # 濕度
            humidity = summary.get("relativehumidity_mean")
            if humidity is not None:
                humidity_text = f"{humidity:.0f}%"
            else:
                humidity_text = "無數據"
            self.table.setItem(row, 7, QTableWidgetItem(humidity_text))
            
            row += 1
            
        # 填充歷史數據
        for entry in historical_entries:
            year_label = entry.get("year", "")
            date = entry.get("date", "")
            summary = entry.get("summary", {})
            
            # 類型
            type_item = QTableWidgetItem(f"歷史 ({year_label})")
            type_item.setForeground(QColor("#6c757d"))
            self.table.setItem(row, 0, type_item)
            
            # 日期
            self.table.setItem(row, 1, QTableWidgetItem(date))
            
            # 天氣圖示
            precip = summary.get("precipitation_sum", 0)
            cloud = summary.get("cloudcover_mean", 0)
            if precip > 5:
                icon = "🌧️ 降雨"
            elif precip > 0:
                icon = "🌦️ 陣雨"
            elif cloud > 50:
                icon = "☁️ 多雲"
            elif cloud > 20:
                icon = "⛅ 局部雲"
            else:
                icon = "☀️ 晴天"
            self.table.setItem(row, 2, QTableWidgetItem(icon))
            
            # 溫度範圍
            temp_min = summary.get("temperature_min")
            temp_max = summary.get("temperature_max")
            if temp_min is not None and temp_max is not None:
                temp_text = f"{temp_min:.1f}°C ~ {temp_max:.1f}°C"
            else:
                temp_text = "無數據"
            self.table.setItem(row, 3, QTableWidgetItem(temp_text))
            
            # 降雨
            rain_text = f"{precip:.1f} mm"
            self.table.setItem(row, 4, QTableWidgetItem(rain_text))
            
            # 雲量
            cloud_text = f"{cloud:.0f}%"
            self.table.setItem(row, 5, QTableWidgetItem(cloud_text))
            
            # 風速
            wind_speed = summary.get("windspeed_max")
            wind_dir = summary.get("winddirection_cardinal", "")
            if wind_speed:
                wind_text = f"{wind_dir} {wind_speed:.0f} km/h"
            else:
                wind_text = "無數據"
            self.table.setItem(row, 6, QTableWidgetItem(wind_text))
            
            # 濕度
            humidity = summary.get("relativehumidity_mean")
            if humidity is not None:
                humidity_text = f"{humidity:.0f}%"
            else:
                humidity_text = "無數據"
            self.table.setItem(row, 7, QTableWidgetItem(humidity_text))
            
            row += 1
            
        # 調整行高
        for i in range(self.table.rowCount()):
            self.table.setRowHeight(i, 40)


# Demo 主程式
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = RaceWeatherDemo3Table()
    widget.setWindowTitle("Demo 3: 資料表式天氣預報")
    widget.resize(1200, 500)
    
    # 載入測試數據
    json_path = "json/weather/race_weather_forecast_2025_united_states_grand_prix_20251013T031246Z.json"
    if Path(json_path).exists():
        widget.load_weather_data(json_path)
    
    widget.show()
    sys.exit(app.exec_())
