#!/usr/bin/env python3
"""
驗證 GUI 能正確讀取和顯示名次欄位
"""
import json

print("=" * 70)
print("GUI 名次欄位驗證")
print("=" * 70)

# 讀取 JSON
json_path = "json/qualifying_prediction_2025_Mexico.json"
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data['predictions']

print(f"\n✅ 讀取 JSON: {json_path}")
print(f"✅ 找到 {len(predictions)} 個預測\n")

# 模擬 GUI 表格顯示
print("模擬 GUI 表格顯示:")
print("=" * 90)
print(f"{'排名':<6} {'車手':<6} {'車隊':<12} {'FP3預測名次':<12} {'FP3時間':<10} {'預測時間':<10} {'Q名次':<8} {'Q結果':<10}")
print("-" * 90)

for pred in predictions[:10]:  # 顯示前 10 名
    rank = pred['rank']
    driver = pred['driver']
    team = pred['team'][:10]  # 截短隊名
    
    # 這些欄位應該直接來自 JSON
    fp3_rank = pred.get('fp3_predicted_rank', 'N/A')
    q_rank = pred.get('actual_q_rank', 'N/A')
    
    fp3_time = f"{pred['fp3_time']:.3f}s"
    pred_time = f"{pred['predicted_time']:.3f}s"
    q_time = f"{pred['actual_q_time']:.3f}s" if pred.get('actual_q_time') else "N/A"
    
    print(f"{rank:<6} {driver:<6} {team:<12} {fp3_rank:<12} {fp3_time:<10} {pred_time:<10} {q_rank:<8} {q_time:<10}")

print("\n" + "=" * 70)
print("驗證結果:")
print("=" * 70)

# 檢查所有必要欄位
all_have_fp3_rank = all('fp3_predicted_rank' in p for p in predictions)
all_q_times_have_rank = all(
    'actual_q_rank' in p 
    for p in predictions 
    if p.get('actual_q_time') is not None
)

print(f"✅ 所有車手都有 fp3_predicted_rank: {all_have_fp3_rank}")
print(f"✅ 有 Q 時間的車手都有 actual_q_rank: {all_q_times_have_rank}")

if all_have_fp3_rank and all_q_times_have_rank:
    print("\n🎉 JSON 格式完全符合 GUI 需求！")
    print("   GUI 應該能正確顯示所有名次欄位")
    print("\n💡 測試步驟:")
    print("   1. 打開 F1T GUI")
    print("   2. 選擇 Qualifying Prediction 模組")
    print("   3. 選擇 2025 Mexico")
    print("   4. 檢查 'Q名次' 欄位是否顯示數字（1, 2, 3...）")
    print("   5. 檢查 'FP3預測名次' 欄位是否顯示數字")
else:
    print("\n❌ JSON 格式有問題，需要檢查")
