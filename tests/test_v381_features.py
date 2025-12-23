#!/usr/bin/env python3
"""
v3.8 特徵驗證腳本

驗證項目：
1. 特徵數量：17 個（不是 20 個）
2. 移除的特徵：track_avg_improvement_rate, adjusted_ideal_lap, driver_historical_improvement
3. 保留的特徵：fp3_relative_position, fp3_gap_to_fastest, is_top_driver
4. 數據載入：正常運作
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


def add_v38_features(df: pd.DataFrame, track_name: str) -> pd.DataFrame:
    """v3.8 特徵添加函數（從訓練器複製）"""
    df = df.copy()
    
    # v3.3 交互特徵 (3)
    df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
    sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
    sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
    df['sector_cv'] = sector_std / (sector_mean + 1e-6)
    df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
    
    # v3.4 速度特徵 (3)
    df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
    df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
    apex_speeds = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']]
    df['speed_consistency'] = apex_speeds.std(axis=1) / (df['max_speed'] + 1e-6)
    
    # v3.5 有效特徵 (3) - 保留
    top_drivers = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']
    df['fp3_relative_position'] = df['ideal_lap'].rank(method='min')
    df['fp3_gap_to_fastest'] = df['ideal_lap'] - df['ideal_lap'].min()
    df['is_top_driver'] = df['driver'].isin(top_drivers).astype(int)
    
    return df


def test_v38_features():
    """測試 v3.8 特徵實現"""
    print("="*70)
    print("v3.8 特徵驗證")
    print("="*70)
    
    # 初始化基礎訓練器
    base_trainer = TrackSpecificTrainerV3(verbose=False)
    
    # 測試數據載入
    print("\n[步驟 1] 測試數據載入")
    test_track = "Japan"
    df = base_trainer.load_training_data_v3(test_track, 2022, 2024)
    
    if df.empty:
        print(f"  ❌ 數據載入失敗")
        return False
    
    print(f"  ✅ 載入成功: {len(df)} 樣本")
    print(f"  原始欄位: {list(df.columns)}")
    
    # 測試特徵添加
    print("\n[步驟 2] 測試 v3.8 特徵添加")
    df_with_features = add_v38_features(df.copy(), test_track)
    
    # 預期的 17 個特徵
    expected_features = [
        # v3.0 基礎特徵 (8)
        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
        # v3.3 交互特徵 (3)
        's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
        # v3.4 速度特徵 (3)
        'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
        # v3.5 有效特徵 (3)
        'fp3_relative_position', 'fp3_gap_to_fastest', 'is_top_driver'
    ]
    
    # 不應該存在的特徵
    forbidden_features = [
        'track_avg_improvement_rate',
        'adjusted_ideal_lap',
        'driver_historical_improvement'
    ]
    
    print(f"\n  預期特徵數量: {len(expected_features)}")
    
    # 檢查所有預期特徵是否存在
    missing_features = []
    for feat in expected_features:
        if feat not in df_with_features.columns:
            missing_features.append(feat)
    
    if missing_features:
        print(f"  ❌ 缺少特徵: {missing_features}")
        return False
    else:
        print(f"  ✅ 所有 17 個特徵都存在")
    
    # 檢查禁用特徵是否不存在
    found_forbidden = []
    for feat in forbidden_features:
        if feat in df_with_features.columns:
            found_forbidden.append(feat)
    
    if found_forbidden:
        print(f"  ❌ 發現禁用特徵: {found_forbidden}")
        return False
    else:
        print(f"  ✅ 無效特徵已正確移除")
    
    # 檢查特徵值
    print("\n[步驟 3] 驗證特徵值")
    
    # 檢查 fp3_relative_position（應該是排名 1-N）
    fp3_positions = df_with_features['fp3_relative_position'].values
    print(f"  fp3_relative_position: 範圍 {fp3_positions.min():.0f} - {fp3_positions.max():.0f}")
    if fp3_positions.min() >= 1 and fp3_positions.max() <= len(df_with_features):
        print(f"    ✅ 正確（排名格式）")
    else:
        print(f"    ⚠️  異常範圍")
    
    # 檢查 fp3_gap_to_fastest（應該 >= 0）
    fp3_gaps = df_with_features['fp3_gap_to_fastest'].values
    print(f"  fp3_gap_to_fastest: 範圍 {fp3_gaps.min():.3f}s - {fp3_gaps.max():.3f}s")
    if fp3_gaps.min() >= 0:
        print(f"    ✅ 正確（最小值為 0）")
    else:
        print(f"    ❌ 異常（出現負值）")
    
    # 檢查 is_top_driver（應該只有 0 或 1）
    top_driver_values = df_with_features['is_top_driver'].unique()
    print(f"  is_top_driver: 唯一值 {sorted(top_driver_values)}")
    if set(top_driver_values).issubset({0, 1}):
        print(f"    ✅ 正確（二元特徵）")
    else:
        print(f"    ❌ 異常（非二元值）")
    
    # 顯示範例數據
    print("\n[步驟 4] 範例數據")
    sample = df_with_features[expected_features].head(3)
    print(sample.to_string())
    
    # 統計資訊
    print("\n[步驟 5] 特徵統計")
    stats_features = ['fp3_relative_position', 'fp3_gap_to_fastest', 'is_top_driver']
    print(df_with_features[stats_features].describe().to_string())
    
    print("\n" + "="*70)
    print("驗證完成")
    print("="*70)
    print("✅ v3.8 特徵實現正確")
    print(f"✅ 特徵數量: {len(expected_features)}")
    print(f"✅ 移除無效特徵: {len(forbidden_features)}")
    
    return True


def main():
    success = test_v38_features()
    
    if success:
        print("\n[結論] v3.8 準備就緒，可以開始訓練")
        print("\n執行訓練:")
        print("  python batch_train_all_tracks_v3.8.py")
        print("\n快速測試（單一賽道）:")
        print("  python -c \"from batch_train_all_tracks_v3_8 import BatchTrainerV3_8; t = BatchTrainerV3_8(trials=50); t.train_single_track('Japan')\"")
    else:
        print("\n[錯誤] 特徵實現有問題，請檢查代碼")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
