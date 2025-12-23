#!/usr/bin/env python3
"""檢查噪音過濾效果"""
import json
from pathlib import Path

# 讀取簡化版 JSON
base_dir = Path(".")
simple = json.load(open(base_dir / '2025_f1_parts_changes_simple.json', encoding='utf-8'))

print("=" * 70)
print("噪音過濾效果檢查")
print("=" * 70)

print(f"\n📊 記錄數統計:")
print(f"   簡化版: {len(simple)} 筆")

# 檢查噪音關鍵字
noise_keywords = [
    'request from the team',
    'Article 40.3',
    'Jo Bauer',
    'Technical Delegate',
    'All above parts',
    'Sporting Regulations',
    'approval of the',
    'being in accordance',
    'From The FIA'
]

print(f"\n🔍 噪音關鍵字檢查:")
found_noise = []
for keyword in noise_keywords:
    matches = [r for r in simple if keyword in r.get('部件', '')]
    if matches:
        print(f"   ❌ '{keyword}': 找到 {len(matches)} 筆")
        found_noise.extend(matches)
    else:
        print(f"   ✅ '{keyword}': 0 筆")

# 顯示範例
if found_noise:
    print(f"\n⚠️  仍有噪音記錄範例:")
    for r in found_noise[:5]:
        part = r.get('部件', '')
        print(f"   - {part[:80]}...")
else:
    print(f"\n✅ 沒有找到噪音記錄！過濾成功")

# 檢查有效部件範例
print(f"\n📋 有效部件記錄範例 (前 10 筆):")
valid_parts = simple[:10]
for idx, r in enumerate(valid_parts, 1):
    print(f"   {idx}. {r.get('車隊'):15s} {r.get('部件')[:50]}")

print(f"\n{'='*70}")
