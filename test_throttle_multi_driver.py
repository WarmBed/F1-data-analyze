# -*- coding: utf-8 -*-
"""測試 Throttle Line Chart 多車手功能"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

from modules.gui.lap_analysis.Throttle_analysis.throttle_line_chart_analysis.throttle_duration_chart_widget import ThrottleDurationChartWidget
print('Import successful!', flush=True)

# Test ThrottleDurationChartWidget methods
widget = ThrottleDurationChartWidget()
print('ThrottleDurationChartWidget created', flush=True)
print('Has update_series_multi_driver:', hasattr(widget, 'update_series_multi_driver'), flush=True)
print('Has _get_driver_color:', hasattr(widget, '_get_driver_color'), flush=True)
print('Has _should_use_dashed_line:', hasattr(widget, '_should_use_dashed_line'), flush=True)

# Test color helper
from PyQt5.QtGui import QColor
color = widget._get_driver_color('VER')
print(f'VER color: {color.name()}')

# Test dashed line detection
widget._team_color_usage = {}
dashed = widget._should_use_dashed_line('VER')
print(f'VER should use dashed (first): {dashed}')
dashed2 = widget._should_use_dashed_line('PER')
print(f'PER should use dashed (second Red Bull): {dashed2}')

# Test update_series_multi_driver
print('\nTesting update_series_multi_driver...')
test_data = {
    'VER': [
        {'lap_number': 1, 'full_throttle_ratio_percent': 65.0, 'average_throttle_percent': 55.0},
        {'lap_number': 2, 'full_throttle_ratio_percent': 68.0, 'average_throttle_percent': 58.0},
    ],
    'PER': [
        {'lap_number': 1, 'full_throttle_ratio_percent': 63.0, 'average_throttle_percent': 53.0},
        {'lap_number': 2, 'full_throttle_ratio_percent': 66.0, 'average_throttle_percent': 56.0},
    ],
}
test_tooltip = {
    'VER': {1: {'lap_number': 1}, 2: {'lap_number': 2}},
    'PER': {1: {'lap_number': 1}, 2: {'lap_number': 2}},
}

widget.update_series_multi_driver(
    all_drivers_data=test_data,
    all_tooltip_maps=test_tooltip,
    selected_drivers=['VER'],  # Only VER selected
    show_ratio=True,
    show_average=False,
)
print('update_series_multi_driver executed successfully!')
print(f'Number of data series: {len(widget.data_series)}')

print('\nAll tests passed!')
