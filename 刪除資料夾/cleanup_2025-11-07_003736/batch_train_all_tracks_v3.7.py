#!/usr/bin/env python3
"""
v3.7 批次訓練器 - v3.5 特徵工程 + Optuna 優化

v3.7 = v3.5 架構 + v3.6 優化策略
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
特徵架構 (20 特徵) - 與 v3.5 完全相同:

【v3.0 基礎特徵 (8)】
  1-4.  ideal_s1, ideal_s2, ideal_s3, ideal_lap
  5-7.  low_speed_apex, mid_speed_apex, high_speed_apex
  8.    max_speed

【v3.3 交互特徵 (3)】
  9.    s1_s2_ratio
  10.   sector_cv
  11.   s2_lap_ratio

【v3.4 速度特徵 (3)】
  12.   max_speed_lap_ratio
  13.   max_speed_s2_ratio
  14.   speed_consistency

【v3.5 改進率特徵 (6)】
  15.   track_avg_improvement_rate
  16.   adjusted_ideal_lap
  17.   fp3_relative_position
  18.   fp3_gap_to_fastest
  19.   is_top_driver
  20.   driver_historical_improvement

優化策略 (來自 v3.6):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Optuna 超參數優化 (500 trials)
- TPESampler + MedianPruner
- 交叉驗證 (3-fold)
- 搜索空間:
  * n_estimators: 50-500
  * max_depth: 2-8
  * learning_rate: 0.001-0.3
  * subsample: 0.6-1.0
  * colsample_bytree: 0.6-1.0
  * min_child_weight: 1-10
  * gamma: 0-5
  * reg_alpha: 0-10
  * reg_lambda: 0-10
"""
import sys
import json
import pickle
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score, KFold
from xgboost import XGBRegressor
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

