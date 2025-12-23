import fastf1
fastf1.Cache.enable_cache('f1_analysis_cache')

session = fastf1.get_session(2025, 'Abu Dhabi', 'R')
session.load()

laps = session.laps
ver_laps = laps[laps['Driver']=='VER']

print(f"VER total laps in FastF1: {len(ver_laps)}")
print(f"VER lap numbers: {sorted(ver_laps['LapNumber'].tolist())}")

# Check status
results = session.results
ver_result = results[results['Abbreviation']=='VER']
print(f"\nVER final position: {ver_result['Position'].values}")
print(f"VER status: {ver_result['Status'].values}")
print(f"VER points: {ver_result['Points'].values}")

# Check JSON driver count
import json
with open('json/live_timing_traffic_distance_2025_Abu_Dhabi_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['data']['drivers']
print(f"\n--- JSON Data ---")
for drv_num, d in drivers.items():
    tla = d.get('driver_tla', drv_num)
    laps_analyzed = d.get('laps_analyzed', 0)
    per_lap = d.get('per_lap', [])
    if per_lap:
        min_lap = min(x['lap'] for x in per_lap)
        max_lap = max(x['lap'] for x in per_lap)
    else:
        min_lap = max_lap = 0
    print(f"{tla}: {laps_analyzed} laps analyzed (Lap {min_lap}-{max_lap})")
