import json

data = json.load(open('fp2_q_v3.10_training_results.json'))
cv_maes = [v['cv_mae'] for v in data.values()]
r2s = [v['train_r2'] for v in data.values()]
samples = [v['sample_count'] for v in data.values()]

print(f'\n=== 2022-2025 訓練結果摘要 ===')
print(f'訓練賽道數: {len(data)}')
print(f'總樣本數: {sum(samples)}')
print(f'平均 CV MAE: {sum(cv_maes)/len(cv_maes):.3f} 秒')
print(f'平均 Train R²: {sum(r2s)/len(r2s):.4f}')

best_idx = cv_maes.index(min(cv_maes))
worst_idx = cv_maes.index(max(cv_maes))
most_samples_idx = samples.index(max(samples))
least_samples_idx = samples.index(min(samples))

tracks = list(data.keys())
print(f'\n最佳 MAE: {min(cv_maes):.3f} 秒 ({tracks[best_idx]})')
print(f'最差 MAE: {max(cv_maes):.3f} 秒 ({tracks[worst_idx]})')
print(f'\n樣本最多: {max(samples)} ({tracks[most_samples_idx]})')
print(f'樣本最少: {min(samples)} ({tracks[least_samples_idx]})')
