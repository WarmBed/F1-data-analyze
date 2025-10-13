#!/usr/bin/env python3
"""
Race Weather Widget Demo Gallery
天氣 Widget 展示廳 - 展示所有 5 種風格

Author: F1T Team
Date: 2025-10-13
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 導入所有 Demo
from demo_weather_widget_01_card_style import RaceWeatherDemo1CardStyle
from demo_weather_widget_02_timeline import RaceWeatherDemo2Timeline
from demo_weather_widget_03_table import RaceWeatherDemo3Table
from demo_weather_widget_04_chart import RaceWeatherDemo4Chart
from demo_weather_widget_05_compact import RaceWeatherDemo5Compact


class WeatherDemoGallery(QMainWindow):
    """天氣 Widget Demo 展示廳"""
    
    def __init__(self):
        super().__init__()
        self.current_json_path = None
        self._init_ui()
        self._load_default_data()
        
    def _init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("F1T 天氣 Widget Demo 展示廳")
        self.resize(1400, 800)
        
        # 主要容器
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 標題
        title_label = QLabel("F1T Race Weather Widget - 5 種風格展示", self)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 說明
        desc_label = QLabel(
            "以下展示 5 種不同風格的天氣預報 Widget，請選擇您喜歡的風格以整合至主 GUI",
            self
        )
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # 載入數據按鈕
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.load_btn = QPushButton("載入天氣 JSON 檔案", self)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        self.load_btn.clicked.connect(self._load_custom_data)
        button_layout.addWidget(self.load_btn)
        
        self.current_file_label = QLabel("當前檔案: 無", self)
        self.current_file_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        button_layout.addWidget(self.current_file_label)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Tab Widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 10px 20px;
                margin-right: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                color: #0066cc;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Demo 1: Card Style
        self.demo1 = RaceWeatherDemo1CardStyle()
        self.tab_widget.addTab(self.demo1, "Demo 1: 卡片式")
        
        # Demo 2: Timeline
        self.demo2 = RaceWeatherDemo2Timeline()
        self.tab_widget.addTab(self.demo2, "Demo 2: 時間軸式")
        
        # Demo 3: Table
        self.demo3 = RaceWeatherDemo3Table()
        self.tab_widget.addTab(self.demo3, "Demo 3: 資料表式")
        
        # Demo 4: Chart
        self.demo4 = RaceWeatherDemo4Chart()
        self.tab_widget.addTab(self.demo4, "Demo 4: 圖表式")
        
        # Demo 5: Compact
        self.demo5 = RaceWeatherDemo5Compact()
        self.tab_widget.addTab(self.demo5, "Demo 5: 緊湊式")
        
        layout.addWidget(self.tab_widget)
        
        # 底部資訊
        info_layout = QHBoxLayout()
        
        info_labels = [
            ("Demo 1: 卡片式", "3 個天氣卡片橫向排列，視覺化天氣圖示，包含歷史對比"),
            ("Demo 2: 時間軸式", "橫向時間軸展示，節點連接線，突出比賽日"),
            ("Demo 3: 資料表式", "完整數據表格，詳細資訊展示，適合數據分析"),
            ("Demo 4: 圖表式", "溫度曲線與降雨柱狀圖，歷史數據虛線對比"),
            ("Demo 5: 緊湊式", "最小空間佔用，可折疊區塊，快速瀏覽模式")
        ]
        
        for title, desc in info_labels:
            label = QLabel(f"● {title}\n  {desc}", self)
            label.setStyleSheet("font-size: 10px; color: #6c757d;")
            info_layout.addWidget(label)
            
        layout.addLayout(info_layout)
        
    def _load_default_data(self):
        """載入預設數據"""
        default_path = "json/weather/race_weather_forecast_2025_united_states_grand_prix_20251013T031246Z.json"
        
        if Path(default_path).exists():
            self._load_data(default_path)
        else:
            QMessageBox.warning(
                self,
                "找不到預設數據",
                f"找不到預設天氣 JSON 檔案：\n{default_path}\n\n"
                "請使用「載入天氣 JSON 檔案」按鈕選擇檔案。"
            )
            
    def _load_custom_data(self):
        """載入自訂數據"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇天氣 JSON 檔案",
            "json/weather",
            "JSON 檔案 (*.json)"
        )
        
        if file_path:
            self._load_data(file_path)
            
    def _load_data(self, json_path: str):
        """載入數據到所有 Demo"""
        try:
            self.current_json_path = json_path
            
            # 載入到所有 Demo
            self.demo1.load_weather_data(json_path)
            self.demo2.load_weather_data(json_path)
            self.demo3.load_weather_data(json_path)
            self.demo4.load_weather_data(json_path)
            self.demo5.load_weather_data(json_path)
            
            # 更新檔案標籤
            file_name = Path(json_path).name
            self.current_file_label.setText(f"當前檔案: {file_name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "載入失敗",
                f"載入天氣數據時發生錯誤：\n{str(e)}"
            )


# Demo 主程式
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    gallery = WeatherDemoGallery()
    gallery.show()
    
    sys.exit(app.exec_())
