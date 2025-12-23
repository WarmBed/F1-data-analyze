"""檢查修正後的 Azerbaijan 統一速度範圍"""
import json

json_file = "json/all_drivers_straight_line_speed_2025_Azerbaijan_R.json"

print(f"📁 檢查檔案: {json_file}\n")

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

metadata = data.get("metadata", {})
unified_range = metadata.get("unified_speed_range", {})

print("=" * 60)
print("🎯 統一速度範圍")
print("=" * 60)
print(f"起始速度: {unified_range.get('start_speed_kmh')} km/h")
print(f"終點速度: {unified_range.get('end_speed_kmh')} km/h")
print(f"調整原因:\n  {unified_range.get('adjustment_reason')}")
print("=" * 60)

# 檢查是否為 10 km/h 階梯
end_speed = unified_range.get('end_speed_kmh')
if end_speed and end_speed % 10 == 0:
    print(f"\n✅ 終點速度 {end_speed} km/h 符合 10 km/h 階梯標準")
else:
    print(f"\n⚠️  終點速度 {end_speed} km/h 不是 10 km/h 的倍數")

# 統計有效數據
drivers = data.get("driver_speeds", [])
with_data = [d for d in drivers if d.get('acceleration_time_100_300_seconds') is not None]
print(f"\n📊 數據統計:")
print(f"  總車手數: {len(drivers)}")
print(f"  有加速數據: {len(with_data)} ({len(with_data)/len(drivers)*100:.1f}%)")
