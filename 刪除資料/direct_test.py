# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedTelemetryChartWidget

# Write to file
with open("test_output_direct.txt", "w", encoding="utf-8") as f:
    f.write("=== TIME AXIS TOGGLE TEST ===\n")
    
    app = QApplication(sys.argv)
    chart = SpeedTelemetryChartWidget()
    
    f.write(f"\nINITIAL STATE:\n")
    f.write(f"  use_time_axis: {chart.use_time_axis}\n")
    f.write(f"  x_axis_title: {repr(chart.x_axis_title)}\n")
    
    # Set data with time
    distance = [0, 100, 200, 300, 400, 500]
    speed1 = [150, 180, 220, 250, 280, 300]
    speed2 = [140, 170, 210, 240, 270, 290]
    time_data = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
    
    chart.set_speed_data(distance, speed1, speed2, "VER", "LEC", time_data=time_data)
    
    f.write(f"\nAFTER SET_DATA:\n")
    f.write(f"  time_axis_available: {chart.time_axis_available}\n")
    f.write(f"  x_axis_title: {repr(chart.x_axis_title)}\n")
    
    # Toggle to time axis
    success = chart.toggle_time_axis(True)
    
    f.write(f"\nAFTER TOGGLE TO TIME:\n")
    f.write(f"  success: {success}\n")
    f.write(f"  use_time_axis: {chart.use_time_axis}\n")
    f.write(f"  x_axis_title: {repr(chart.x_axis_title)}\n")
    
    # Toggle back to distance
    success = chart.toggle_time_axis(False)
    
    f.write(f"\nAFTER TOGGLE TO DISTANCE:\n")
    f.write(f"  success: {success}\n")
    f.write(f"  use_time_axis: {chart.use_time_axis}\n")
    f.write(f"  x_axis_title: {repr(chart.x_axis_title)}\n")
    
    f.write("\n=== TEST COMPLETE ===\n")

print("Test results written to test_output_direct.txt")
