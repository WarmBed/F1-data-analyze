#!/usr/bin/env python3
"""檢查 Abu Dhabi 2025 FP2→Q 預測準確度"""

import json
from pathlib import Path

json_file = Path("json/fp2_qualifying_prediction_2025_Abu Dhabi.json")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data.get('predictions', [])

print("="*70)
print("Abu Dhabi 2025 FP2→Q 預測結果（含所有調整因子）")
print("="*70)
print(f"{'排名':<4} {'車手':<4} {'車隊':<18} {'預測時間':<10} {'實際時間':<10} {'誤差':<8} {'排名差'}")
print("-"*70)

total_error = 0
total_rank_error = 0
count = 0

for p in predictions:
    driver = p.get('driver', '?')
    team = p.get('team', '?')[:18]
    predicted = p.get('predicted_time', 0)
    actual = p.get('actual_q_time', 0)
    rank = p.get('rank', 0)
    actual_rank = p.get('actual_q_rank', 0)
    
    if actual:
        error = predicted - actual
        rank_diff = rank - actual_rank
        total_error += abs(error)
        total_rank_error += abs(rank_diff)
        count += 1
        print(f"P{rank:<3} {driver:<4} {team:<18} {predicted:.3f}s    {actual:.3f}s    {error:+.3f}s  {rank_diff:+3d}")
    else:
        print(f"P{rank:<3} {driver:<4} {team:<18} {predicted:.3f}s    N/A       N/A       N/A")

print("-"*70)
if count:
    mae = total_error / count
    avg_rank_error = total_rank_error / count
    print(f"\n統計摘要:")
    print(f"  平均絕對誤差 (MAE): {mae:.3f}s")
    print(f"  平均排名誤差: {avg_rank_error:.2f} 位")
    
    # 顯示 Top 3 預測 vs 實際
    print(f"\nTop 3 對比:")
    print(f"  預測 Top 3: {[p['driver'] for p in predictions[:3]]}")
    actual_top3 = sorted([p for p in predictions if p.get('actual_q_time')], 
                         key=lambda x: x['actual_q_time'])[:3]
    print(f"  實際 Top 3: {[p['driver'] for p in actual_top3]}")
    
    # HAD/HUL 特別關注
    print(f"\nHAD/HUL 預測結果（關鍵車手）:")
    for p in predictions:
        if p['driver'] in ['HAD', 'HUL']:
            print(f"  {p['driver']}: 預測 P{p['rank']}, 實際 P{p.get('actual_q_rank', '?')}")
            print(f"        演進調整: {p.get('evolution_adjustment', 0):+.3f}s")
            print(f"        樂觀度調整: {p.get('optimism_adjustment', 0):+.3f}s")
