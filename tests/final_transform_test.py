#!/usr/bin/env python3
"""
測試修改後的 JSON 格式和 DataLoader
"""
import json

# 讀取最新的 JSON
with open('json/qualifying_prediction_2025_Mexico.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data['predictions']

print("=" * 70)
print("CLI F74 生成的 JSON 格式檢查")
print("=" * 70)

# 檢查前 5 名
print(f"\n✅ 找到 {len(predictions)} 個預測")
print("\n前 5 名車手的完整資料:")
print(f"\n{'排名':<6} {'車手':<6} {'FP3預測名次':<12} {'FP3時間':<12} {'預測時間':<12} {'Q名次':<8} {'Q時間':<12}")
print("-" * 80)

for pred in predictions[:5]:
    rank = pred['rank']
    driver = pred['driver']
    fp3_rank = pred.get('fp3_predicted_rank', 'N/A')
    fp3_time = pred['fp3_time']
    pred_time = pred['predicted_time']
    q_rank = pred.get('actual_q_rank', 'N/A')
    q_time = pred.get('actual_q_time', 'N/A')
    
    print(f"{rank:<6} {driver:<6} {fp3_rank:<12} {fp3_time:<12.3f} {pred_time:<12.3f} {q_rank:<8} {q_time if q_time == 'N/A' else f'{q_time:.3f}':<12}")

# 驗證數據完整性
print("\n" + "=" * 70)
print("數據完整性檢查:")
print("=" * 70)

has_fp3_rank = all('fp3_predicted_rank' in p for p in predictions)
has_q_rank_for_q_time = all(
    'actual_q_rank' in p 
    for p in predictions 
    if p.get('actual_q_time') is not None
)

print(f"✅ 所有車手都有 fp3_predicted_rank: {has_fp3_rank}")
print(f"✅ 有 Q 時間的車手都有 actual_q_rank: {has_q_rank_for_q_time}")

if has_fp3_rank and has_q_rank_for_q_time:
    print("\n🎉 CLI F74 輸出格式完全正確！")
    print("   前端 GUI 可以直接使用這些欄位，不需要重複計算")
else:
    print("\n❌ 數據格式有問題")
