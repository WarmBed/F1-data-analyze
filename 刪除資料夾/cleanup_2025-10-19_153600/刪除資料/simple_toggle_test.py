# -*- coding: utf-8 -*-
"""
簡化的時間軸切換測試 - 直接輸出到文件
"""
import sys
from PyQt5.QtWidgets import QApplication

# 直接打開輸出文件
output_file = open("toggle_test_output.txt", "w", encoding="utf-8")

def log(msg):
    """同時輸出到文件和終端"""
    print(msg)
    output_file.write(msg + "\n")
    output_file.flush()

log("="*80)
log("SIMPLIFIED TIME AXIS TOGGLE TEST")
log("="*80)

from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget

app = QApplication(sys.argv)

log("\n[1] Creating widget...")
widget = SpeedAnalysisChartWidget()

log("\n[2] Preparing test data...")
distance = list(range(0, 6000, 100))
speed1 = [150 + i * 2 for i in range(len(distance))]
speed2 = [140 + i * 2 for i in range(len(distance))]
time_data = [i * 0.1 for i in range(len(distance))]

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
        'drivers': [{'code': 'VER'}, {'code': 'LEC'}],
        'sectors': []
    },
    'statistics': {}
}

log("\n[3] Loading data...")
widget.update_speed_data(test_data)

log(f"\n[4] Initial state:")
log(f"  time_axis_available: {widget.chart_widget.time_axis_available}")
log(f"  use_time_axis: {widget.chart_widget.use_time_axis}")
log(f"  x_axis_title: {widget.chart_widget.x_axis_title}")
log(f"  checkbox exists: {hasattr(widget, 'time_axis_checkbox')}")

if hasattr(widget, 'time_axis_checkbox'):
    log(f"  checkbox enabled: {widget.time_axis_checkbox.isEnabled()}")
    log(f"  checkbox checked: {widget.time_axis_checkbox.isChecked()}")

log("\n"+ "="*80)
log("[5] TOGGLING CHECKBOX TO TIME AXIS...")
log("="*80)

if hasattr(widget, 'time_axis_checkbox') and widget.time_axis_checkbox:
    widget.time_axis_checkbox.setChecked(True)
    app.processEvents()
    
    log(f"\n[6] After toggle:")
    log(f"  use_time_axis: {widget.chart_widget.use_time_axis}")
    log(f"  x_axis_title: {widget.chart_widget.x_axis_title}")
    log(f"  checkbox checked: {widget.time_axis_checkbox.isChecked()}")
else:
    log("\nERROR: Checkbox not found!")

log("\n" + "="*80)
log("TEST COMPLETE")
log("="*80)

output_file.close()
print("\nOutput written to: toggle_test_output.txt")
