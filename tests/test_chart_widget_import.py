"""
測試 chart_widget 匯入 - 調試版本
"""

import sys

print("開始測試...")
print("[1] 匯入 typing...")
from typing import Dict

print("[2] 匯入 numpy...")
import numpy as np

print("[3] 匯入 PyQt5.QtWidgets...")
from PyQt5.QtWidgets import QWidget, QMessageBox

print("[4] 匯入 PyQt5.QtCore...")
from PyQt5.QtCore import Qt, QRect, pyqtSignal

print("[5] 匯入 PyQt5.QtGui...")
from PyQt5.QtGui import QPainter, QColor

print("[6] 匯入 core.gui_i18n...")
from core.gui_i18n import tr

print("[7] 匯入 themes...")
from modules.gui.themes import color_palette_provider

print("[8] 匯入 chart_widget 類別...")
try:
    from modules.gui.all_drivers_corner_box_plot_analysis.corner_low_speed_box_plot_chart_widget import (
        CornerLowSpeedBoxPlotChartWidget
    )
    print("✅ chart_widget 匯入成功！")
except Exception as e:
    print(f"❌ chart_widget 匯入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("所有測試完成！")
