#!/usr/bin/env python3
"""測試 United States 緩存匹配錯誤問題"""

# 模擬 cache_service 的邏輯
race_name_variants = {
    'australia': ['australia', 'australian', 'australian_grand_prix'],
    'united_states': ['united_states', 'us', 'american', 'austin', 'cota'],
}

race_name_lookup = {}
for standard_name, variants in race_name_variants.items():
    for variant in variants:
        race_name_lookup[variant.lower()] = standard_name

# 測試 'United States' 的標準化
race = 'United States'
race_lower = race.lower().replace(' ', '_').replace('-', '_')
normalized = race_name_lookup.get(race_lower, race_lower)

print("=" * 70)
print("🚨 United States 緩存匹配錯誤診斷")
print("=" * 70)

print(f'\n📝 輸入賽事: {race}')
print(f'   小寫化: {race_lower}')
print(f'   標準化: {normalized}')
print(f'   變體列表: {race_name_variants.get(normalized, [])}')

# 測試檔案名稱匹配
file_name = 'all_incidents_summary_2025_Australia_R.json'.lower().replace('-', '_').replace(' ', '_')
print(f'\n📄 測試檔案: all_incidents_summary_2025_Australia_R.json')
print(f'   處理後: {file_name}')

# 檢查是否匹配
variants = set(race_name_variants.get(normalized, []))
variants.add(normalized)
print(f'\n🔍 搜尋變體: {variants}')

print(f'\n驗證每個變體是否匹配:')
for variant in variants:
    token = variant.lower().replace(' ', '_')
    is_match = token in file_name
    status = '❌ 錯誤匹配！' if is_match else '✅ 正確不匹配'
    print(f'  {status} 變體 "{token}" → in "{file_name}": {is_match}')

# 檢查子字串問題
print(f'\n🔬 子字串檢查 (這就是問題所在):')
print(f'  "american" in "{file_name}": {"american" in file_name}')
print(f'  "us" in "{file_name}": {"us" in file_name}')  # ⚠️ 這個是關鍵！
print(f'  "austin" in "{file_name}": {"austin" in file_name}')
print(f'  "australia" in "{file_name}": {"australia" in file_name}')

print(f'\n🚨 **問題根源**:')
print(f'  檔案名稱 "australia" 包含子字串 "us"!')
print(f'  因為 "united_states" 的變體中有 "us"')
print(f'  而 "australia" 字面上包含 "us" (a-u-s-tralia)')
print(f'  導致錯誤匹配！')

print(f'\n💡 解決方案:')
print(f'  1. 使用完整單詞匹配 (word boundary)')
print(f'  2. 禁止使用 "us" 這種超短變體')
print(f'  3. 使用更嚴格的分隔符檢查')
