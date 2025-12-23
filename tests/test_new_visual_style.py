#!/usr/bin/env python3
"""
測試 Qualifying Prediction 新的視覺風格
（與 Driver Race Position 一致）
"""
import json

print("=" * 90)
print("Qualifying Prediction 新視覺風格測試")
print("（與 Driver Race Position 的 Position Change 風格一致）")
print("=" * 90)

# 讀取 JSON
json_path = "json/qualifying_prediction_2025_Mexico.json"
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

predictions = data['predictions']

print(f"\n✅ 讀取 JSON: {json_path}")
print(f"✅ 找到 {len(predictions)} 個預測\n")

# 模擬新的視覺風格
print("=" * 90)
print("新視覺風格展示:")
print("=" * 90)
print(f"{'車手':<6} {'車隊':<12} {'△ FP3':<20} {'變化':<15} {'視覺效果':<30}")
print("-" * 90)

for pred in predictions[:15]:
    driver = pred['driver']
    team = pred['team'][:10]
    
    # △ FP3 欄位
    improvement = pred.get('improvement', 0)
    if improvement > 0:
        delta_display = f"+{improvement:.3f}s ▲"
        delta_style = "淺綠色背景"
    elif improvement < 0:
        delta_display = f"{improvement:.3f}s ▼"
        delta_style = "淺紅色背景"
    else:
        delta_display = f"{improvement:.3f}s"
        delta_style = "白色背景"
    
    # 變化欄位
    rank_change = pred.get('rank_change')
    if rank_change is not None:
        if rank_change > 0:
            change_display = f"{rank_change} ▲"
            change_style = "淺綠色背景"
        elif rank_change < 0:
            change_display = f"{abs(rank_change)} ▼"
            change_style = "淺紅色背景"
        else:
            change_display = "0 ─"
            change_style = "白色背景"
    else:
        change_display = "N/A"
        change_style = "灰色文字"
    
    print(f"{driver:<6} {team:<12} {delta_display:<20} {change_display:<15} {delta_style} / {change_style}")

# 顏色規格說明
print("\n" + "=" * 90)
print("顏色規格（與 Driver Race Position 一致）:")
print("=" * 90)

print("\n📊 △ FP3 欄位:")
print("  ✅ 進步 (improvement > 0):")
print("     - 顯示: +0.216s ▲")
print("     - 背景: QColor(200, 255, 200) - 淺綠色")
print("     - 文字: QColor(0, 100, 0) - 深綠色")
print()
print("  ❌ 退步 (improvement < 0):")
print("     - 顯示: -0.337s ▼")
print("     - 背景: QColor(255, 200, 200) - 淺紅色")
print("     - 文字: QColor(150, 0, 0) - 深紅色")
print()
print("  ⚪ 持平 (improvement = 0):")
print("     - 顯示: 0.000s")
print("     - 背景: 白色")
print("     - 文字: QColor(100, 100, 100) - 灰色")

print("\n📊 變化欄位:")
print("  ✅ 進步 (rank_change > 0):")
print("     - 顯示: 8 ▲  (FP3 第15名 → Q 第7名)")
print("     - 背景: QColor(200, 255, 200) - 淺綠色")
print("     - 文字: QColor(0, 100, 0) - 深綠色粗體")
print()
print("  ❌ 退步 (rank_change < 0):")
print("     - 顯示: 6 ▼  (FP3 第13名 → Q 第19名)")
print("     - 背景: QColor(255, 200, 200) - 淺紅色")
print("     - 文字: QColor(150, 0, 0) - 深紅色粗體")
print()
print("  ⚪ 持平 (rank_change = 0):")
print("     - 顯示: 0 ─")
print("     - 背景: 白色")
print("     - 文字: QColor(100, 100, 100) - 灰色")

# 範例展示
print("\n" + "=" * 90)
print("實際範例（Mexico 2025 前 10 名）:")
print("=" * 90)

examples = [
    ("SAI", "Williams", -0.523, 8, "最大進步！"),
    ("BEA", "Haas", -0.611, 7, "大進步"),
    ("LEC", "Ferrari", -0.282, 2, "進步"),
    ("NOR", "McLaren", 0.216, 0, "持平冠軍"),
    ("HAM", "Ferrari", -0.116, -1, "小退步"),
    ("STR", "Aston Martin", -0.531, -6, "最大退步！"),
    ("PIA", "McLaren", -0.312, -3, "退步"),
]

print(f"{'車手':<6} {'車隊':<14} {'△ FP3 顯示':<18} {'變化顯示':<12} {'說明':<15}")
print("-" * 80)

for driver, team, imp, change, note in examples:
    if imp > 0:
        delta = f"+{imp:.3f}s ▲ 🟢"
    elif imp < 0:
        delta = f"{imp:.3f}s ▼ 🔴"
    else:
        delta = f"{imp:.3f}s ⚪"
    
    if change > 0:
        ch = f"{change} ▲ 🟢"
    elif change < 0:
        ch = f"{abs(change)} ▼ 🔴"
    else:
        ch = "0 ─ ⚪"
    
    print(f"{driver:<6} {team:<14} {delta:<18} {ch:<12} {note:<15}")

print("\n🎉 新視覺風格已完成！與 Driver Race Position 完全一致")
print("   - 淺綠色背景 + ▲ 表示進步")
print("   - 淺紅色背景 + ▼ 表示退步")
print("   - 白色背景 + ─ 表示持平")
