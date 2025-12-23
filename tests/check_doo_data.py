import json

json_path = r"C:\Users\mike2\OneDrive\Code\F1-data-analyze\json\all_drivers_straight_line_speed_2025_China_R.json"

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找到 DOO
doo = [d for d in data['data']['driver_speeds'] if d['driver'] == 'DOO'][0]

print("=" * 80)
print("🔍 DOO Segment 數據檢查（最新 JSON）")
print("=" * 80)
print(f"\n✅ 基本資訊:")
print(f"  車手: {doo['driver']}")
print(f"  最高速度: {doo.get('max_speed_kmh')} km/h")
print(f"  最高速度位置: {doo.get('distance_m')} m")
print(f"\n⚠️  Segment 加速數據:")
print(f"  加速時間: {doo.get('segment_accel_time_seconds')} 秒")
print(f"  起始速度: {doo.get('segment_start_speed_kmh')} km/h")
print(f"  終點速度: {doo.get('segment_end_speed_kmh')} km/h")
print(f"  速度增益: {doo.get('segment_speed_gain_kmh')} km/h")
print(f"  加速距離: {doo.get('segment_accel_distance_meters')} m")
print(f"  平均加速度: {doo.get('segment_avg_acceleration_ms2')} m/s²")
print(f"\n📍 位置資訊:")
print(f"  在核心範圍內: {doo.get('in_core_range')}")
print(f"  測量備註: {doo.get('measurement_notes')}")

# 檢查 algorithm_version
print(f"\n📋 Metadata:")
print(f"  Algorithm Version: {data['data'].get('algorithm_version')}")
print(f"  Has unified_speed_range: {'unified_speed_range' in data['data'].get('metadata', {})}")

# 檢查 reference_segment
if 'reference_segment' in data['data']:
    ref = data['data']['reference_segment']
    print(f"\n📏 Reference Segment:")
    print(f"  segment_distance_start: {ref.get('segment_distance_start')} m")
    print(f"  segment_distance_end: {ref.get('segment_distance_end')} m")
    print(f"  Has unified_start_speed: {' unified_start_speed' in ref}")
    print(f"  Has unified_end_speed: {'unified_end_speed' in ref}")

print("\n" + "=" * 80)
