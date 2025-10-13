#!/usr/bin/env python3
"""
Demo 2 測試腳本 - 使用降雨天氣測試數據
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# 導入 Demo 2
from demo_weather_widget_02_timeline import RaceWeatherDemo2Timeline


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = RaceWeatherDemo2Timeline()
    widget.setWindowTitle("Demo 2: 時間軸式天氣預報 (降雨天氣測試)")
    widget.resize(1000, 500)
    
    # 載入測試數據（降雨天氣）
    test_json = "json/weather/test_rainy_weather_demo.json"
    if Path(test_json).exists():
        widget.load_weather_data(test_json)
        print(f"✅ 已載入測試數據: {test_json}")
    else:
        print(f"❌ 找不到測試數據: {test_json}")
    
    widget.show()
    sys.exit(app.exec_())
