"""測試 Sprint Session 映射是否正確"""
import sys
sys.path.insert(0, '.')

from modules.gui.shared.season_calendar_provider import SESSION_NAME_MAPPING

print("=" * 60)
print("測試 SESSION_NAME_MAPPING")
print("=" * 60)

# 檢查映射
sprint_mapping = [item for item in SESSION_NAME_MAPPING if "sprint" in item[0].lower()]
print(f"\n找到 {len(sprint_mapping)} 個 Sprint 相關映射：")
for pattern, code in sprint_mapping:
    print(f"  '{pattern}' → '{code}'")

# 測試映射函數
test_cases = [
    "Sprint Shootout",
    "Sprint Qualifying", 
    "Sprint",
    "SPRINT",
    "sprint",
]

print("\n" + "=" * 60)
print("測試映射函數")
print("=" * 60)

def map_session_code(name: str):
    """模擬 _map_session_code 邏輯"""
    lower_name = name.lower()
    for pattern, code in SESSION_NAME_MAPPING:
        if pattern in lower_name:
            return code
    return None

for test_name in test_cases:
    result = map_session_code(test_name)
    status = "✅" if result else "❌"
    print(f"{status} '{test_name}' → '{result}'")

print("\n" + "=" * 60)
print("測試 ordered_codes")
print("=" * 60)

# 直接讀取檔案內容
with open('modules/gui/shared/season_calendar_provider.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'ordered_codes = ["FP1", "FP2", "FP3", "FP4", "SQ", "S", "Q", "R"]' in content:
        print("✅ ordered_codes 包含 'S'")
    else:
        print("❌ ordered_codes 不包含 'S'")

print("\n測試完成！")
