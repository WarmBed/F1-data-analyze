#!/usr/bin/env python3
"""深度分析 Azerbaijan 加速數據缺失原因"""

import json

# 讀取 JSON
with open('json/all_drivers_straight_line_speed_2025_Azerbaijan_R.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

data = raw_data['data']['data']
drivers = data['driver_speeds']

print("=" * 80)
print("Azerbaijan 2025 直線速度分析 - 數據缺失調查")
print("=" * 80)
print()

# 統計
total = len(drivers)
with_data = [d for d in drivers if d.get('acceleration_time_100_300_seconds') is not None]
without_data = [d for d in drivers if d.get('acceleration_time_100_300_seconds') is None]

print(f"📊 統計資訊:")
print(f"   總車手數: {total}")
print(f"   有加速數據: {len(with_data)} ({len(with_data)/total*100:.1f}%)")
print(f"   無加速數據: {len(without_data)} ({len(without_data)/total*100:.1f}%)")
print()

# 列出有數據的車手
print("✅ 有加速數據的車手:")
for d in sorted(with_data, key=lambda x: x['acceleration_time_100_300_seconds']):
    print(f"   {d['driver']:3s} ({d['team']:20s}) - {d['acceleration_time_100_300_seconds']:.3f}s "
          f"@ {d['max_speed_kmh']:.0f} km/h - {d['measurement_notes']}")
print()

# 列出沒有數據的車手（顯示前 5 個）
print("❌ 無加速數據的車手（前 5 個）:")
for d in without_data[:5]:
    notes = d.get('measurement_notes', 'No notes')
    in_core = d.get('in_core_range', 'Unknown')
    print(f"   {d['driver']:3s} ({d['team']:20s}) - Max: {d['max_speed_kmh']:.0f} km/h")
    print(f"       Core範圍: {in_core}, 備註: {notes}")
print()

# 分析 in_core_range 分佈
in_core_count = sum(1 for d in drivers if d.get('in_core_range') == 'True')
not_in_core_count = sum(1 for d in drivers if d.get('in_core_range') == 'False')

print(f"🎯 測量範圍分析:")
print(f"   在核心範圍內 (in_core_range=True): {in_core_count}")
print(f"   超出核心範圍 (in_core_range=False): {not_in_core_count}")
print()

# 檢查統一速度範圍
unified = data['metadata']['unified_speed_range']
print(f"⚙️  統一速度範圍:")
print(f"   起始速度: {unified['start_speed_kmh']:.0f} km/h")
print(f"   終點速度: {unified['end_speed_kmh']:.0f} km/h")
print(f"   調整原因: {unified['adjustment_reason']}")
print()

# 檢查參考區段
ref_seg = data['reference_segment']
print(f"📏 參考區段（VER 最速圈）:")
print(f"   起始距離: {ref_seg['segment_distance_start']:.1f}m")
print(f"   終點距離: {ref_seg['segment_distance_end']:.1f}m")
print(f"   區段長度: {ref_seg['segment_length']:.1f}m")
print(f"   起始速度: {ref_seg['segment_start_speed']:.0f} km/h → {ref_seg['unified_start_speed']:.0f} km/h")
print(f"   最高速度: {ref_seg['segment_max_speed']:.0f} km/h → {ref_seg['unified_end_speed']:.0f} km/h")
print()

# 關鍵分析：為什麼 null？
print("=" * 80)
print("🔍 關鍵問題分析")
print("=" * 80)
print()
print("❓ 為什麼 15 位車手沒有加速數據？")
print()
print("可能原因 1: 統一終點速度過低")
print(f"   - 終點速度: {unified['end_speed_kmh']:.0f} km/h（使用最高速度）")
print(f"   - 最快車手 (NOR): {with_data[0]['max_speed_kmh']:.0f} km/h")
print(f"   - 問題：很多車手的最高速度 > 324 km/h，無法完成 150→324 的加速測量")
print()

print("可能原因 2: 測量點超出核心範圍")
print(f"   - {not_in_core_count}/{total} 車手測量點超出核心範圍")
print(f"   - CLI 演算法可能要求測量點必須在核心範圍內")
print()

print("可能原因 3: CLI 演算法邏輯限制")
print("   - F48 v2.1 演算法可能有特定的速度範圍要求")
print("   - 如果車手的最高速度遠超過統一終點速度，可能無法計算")
print()

# 驗證假設：檢查有數據車手的最高速度
print("驗證假設：有數據車手的最高速度範圍")
max_speeds_with_data = [d['max_speed_kmh'] for d in with_data]
max_speeds_without_data = [d['max_speed_kmh'] for d in without_data]

print(f"   有數據車手最高速度: {min(max_speeds_with_data):.0f} - {max(max_speeds_with_data):.0f} km/h")
print(f"   無數據車手最高速度: {min(max_speeds_without_data):.0f} - {max(max_speeds_without_data):.0f} km/h")
print()

if max(max_speeds_with_data) > unified['end_speed_kmh']:
    print("⚠️  發現：有數據的車手最高速度也超過統一終點速度！")
    print("   → 說明統一終點速度不是問題根源")
else:
    print("✅ 有數據的車手最高速度都在統一終點速度範圍內")
print()

print("=" * 80)
print("📌 結論")
print("=" * 80)
print()
print("Azerbaijan 賽事加速數據缺失的根本原因可能是：")
print("1. CLI 演算法對測量點的嚴格要求（必須在核心範圍內）")
print("2. Azerbaijan 賽道的特殊性（長直線但測量點分散）")
print("3. 演算法版本限制（F48 v2.1 可能對某些情況無法處理）")
print()
print("建議：")
print("1. 檢查 CLI 的 F48 演算法實現，了解為什麼會產生 null")
print("2. 考慮放寬 in_core_range 的限制")
print("3. 或在 GUI 中清楚標示「數據不可用」而非顯示 0")
