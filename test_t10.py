#!/usr/bin/env python3
"""測試 0-10 km/h 功能"""
from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader

loader = StartReactionDataLoader(2025, 'Abu_Dhabi', 'R')
data = loader.load_data()

print("=" * 60)
print("0-10 km/h (離合器反應) 和 0-20 km/h (起步反應) 測試")
print("=" * 60)
print(f"\n車手數量: {len(data['drivers'])}")
print(f"\n{'車手':<6} | {'0-10 km/h':>12} | {'0-20 km/h':>12}")
print("-" * 40)

# 按 t10 排序
sorted_drivers = sorted([d for d in data['drivers'] if d.get('t10')], key=lambda x: x['t10'])

for d in sorted_drivers[:10]:
    t10 = d.get('t10', 0)
    t20 = d.get('t20', 0)
    print(f"{d['name']:<6} | {t10:>10.3f}s | {t20:>10.3f}s")

print("\n" + "=" * 60)
print("測試成功！")
