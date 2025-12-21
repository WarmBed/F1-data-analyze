"""
檢查 HAM 的分段數據
"""
import json

# 讀取 JSON
with open('json/ideal_lap_ranking_2023_Japan_R.json', encoding='utf-8') as f:
    data = json.load(f)

# HAM 是第 3 名
ham = data['analysis_result']['ranking'][2]

print("=== HAM (第 3 名) ===")
print(f"理想圈: {ham['ideal_lap_time']}")
print(f"最速圈: {ham['fastest_lap_time']}")
print(f"差異: {ham['time_gap']}")
print()

print("分段:")
sb = ham['sector_breakdown']
for i in [1, 2, 3]:
    sector_key = f'sector_{i}'
    sector_data = sb[sector_key]
    print(f"  S{i}: {sector_data['time']:.3f}s - is_optimal_in_fastest={sector_data['is_optimal_in_fastest']}")
