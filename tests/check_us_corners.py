#!/usr/bin/env python3
"""檢查 United States JSON 的 official_corners 數據"""
import json

# 讀取 JSON 檔案
with open('json/historical_flags_United_States_2022-2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*70)
print("United States JSON 結構檢查")
print("="*70)

# 檢查頂層結構
print(f"\n1. 頂層鍵: {list(data.keys())}")

# 檢查 data 層級
print(f"\n2. data 層級的鍵: {list(data['data'].keys())}")

# 檢查 official_corners
official_corners = data['data']['official_corners']
print(f"\n3. official_corners 結構:")
print(f"   - available: {official_corners.get('available')}")
print(f"   - count: {official_corners.get('count')}")
print(f"   - corners 數組長度: {len(official_corners.get('corners', []))}")

# 檢查具體彎道數據
corners = official_corners.get('corners', [])
if corners:
    print(f"\n4. 彎道樣本:")
    print(f"   第 1 個彎道: {corners[0]}")
    print(f"   第 10 個彎道: {corners[9]}")
    print(f"   第 20 個彎道: {corners[-1]}")
    
    # 檢查所有彎道是否有有效座標
    invalid_corners = []
    for i, corner in enumerate(corners, 1):
        x = corner.get('x', 0)
        y = corner.get('y', 0)
        if x == 0 and y == 0:
            invalid_corners.append(i)
    
    if invalid_corners:
        print(f"\n⚠️  警告: 以下彎道的座標為 (0, 0): {invalid_corners}")
    else:
        print(f"\n✅ 所有 {len(corners)} 個彎道都有有效座標")
else:
    print("\n❌ 錯誤: corners 數組為空!")

# 比較 Brazil 的結構
print("\n" + "="*70)
print("Brazil JSON 結構檢查 (對照)")
print("="*70)

with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    brazil_data = json.load(f)

brazil_corners = brazil_data['data']['official_corners']
print(f"\nBrazil official_corners:")
print(f"   - available: {brazil_corners.get('available')}")
print(f"   - count: {brazil_corners.get('count')}")
print(f"   - corners 數組長度: {len(brazil_corners.get('corners', []))}")

if brazil_corners.get('corners'):
    print(f"   第 1 個彎道: {brazil_corners['corners'][0]}")
