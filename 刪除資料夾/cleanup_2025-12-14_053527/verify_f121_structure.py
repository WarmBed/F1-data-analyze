"""驗證 F121 新結構（已移除模式 B）"""
import json

# 讀取 JSON
data = json.load(open('json/fp2_straight_line_all_laps_analysis_2025_Abu Dhabi_R.json', 'r', encoding='utf-8'))

print("=" * 60)
print("F121 JSON 結構驗證 - 模式 B 移除確認")
print("=" * 60)
print()

print("[頂層鍵]")
print(f"  {list(data.keys())}")
print()

print("[新結構驗證]")
print(f"  ✅ 'drivers' 鍵存在: {('drivers' in data)}")
print(f"  ✅ 'summary' 鍵存在: {('summary' in data)}")
print()

print("[舊結構移除確認]")
print(f"  ❌ 'mode_a_unified' 存在: {('mode_a_unified' in data)}")
print(f"  ❌ 'mode_b_grouped' 存在: {('mode_b_grouped' in data)}")
print()

print("[數據統計]")
print(f"  總車手數: {len(data.get('drivers', []))}")
print()

print("[範例車手數據 - HAM]")
ham = next((d for d in data.get('drivers', []) if d['driver'] == 'HAM'), None)
if ham:
    print(f"  車手: {ham['driver']}")
    print(f"  絕對最高速度: {ham.get('absolute_max_speed_kmh')} km/h")
    print(f"  最高速度圈數: {ham.get('absolute_max_speed_lap')}")
    print(f"  有效圈數: {ham.get('valid_lap_numbers')}")
    print(f"  中位數速度: {ham.get('speed_stats', {}).get('median')} km/h")
    print(f"  加速 100→300 (中位數): {ham.get('acceleration_100_300_stats', {}).get('median')} s")
    print(f"  推算到最高速 (中位數): {ham.get('time_to_max_speed_stats', {}).get('median')} s")
else:
    print("  ⚠️ 找不到 HAM 數據")
print()

print("[總結]")
if 'drivers' in data and 'summary' in data and 'mode_a_unified' not in data and 'mode_b_grouped' not in data:
    print("  ✅ 結構驗證通過 - 模式 B 已完全移除")
else:
    print("  ❌ 結構驗證失敗 - 仍有舊結構殘留")
print("=" * 60)
