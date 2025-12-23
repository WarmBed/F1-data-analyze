#!/usr/bin/env python3
"""
檢查 detailed_laptime_analysis JSON 檔案的詳細結構
"""

import json
from pathlib import Path

filepath = Path("json/detailed_laptime_analysis_2025_United States_R_all_drivers.json")

print(f"檢查檔案: {filepath}")
print(f"檔案大小: {filepath.stat().st_size / 1024:.1f} KB")
print()

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("JSON 結構分析")
print("="*80)

# 頂層鍵
print(f"\n📋 Top-level keys: {list(data.keys())}")

# Metadata
metadata = data.get('metadata', {})
print(f"\n📊 Metadata:")
for key, value in metadata.items():
    print(f"   {key}: {value}")

# All drivers
all_drivers = data.get('all_drivers_detailed_laptime', {})
print(f"\n👥 All drivers: {list(all_drivers.keys())}")

# 檢查每個車手的數據結構
print(f"\n🔍 各車手數據結構:")
for driver, driver_data in list(all_drivers.items())[:3]:  # 只看前3個
    print(f"\n   {driver}:")
    print(f"      Keys: {list(driver_data.keys())}")
    
    detailed_laps = driver_data.get('detailed_laps', [])
    print(f"      detailed_laps 數量: {len(detailed_laps)}")
    
    if detailed_laps:
        sample_lap = detailed_laps[0]
        print(f"      範例圈數據 keys: {list(sample_lap.keys())}")
        print(f"      Lap {sample_lap.get('lap_number')}: {sample_lap.get('lap_time_seconds'):.3f}s")

# 檢查 VER
print(f"\n🏎️  VER 詳細資訊:")
ver_data = all_drivers.get('VER', {})
print(f"   VER keys: {list(ver_data.keys())}")

# 檢查兩種可能的鍵名
ver_laps = ver_data.get('detailed_laps', []) or ver_data.get('detailed_lap_data', [])
key_name = 'detailed_lap_data' if ver_data.get('detailed_lap_data') else 'detailed_laps'
print(f"   使用的鍵名: {key_name}")
print(f"   VER {key_name} 數量: {len(ver_laps)}")

if ver_laps:
    valid_laps = [l for l in ver_laps if l.get('lap_time_seconds') is not None or l.get('LapTime(Seconds)') is not None]
    print(f"   VER 有效圈數: {len(valid_laps)}")
    
    if valid_laps:
        # 嘗試兩種鍵名
        lap_time_key = 'lap_time_seconds' if 'lap_time_seconds' in valid_laps[0] else 'LapTime(Seconds)'
        fastest = min(valid_laps, key=lambda x: x.get(lap_time_key, 999))
        fastest_time = fastest.get(lap_time_key)
        lap_num = fastest.get('lap_number') or fastest.get('LapNumber')
        
        print(f"   VER 最速圈: Lap {lap_num} - {fastest_time:.3f}s ({fastest_time/60:.0f}:{fastest_time%60:06.3f})")
        print(f"   範例圈數據 keys: {list(valid_laps[0].keys())}")
else:
    print(f"   ❌ VER 沒有圈數數據！")

# 檢查是否有其他車手有數據
drivers_with_data = {}
for d in all_drivers:
    laps = all_drivers[d].get('detailed_laps', []) or all_drivers[d].get('detailed_lap_data', [])
    drivers_with_data[d] = len(laps)

non_empty = {d: c for d, c in drivers_with_data.items() if c > 0}

print(f"\n📈 有數據的車手:")
for driver, count in sorted(non_empty.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"   {driver}: {count} 圈")

if not non_empty:
    print(f"   ❌ 所有車手都沒有圈數數據！")
    print(f"   💡 這個 JSON 檔案可能生成失敗，需要重新生成")
else:
    print(f"\n總共 {len(non_empty)} 位車手有數據")
