#!/usr/bin/env python3
"""簡化測試: 只測試 Import 和基本方法"""

from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

print("測試 1: Widget Import")
from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_widget import IdealLapSectorHeatmapWidget
print("✅ Widget 導入成功")

print("\n測試 2: Widget 方法檢查")
widget = IdealLapSectorHeatmapWidget()
methods = ['set_data', 'render_heatmap', 'clear_data', 'get_current_data', 'save_plot']
for m in methods:
    exists = hasattr(widget, m)
    print(f"  {m}: {'✅' if exists else '❌'}")

print("\n測試 3: MDI Import")
from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi import IdealLapSectorHeatmapMDI
print("✅ MDI 導入成功")

print("\n測試 4: MDI 初始化")
mdi = IdealLapSectorHeatmapMDI()
print(f"✅ MDI 類型: {type(mdi.chart_widget).__name__}")

print("\n🎉 基本測試通過！")
