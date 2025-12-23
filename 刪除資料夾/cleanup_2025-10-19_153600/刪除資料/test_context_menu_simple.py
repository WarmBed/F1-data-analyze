#!/usr/bin/env python3
"""
簡化的右鍵選單測試 - 只測試方法存在性
"""

print("測試開始...")

# 直接讀取文件內容檢查
with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

required_methods = [
    'def _get_chart_widget(',
    'def _detect_module_type(',
    'def _show_axis_control_menu(',
    'def _reset_chart_view(',
    'def _show_axis_range_dialog(',
    'def _get_current_axis_range(',
    'def _set_axis_range(',
]

print("\n檢查方法定義:")
for method in required_methods:
    if method in content:
        print(f"  ✅ {method.strip('(').strip()} 已定義")
    else:
        print(f"  ❌ {method.strip('(').strip()} 未找到")

# 檢查模組類型檢測邏輯
print("\n檢查模組類型檢測:")
module_types = [
    'speed_analysis',
    'brake_analysis',
    'throttle_analysis',
    'rain_analysis',
    'laptime_boxplot',
    'detailed_lap_table',
    'throttle_boxplot',
    'throttle_line_chart',
]

for mod_type in module_types:
    if f"'{mod_type}'" in content:
        print(f"  ✅ {mod_type} 類型檢測已實現")
    else:
        print(f"  ❌ {mod_type} 類型檢測未實現")

# 檢查選單項目
print("\n檢查選單項目:")
menu_items = [
    'Reset View',
    'Set X-Axis Range',
    'Set Y-Axis Range',
    'Close Window',
]

for item in menu_items:
    if item in content:
        print(f"  ✅ '{item}' 選單項已添加")
    else:
        print(f"  ❌ '{item}' 選單項未找到")

print("\n測試完成！")
