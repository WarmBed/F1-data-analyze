#!/usr/bin/env python3
"""顯示主要升級統計資訊"""
import json

with open('2025_f1_major_upgrades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

metadata = data['metadata']
stats = metadata['統計資訊']

print("="*80)
print("📊 2025 F1 主要部件升級統計")
print("="*80)
print(f"\n總主要升級次數: {stats['總升級次數']} 次")
print(f"數據源: {metadata['數據源']}")
print(f"生成時間: {metadata['生成時間']}")

print("\n" + "="*80)
print("🏆 各車隊主要升級次數:")
print("="*80)
for team, count in stats['各車隊主要升級次數'].items():
    print(f"  {team:<25} {count:>3} 次")

print("\n" + "="*80)
print("🔧 各部件類別次數:")
print("="*80)
for category, count in stats['各部件類別次數'].items():
    print(f"  {category:<25} {count:>3} 次")

print("\n" + "="*80)
print("👨‍🏎️ 各車手主要升級次數 (Top 10):")
print("="*80)
for driver, count in list(stats['各車手主要升級次數'].items())[:10]:
    print(f"  {driver:<25} {count:>3} 次")

print("\n" + "="*80)
print(f"✅ 詳細記錄已儲存至: 2025_f1_major_upgrades.json")
print(f"   共 {len(data['主要部件升級記錄'])} 筆主要部件升級記錄")
print("="*80)
