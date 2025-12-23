import json

with open('json/live_timing_traffic_distance_2025_Abu_Dhabi_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['data']['drivers']
for k, d in drivers.items():
    if d.get('driver_tla') == 'VER':
        per_lap = d.get('per_lap', [])
        laps = [x['lap'] for x in per_lap]
        print(f'VER laps: {sorted(laps)}')
        print(f'Total: {len(laps)} laps')
        if laps:
            print(f'Min: {min(laps)}, Max: {max(laps)}')
            missing = [i for i in range(min(laps), max(laps)+1) if i not in laps]
            print(f'Missing laps: {missing}')
        break
