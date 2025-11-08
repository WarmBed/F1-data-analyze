#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 DNF 顯示功能
- 測試 CLI Function 25 的 DNF 檢測
- 測試 GUI 模組的 DNF 渲染
"""

import sys
import json
from pathlib import Path

print("=" * 80)
print("🧪 測試 DNF 顯示功能")
print("=" * 80)

# ============================================================
# 測試 1: 驗證 CLI 輸出的 DNF 數據
# ============================================================
print("\n📋 測試 1: 驗證 CLI JSON 輸出")
print("-" * 80)

json_file = Path("json/driver_race_position_2024_Italy_R.json")

if not json_file.exists():
    print(f"❌ 找不到測試檔案: {json_file}")
    print("💡 請先執行: python f1_analysis_modular_main.py -f 25 -y 2024 -r Italy -s R")
    sys.exit(1)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 檢查 DNF 車手
all_drivers = data.get('all_drivers_position_analysis', {})
dnf_drivers = []
finished_drivers = []

for driver, info in all_drivers.items():
    finishing_pos = info.get('finishing_position')
    if finishing_pos == "DNF":
        dnf_drivers.append((driver, info.get('team', 'Unknown')))
    elif isinstance(finishing_pos, int):
        finished_drivers.append((driver, finishing_pos, info.get('team', 'Unknown')))

print(f"✅ 完賽車手: {len(finished_drivers)} 位")
print(f"✅ DNF 車手: {len(dnf_drivers)} 位")

if dnf_drivers:
    print("\n🚩 DNF 車手列表:")
    for driver, team in dnf_drivers:
        print(f"   - {driver} ({team}): DNF")
else:
    print("⚠️  沒有找到 DNF 車手（2024 Italy R 應該有 TSU 退賽）")

# ============================================================
# 測試 2: 測試 GUI Widget 的 DNF 處理
# ============================================================
print("\n" + "=" * 80)
print("📋 測試 2: GUI Widget DNF 處理")
print("-" * 80)

from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtCore import Qt

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# 導入 Widget
sys.path.insert(0, 'modules/gui/driver_position_analysis')
from driver_position_analysis_widget import DriverPositionAnalysisWidget

# 測試 _create_position_item() 方法
widget = DriverPositionAnalysisWidget()

print("\n🔍 測試 _create_position_item() 方法:")

# 測試案例 1: 正常位置
test_cases = [
    (1, "P1", 1, "正常位置 P1"),
    (10, "P10", 10, "正常位置 P10"),
    ("DNF", "DNF", 998, "DNF 狀態"),
    (None, "N/A", 999, "無數據 N/A"),
]

all_passed = True
for position_input, expected_text, expected_sort, description in test_cases:
    item = widget._create_position_item(position_input)
    actual_text = item.text()
    actual_sort = item.data(Qt.UserRole)  # 使用 UserRole 獲取排序值
    
    text_match = actual_text == expected_text
    sort_match = actual_sort == expected_sort
    
    if text_match and sort_match:
        print(f"   ✅ {description}")
        print(f"      輸入: {position_input} → 顯示: '{actual_text}' (排序: {actual_sort})")
    else:
        print(f"   ❌ {description}")
        print(f"      輸入: {position_input}")
        print(f"      預期: '{expected_text}' (排序: {expected_sort})")
        print(f"      實際: '{actual_text}' (排序: {actual_sort})")
        all_passed = False

# ============================================================
# 測試 3: 排序邏輯驗證
# ============================================================
print("\n" + "=" * 80)
print("📋 測試 3: DNF 排序邏輯")
print("-" * 80)

positions = [5, "DNF", 1, None, 10, 3]
items = [widget._create_position_item(pos) for pos in positions]

# 按照 UserRole 排序
sorted_items = sorted(items, key=lambda x: x.data(Qt.UserRole))
sorted_texts = [item.text() for item in sorted_items]

print(f"排序前: {positions}")
print(f"排序後: {sorted_texts}")

expected_order = ["P1", "P3", "P5", "P10", "DNF", "N/A"]
if sorted_texts == expected_order:
    print(f"✅ 排序正確: {expected_order}")
else:
    print(f"❌ 排序錯誤!")
    print(f"   預期: {expected_order}")
    print(f"   實際: {sorted_texts}")
    all_passed = False

# ============================================================
# 總結
# ============================================================
print("\n" + "=" * 80)
if all_passed and dnf_drivers:
    print("🎉 所有測試通過！DNF 功能運作正常")
    print("=" * 80)
    print("\n下一步：執行完整 GUI 測試")
    print("命令: python f1t_gui_main.py")
    sys.exit(0)
else:
    print("❌ 部分測試失敗，請檢查上方輸出")
    print("=" * 80)
    sys.exit(1)
