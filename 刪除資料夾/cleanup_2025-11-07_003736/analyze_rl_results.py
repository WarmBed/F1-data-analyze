"""分析 PPO 訓練結果"""
import json
import numpy as np
from pathlib import Path

# 讀取訓練歷史
history_file = Path('rl_training_history.json')
with open(history_file, 'r', encoding='utf-8') as f:
    history = json.load(f)

print(f"{'='*70}")
print(f"PPO 訓練結果分析")
print(f"{'='*70}\n")

# 基本統計
total_steps = len(history)
accuracies = [step['accuracy'] for step in history]
best_accuracy = max(accuracies)
avg_accuracy = sum(accuracies) / len(accuracies)
baseline = 0.58

print(f"訓練統計:")
print(f"  總步數: {total_steps}")
print(f"  基準準確率: {baseline:.2%}")
print(f"  平均準確率: {avg_accuracy:.2%} ({(avg_accuracy-baseline)*100:+.2f}%)")
print(f"  最佳準確率: {best_accuracy:.2%} ({(best_accuracy-baseline)*100:+.2f}%)")
print(f"  標準差: {np.std(accuracies):.4f}")

# 找出最佳配置
best_step = max(history, key=lambda x: x['accuracy'])
print(f"\n最佳配置 (Step {best_step['step']}):")
print(f"  準確率: {best_step['accuracy']:.2%}")
print(f"  賽道: {best_step['track']}")
print(f"  特徵: {best_step['feature']}")
print(f"  調整量: {best_step['delta']:+.4f}")
print(f"  舊值: {best_step['old_value']:.4f}")
print(f"  新值: {best_step['new_value']:.4f}")

# 按賽道統計調整次數
track_counts = {}
for step in history:
    track = step['track']
    track_counts[track] = track_counts.get(track, 0) + 1

print(f"\n賽道調整次數:")
for track, count in sorted(track_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {track:20s}: {count:4d} 次")

# 特徵調整統計
feature_stats = {'improvement_weight': [], 'speed_weight': []}
for step in history:
    feature = step['feature']
    feature_stats[feature].append(step['new_value'])

print(f"\n特徵權重分布:")
for feature, values in feature_stats.items():
    print(f"  {feature:20s}: 平均 {np.mean(values):.3f}, "
          f"範圍 [{np.min(values):.3f}, {np.max(values):.3f}]")

# 最後 10 步配置
print(f"\n最後 10 步調整:")
for step in history[-10:]:
    print(f"  Step {step['step']:4d}: {step['track']:15s} "
          f"{step['feature']:20s} {step['delta']:+.3f} → "
          f"{step['new_value']:.3f} (準確率: {step['accuracy']:.2%})")

# 找出所有超過基準的配置
improvements = [s for s in history if s['accuracy'] > baseline]
print(f"\n超過基準的配置數量: {len(improvements)}/{total_steps} ({len(improvements)/total_steps*100:.1f}%)")
if improvements:
    print(f"前 5 個改進:")
    for i, step in enumerate(sorted(improvements, key=lambda x: x['accuracy'], reverse=True)[:5], 1):
        print(f"  {i}. Step {step['step']:4d}: {step['accuracy']:.2%} "
              f"({step['track']}, {step['feature']}, {step['delta']:+.3f})")

# 保存最佳配置
best_config = {}
tracks = [
    'Bahrain', 'Saudi_Arabia', 'Japan', 'Monaco', 'Canada',
    'Great_Britain', 'Hungary', 'Netherlands', 'Italy', 'Azerbaijan'
]

# 從最佳步驟提取完整配置（需要重建）
# 這裡簡化：使用最後一步的配置
print(f"\n注意: 完整的最佳配置需要從訓練模型中提取")
print(f"建議使用: python f1_rl_optimizer.py --mode test")

print(f"\n{'='*70}")
