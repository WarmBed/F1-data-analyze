import sys
print('Starting...', flush=True)

from PyQt5.QtWidgets import QApplication
print('QApplication imported', flush=True)

app = QApplication(sys.argv)
print('App created', flush=True)

try:
    from modules.gui.lap_analysis.Throttle_analysis.throttle_line_chart_analysis.throttle_duration_chart_widget import ThrottleDurationChartWidget
    print('Widget imported successfully', flush=True)
    
    widget = ThrottleDurationChartWidget()
    print('Widget created', flush=True)
    print(f'Has update_series_multi_driver: {hasattr(widget, "update_series_multi_driver")}', flush=True)
    print(f'Has _get_driver_color: {hasattr(widget, "_get_driver_color")}', flush=True)
    
except Exception as e:
    print(f'Error: {e}', flush=True)
    import traceback
    traceback.print_exc()

print('Done', flush=True)
