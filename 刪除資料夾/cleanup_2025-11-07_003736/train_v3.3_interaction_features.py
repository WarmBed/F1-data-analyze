#!/usr/bin/env python3
"""
F1 v3.3 訓練腳本 - 方案 C：交互特徵實驗

設計原則：
- 基於 v3.0 的 8 個物理特徵
- 添加 3 個交互特徵：
  1. s1_s2_ratio: S1/S2 時間比率（捕捉賽道平衡）
  2. sector_cv: Sector 變異係數（捕捉一致性）
  3. s2_lap_ratio: S2/Ideal Lap 比率（捕捉 S2 權重）
- 總計 11 個特徵
- 使用 XGBRegressor（與 v3.0 相同參數）

目標：
- 減少 Abu Dhabi S2 主導性（46.85% → ?）
- 保持 Mexico 高效能（R² 0.8044）
- 提供更豐富的特徵空間
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 機器學習庫
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# 複用現有訓練器載入數據
import sys
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class TrainerV3_3_InteractionFeatures:
    """v3.3 訓練器 - 交互特徵實驗"""
    
    def __init__(self):
        """初始化訓練器"""
        self.base_trainer = TrackSpecificTrainerV3(verbose=True)
        self.models_dir = Path("models/track_specific_v3.3")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*70)
        print("F1 v3.3 訓練器 - 方案 C：交互特徵實驗")
        print("="*70)
        print("\n基礎特徵 (v3.0 - 8 特徵):")
        print("  1. ideal_s1, ideal_s2, ideal_s3, ideal_lap")
        print("  2. low_speed_apex, mid_speed_apex, high_speed_apex")
        print("  3. max_speed")
        print("\n新增交互特徵 (3 特徵):")
        print("  4. s1_s2_ratio = ideal_s1 / ideal_s2")
        print("  5. sector_cv = std(S1,S2,S3) / mean(S1,S2,S3)")
        print("  6. s2_lap_ratio = ideal_s2 / ideal_lap")
        print("\n總計：11 特徵")
        print("="*70)
    
    def add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加交互特徵
        
        Args:
            df: 原始數據（包含 v3.0 的 8 個特徵）
        
        Returns:
            添加交互特徵後的數據
        """
        df = df.copy()
        
        # 交互特徵 1: S1/S2 比率（賽道平衡指標）
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        
        # 交互特徵 2: Sector 變異係數（一致性指標）
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        
        # 交互特徵 3: S2/Lap 比率（S2 權重指標）
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        return df
    
    def train_track_model(self, track_name: str, start_year: int = 2022, 
                         end_year: int = 2024) -> Dict:
        """
        訓練單一賽道模型（v3.3）
        
        Args:
            track_name: 賽道名稱
            start_year: 起始年份
            end_year: 結束年份
        
        Returns:
            訓練結果字典
        """
        print(f"\n{'='*70}")
        print(f"訓練賽道: {track_name}")
        print(f"{'='*70}")
        
        # 步驟 1: 使用 v3 訓練器載入數據
        df = self.base_trainer.load_training_data_v3(track_name, start_year, end_year)
        
        if df.empty:
            print(f"[ERROR] {track_name} - 無可用數據")
            return None
        
        # 步驟 2: 添加交互特徵
        print(f"\n[特徵工程] 添加交互特徵...")
        df = self.add_interaction_features(df)
        
        # 檢查 NaN/Inf
        if df.isnull().any().any() or np.isinf(df.select_dtypes(include=[np.number])).any().any():
            print(f"[WARNING] 偵測到 NaN/Inf，正在清理...")
            df = df.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"[OK] 交互特徵添加完成，總特徵數: {len(df.columns) - 2}")
        
        # 步驟 3: 準備特徵和目標
        feature_cols = [
            'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
            'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
            's1_s2_ratio', 'sector_cv', 's2_lap_ratio'  # 新增交互特徵
        ]
        
        X = df[feature_cols]
        y = df['actual_q_time']
        
        # 步驟 4: 訓練模型（使用 v3.0 相同參數）
        print(f"\n[訓練] XGBoost 模型...")
        model = XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X, y)
        
        # 步驟 5: 評估效能
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        
        print(f"\n[效能指標]")
        print(f"  R² Score: {r2:.4f}")
        print(f"  MAE: {mae:.3f} 秒")
        
        # 步驟 6: 特徵重要性
        feature_importance = dict(zip(feature_cols, model.feature_importances_))
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n[特徵重要性]")
        for feat, imp in sorted_features:
            print(f"  {feat:20s}: {imp*100:6.2f}%")
        
        # 檢查交互特徵效果
        interaction_importance = sum([
            feature_importance.get('s1_s2_ratio', 0),
            feature_importance.get('sector_cv', 0),
            feature_importance.get('s2_lap_ratio', 0)
        ])
        print(f"\n[交互特徵總占比]: {interaction_importance*100:.2f}%")
        
        # 步驟 7: 保存模型
        model_file = self.models_dir / f"{track_name}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        print(f"\n[保存] 模型已保存: {model_file}")
        
        # 返回結果
        return {
            'track_name': track_name,
            'r2_score': r2,
            'mae': mae,
            'feature_importance': feature_importance,
            'interaction_importance': interaction_importance,
            'n_samples': len(df)
        }
    
    def compare_with_v3_0(self, track_name: str, v3_3_results: Dict) -> None:
        """
        對比 v3.0 和 v3.3 效能
        
        Args:
            track_name: 賽道名稱
            v3_3_results: v3.3 訓練結果
        """
        print(f"\n{'='*70}")
        print(f"效能對比: {track_name}")
        print(f"{'='*70}")
        
        # 載入 v3.0 模型和結果
        v3_0_model_file = Path("models/track_specific_v3") / f"{track_name}.pkl"
        
        if not v3_0_model_file.exists():
            print(f"[WARNING] 找不到 v3.0 模型: {v3_0_model_file}")
            return
        
        # 讀取 v3.0 效能（從訓練報告或重新計算）
        # 這裡使用已知的 v3.0 基準數據
        v3_0_baselines = {
            'Mexico': {'r2': 0.8044, 'mae': 0.379, 's2_importance': 28.62},
            'Abu Dhabi': {'r2': 0.5467, 'mae': 0.475, 's2_importance': 46.85}
        }
        
        if track_name not in v3_0_baselines:
            print(f"[INFO] {track_name} 無 v3.0 基準數據")
            return
        
        v3_0_data = v3_0_baselines[track_name]
        
        # 計算改進
        r2_change = ((v3_3_results['r2_score'] - v3_0_data['r2']) / v3_0_data['r2']) * 100
        mae_change = ((v3_3_results['mae'] - v3_0_data['mae']) / v3_0_data['mae']) * 100
        
        # 獲取 v3.3 的 S2 重要性
        s2_importance_v3_3 = v3_3_results['feature_importance'].get('ideal_s2', 0) * 100
        s2_change = s2_importance_v3_3 - v3_0_data['s2_importance']
        
        print(f"\n版本          R² Score    MAE (秒)    S2 重要性")
        print(f"-" * 60)
        print(f"v3.0 (8特徵)  {v3_0_data['r2']:.4f}     {v3_0_data['mae']:.3f}      {v3_0_data['s2_importance']:.2f}%")
        print(f"v3.3 (11特徵) {v3_3_results['r2_score']:.4f}     {v3_3_results['mae']:.3f}      {s2_importance_v3_3:.2f}%")
        print(f"-" * 60)
        print(f"變化          {r2_change:+.1f}%       {mae_change:+.1f}%      {s2_change:+.1f}%")
        
        # 評估
        print(f"\n[評估]")
        if r2_change > 0:
            print(f"  ✅ R² 改進 {r2_change:.1f}%")
        else:
            print(f"  ❌ R² 下降 {abs(r2_change):.1f}%")
        
        if mae_change < 0:
            print(f"  ✅ MAE 改進 {abs(mae_change):.1f}%")
        else:
            print(f"  ❌ MAE 增加 {mae_change:.1f}%")
        
        if abs(s2_change) < 5:
            print(f"  ⚠️  S2 占比變化小 ({s2_change:+.1f}%)")
        elif s2_change < 0:
            print(f"  ✅ S2 占比降低 {abs(s2_change):.1f}%")
        else:
            print(f"  ❌ S2 占比增加 {s2_change:.1f}%")
        
        print(f"\n[交互特徵貢獻]")
        print(f"  交互特徵總占比: {v3_3_results['interaction_importance']*100:.2f}%")
        print(f"  s1_s2_ratio: {v3_3_results['feature_importance'].get('s1_s2_ratio', 0)*100:.2f}%")
        print(f"  sector_cv: {v3_3_results['feature_importance'].get('sector_cv', 0)*100:.2f}%")
        print(f"  s2_lap_ratio: {v3_3_results['feature_importance'].get('s2_lap_ratio', 0)*100:.2f}%")


