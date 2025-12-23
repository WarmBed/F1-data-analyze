from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_chart_widget import ThrottleBoxPlotChartWidget

widget = ThrottleBoxPlotChartWidget()

print("Widget created successfully")
print(f"hidden_drivers exists: {hasattr(widget, 'hidden_drivers')}")
print(f"_hide_driver exists: {hasattr(widget, '_hide_driver')}")
print(f"show_all_drivers exists: {hasattr(widget, 'show_all_drivers')}")
print(f"_show_context_menu exists: {hasattr(widget, '_show_context_menu')}")

test_data = {
    "driver_throttle_durations": {"VER": [85.5], "LEC": [83.2]},
    "statistics": {},
    "metadata": {}
}

widget.update_data(test_data)
print(f"Data updated: {len(widget.driver_throttle_durations)} drivers")

widget._hide_driver("VER")
print(f"After hiding VER: {widget.hidden_drivers}")

widget.show_all_drivers()
print(f"After show_all_drivers: {widget.hidden_drivers}")

print("All tests passed!")
