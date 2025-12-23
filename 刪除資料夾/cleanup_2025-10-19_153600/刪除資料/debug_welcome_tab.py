#!/usr/bin/env python3
"""
調試 Welcome Tab 的賽事名稱提取
"""
import sys
from PyQt5.QtWidgets import QApplication, QComboBox

# 模擬 SeasonEvent
class SeasonEvent:
    def __init__(self, race_key, display_name, is_completed=True):
        self.race_key = race_key
        self.display_name = display_name
        self.is_completed = is_completed

# 創建測試應用
app = QApplication(sys.argv)

# 創建 race_combo
race_combo = QComboBox()

# 添加測試數據（模擬實際 GUI）
events = [
    SeasonEvent("bahrain", "Bahrain (2025-03-01)"),
    SeasonEvent("singapore", "Singapore (2025-10-05)"),
    SeasonEvent("united_states", "United States (2025-10-20)"),
]

for event in events:
    label = event.display_name
    race_combo.addItem(label, event)  # addItem(display_text, user_data)

# 設置當前索引為 Singapore
race_combo.setCurrentIndex(1)

print("=" * 70)
print("測試 race_combo 數據提取")
print("=" * 70)

# 方法 1: currentText() - 返回顯示文字
display_text = race_combo.currentText()
print(f"\n1. currentText() 返回:")
print(f"   {display_text}")
print(f"   ❌ 包含日期，不適合直接傳給 API")

# 方法 2: currentData() - 返回 user_data (SeasonEvent 物件)
event_data = race_combo.currentData()
print(f"\n2. currentData() 返回:")
print(f"   {event_data}")
print(f"   類型: {type(event_data)}")

if event_data and hasattr(event_data, 'race_key'):
    race_key = event_data.race_key
    # 轉換為標題格式
    race_name = race_key.replace('_', ' ').title()
    print(f"   race_key: {race_key}")
    print(f"   ✅ 轉換後: {race_name}")
    print(f"   ✅ 適合傳給 API")
else:
    print(f"   ❌ 無法取得 race_key")

# 方法 3: 降級方案（從顯示文字移除日期）
if '(' in display_text:
    fallback_race = display_text.split('(')[0].strip()
    print(f"\n3. 降級方案（從顯示文字提取）:")
    print(f"   原始: {display_text}")
    print(f"   提取: {fallback_race}")
    print(f"   ⚠️  僅在 currentData() 失敗時使用")

print("\n" + "=" * 70)
print("結論: 使用 currentData().race_key 並轉換為標題格式")
print("=" * 70)

# 測試所有賽事
print("\n所有賽事轉換測試:")
print("-" * 70)
for i in range(race_combo.count()):
    race_combo.setCurrentIndex(i)
    event = race_combo.currentData()
    if event and hasattr(event, 'race_key'):
        race_name = event.race_key.replace('_', ' ').title()
        print(f"{event.display_name:30s} → {race_name}")
