"""
最簡化的低速彎道箱型圖測試
直接測試 chart_widget 繪圖功能
"""

import sys
from pathlib import Path

# 確保可以匯入專案模組
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

print("=" * 80)
print(" 低速彎道箱型圖 - 簡化測試（僅測試圖表組件）")
print("=" * 80)
print()

# 創建 Qt 應用程式
print("[1/2] 創建 Qt 應用程式...")
app = QApplication(sys.argv)
print("      ✅ Qt 應用程式已創建")

# 創建主視窗
print("[2/2] 創建圖表視窗...")
main_window = QMainWindow()
main_window.setWindowTitle("F1T - Low-Speed Corner Box Plot (Chart Only)")
main_window.setGeometry(100, 100, 1000, 700)

# 直接匯入並創建 chart widget
print("  → 匯入 chart widget...")
try:
    from modules.gui.all_drivers_corner_box_plot_analysis.corner_low_speed_box_plot_chart_widget import (
        CornerLowSpeedBoxPlotChartWidget
    )
    print("      ✅ Chart widget 匯入成功")
except Exception as exc:
    print(f"      ❌ Chart widget 匯入失敗: {exc}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("  → 創建 chart widget 實例...")
chart_widget = CornerLowSpeedBoxPlotChartWidget()
main_window.setCentralWidget(chart_widget)
print("      ✅ Chart widget 已創建")

# 準備測試數據
print()
print("  → 準備測試數據...")
test_data = {
    "driver_apex_speeds": {
        "VER": [68.2, 68.5, 67.9, 68.3, 68.1],
        "PER": [67.5, 67.8, 67.3, 67.6, 67.4],
        "LEC": [68.0, 68.2, 67.8, 68.1, 67.9],
        "SAI": [67.3, 67.5, 67.1, 67.4, 67.2],
    },
    "corner_info": {
        "corner_name": "T13 (Test Data)",
        "corner_type": "low_speed",
    }
}

print("  → 更新圖表數據...")
chart_widget.update_data(test_data)
print("      ✅ 圖表數據已更新")

print()
print("=" * 80)
print(" 🚀 圖表視窗已啟動（僅顯示圖表，無控制面板）")
print("=" * 80)
print()
print("📊 測試數據:")
print("  - VER: 5 個樣本")
print("  - PER: 5 個樣本")
print("  - LEC: 5 個樣本")
print("  - SAI: 5 個樣本")
print()
print("✅ 如果看到箱型圖，表示繪圖功能正常")
print("❌ 如果崩潰或空白，表示需要修正 chart_widget")
print()

# 顯示視窗
main_window.show()

# 啟動事件循環
sys.exit(app.exec_())
