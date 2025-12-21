#!/usr/bin/env python3
"""驗證 Function 29 簡化版清理結果"""
import json
from pathlib import Path

print("=" * 60)
print("Function 29 簡化版驗證")
print("=" * 60)

# 檢查 JSON 檔案
json_file = "2025_f1_parts_changes_classified.json"
if Path(json_file).exists():
    data = json.load(open(json_file, encoding='utf-8'))
    
    print(f"\n✅ 主 JSON 檔案: {json_file}")
    print(f"   總記錄數: {len(data)}")
    
    races = set(r.get("賽事", "Unknown") for r in data)
    print(f"   涵蓋賽事: {len(races)} 場")
    
    noise = [r for r in data if "噪音" in r.get("變更類型", "")]
    print(f"   噪音記錄: {len(noise)} 筆 ({len(noise)/len(data)*100:.1f}%)")
    
    unclassified = [r for r in data if "未分類" in r.get("變更類型", "")]
    print(f"   未分類記錄: {len(unclassified)} 筆 ({len(unclassified)/len(data)*100:.1f}%)")
    
    valid = len(data) - len(noise) - len(unclassified)
    print(f"   有效記錄: {valid} 筆 ({valid/len(data)*100:.1f}%)")
else:
    print(f"\n❌ 找不到: {json_file}")

# 檢查舊版檔案是否已刪除
print(f"\n{'='*60}")
print("舊版 JSON 檔案檢查")
print("=" * 60)

old_files = [
    "2025_f1_parts_changes_v2_classified.json",
    "2025_f1_parts_changes_v2_normalized.json",
    "2025_f1_parts_changes_v2_classified_with_categories.json"
]

all_deleted = True
for file in old_files:
    if Path(file).exists():
        print(f"❌ 仍存在: {file}")
        all_deleted = False
    else:
        print(f"✅ 已刪除: {file}")

if all_deleted:
    print(f"\n✅ 所有舊版檔案已成功刪除")
else:
    print(f"\n⚠️  仍有舊版檔案存在")

# 顯示最終檔案列表
print(f"\n{'='*60}")
print("最終 JSON 檔案列表")
print("=" * 60)

parts_files = list(Path(".").glob("*f1_parts_changes*.json"))
if parts_files:
    for f in sorted(parts_files):
        size_kb = f.stat().st_size / 1024
        print(f"📄 {f.name} ({size_kb:.1f} KB)")
else:
    print("⚠️  沒有找到 Parts Changes JSON 檔案")

print(f"\n{'='*60}")
print("✅ 驗證完成")
print("=" * 60)
