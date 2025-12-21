#!/usr/bin/env python3
"""測試 F92 FP2 數據載入"""

from CLI_modules.cli.prediction.f92_hybrid_predictor import F92HybridPredictor

predictor = F92HybridPredictor(verbose=True)

# 測試 Japan 2025 FP2 載入
print('='*60)
print('測試 Japan 2025 FP2 載入')
print('='*60)
fp2_data = predictor._load_fp2_data(2025, 'Japan')
if fp2_data:
    source = fp2_data.get('source', 'LiveF1')
    print(f'成功! FP2 數據來源: {source}')
    print(f'  最快圈: {fp2_data["fp2_best_lap"]:.3f}s')
    print(f'  平均圈: {fp2_data["fp2_mean_lap"]:.3f}s')
    print(f'  有效圈數: {fp2_data["fp2_lap_count"]}')
else:
    print('失敗! 無法載入 FP2 數據')

# 測試 Mexico 2025 FP2 載入
print('\n' + '='*60)
print('測試 Mexico 2025 FP2 載入')
print('='*60)
fp2_data = predictor._load_fp2_data(2025, 'Mexico')
if fp2_data:
    source = fp2_data.get('source', 'LiveF1')
    print(f'成功! FP2 數據來源: {source}')
    print(f'  最快圈: {fp2_data["fp2_best_lap"]:.3f}s')
    print(f'  平均圈: {fp2_data["fp2_mean_lap"]:.3f}s')
    print(f'  有效圈數: {fp2_data["fp2_lap_count"]}')
else:
    print('失敗! 無法載入 FP2 數據')
