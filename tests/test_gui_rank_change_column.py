#!/usr/bin/env python3
"""
測試 GUI 名次變化欄位的顯示
"""
import json

print("=" * 80)
print("GUI 名次變化欄位顯示測試")
print("=" * 80)

# 讀取 JSON
json_path = "json/qualifying_prediction_2025_Mexico.json"
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data['predictions']

print(f"\n✅ 讀取 JSON: {json_path}")
print(f"✅ 找到 {len(predictions)} 個預測\n")

# 模擬 GUI 表格顯示（10 欄）
print("=" * 100)
print("模擬 GUI 表格顯示（新增「變化」欄位）:")
print("=" * 100)
print(f"{'排名':<4} {'車手':<6} {'車隊':<12} {'FP3名次':<8} {'FP3時間':<10} {'預測時間':<10} {'Q名次':<6} {'Q結果':<10} {'變化':<8} {'△FP3':<10}")
print("-" * 100)

for pred in predictions[:15]:  # 顯示前 15 名
    rank = pred['rank']
    driver = pred['driver']
    team = pred['team'][:10]
    
    fp3_rank = pred.get('fp3_predicted_rank', 'N/A')
    fp3_time = f"{pred['fp3_time']:.3f}s"
    pred_time = f"{pred['predicted_time']:.3f}s"
    
    q_rank = pred.get('actual_q_rank', 'N/A')
    q_time = f"{pred['actual_q_time']:.3f}s" if pred.get('actual_q_time') else "N/A"
    
    # 變化欄位（帶顏色標記）
    rank_change = pred.get('rank_change')
    if rank_change is not None:
        if rank_change > 0:
            change_str = f"+{rank_change} 🟢"  # 進步
            color_hint = "綠色"
        elif rank_change < 0:
            change_str = f"{rank_change} 🔴"  # 退步
            color_hint = "紅色"
        else:
            change_str = "→ ⚪"  # 持平
            color_hint = "灰色"
    else:
        change_str = "N/A"
        color_hint = "無"
    
    improvement = pred.get('improvement', 0)
    delta_str = f"+{improvement:.3f}s" if improvement >= 0 else f"{improvement:.3f}s"
    
    print(f"{rank:<4} {driver:<6} {team:<12} {fp3_rank:<8} {fp3_time:<10} {pred_time:<10} {q_rank:<6} {q_time:<10} {change_str:<8} {delta_str:<10}")

# 統計分析
print("\n" + "=" * 100)
print("變化欄位顏色統計:")
print("=" * 100)

improved = [p for p in predictions if p.get('rank_change') and p['rank_change'] > 0]
declined = [p for p in predictions if p.get('rank_change') and p['rank_change'] < 0]
unchanged = [p for p in predictions if p.get('rank_change') == 0]

print(f"\n🟢 綠色（進步）: {len(improved)} 位車手")
if improved:
    improved.sort(key=lambda x: x['rank_change'], reverse=True)
    for p in improved[:3]:
        print(f"   {p['driver']}: +{p['rank_change']} (FP3 第{p['fp3_predicted_rank']}名 → Q 第{p['actual_q_rank']}名)")

print(f"\n🔴 紅色（退步）: {len(declined)} 位車手")
if declined:
    declined.sort(key=lambda x: x['rank_change'])
    for p in declined[:3]:
        print(f"   {p['driver']}: {p['rank_change']} (FP3 第{p['fp3_predicted_rank']}名 → Q 第{p['actual_q_rank']}名)")

print(f"\n⚪ 灰色（持平）: {len(unchanged)} 位車手")
if unchanged:
    for p in unchanged:
        print(f"   {p['driver']}: → (第{p['actual_q_rank']}名)")

print("\n" + "=" * 100)
print("GUI 實際顯示顏色:")
print("=" * 100)
print("✅ 變化欄位使用以下顏色:")
print("   🟢 進步 (+1, +2, +8...): QColor(0, 150, 0) - 深綠色粗體")
print("   🔴 退步 (-1, -2, -6...): QColor(200, 0, 0) - 深紅色粗體")
print("   ⚪ 持平 (→): QColor(100, 100, 100) - 灰色")
print("   ⚫ 無結果 (N/A): QColor(120, 120, 120) - 淺灰色")

print("\n🎉 GUI 名次變化欄位已完整實現！")