def main():
    """主函數 - 執行 v3.3 訓練"""
    
    trainer = TrainerV3_3_InteractionFeatures()
    
    # 優先訓練賽道
    priority_tracks = ['Mexico', 'Abu Dhabi']
    
    results = {}
    
    for track in priority_tracks:
        print(f"\n\n{'#'*70}")
        print(f"# 賽道 {priority_tracks.index(track)+1}/{len(priority_tracks)}: {track}")
        print(f"{'#'*70}")
        
        result = trainer.train_track_model(track, start_year=2022, end_year=2024)
        
        if result:
            results[track] = result
            
            # 對比 v3.0
            trainer.compare_with_v3_0(track, result)
    
    # 總結
    print(f"\n\n{'='*70}")
    print("v3.3 訓練完成總結")
    print(f"{'='*70}")
    
    for track, result in results.items():
        print(f"\n{track}:")
        print(f"  R² Score: {result['r2_score']:.4f}")
        print(f"  MAE: {result['mae']:.3f} 秒")
        print(f"  交互特徵占比: {result['interaction_importance']*100:.2f}%")
    
    # 保存結果
    output_file = Path("v3.3_interaction_features_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        # 轉換 numpy 類型為 Python 原生類型
        serializable_results = {}
        for track, result in results.items():
            serializable_results[track] = {
                'track_name': result['track_name'],
                'r2_score': float(result['r2_score']),
                'mae': float(result['mae']),
                'interaction_importance': float(result['interaction_importance']),
                'n_samples': int(result['n_samples']),
                'feature_importance': {k: float(v) for k, v in result['feature_importance'].items()}
            }
        
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[保存] 結果已保存: {output_file}")
    print("\n✅ v3.3 訓練完成！")


if __name__ == "__main__":
    main()
