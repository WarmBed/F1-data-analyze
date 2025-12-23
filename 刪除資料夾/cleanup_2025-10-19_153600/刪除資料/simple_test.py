# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedTelemetryChartWidget

print("=== TIME AXIS TOGGLE TEST ===")
app = QApplication(sys.argv)
chart = SpeedTelemetryChartWidget()

print(f"\nINITIAL STATE:")
print(f"  use_time_axis: {chart.use_time_axis}")
print(f"  x_axis_title: {repr(chart.x_axis_title)}")

# Set data with time
distance = [0, 100, 200, 300, 400, 500]
speed1 = [150, 180, 220, 250, 280, 300]
speed2 = [140, 170, 210, 240, 270, 290]
time_data = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

chart.set_speed_data(distance, speed1, speed2, "VER", "LEC", time_data=time_data)

print(f"\nAFTER SET_DATA:")
print(f"  time_axis_available: {chart.time_axis_available}")
print(f"  x_axis_title: {repr(chart.x_axis_title)}")

# Toggle to time axis
success = chart.toggle_time_axis(True)

print(f"\nAFTER TOGGLE TO TIME:")
print(f"  success: {success}")
print(f"  use_time_axis: {chart.use_time_axis}")
print(f"  x_axis_title: {repr(chart.x_axis_title)}")

# Toggle back to distance
success = chart.toggle_time_axis(False)

print(f"\nAFTER TOGGLE TO DISTANCE:")
print(f"  success: {success}")
print(f"  use_time_axis: {chart.use_time_axis}")
print(f"  x_axis_title: {repr(chart.x_axis_title)}")

print("\n=== TEST COMPLETE ===")
