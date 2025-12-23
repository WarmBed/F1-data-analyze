#!/usr/bin/env python3
"""
測試 Lap 參數匹配邏輯
"""

import json
from api.services.cache_service import F1AnalysisCacheService

# 初始化服務
cache_service = F1AnalysisCacheService()

# 載入測試 JSON
with open('json/comparison_telemetry_VER_LEC_2025_Australia_R_Lap1_Lap1.json', 'r', encoding='utf-8') as f:
    test_data = json.load(f)

print("=" * 80)
print("測試 Lap 參數匹配邏輯")
print("=" * 80)

print("\n📁 測試檔案 metadata:")
metadata = test_data.get('metadata', {})
for key, value in metadata.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 80)
print("測試案例 1: 請求 Lap1=1, Lap2=1 (應該匹配)")
print("=" * 80)

result = cache_service._result_matches_params(
    result=test_data,
    year=2025,
    race="Australia",
    session="R",
    driver1="VER",
    driver2="LEC",
    lap=None,
    lap1=1,
    lap2=1
)

print(f"\n匹配結果: {result}")
print(f"預期: True")
print(f"狀態: {'✅ 通過' if result else '❌ 失敗'}")

print("\n" + "=" * 80)
print("測試案例 2: 請求 Lap1=99, Lap2=99 (不應該匹配)")
print("=" * 80)

result = cache_service._result_matches_params(
    result=test_data,
    year=2025,
    race="Australia",
    session="R",
    driver1="VER",
    driver2="LEC",
    lap=None,
    lap1=99,
    lap2=99
)

print(f"\n匹配結果: {result}")
print(f"預期: False")
print(f"狀態: {'❌ 失敗 - 不應該匹配但卻匹配了！' if result else '✅ 通過'}")

print("\n" + "=" * 80)
print("測試案例 3: 請求 Lap1=52, Lap2=47 (不應該匹配)")
print("=" * 80)

result = cache_service._result_matches_params(
    result=test_data,
    year=2025,
    race="Australia",
    session="R",
    driver1="VER",
    driver2="LEC",
    lap=None,
    lap1=52,
    lap2=47
)

print(f"\n匹配結果: {result}")
print(f"預期: False")
print(f"狀態: {'❌ 失敗 - 不應該匹配但卻匹配了！' if result else '✅ 通過'}")

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)
