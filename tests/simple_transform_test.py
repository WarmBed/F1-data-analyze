#!/usr/bin/env python3
"""
直接測試數據轉換邏輯（不使用 Qt）
"""
import json

# 讀取 JSON
with open('json/qualifying_prediction_2025_Mexico.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data['predictions']

print("=" * 60)
print("原始數據（第一位車手）:")
print("=" * 60)
pred = predictions[0]
print(f"車手: {pred['driver']}")
print(f"Q 時間: {pred.get('actual_q_time')}")
print(f"Q 名次: {pred.get('actual_q_rank', 'KEY NOT FOUND')}")
print(f"FP3 預測名次: {pred.get('fp3_predicted_rank', 'KEY NOT FOUND')}")

# ========== 模擬 _transform_data_for_display() 的邏輯 ==========

# 1. FP3 預測名次：根據 FP3 時間排序
fp3_sorted = sorted(predictions, key=lambda x: x["fp3_time"])
for rank, pred in enumerate(fp3_sorted, start=1):
    pred["fp3_predicted_rank"] = rank

# 2. Q 名次：根據實際 Q 結果排序
drivers_with_q = [p for p in predictions if p.get("actual_q_time") is not None]
if drivers_with_q:
    q_sorted = sorted(drivers_with_q, key=lambda x: x["actual_q_time"])
    for rank, pred in enumerate(q_sorted, start=1):
        pred["actual_q_rank"] = rank

print("\n" + "=" * 60)
print("處理後數據（第一位車手）:")
print("=" * 60)
pred = predictions[0]
print(f"車手: {pred['driver']}")
print(f"Q 時間: {pred.get('actual_q_time')}")
print(f"Q 名次: {pred.get('actual_q_rank', 'KEY NOT FOUND')}")
print(f"FP3 預測名次: {pred.get('fp3_predicted_rank', 'KEY NOT FOUND')}")

# 顯示前 5 名的 Q 名次
print("\n" + "=" * 60)
print("前 5 名 Q 名次:")
print("=" * 60)
sorted_by_q = sorted(
    [p for p in predictions if p.get('actual_q_rank')],
    key=lambda x: x['actual_q_rank']
)[:5]

for p in sorted_by_q:
    print(f"{p['actual_q_rank']:2d}. {p['driver']:3s} - Q: {p['actual_q_time']:.3f}s, FP3 預測名次: {p.get('fp3_predicted_rank', 'N/A')}")

print("\n✅ 轉換邏輯測試成功！")
