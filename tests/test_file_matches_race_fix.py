#!/usr/bin/env python3
"""測試修復後的 _file_matches_race 函數"""

import re

def _file_matches_race_OLD(file_path: str, race: str, race_name_variants: dict) -> bool:
    """舊版本 - 有 BUG"""
    race_name_lookup = {}
    for standard_name, variants in race_name_variants.items():
        for variant in variants:
            race_name_lookup[variant.lower()] = standard_name
    
    if not race or race == "*":
        return True

    race_lower = race.lower().replace(' ', '_').replace('-', '_')
    normalized_target = race_name_lookup.get(race_lower, race_lower)
    variants = set(race_name_variants.get(normalized_target, []))
    variants.add(normalized_target)
    file_name = file_path.lower().replace("-", "_").replace(" ", "_")

    for variant in variants:
        token = variant.lower().replace(" ", "_")
        if token and token in file_name:
            return True

    return False

def _file_matches_race_NEW(file_path: str, race: str, race_name_variants: dict) -> bool:
    """新版本 - 已修復"""
    race_name_lookup = {}
    for standard_name, variants in race_name_variants.items():
        for variant in variants:
            race_name_lookup[variant.lower()] = standard_name
    
    if not race or race == "*":
        return True

    race_lower = race.lower().replace(' ', '_').replace('-', '_')
    normalized_target = race_name_lookup.get(race_lower, race_lower)
    variants = set(race_name_variants.get(normalized_target, []))
    variants.add(normalized_target)
    file_name = file_path.lower().replace("-", "_").replace(" ", "_")

    for variant in variants:
        token = variant.lower().replace(" ", "_")
        if not token:
            continue
        
        # 🔧 FIX: 使用單詞邊界匹配
        pattern = r'(?:^|_)' + re.escape(token) + r'(?:_|\.json$|$)'
        if re.search(pattern, file_name):
            return True

    return False

# 測試資料
race_name_variants = {
    'australia': ['australia', 'australian', 'australian_grand_prix'],
    'united_states': ['united_states', 'us', 'american', 'austin', 'cota'],
    'japan': ['japan', 'japanese', 'japanese_grand_prix'],
}

test_cases = [
    # (檔案名稱, 請求賽事, 預期結果)
    ("all_incidents_summary_2025_Australia_R.json", "United States", False),  # ⚠️ 關鍵測試
    ("all_incidents_summary_2025_Australia_R.json", "Australia", True),
    ("track_path_analysis_2025_United_States_R.json", "United States", True),
    ("track_path_analysis_2025_Austin_R.json", "United States", True),
    ("track_path_analysis_2025_COTA_R.json", "United States", True),
    ("track_path_analysis_2025_Japan_R.json", "Japan", True),
    ("track_path_analysis_2025_Japan_R.json", "United States", False),
    ("rain_analysis_2025_US_Grand_Prix_R.json", "United States", True),
]

print("=" * 80)
print("🧪 _file_matches_race 修復驗證測試")
print("=" * 80)

print("\n測試結果:")
all_passed = True

for file_name, race, expected in test_cases:
    old_result = _file_matches_race_OLD(file_name, race, race_name_variants)
    new_result = _file_matches_race_NEW(file_name, race, race_name_variants)
    
    old_status = "✅" if old_result == expected else "❌"
    new_status = "✅" if new_result == expected else "❌"
    
    if new_result != expected:
        all_passed = False
    
    print(f"\n檔案: {file_name}")
    print(f"  請求賽事: {race}")
    print(f"  預期結果: {expected}")
    print(f"  舊版結果: {old_result} {old_status}")
    print(f"  新版結果: {new_result} {new_status}")
    
    if old_result != new_result:
        print(f"  🔧 修復: {'修正錯誤匹配' if not expected and old_result else '行為已變更'}")

print("\n" + "=" * 80)
if all_passed:
    print("✅ 所有測試通過！修復成功！")
else:
    print("❌ 部分測試失敗，需要進一步調整")
print("=" * 80)

# 特別顯示關鍵修復
print("\n🎯 關鍵修復驗證:")
print("  檔案: all_incidents_summary_2025_Australia_R.json")
print("  請求: United States")
old_match = _file_matches_race_OLD("all_incidents_summary_2025_Australia_R.json", "United States", race_name_variants)
new_match = _file_matches_race_NEW("all_incidents_summary_2025_Australia_R.json", "United States", race_name_variants)
print(f"  舊版: {old_match} {'❌ 錯誤匹配' if old_match else '✅'}")
print(f"  新版: {new_match} {'❌ 仍然錯誤' if new_match else '✅ 已修復'}")
