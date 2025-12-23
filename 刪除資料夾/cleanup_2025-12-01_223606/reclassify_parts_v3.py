#!/usr/bin/env python3
"""
重新分類 2025 F1 Parts Changes - V3.0
使用更新的分類器（含 15 個主分類 + 61 個子分類）
"""
import json
from CLI_modules.cli.core.fia_parts_classifier import UpgradeClassifierV2

print("=" * 80)
print("重新分類 2025 F1 Parts Changes - V3.0")
print("含完整分類層級：15 個主分類 + 61 個子分類")
print("=" * 80)

# 讀取原始資料
input_file = "2025_f1_parts_changes_v2_normalized.json"
output_file = "2025_f1_parts_changes_v2_classified.json"

print(f"\n[1/4] 讀取原始資料: {input_file}")
with open(input_file, 'r', encoding='utf-8') as f:
    original_data = json.load(f)

print(f"   ✅ 載入 {len(original_data)} 筆原始記錄")

# 初始化分類器 V3.0
print("\n[2/4] 初始化分類器 V3.0...")
classifier = UpgradeClassifierV2()
print("   ✅ 分類器已就緒")
print("   • 15 個主分類")
print("   • 61 個子分類")
print("   • 6 種變更類型")

# 執行分類
print("\n[3/4] 開始批次分類...")
reclassified_data = classifier.classify_batch(original_data, remove_duplicates=True)
print(f"   ✅ 分類完成：{len(reclassified_data)} 筆記錄（已去重）")

# 統計分析
from collections import Counter

change_types = Counter([r.get("變更類型", "未知") for r in reclassified_data])
main_categories = Counter([r.get("主分類", "未知") for r in reclassified_data])
sub_categories = Counter([r.get("子分類", "未知") for r in reclassified_data])

print("\n   📊 變更類型統計:")
for ctype, count in change_types.most_common():
    pct = count / len(reclassified_data) * 100
    print(f"      {ctype}: {count} ({pct:.1f}%)")

print("\n   📊 主分類統計 (Top 10):")
for main_cat, count in main_categories.most_common(10):
    pct = count / len(reclassified_data) * 100
    print(f"      {main_cat}: {count} ({pct:.1f}%)")

print("\n   📊 子分類統計 (Top 10):")
for sub_cat, count in sub_categories.most_common(10):
    pct = count / len(reclassified_data) * 100
    print(f"      {sub_cat}: {count} ({pct:.1f}%)")

# 保存結果
print(f"\n[4/4] 保存分類結果: {output_file}")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(reclassified_data, f, ensure_ascii=False, indent=2)

print(f"   ✅ 檔案已保存：{len(reclassified_data)} 筆記錄")

# 驗證完整性
print("\n[驗證] 檢查欄位完整性...")
sample = reclassified_data[0] if reclassified_data else {}
required_fields = ["主分類", "子分類", "變更類型", "分類信心度"]
for field in required_fields:
    if field in sample:
        print(f"   ✅ {field}: {sample[field]}")
    else:
        print(f"   ❌ {field}: 缺失!")

print("\n" + "=" * 80)
print("✅ 重新分類完成！")
print("=" * 80)
print(f"輸出檔案: {output_file}")
print(f"總記錄數: {len(reclassified_data)}")
print(f"主分類數: {len(main_categories)}")
print(f"子分類數: {len(sub_categories)}")
