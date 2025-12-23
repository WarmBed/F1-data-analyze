"""
檢查 ANT 的過濾統計和速度數據
"""
import json

data = json.load(open('json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json', 'r', encoding='utf-8'))
ant = [d for d in data['mode_a_unified']['drivers'] if d['driver'] == 'ANT'][0]

print('ANT filtering_summary:')
print(json.dumps(ant['filtering_summary'], indent=2))
print()
print(f'Total laps: {ant["total_laps"]}')
print(f'Valid laps (T6): {ant["corners"]["low_speed_corner_6"]["valid_laps"]}')
print()
print('T6 統計:')
t6 = ant['corners']['low_speed_corner_6']
print(f'  中位數: {t6["median_speed"]:.1f} km/h')
print(f'  平均: {t6["mean_speed"]:.1f} km/h')
print(f'  最小: {t6["min_speed"]:.1f} km/h')
print(f'  最大: {t6["max_speed"]:.1f} km/h')
print()
print('所有速度值:')
for i, s in enumerate(t6['speeds_raw']):
    flag = ' [!]' if s > 100 else ''
    print(f'  {i+1:2d}: {s:.1f} km/h{flag}')
