#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, '.')

from modules.gui.qualifying_prediction.qualifying_prediction_data_loader import QualifyingPredictionDataLoader

# 創建 loader
loader = QualifyingPredictionDataLoader(year='2025', race='Mexico')
loader._debug_enabled = True

# 讀取 JSON
data = json.load(open('json/qualifying_prediction_2025_Mexico.json', 'r', encoding='utf-8'))

print("=" * 60)
print("原始數據（第一位車手）:")
print("=" * 60)
pred = data['predictions'][0]
print(f"車手: {pred['driver']}")
print(f"Q 時間: {pred.get('actual_q_time')}")
print(f"Q 名次: {pred.get('actual_q_rank', 'KEY NOT FOUND')}")
print(f"FP3 預測名次: {pred.get('fp3_predicted_rank', 'KEY NOT FOUND')}")

# 處理數據
processed = loader._process_data(data)

print("\n" + "=" * 60)
print("處理後數據（第一位車手）:")
print("=" * 60)
pred = processed['predictions'][0]
print(f"車手: {pred['driver']}")
print(f"Q 時間: {pred.get('actual_q_time')}")
print(f"Q 名次: {pred.get('actual_q_rank', 'KEY NOT FOUND')}")
print(f"FP3 預測名次: {pred.get('fp3_predicted_rank', 'KEY NOT FOUND')}")

# 顯示前 5 名的 Q 名次
print("\n" + "=" * 60)
print("前 5 名 Q 名次:")
print("=" * 60)
sorted_by_q = sorted(
    [p for p in processed['predictions'] if p.get('actual_q_rank')],
    key=lambda x: x['actual_q_rank']
)[:5]

for p in sorted_by_q:
    print(f"{p['actual_q_rank']:2d}. {p['driver']:3s} - Q: {p['actual_q_time']:.3f}s, FP3 預測名次: {p.get('fp3_predicted_rank', 'N/A')}")
