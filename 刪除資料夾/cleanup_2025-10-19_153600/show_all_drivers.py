import json

with open('json/all_drivers_straight_line_speed_2025_Azerbaijan_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)['data']

print("所有車手速度與加速數據：\n")
print(f"{'車手':<4} {'車隊':<18} {'最高速度':<10} {'加速時間':<10} {'核心範圍':<10}")
print("=" * 70)

for dr in sorted(data['driver_speeds'], key=lambda x: x['driver']):
    driver = dr['driver']
    team = dr['team'][:16]
    max_speed = f"{dr['max_speed_kmh']:.0f} km/h"
    accel = f"{dr['acceleration_time_100_300_seconds']:.3f}s" if dr.get('acceleration_time_100_300_seconds') else "None"
    core = str(dr.get('in_core_range', 'Unknown'))
    
    print(f"{driver:<4} {team:<18} {max_speed:<10} {accel:<10} {core:<10}")
