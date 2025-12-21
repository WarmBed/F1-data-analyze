#!/usr/bin/env python3
"""
測試 Throttle Box Plot 右鍵 Filter 功能
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication

print("=" * 70)
print("測試 Throttle Box Plot 右鍵 Filter 功能")
print("=" * 70)

# 創建 QApplication
app = QApplication(sys.argv)

# 測試 1: 導入模組
print("\n[測試 1] 導入 ThrottleBoxPlotChartWidget...")
try:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_chart_widget import (
        ThrottleBoxPlotChartWidget
    )
    print("  ✅ ThrottleBoxPlotChartWidget 導入成功")
except Exception as e:
    print(f"  ❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 2: 檢查方法是否存在
print("\n[測試 2] 檢查新增方法...")
required_methods = [
    '_show_context_menu',
    '_hide_driver',
    'show_all_drivers'
]

widget = ThrottleBoxPlotChartWidget()

for method_name in required_methods:
    if hasattr(widget, method_name):
        print(f"  ✅ {method_name} 方法存在")
    else:
        print(f"  ❌ {method_name} 方法不存在")

# 測試 3: 檢查屬性
print("\n[測試 3] 檢查新增屬性...")
if hasattr(widget, 'hidden_drivers'):
    print(f"  ✅ hidden_drivers 屬性存在 (類型: {type(widget.hidden_drivers)})")
    if isinstance(widget.hidden_drivers, set):
        print(f"  ✅ hidden_drivers 是 set 類型")
    else:
        print(f"  ❌ hidden_drivers 不是 set 類型")
else:
    print("  ❌ hidden_drivers 屬性不存在")

# 測試 4: 測試隱藏功能
print("\n[測試 4] 測試隱藏車手功能...")
try:
    # 創建模擬數據
    test_data = {
        "driver_throttle_durations": {
            "VER": [85.5, 86.0, 84.8],
            "LEC": [83.2, 84.1, 83.8],
            "HAM": [82.5, 83.0, 82.8],
        },
        "statistics": {
            "VER": {"min": 84.8, "q1": 85.15, "median": 85.5, "q3": 85.75, "max": 86.0, "mean": 85.43, "count": 3},
            "LEC": {"min": 83.2, "q1": 83.5, "median": 83.8, "q3": 83.95, "max": 84.1, "mean": 83.7, "count": 3},
            "HAM": {"min": 82.5, "q1": 82.65, "median": 82.8, "q3": 82.9, "max": 83.0, "mean": 82.77, "count": 3},
        },
        "metadata": {}
    }
    
    widget.update_data(test_data)
    print(f"  ✅ 數據更新成功，共 {len(widget.driver_throttle_durations)} 位車手")
    
    # 測試隱藏功能
    widget._hide_driver("VER")
    if "VER" in widget.hidden_drivers:
        print("  ✅ VER 已加入隱藏集合")
    else:
        print("  ❌ VER 未加入隱藏集合")
    
    # 測試恢復功能
    widget.show_all_drivers()
    if len(widget.hidden_drivers) == 0:
        print("  ✅ show_all_drivers() 成功清空隱藏集合")
    else:
        print(f"  ❌ show_all_drivers() 未清空隱藏集合 (剩餘: {widget.hidden_drivers})")
    
except Exception as e:
    print(f"  ❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 5: 檢查 MDI 的 reset_chart_view
print("\n[測試 5] 檢查 MDI 的 reset_chart_view 方法...")
try:
    from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import (
        ThrottleBoxPlotAnalysis
    )
    print("  ✅ ThrottleBoxPlotAnalysis 導入成功")
    
    if hasattr(ThrottleBoxPlotAnalysis, 'reset_chart_view'):
        print("  ✅ reset_chart_view 方法存在")
    else:
        print("  ❌ reset_chart_view 方法不存在")
    
except Exception as e:
    print(f"  ❌ 導入失敗: {e}")

print("\n" + "=" * 70)
print("測試完成！")
print("=" * 70)
print("\n📝 下一步：啟動 GUI 進行手動測試")
print("   1. 執行: python f1t_gui_main.py")
print("   2. 開啟 Throttle Box Plot 分析模組")
print("   3. 右鍵點擊任意箱型圖 → 選擇 'Hide {DRIVER}'")
print("   4. 點擊主 GUI 的 'Show All Data' 按鈕 → 恢復隱藏車手")
