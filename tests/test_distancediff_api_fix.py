#!/usr/bin/env python3
"""測試 Distancediff API 修復"""

import sys
import os

# 確保可以導入 API 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from api.routers.analysis import _merge_cross_event_telemetry

# 創建模擬數據
print("🔄 創建模擬跨賽事比較數據...")

# 車手1數據
data1 = {
    "results": {
        "telemetry_comparison": {
            "Speed": {
                "name": "Speed",
                "driver1_data": list(range(100, 200)),  # 100-200 km/h
                "distance": list(range(0, 5000, 50)),   # 0-5000m
                "driver1_time_seconds": list(np.linspace(0, 100, 100))  # 0-100秒
            }
        }
    },
    "comparison_info": {
        "driver1": "VER",
        "lap_time1": "1:30.123",
        "compound1": "SOFT",
        "tyre_life1": "5"
    }
}

# 車手2數據
data2 = {
    "results": {
        "telemetry_comparison": {
            "Speed": {
                "name": "Speed",
                "driver1_data": list(range(95, 195)),   # 95-195 km/h (稍慢)
                "distance": list(range(0, 5000, 50)),   # 0-5000m
                "driver1_time_seconds": list(np.linspace(0, 102, 100))  # 0-102秒 (稍慢)
            }
        }
    },
    "comparison_info": {
        "driver1": "LEC",
        "lap_time1": "1:30.456",
        "compound1": "MEDIUM",
        "tyre_life1": "3"
    }
}

print("✅ 模擬數據創建完成")
print()

# 測試合併函數
print("🧪 測試 _merge_cross_event_telemetry()...")
result = _merge_cross_event_telemetry(
    data1, data2,
    driver1="VER", year1=2025, race1="Australia", session1="R", lap1=99,
    driver2="LEC", year2=2025, race2="Australia", session2="Q", lap2=99
)

print()
print("=" * 60)
print("測試結果")
print("=" * 60)

# 檢查 telemetry_comparison
tc = result.get("telemetry_comparison", {})
print(f"\n✅ telemetry_comparison keys: {list(tc.keys())}")

# 檢查 Speeddiff
if "Speeddiff" in tc:
    speeddiff = tc["Speeddiff"]
    print(f"\n✅ Speeddiff 已添加")
    print(f"   - distance 點數: {len(speeddiff.get('distance', []))}")
    print(f"   - speed_difference 點數: {len(speeddiff.get('speed_difference', []))}")
    print(f"   - 前5個速度差: {speeddiff.get('speed_difference', [])[:5]}")
else:
    print(f"\n❌ Speeddiff 未添加")

# 檢查 Distancediff
if "Distancediff" in tc:
    distancediff = tc["Distancediff"]
    print(f"\n✅ Distancediff 已添加")
    print(f"   - distance 點數: {len(distancediff.get('distance', []))}")
    print(f"   - distance_difference 點數: {len(distancediff.get('distance_difference', []))}")
    print(f"   - 前5個距離差: {distancediff.get('distance_difference', [])[:5]}")
    print(f"   - 距離差範圍: {min(distancediff.get('distance_difference', [])):.2f} ~ {max(distancediff.get('distance_difference', [])):.2f} m")
else:
    print(f"\n❌ Distancediff 未添加")

# 檢查 distance_difference 欄位
dist_diff = result.get("distance_difference", {})
if dist_diff and "distance_difference" in dist_diff:
    print(f"\n✅ distance_difference 欄位已更新")
    print(f"   - 點數: {len(dist_diff.get('distance_difference', []))}")
else:
    print(f"\n⚠️ distance_difference 欄位未更新或為空")

print()
print("=" * 60)
print("✅ API 修復測試完成")
print("=" * 60)
