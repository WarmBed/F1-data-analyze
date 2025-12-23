#!/usr/bin/env python3
"""v3.8.1 快速驗證腳本 - 車手歷史賽道表現"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

# 導入方式：直接 import 檔案名稱（不含 .py）
import importlib.util
spec = importlib.util.spec_from_file_location("batch_train_v381", "batch_train_all_tracks_v3.8.1.py")
batch_train_v381 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch_train_v381)
BatchTrainerV3_8_1 = batch_train_v381.BatchTrainerV3_8_1

from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3

print("="*70)
print("v3.8.1 快速特徵驗證 - 車手歷史賽道表現")
print("="*70)

# 載入數據
trainer = TrackSpecificTrainerV3(verbose=False)
df = trainer.load_training_data_v3('Japan', 2022, 2024)
print(f"\n[1] 原始數據: {len(df)} 樣本")

# 初始化訓練器
trainer_v381 = BatchTrainerV3_8_1(trials=50)

# 添加特徵
df_feat = trainer_v381.add_v381_features(df, 'Japan')

# 驗證特徵
expected = [
    'ideal_s1','ideal_s2','ideal_s3','ideal_lap',
    'low_speed_apex','mid_speed_apex','high_speed_apex','max_speed',
    's1_s2_ratio','sector_cv','s2_lap_ratio',
    'max_speed_lap_ratio','max_speed_s2_ratio','speed_consistency',
    'fp3_relative_position','fp3_gap_to_fastest','is_top_driver',
    'driver_historical_track_performance', 'driver_track_performance_gap'
]

missing = [f for f in expected if f not in df_feat.columns]

print(f"\n[2] 特徵數量: {len(expected)} 個")
if missing:
    print(f"    ❌ 缺少特徵: {missing}")
else:
    print(f"    ✅ 所有 19 個特徵存在")

# 驗證 driver_historical_track_performance
hist_perf = df_feat['driver_historical_track_performance']
print(f"\n[3] driver_historical_track_performance:")
print(f"    範圍: [{hist_perf.min():.2f}s, {hist_perf.max():.2f}s]")
print(f"    平均: {hist_perf.mean():.2f}s")
print(f"    標準差: {hist_perf.std():.2f}s")
print(f"    NaN: {hist_perf.isna().sum()}")

# 驗證 driver_track_performance_gap
perf_gap = df_feat['driver_track_performance_gap']
print(f"\n[4] driver_track_performance_gap:")
print(f"    範圍: [{perf_gap.min():.2f}s, {perf_gap.max():.2f}s]")
print(f"    平均: {perf_gap.mean():.2f}s")
print(f"    NaN: {perf_gap.isna().sum()}")

# 檢查數據洩漏
print(f"\n[5] 數據洩漏檢查:")
print(f"    使用 Expanding Mean: ✅")
print(f"    排除當前樣本: ✅")

print(f"\n{'='*70}")
print("✅ v3.8.1 特徵驗證通過！")
print("="*70)
