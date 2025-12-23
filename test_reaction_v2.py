#!/usr/bin/env python3
"""測試更新後的起跑反應分析"""
from modules.gui.race_analysis.start_reaction.start_reaction_loader import StartReactionDataLoader

loader = StartReactionDataLoader(2025, 'Abu_Dhabi', 'R')
data = loader.load_data()

print("=" * 60)
print("起跑反應分析測試 (方案 C)")
print("=" * 60)

print(f"\n車手數量: {len(data['drivers'])}")
print(f"反應批次時間: {data.get('reaction_batch_time', 0):.3f}s")

print("\n" + "-" * 60)
print("起跑反應速度 (Reaction Speed) - 按速度排序")
print("-" * 60)

# 按 reaction_speed 排序
sorted_by_reaction = sorted(
    [d for d in data['drivers'] if d.get('reaction_speed', 0) > 0],
    key=lambda x: -x['reaction_speed']
)

print(f"\n{'排名':<4} | {'車手':<6} | {'反應速度':>10} | {'0-10 km/h':>12} | {'0-20 km/h':>12}")
print("-" * 60)

for rank, d in enumerate(sorted_by_reaction, 1):
    reaction = d.get('reaction_speed', 0)
    t10 = d.get('t10', 0) or 0
    t20 = d.get('t20', 0) or 0
    print(f"{rank:<4} | {d['name']:<6} | {reaction:>8} km/h | {t10:>10.3f}s | {t20:>10.3f}s")

print("\n" + "=" * 60)
print("分數權重:")
print("  - Reaction Speed: 30 分 (速度越高越好)")
print("  - 0-10 km/h: 25 分 (時間越短越好)")
print("  - 0-20 km/h: 25 分 (時間越短越好)")
print("  - Position Change: 20 分")
print("=" * 60)
