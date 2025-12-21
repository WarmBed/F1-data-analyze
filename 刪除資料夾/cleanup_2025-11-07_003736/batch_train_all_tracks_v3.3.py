#!/usr/bin/env python3
"""
批次訓練所有賽道的 v3.3 模型 (2022-2024)
然後對 2025 賽季進行預測並生成完整分析報告

v3.3 特徵架構 (11 特徵):
- v3.0 基礎特徵 (8): ideal_s1/s2/s3/lap, low/mid/high_speed_apex, max_speed
- 交互特徵 (3): s1_s2_ratio, sector_cv, s2_lap_ratio
"""
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

# 導入 v3.0 trainer 用於數據載入
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class BatchTrainerV3_3:
    """v3.3 批次訓練器"""
    
    def __init__(self):
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        self.models_dir = Path("models/track_specific_v3.3")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {}
        self.prediction_results = {}
    
    def add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加交互特徵"""
        df = df.copy()
        
        # 交互特徵 1: S1/S2 比率
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        
        # 交互特徵 2: Sector 變異係數
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        
        # 交互特徵 3: S2/Lap 比率
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        return df
    
    def train_single_track(self, race_name: str, start_year: int = 2022, 
                          end_year: int = 2024) -> dict:
        """訓練單一賽道模型"""
        print(f"\n{'='*70}")
        print(f"Training: {race_name}")
        print(f"{'='*70}")
        
        try:
            # 步驟 1: 使用 v3.0 trainer 載入數據
            df = self.base_trainer.load_training_data_v3(race_name, start_year, end_year)
            
            if df.empty:
                print(f"  [SKIP] No data available")
                return None
            
            # 步驟 2: 添加交互特徵
            df = self.add_interaction_features(df)
            
            # 清理 NaN/Inf
            if df.isnull().any().any() or np.isinf(df.select_dtypes(include=[np.number])).any().any():
                df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] No valid data after cleaning")
                return None
            
            # 步驟 3: 準備特徵
            feature_cols = [
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio'
            ]
            
            X = df[feature_cols]
            y = df['actual_q_time']
            
            # 步驟 4: 訓練模型
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
            
            # 步驟 6: 保存模型
            model_file = self.models_dir / f"{race_name}.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(model, f)
            
            # 步驟 7: 特徵重要性
            feature_importance = dict(zip(feature_cols, model.feature_importances_))
            
            print(f"  [SUCCESS] R² {r2:.4f}, MAE {mae:.3f}s, Samples {len(df)}")
            
            return {
                'race': race_name,
                'r2_score': float(r2),
                'mae': float(mae),
                'n_samples': int(len(df)),
                'feature_importance': {k: float(v) for k, v in feature_importance.items()},
                'model_path': str(model_file)
            }
        
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def predict_2025(self, race_name: str) -> dict:
        """對 2025 賽季進行預測"""
        print(f"\n[2025 預測] {race_name}")
        
        try:
            # 載入模型
            model_file = self.models_dir / f"{race_name}.pkl"
            if not model_file.exists():
                print(f"  [SKIP] Model not found")
                return None
            
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            
            # 載入 2025 數據
            df = self.base_trainer.load_training_data_v3(race_name, start_year=2025, end_year=2025)
            
            if df.empty:
                print(f"  [SKIP] No 2025 data")
                return None
            
            # 添加交互特徵
            df = self.add_interaction_features(df)
            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] No valid 2025 data after cleaning")
                return None
            
            # 預測
            feature_cols = [
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio'
            ]
            
            X = df[feature_cols]
            y_true = df['actual_q_time'].values
            y_pred = model.predict(X)
            
            # 計算指標
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            
            # Spearman 相關性
            spearman_corr, _ = spearmanr(y_true, y_pred)
            
            # Top N 準確率
            def top_n_accuracy(y_true, y_pred, n):
                true_top_n = set(np.argsort(y_true)[:n])
                pred_top_n = set(np.argsort(y_pred)[:n])
                return len(true_top_n & pred_top_n) / n
            
            top3 = top_n_accuracy(y_true, y_pred, min(3, len(y_true)))
            top10 = top_n_accuracy(y_true, y_pred, min(10, len(y_true)))
            
            print(f"  [OK] MAE {mae:.3f}s, R² {r2:.4f}, Spearman {spearman_corr:.3f}, Top3 {top3:.1%}, Top10 {top10:.1%}")
            
            return {
                'race': race_name,
                'mae': float(mae),
                'r2_score': float(r2),
                'spearman': float(spearman_corr),
                'top3_accuracy': float(top3),
                'top10_accuracy': float(top10),
                'n_samples': int(len(df))
            }
        
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None
    
    def compare_with_v3_0(self, race_name: str, v3_3_result: dict) -> dict:
        """對比 v3.0 效能"""
        v3_0_model_file = Path("models/track_specific_v3") / f"{race_name}.pkl"
        
        if not v3_0_model_file.exists():
            return None
        
        # 這裡簡化處理，實際應重新載入 v3.0 數據評估
        # 為了速度，使用已知的基準數據
        return {
            'v3_0_available': True
        }


def main():
    """主函數"""
    print("\n" + "="*70)
    print("F1 v3.3 批次訓練 - 所有賽道 (2022-2024)")
    print("="*70)
    
    trainer = BatchTrainerV3_3()
    
    # 定義所有賽道
    all_tracks = [
        'Abu Dhabi', 'Australia', 'Austria', 'Azerbaijan', 'Bahrain', 'Belgium',
        'Brazil', 'Canada', 'China', 'Dutch', 'Emilia Romagna', 'France',
        'Great Britain', 'Hungary', 'Italy', 'Japan', 'Las Vegas', 'Mexico',
        'Miami', 'Monaco', 'Netherlands', 'Saudi Arabia', 'Singapore', 'Spain',
        'United States'
    ]
    
    # 階段 1: 訓練所有賽道
    print(f"\n{'#'*70}")
    print("# 階段 1: 訓練模型 (2022-2024)")
    print(f"{'#'*70}")
    
    training_results = {}
    for i, track in enumerate(all_tracks, 1):
        print(f"\n[{i}/{len(all_tracks)}] {track}")
        result = trainer.train_single_track(track, 2022, 2024)
        if result:
            training_results[track] = result
    
    # 階段 2: 2025 預測
    print(f"\n\n{'#'*70}")
    print("# 階段 2: 2025 賽季預測")
    print(f"{'#'*70}")
    
    prediction_results = {}
    for track in training_results.keys():
        result = trainer.predict_2025(track)
        if result:
            prediction_results[track] = result
    
    # 階段 3: 生成報告
    print(f"\n\n{'#'*70}")
    print("# 階段 3: 生成分析報告")
    print(f"{'#'*70}")
    
    # 統計
    successful_trains = len(training_results)
    successful_predictions = len(prediction_results)
    
    print(f"\n[訓練統計]")
    print(f"  成功訓練: {successful_trains}/{len(all_tracks)} 賽道")
    print(f"  平均 R²: {np.mean([r['r2_score'] for r in training_results.values()]):.4f}")
    print(f"  平均 MAE: {np.mean([r['mae'] for r in training_results.values()]):.3f}s")
    
    if prediction_results:
        print(f"\n[2025 預測統計]")
        print(f"  成功預測: {successful_predictions} 賽道")
        print(f"  平均 Spearman: {np.mean([r['spearman'] for r in prediction_results.values()]):.3f}")
        print(f"  平均 Top3: {np.mean([r['top3_accuracy'] for r in prediction_results.values()]):.1%}")
        print(f"  平均 Top10: {np.mean([r['top10_accuracy'] for r in prediction_results.values()]):.1%}")
    
    # 保存結果
    output = {
        'metadata': {
            'version': 'v3.3',
            'training_period': '2022-2024',
            'prediction_year': 2025,
            'timestamp': datetime.now().isoformat()
        },
        'training_results': training_results,
        'prediction_results': prediction_results
    }
    
    output_file = Path('v3.3_batch_training_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n[保存] 結果已保存: {output_file}")
    
    # 顯示 Top 5 和 Bottom 5
    if training_results:
        sorted_tracks = sorted(training_results.items(), key=lambda x: x[1]['r2_score'], reverse=True)
        
        print(f"\n{'='*70}")
        print("Top 5 表現最佳賽道 (訓練 R²)")
        print(f"{'='*70}")
        for track, result in sorted_tracks[:5]:
            print(f"  {track:20s}: R² {result['r2_score']:.4f}, MAE {result['mae']:.3f}s")
        
        print(f"\n{'='*70}")
        print("Bottom 5 需要改進賽道")
        print(f"{'='*70}")
        for track, result in sorted_tracks[-5:]:
            print(f"  {track:20s}: R² {result['r2_score']:.4f}, MAE {result['mae']:.3f}s")
    
    if prediction_results:
        sorted_predictions = sorted(prediction_results.items(), key=lambda x: x[1]['spearman'], reverse=True)
        
        print(f"\n{'='*70}")
        print("Top 5 預測最準賽道 (2025 Spearman)")
        print(f"{'='*70}")
        for track, result in sorted_predictions[:5]:
            print(f"  {track:20s}: Spearman {result['spearman']:.3f}, Top3 {result['top3_accuracy']:.1%}")
        
        print(f"\n{'='*70}")
        print("Bottom 5 預測待改進賽道")
        print(f"{'='*70}")
        for track, result in sorted_predictions[-5:]:
            print(f"  {track:20s}: Spearman {result['spearman']:.3f}, Top3 {result['top3_accuracy']:.1%}")
    
    print(f"\n✅ v3.3 批次訓練完成！")


if __name__ == "__main__":
    main()
