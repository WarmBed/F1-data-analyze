#!/usr/bin/env python3
"""測試排位賽預測模組的新欄位（Q 名次和 FP3 預測名次）"""

import json

# 讀取 Mexico 2025 JSON
with open('json/qualifying_prediction_2025_Mexico.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data['predictions']

print("=" * 80)
print("測試新欄位：Q 名次和 FP3 預測名次")
print("=" * 80)

# 計算 FP3 預測名次
fp3_sorted = sorted(predictions, key=lambda x: x['fp3_time'])
for rank, pred in enumerate(fp3_sorted, start=1):
    pred['fp3_predicted_rank'] = rank

# 計算 Q 名次
drivers_with_q = [p for p in predictions if p.get('actual_q_time') is not None]
if drivers_with_q:
    q_sorted = sorted(drivers_with_q, key=lambda x: x['actual_q_time'])
    for rank, pred in enumerate(q_sorted, start=1):
        pred['actual_q_rank'] = rank

# 顯示前 5 名
print("\n前 5 名車手（按預測時間排序）:")
print(f"{'排名':<6}{'車手':<8}{'FP3預測名次':<12}{'FP3時間':<12}{'預測時間':<12}{'Q名次':<8}{'Q結果':<12}")
print("-" * 80)

for i, pred in enumerate(sorted(predictions, key=lambda x: x['predicted_time'])[:5], start=1):
    driver = pred['driver']
    fp3_rank = pred.get('fp3_predicted_rank', 'N/A')
    fp3_time = f"{pred['fp3_time']:.3f}s"
    pred_time = f"{pred['predicted_time']:.3f}s"
    q_rank = pred.get('actual_q_rank', 'N/A')
    q_time = f"{pred['actual_q_time']:.3f}s" if pred['actual_q_time'] else "N/A"
    
    print(f"{i:<6}{driver:<8}{fp3_rank:<12}{fp3_time:<12}{pred_time:<12}{q_rank:<8}{q_time:<12}")

print("\n✅ 測試完成！")
print("\n預期結果：")
print("  - FP3 預測名次：根據 FP3 時間排序的名次")
print("  - Q 名次：根據實際 Q 結果排序的名次")
