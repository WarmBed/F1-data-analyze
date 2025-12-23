#!/usr/bin/env python3
"""檢查所有短變體是否有類似的子字串匹配風險"""

import re

# 從 cache_service.py 複製的完整 race_name_variants
race_name_variants = {
    'bahrain': ['bahrain', 'bahraini', 'sakhir'],
    'saudi_arabia': ['saudi_arabia', 'saudi', 'jeddah'],
    'australia': ['australia', 'australian', 'albert_park', 'melbourne'],
    'japan': ['japan', 'japanese', 'suzuka'],
    'china': ['china', 'chinese', 'shanghai'],
    'miami': ['miami', 'miami_grand_prix'],
    'emilia_romagna': ['emilia_romagna', 'emilia-romagna', 'imola'],
    'monaco': ['monaco', 'monte_carlo'],
    'canada': ['canada', 'canadian', 'montreal'],
    'spain': ['spain', 'spanish', 'barcelona', 'catalunya'],
    'austria': ['austria', 'austrian', 'red_bull_ring', 'spielberg'],
    'great_britain': ['great_britain', 'britain', 'british', 'silverstone', 'uk'],
    'hungary': ['hungary', 'hungarian', 'hungaroring'],
    'belgium': ['belgium', 'belgian', 'spa'],
    'netherlands': ['netherlands', 'dutch', 'zandvoort'],
    'italy': ['italy', 'italian', 'monza'],
    'azerbaijan': ['azerbaijan', 'azerbaijani', 'baku'],
    'singapore': ['singapore', 'singaporean', 'marina_bay'],
    'united_states': ['united_states', 'us', 'american', 'austin', 'cota'],
    'mexico': ['mexico', 'mexican', 'mexico_city'],
    'brazil': ['brazil', 'brazilian', 'sao_paulo', 'interlagos'],
    'las_vegas': ['las_vegas', 'vegas', 'las vegas'],
    'qatar': ['qatar', 'qatari', 'losail'],
    'abu_dhabi': ['abu_dhabi', 'abu dhabi', 'yas_marina']
}

# 收集所有短變體（3個字符或更少）
short_tokens = []
for race, variants in race_name_variants.items():
    for variant in variants:
        token = variant.lower().replace(" ", "_").replace("-", "_")
        if len(token) <= 3:
            short_tokens.append((race, token))

print("=" * 80)
print("🔍 短變體子字串匹配風險分析")
print("=" * 80)
print(f"\n找到 {len(short_tokens)} 個短變體（≤3 字符）：")

for race, token in sorted(short_tokens, key=lambda x: (len(x[1]), x[1])):
    print(f"  {token:10s} ({len(token)} chars) → {race}")

print("\n" + "=" * 80)
print("🧪 測試短變體在所有賽事名稱中的子字串匹配風險")
print("=" * 80)

risks_found = []

for test_race, test_token in short_tokens:
    # 檢查此變體是否會匹配到其他賽事名稱
    for other_race in race_name_variants.keys():
        if other_race == test_race:
            continue
        
        race_name_lower = other_race.lower()
        
        # 舊版本的簡單子字串檢查
        if test_token in race_name_lower:
            risks_found.append({
                'token': test_token,
                'source_race': test_race,
                'matches': other_race,
                'position': race_name_lower.find(test_token)
            })

if risks_found:
    print(f"\n⚠️  發現 {len(risks_found)} 個潛在風險：\n")
    for risk in risks_found:
        print(f"❌ 變體 '{risk['token']}' ({risk['source_race']})")
        print(f"   → 會錯誤匹配到 '{risk['matches']}' (位置: {risk['position']})")
        print(f"   → 檔案範例: race_data_2025_{risk['matches']}_R.json\n")
else:
    print("\n✅ 沒有發現其他潛在風險！")

print("=" * 80)
print("💡 修復驗證")
print("=" * 80)

# 測試修復後的邏輯
def test_word_boundary(token, file_name):
    """測試單詞邊界匹配"""
    pattern = r'(?:^|_)' + re.escape(token) + r'(?:_|\.json$|$)'
    return bool(re.search(pattern, file_name))

print("\n測試修復後的單詞邊界匹配：")
for risk in risks_found[:5]:  # 只測試前5個
    file_name = f"race_data_2025_{risk['matches']}_r.json"
    old_match = risk['token'] in file_name.lower()
    new_match = test_word_boundary(risk['token'], file_name.lower())
    
    print(f"\n檔案: {file_name}")
    print(f"  變體: '{risk['token']}' (來自 {risk['source_race']})")
    print(f"  舊版匹配: {old_match} {'❌' if old_match else '✅'}")
    print(f"  新版匹配: {new_match} {'❌ 仍然錯誤' if new_match else '✅ 已修復'}")

print("\n" + "=" * 80)
