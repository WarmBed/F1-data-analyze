"""快速掃描 JSON 中每位車手的圈數範圍"""
import json

with open('json/live_timing_traffic_distance_2025_Abu_Dhabi_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['data']['drivers']

print("=== Abu Dhabi 2025 R - Traffic Analysis Lap Coverage ===\n")
print(f"{'Driver':<6} {'Laps Analyzed':<15} {'Lap Range':<15} {'Missing Laps (front)':<20}")
print("-" * 60)

for drv_num, d in sorted(drivers.items(), key=lambda x: x[1].get('driver_tla', '')):
    tla = d.get('driver_tla', drv_num)
    laps_analyzed = d.get('laps_analyzed', 0)
    per_lap = d.get('per_lap', [])
    
    if per_lap:
        lap_nums = [x['lap'] for x in per_lap]
        min_lap = min(lap_nums)
        max_lap = max(lap_nums)
        
        # 缺少的前面幾圈
        missing_front = min_lap - 2  # 第一圈通常沒有（因為是 out lap）
        missing_str = f"Lap 2-{min_lap-1}" if missing_front > 0 else "None"
    else:
        min_lap = max_lap = 0
        missing_str = "All"
    
    print(f"{tla:<6} {laps_analyzed:<15} Lap {min_lap}-{max_lap:<5} {missing_str}")
