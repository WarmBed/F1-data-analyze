# -*- coding: utf-8 -*-
"""
完整的時間軸切換日誌測試
追蹤從 checkbox 點擊到畫面更新的完整流程
"""
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 配置詳細日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('time_axis_toggle_trace.log', mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("f1.console")
logger.setLevel(logging.DEBUG)

print("=" * 100)
print("TIME AXIS TOGGLE COMPLETE TRACE TEST")
print("=" * 100)
print("Logging to: time_axis_toggle_trace.log")
print("")

from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import (
    SpeedTelemetryChartWidget,
    SpeedAnalysisChartWidget
)

app = QApplication(sys.argv)

# 創建完整的圖表組件（包含 checkbox）
print("\n[MAIN] Creating SpeedAnalysisChartWidget (with checkbox)...")
widget = SpeedAnalysisChartWidget()

# 設定測試數據
print("[MAIN] Setting test data with time series...")
distance = list(range(0, 6000, 100))  # 0-5900m, 每100m一個點
speed1 = [150 + i * 2 for i in range(len(distance))]
speed2 = [140 + i * 2 for i in range(len(distance))]
time_data = [i * 0.1 for i in range(len(distance))]  # 0-5.9秒

test_data = {
    'speed_data': {
        'distance': distance,
        'driver1_speed': speed1,
        'driver2_speed': speed2,
        'driver1_name': 'VER',
        'driver2_name': 'LEC'
    },
    'time_series': {
        'driver1': {
            'channels': {
                'Speed': {
                    'time_seconds': time_data
                }
            }
        }
    },
    'metadata': {
        'drivers': [
            {'code': 'VER'},
            {'code': 'LEC'}
        ],
        'sectors': []
    },
    'statistics': {}
}

widget.update_speed_data(test_data)

print("\n[MAIN] Data loaded. Chart state:")
print(f"  chart_widget.time_axis_available: {widget.chart_widget.time_axis_available}")
print(f"  chart_widget.use_time_axis: {widget.chart_widget.use_time_axis}")
print(f"  chart_widget.x_axis_title: {widget.chart_widget.x_axis_title}")
print(f"  time_axis_checkbox exists: {hasattr(widget, 'time_axis_checkbox')}")
print(f"  time_axis_checkbox enabled: {widget.time_axis_checkbox.isEnabled() if hasattr(widget, 'time_axis_checkbox') else 'N/A'}")

# 模擬使用者勾選 checkbox
print("\n" + "=" * 100)
print("[MAIN] SIMULATING USER CHECKBOX TOGGLE...")
print("=" * 100)
print("")

if hasattr(widget, 'time_axis_checkbox') and widget.time_axis_checkbox:
    print("[MAIN] Triggering checkbox stateChanged signal...")
    widget.time_axis_checkbox.setChecked(True)
    print("[MAIN] Checkbox toggled to: CHECKED")
    
    # 強制處理事件
    app.processEvents()
    
    print("\n[MAIN] After toggle:")
    print(f"  chart_widget.use_time_axis: {widget.chart_widget.use_time_axis}")
    print(f"  chart_widget.x_axis_title: {widget.chart_widget.x_axis_title}")
else:
    print("[MAIN] ERROR: time_axis_checkbox not found!")

print("\n" + "=" * 100)
print("TEST COMPLETE - Check time_axis_toggle_trace.log for detailed trace")
print("=" * 100)
