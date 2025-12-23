#!/usr/bin/env python3
"""
測試新的欄位順序
"""
import json

print("=" * 100)
print("GUI 欄位順序調整測試 (2025-11-05)")
print("=" * 100)

# 讀取 JSON
json_path = "json/qualifying_prediction_2025_Mexico.json"
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data['predictions']

print(f"\n✅ 讀取 JSON: {json_path}")
print(f"✅ 找到 {len(predictions)} 個預測\n")

# 新的欄位順序
print("=" * 110)
print("新欄位順序: 車手 → 車隊 → FP3時間 → 預測時間 → Q時間 → △FP3 → 預測名次 → Q名次 → 變化")
print("=" * 110)

# 表頭
print(f"{'排名':<4} {'車手':<6} {'車隊':<12} {'FP3時間':<10} {'預測時間':<10} {'Q時間':<10} {'△FP3':<10} {'預測名次':<8} {'Q名次':<6} {'變化':<8}")
print("-" * 110)

# 顯示前 15 名
for pred in predictions[:15]:
    rank = pred['rank']
    driver = pred['driver']
    team = pred['team'][:10]
    
    fp3_time = f"{pred['fp3_time']:.3f}s"
    pred_time = f"{pred['predicted_time']:.3f}s"
    q_time = f"{pred['actual_q_time']:.3f}s" if pred.get('actual_q_time') else "N/A"
    
    improvement = pred.get('improvement', 0)
    delta_str = f"+{improvement:.3f}s" if improvement >= 0 else f"{improvement:.3f}s"
    
    fp3_rank = pred.get('fp3_predicted_rank', 'N/A')
    q_rank = pred.get('actual_q_rank', 'N/A')
    
    # 變化欄位
    rank_change = pred.get('rank_change')
    if rank_change is not None:
        if rank_change > 0:
            change_str = f"+{rank_change} 🟢"
        elif rank_change < 0:
            change_str = f"{rank_change} 🔴"
        else:
            change_str = "→ ⚪"
    else:
        change_str = "N/A"
    
    print(f"{rank:<4} {driver:<6} {team:<12} {fp3_time:<10} {pred_time:<10} {q_time:<10} {delta_str:<10} {fp3_rank:<8} {q_rank:<6} {change_str:<8}")

print("\n" + "=" * 110)
print("欄位說明:")
print("=" * 110)
print("""
1. 車手 - 車手代號（背景色）
2. 車隊 - 車隊名稱（背景色）
3. FP3時間 - FP3 最快圈速
4. 預測時間 - 模型預測的 Q 時間（粗體）
5. Q時間 - 實際 Q 最快圈速
6. △FP3 - 預測時間與 FP3 的差異（梯度背景色）
7. 預測名次 - 根據 FP3 時間排序的名次
8. Q名次 - 實際 Q 排位結果（綠色粗體）
9. 變化 - 預測名次 vs Q名次的變化（綠色=進步，紅色=退步）
""")

print("=" * 110)
print("顏色方案:")
print("=" * 110)
print("""
【變化欄位】
  🟢 +N (進步): QColor(0, 150, 0) - 深綠色粗體
  🔴 -N (退步): QColor(200, 0, 0) - 深紅色粗體
  ⚪ → (持平): QColor(100, 100, 100) - 灰色

【△FP3 欄位】
  梯度背景色: 根據改善幅度自動計算

【Q名次欄位】
  QColor(0, 100, 0) - 綠色粗體

【車手/車隊欄位】
  使用 color_palette_provider 獲取車手專屬背景色
""")

print("\n🎉 欄位順序調整完成！")
print("💡 請在 GUI 中測試 Qualifying Prediction 模組，確認欄位順序正確。")
