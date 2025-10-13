#!/usr/bin/env python3
"""
測試右鍵選單功能
"""

print("=" * 60)
print("右鍵選單功能測試")
print("=" * 60)

# 階段 1: Import 測試
print("\n[階段 1] Import 測試...")
try:
    from f1t_gui_main import CustomMdiArea
    print("✅ CustomMdiArea 載入成功")
except Exception as e:
    print(f"❌ CustomMdiArea 載入失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 階段 2: 方法驗證
print("\n[階段 2] 方法驗證...")
required_methods = [
    '_get_chart_widget',
    '_detect_module_type',
    '_show_axis_control_menu',
    '_reset_chart_view',
    '_show_axis_range_dialog',
    '_get_current_axis_range',
    '_set_axis_range',
    'contextMenuEvent',
]

missing_methods = []
for method_name in required_methods:
    if hasattr(CustomMdiArea, method_name):
        print(f"  ✅ {method_name} 存在")
    else:
        print(f"  ❌ {method_name} 缺失")
        missing_methods.append(method_name)

if missing_methods:
    print(f"\n❌ 缺少 {len(missing_methods)} 個方法")
    exit(1)
else:
    print(f"\n✅ 所有 {len(required_methods)} 個方法都存在")

# 階段 3: 模組類型檢測測試
print("\n[階段 3] 模組類型檢測測試...")
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
mdi = CustomMdiArea()

# 創建模擬 chart widget 進行測試
class MockSpeedWidget:
    pass
MockSpeedWidget.__name__ = 'SpeedChartWidget'

class MockBrakeWidget:
    pass
MockBrakeWidget.__name__ = 'BrakeChartWidget'

class MockRainWidget:
    pass
MockRainWidget.__name__ = 'RainAnalysisChartWidget'

test_cases = [
    (MockSpeedWidget(), 'speed_analysis'),
    (MockBrakeWidget(), 'brake_analysis'),
    (MockRainWidget(), 'rain_analysis'),
    (None, None),
]

for widget, expected_type in test_cases:
    detected_type = mdi._detect_module_type(widget)
    if detected_type == expected_type:
        print(f"  ✅ 檢測正確: {widget.__class__.__name__ if widget else 'None'} → {detected_type}")
    else:
        print(f"  ❌ 檢測錯誤: {widget.__class__.__name__ if widget else 'None'} → {detected_type} (期望: {expected_type})")

print("\n" + "=" * 60)
print("測試完成！")
print("=" * 60)
