#!/usr/bin/env python3
"""測試跨賽事比較 API 的數據格式"""

import requests
import json

# 呼叫 API
print("🔄 呼叫跨賽事比較 API...")
response = requests.post(
    'https://api.f1telemetrystationpro.org/api/v2/analysis/cross-event-comparison',
    params={
        'driver1': 'NOR',
        'year1': '2025',
        'race1': 'Australia',
        'session1': 'R',
        'lap1': '99',
        'driver2': 'VER',
        'year2': '2025',
        'race2': 'Australia',
        'session2': 'Q',
        'lap2': '99'
    },
    timeout=30
)

data = response.json()

# 檢查結構
print("\n=== API Response Structure ===")
print(f"Top-level keys: {list(data.keys())}")

print("\n=== Data Keys ===")
data_dict = data.get('data', {})
print(f"data keys: {list(data_dict.keys())}")

print("\n=== Telemetry Comparison Keys ===")
tc = data_dict.get('telemetry_comparison', {})
print(f"telemetry_comparison keys: {list(tc.keys())}")

# 檢查 Speeddiff
if 'Speeddiff' in tc:
    print("\n=== Speeddiff Structure ===")
    speeddiff = tc['Speeddiff']
    print(f"Speeddiff keys: {list(speeddiff.keys())}")
    print(f"speed_difference 點數: {len(speeddiff.get('speed_difference', []))}")
    print(f"distance 點數: {len(speeddiff.get('distance', []))}")
    print(f"driver1_time_seconds 點數: {len(speeddiff.get('driver1_time_seconds', []))}")
    print(f"driver2_time_seconds 點數: {len(speeddiff.get('driver2_time_seconds', []))}")
    
    # 顯示前 5 個數據點
    print(f"\n前 5 個 speed_difference: {speeddiff.get('speed_difference', [])[:5]}")
    print(f"前 5 個 distance: {speeddiff.get('distance', [])[:5]}")

# 檢查 Distancediff（如果有）
if 'Distancediff' in tc:
    print("\n=== Distancediff Structure ===")
    distancediff = tc['Distancediff']
    print(f"Distancediff keys: {list(distancediff.keys())}")
    print(f"distance_difference 點數: {len(distancediff.get('distance_difference', []))}")
    print(f"distance 點數: {len(distancediff.get('distance', []))}")
else:
    print("\n⚠️ 沒有 Distancediff 數據")

# 檢查 comparison_info
print("\n=== Comparison Info ===")
comp_info = data_dict.get('comparison_info', {})
print(f"comparison_info keys: {list(comp_info.keys())}")

print("\n✅ API 測試完成")
