#!/usr/bin/env python3
"""測試 boxplot chart widget 導入路徑和內容"""

from modules.gui.lap_analysis.lap_box_plot.lap_box_plot_chart_widget import LapTimeBoxPlotChartWidget
import inspect

output = []
output.append("=" * 60)
output.append("Boxplot Chart Widget 導入測試")
output.append("=" * 60)

# 檢查檔案路徑
file_path = inspect.getfile(LapTimeBoxPlotChartWidget)
output.append(f"檔案路徑: {file_path}")

# 檢查源碼
src = inspect.getsource(LapTimeBoxPlotChartWidget._draw_single_box_plot)

output.append(f"有散點圖代碼: {'scatter' in src.lower() or 'jitter' in src.lower()}")
output.append(f"有 print 調試: {'print' in src}")

# 顯示前幾行
lines = src.split('\n')[:15]
output.append("\n方法前 15 行:")
for i, line in enumerate(lines):
    output.append(f"  {i+1}: {line}")

# 寫入檔案
with open('test_boxplot_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("結果已寫入 test_boxplot_result.txt")
