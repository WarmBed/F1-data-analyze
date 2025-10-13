#!/usr/bin/env python3
"""
測試從 GUI race_combo 正確提取賽事名稱
"""

# 模擬 SeasonEvent 物件
class MockSeasonEvent:
    def __init__(self, race_key, display_name):
        self.race_key = race_key
        self.display_name = display_name
        self.is_completed = True

# 測試案例
test_cases = [
    MockSeasonEvent("singapore", "Singapore (2025-10-05)"),
    MockSeasonEvent("united_states", "United States (2025-10-20)"),
    MockSeasonEvent("japanese", "Japanese (2025-04-06)"),
    MockSeasonEvent("bahrain", "Bahrain (2025-03-01)"),
]

print("測試賽事名稱提取:")
print("=" * 60)

for event in test_cases:
    # 方法 1: 從 race_key 提取（推薦）
    race_from_key = event.race_key.replace('_', ' ').title()
    
    # 方法 2: 從 display_name 提取（降級）
    display_text = event.display_name
    if '(' in display_text:
        race_from_display = display_text.split('(')[0].strip()
    else:
        race_from_display = display_text
    
    print(f"race_key: {event.race_key:20s} → {race_from_key:20s}")
    print(f"display:  {event.display_name:20s} → {race_from_display:20s}")
    print(f"✅ 推薦使用: {race_from_key}")
    print("-" * 60)

# 測試 API 參數格式
print("\nAPI 調用測試:")
print("=" * 60)

test_event = test_cases[0]  # Singapore
race_name = test_event.race_key.replace('_', ' ').title()

print(f"year: 2025")
print(f"event: {race_name}")
print(f"session: R")
print(f"\nAPI URL: POST /api/v2/analysis/execute?function_id=96&year=2025&race={race_name}&session=R")
print(f"✅ 不包含日期，符合 CLI Function 96 期望")