# 導入 v3.0 trainer 用於數據載入
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class BatchTrainerV3_7:
    """v3.7 批次訓練器 - v3.5 特徵 + Optuna 優化"""
    
    def __init__(self, trials: int = 500, cv_folds: int = 3, workers: int = 1):
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        self.models_dir = Path("models/track_specific_v3.7")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.trials = trials
        self.cv_folds = cv_folds
        self.workers = workers
        
        self.results = {}
        
        # 從 v3.5 載入賽道改進率
        self.track_improvement_rates = self._load_track_improvement_rates()
        
        # 頂尖車手列表
        self.top_drivers = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']
        
        print(f"\n{'='*70}")
        print(f"v3.7 批次訓練器初始化")
        print(f"{'='*70}")
        print(f"  Optuna trials: {self.trials}")
        print(f"  CV folds: {self.cv_folds}")
        print(f"  Workers: {self.workers}")
        print(f"  特徵數量: 20 (v3.5 完整特徵)")
    
    def _load_track_improvement_rates(self) -> dict:
        """載入賽道改進率（來自 v3.5）"""
        analysis_file = Path("fp3_q_improvement_analysis.json")
        if not analysis_file.exists():
            return self._get_default_improvement_rates()
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        track_rates = {}
        for track, track_data in data['by_track'].items():
            avg_rate = track_data['avg_improvement_rate']
            if avg_rate < -0.05 or avg_rate > 0.15:
                track_rates[track] = 0.015
            else:
                track_rates[track] = avg_rate
        
        return track_rates
    
    def _get_default_improvement_rates(self) -> dict:
        """預設改進率"""
        return {
            'Japan': 0.0136, 'Bahrain': 0.0189, 'Monaco': 0.0159,
            'Italy': 0.0074, 'Mexico': 0.0063, 'Abu Dhabi': 0.0104,
            'Great Britain': 0.015, 'Canada': 0.0362, 'Singapore': 0.0266,
            'Netherlands': 0.0768, 'Saudi Arabia': 0.0035, 'Miami': 0.0119,
            'Azerbaijan': 0.0091, 'United States': 0.0131, 'Las Vegas': 0.0121,
            'Hungary': 0.0874, 'Belgium': 0.0515, 'Australia': 0.0097,
            'Spain': 0.0159, 'China': 0.015, 'Austria': 0.015,
            'Brazil': 0.012, 'Qatar': 0.012, 'Emilia Romagna': 0.012
        }
    
    def clean_outlier_samples(self, df: pd.DataFrame, race_name: str) -> pd.DataFrame:
        """數據清洗（來自 v3.5）"""
        # 移除異常年份數據（根據 v3.5 分析結果）
        outlier_config = {
            'Great Britain': [2022],  # Q 下雨
            'Hungary': [2022],        # FP3 異常
        }
        
        if race_name in outlier_config:
            outlier_years = outlier_config[race_name]
            original_len = len(df)
            df = df[~df['year'].isin(outlier_years)]
            removed = original_len - len(df)
            if removed > 0:
                print(f"  [清洗] 移除 {removed} 個異常樣本 (年份: {outlier_years})")
        
        return df
    
    def add_v35_features(self, df: pd.DataFrame, track_name: str) -> pd.DataFrame:
        """添加 v3.5 所有特徵（20個）"""
        df = df.copy()
        
        # ========== v3.3 交互特徵 ==========
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        # ========== v3.4 速度特徵 ==========
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        apex_speeds = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']]
        df['speed_consistency'] = apex_speeds.std(axis=1) / (df['max_speed'] + 1e-6)
        
        # ========== v3.5 改進率特徵 ==========
        track_rate = self.track_improvement_rates.get(track_name, 0.015)
        df['track_avg_improvement_rate'] = track_rate
        df['adjusted_ideal_lap'] = df['ideal_lap'] * (1 - track_rate)
        df['fp3_relative_position'] = df['ideal_lap'].rank(method='min')
        df['fp3_gap_to_fastest'] = df['ideal_lap'] - df['ideal_lap'].min()
        df['is_top_driver'] = df['driver'].isin(self.top_drivers).astype(int)
        df['driver_historical_improvement'] = df['is_top_driver'] * 0.002
        
        return df
    
    def objective(self, trial: optuna.Trial, X: pd.DataFrame, y: pd.Series) -> float:
        """Optuna 優化目標函數（來自 v3.6）"""
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 500),
            'max_depth': trial.suggest_int('max_depth', 2, 8),
            'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'gamma': trial.suggest_float('gamma', 0, 5),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
            'random_state': 42,
            'verbosity': 0,
            'n_jobs': 1
        }
        
        model = XGBRegressor(**params)
        
        kf = KFold(n_splits=self.cv_folds, shuffle=True, random_state=42)
        cv_scores = cross_val_score(
            model, X, y,
            cv=kf,
            scoring='neg_mean_absolute_error',
            n_jobs=1
        )
        
        return -cv_scores.mean()
    
    def train_single_track(self, race_name: str, start_year: int = 2022, 
                          end_year: int = 2024) -> dict:
        """訓練單一賽道模型（v3.5 特徵 + Optuna 優化）"""
        print(f"\n{'='*70}")
        print(f"Training: {race_name}")
        print(f"{'='*70}")
        
        try:
            # 步驟 1: 載入數據（使用 v3.0 trainer）
            df = self.base_trainer.load_training_data_v3(race_name, start_year, end_year)
            
            if df.empty:
                print(f"  [SKIP] 沒有可用數據")
                return None
            
            print(f"  [原始數據] {len(df)} 樣本")
            
            # 步驟 2: 數據清洗
            df = self.clean_outlier_samples(df, race_name)
            
            if df.empty:
                print(f"  [SKIP] 清洗後無有效數據")
                return None
            
            print(f"  [清洗後] {len(df)} 樣本")
            
            # 步驟 3: 添加 v3.5 特徵
            df = self.add_v35_features(df, race_name)
            
            # 清理 NaN/Inf
            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] 特徵工程後無有效數據")
                return None
            
            # 步驟 4: 準備特徵矩陣 (20 個特徵)
            feature_cols = [
                # v3.0 基礎特徵 (8)
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                # v3.3 交互特徵 (3)
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                # v3.4 速度特徵 (3)
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
                # v3.5 改進率特徵 (6)
                'track_avg_improvement_rate', 'adjusted_ideal_lap',
                'fp3_relative_position', 'fp3_gap_to_fastest',
                'is_top_driver', 'driver_historical_improvement'
            ]
            
            X = df[feature_cols]
            y = df['actual_q_time']
            
            # 步驟 5: Optuna 超參數優化
            print(f"  [Optuna] 開始優化 ({self.trials} trials)...")
            
            study = optuna.create_study(
                direction='minimize',
                sampler=TPESampler(seed=42),
                pruner=MedianPruner(n_startup_trials=10, n_warmup_steps=5)
            )
            
            study.optimize(
                lambda trial: self.objective(trial, X, y),
                n_trials=self.trials,
                n_jobs=self.workers,
                show_progress_bar=False
            )
            
            best_params = study.best_params
            best_cv_mae = study.best_value
            
            print(f"  [Optuna] 最佳 CV MAE: {best_cv_mae:.3f}s (來自 {len(study.trials)} trials)")
            
            # 步驟 6: 使用最佳參數訓練最終模型
            final_params = {**best_params, 'random_state': 42, 'verbosity': 0}
            final_model = XGBRegressor(**final_params)
            final_model.fit(X, y)
            
            # 步驟 7: 評估
            y_pred = final_model.predict(X)
            mae = mean_absolute_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            print(f"  [訓練結果] R² {r2:.4f}, MAE {mae:.3f}s")
            
            # 步驟 8: 保存模型
            model_file = self.models_dir / f"{race_name}.pkl"
            model_data = {
                'model': final_model,
                'feature_names': feature_cols,
                'best_params': best_params,
                'cv_mae': best_cv_mae,
                'train_mae': mae,
                'train_r2': r2,
                'sample_count': len(df),
                'version': 'v3.7'
            }
            
            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"  [保存] {model_file.name}")
            
            # 特徵重要性
            feature_importance = dict(zip(feature_cols, final_model.feature_importances_))
            top5_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            
            print(f"  [Top 5 特徵]")
            for feat, imp in top5_features:
                print(f"    {feat:30s}: {imp*100:5.2f}%")
            
            return {
                'track': race_name,
                'cv_mae': best_cv_mae,
                'train_mae': mae,
                'train_r2': r2,
                'sample_count': len(df),
                'best_params': best_params,
                'feature_importance': feature_importance
            }
        
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def train_all_tracks(self):
        """訓練所有賽道"""
        tracks = [
            'Japan', 'Bahrain', 'Saudi Arabia', 'Monaco', 
            'Canada', 'Great Britain', 'Hungary', 'Netherlands',
            'Italy', 'Azerbaijan'
        ]
        
        print(f"\n{'='*70}")
        print(f"開始批次訓練 v3.7 - {len(tracks)} 個賽道")
        print(f"{'='*70}")
        
        start_time = datetime.now()
        
        for i, track in enumerate(tracks, 1):
            print(f"\n[{i}/{len(tracks)}] {track}")
            result = self.train_single_track(track)
            
            if result:
                self.results[track] = result
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.generate_summary(duration)
        self.save_results()
    
    def generate_summary(self, duration: float):
        """生成訓練總結"""
        if not self.results:
            print("\n[錯誤] 沒有訓練結果")
            return
        
        print(f"\n{'='*70}")
        print("v3.7 訓練總結")
        print(f"{'='*70}")
        
        print(f"\n[成功訓練] {len(self.results)}/10 賽道")
        print(f"[總耗時] {duration/60:.1f} 分鐘 ({duration:.0f}秒)")
        print(f"[平均耗時] {duration/len(self.results):.1f} 秒/賽道")
        
        avg_cv_mae = np.mean([r['cv_mae'] for r in self.results.values()])
        avg_train_mae = np.mean([r['train_mae'] for r in self.results.values()])
        
        print(f"\n[整體表現]")
        print(f"  平均 CV MAE: {avg_cv_mae:.3f}s")
        print(f"  平均訓練 MAE: {avg_train_mae:.3f}s")
        
        print(f"\n[各賽道表現]")
        sorted_tracks = sorted(self.results.items(), key=lambda x: x[1]['cv_mae'])
        
        for track, result in sorted_tracks:
            print(f"  {track:20s}: CV MAE {result['cv_mae']:.3f}s, "
                  f"訓練 MAE {result['train_mae']:.3f}s, "
                  f"{result['sample_count']} 樣本")
    
    def save_results(self):
        """保存訓練結果"""
        output_file = Path("v3.7_training_results.json")
        
        serializable_results = {}
        for track, result in self.results.items():
            serializable_results[track] = {
                'track': result['track'],
                'cv_mae': float(result['cv_mae']),
                'train_mae': float(result['train_mae']),
                'train_r2': float(result['train_r2']),
                'sample_count': int(result['sample_count']),
                'best_params': result['best_params'],
                'feature_importance': {k: float(v) for k, v in result['feature_importance'].items()}
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[保存結果] {output_file}")


def main():
    parser = argparse.ArgumentParser(description='v3.7 批次訓練器')
    parser.add_argument('--trials', type=int, default=500, help='Optuna trials per track')
    parser.add_argument('--cv-folds', type=int, default=3, help='交叉驗證 folds')
    parser.add_argument('--workers', type=int, default=1, help='並行 workers')
    
    args = parser.parse_args()
    
    trainer = BatchTrainerV3_7(
        trials=args.trials,
        cv_folds=args.cv_folds,
        workers=args.workers
    )
    
    trainer.train_all_tracks()
    
    print(f"\n{'='*70}")
    print("完成！")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
