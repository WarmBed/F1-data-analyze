"""驗證分類結果"""
import json

# 讀取分類後的數據
with open('2025_f1_parts_changes_v2_classified_with_categories.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 顯示各主分類的範例
categories = [
    "前翼相關", "後翼相關", "底板相關", "煞車系統", "懸吊系統",
    "動力單元", "變速箱", "轉向系統", "電子系統", "車體結構",
    "冷卻系統", "安全裝備", "感測器", "參數調整", "其他部件"
]

print("="*70)
print("分類結果驗證 - 每個主分類顯示 2 筆範例")
print("="*70)

for cat in categories:
    samples = [r for r in data if r.get('主分類') == cat][:2]
    if samples:
        print(f"\n【{cat}】 (共 {len([r for r in data if r.get('主分類') == cat])} 筆)")
        for i, record in enumerate(samples, 1):
            print(f"  範例 {i}:")
            print(f"    部件: {record.get('部件', 'N/A')}")
            print(f"    子分類: {record.get('子分類', 'N/A')}")
            print(f"    賽事: {record.get('賽事', 'N/A')}")
            print(f"    車隊: {record.get('車隊', 'N/A')}")

print("\n" + "="*70)
print("✅ 驗證完成")
print("="*70)
