#!/usr/bin/env python3
"""
v3.9 批次訓練器 - 動態 is_top_driver 特徵

v3.9 = v3.8 + 動態 is_top_driver
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 核心改進：
  ✅ 移除硬編碼的車手名單 (8 位固定車手)
  ✅ 改用「賽季總積分排名」動態計算 is_top_driver
  ✅ 自動適應每年的車手實力變化，無需手動更新

v3.9 特徵架構 (17 特徵 - 同 v3.8):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

【v3.5 有效特徵 (3)】✅ 改進
  15.   fp3_relative_position (FP3 排名 - 非線性)
  16.   fp3_gap_to_fastest (與最快圈差距 - 獨立資訊)
  17.   is_top_driver (動態計算 - 基於賽季表現排名) ⭐ 改進

is_top_driver 計算邏輯:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  方法：賽季總積分排名法
  
  步驟：
    1. 按年份分組，計算每個車手在該賽季的平均 ideal_lap
    2. ideal_lap 最快的前 N 名車手 = 頂尖車手
    3. is_top_driver = 1 if 在前 N 名, else 0
  
  優點：
    ✅ 客觀：基於實際 FP3 表現，非主觀判斷
    ✅ 自動：無需每年手動更新車手名單
    ✅ 一致：歷史數據使用當時的排名，不受後見之明影響

預期效果:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 性能：預期與 v3.8 相當或略優（部分賽道可能提升）
- 維護：無需每年手動更新車手名單
- 一致性：歷史數據與未來數據處理邏輯統一
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


class BatchTrainerV3_9:
    """v3.9 批次訓練器 - 動態 is_top_driver (17 特徵)"""
    
    def __init__(self, trials: int = 500, cv_folds: int = 3, workers: int = 1, top_n_drivers: int = 8):
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        self.models_dir = Path("models/track_specific_v3.9")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.trials = trials
        self.cv_folds = cv_folds
        self.workers = workers
        self.top_n_drivers = top_n_drivers  # 前 N 名視為頂尖車手
        
        print(f"\n{'='*70}")
        print(f"v3.9 批次訓練器初始化 - 動態 is_top_driver")
        print(f"{'='*70}")
        print(f"  特徵數量: 17 (同 v3.8)")
        print(f"  Optuna trials: {self.trials}")
        print(f"  CV folds: {self.cv_folds}")
        print(f"  Workers: {self.workers}")
        print(f"\n  ✨ 核心改進:")
        print(f"    ✅ 動態計算 is_top_driver (前 {self.top_n_drivers} 名車手)")
        print(f"    ✅ 基於賽季平均 ideal_lap 排名")
        print(f"    ✅ 自動適應每年車手實力變化")
        print(f"\n  ❌ 移除:")
        print(f"    硬編碼車手名單 ['VER', 'HAM', 'LEC', ...]")
        
        self.results = {}
    
    def clean_outlier_samples(self, df: pd.DataFrame, race_name: str) -> pd.DataFrame:
        """數據清洗（繼承自 v3.5）"""
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
    
    def _calculate_is_top_driver_dynamic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        ⭐ 動態計算 is_top_driver (v3.9 核心改進)
        
        邏輯：該賽季平均 ideal_lap 最快的前 N 名車手 = 頂尖車手
        
        Args:
            df: 訓練數據（包含 driver, year, ideal_lap）
        
        Returns:
            添加 is_top_driver 欄位的 DataFrame
        """
        df = df.copy()
        
        # 計算每個車手在每個賽季的平均 ideal_lap
        avg_performance = df.groupby(['year', 'driver'])['ideal_lap'].mean().reset_index()
        avg_performance.rename(columns={'ideal_lap': 'avg_ideal_lap'}, inplace=True)
        
        # 每年取平均最快的前 N 名
        top_drivers_per_year = (
            avg_performance.sort_values(['year', 'avg_ideal_lap'], ascending=[True, True])
            .groupby('year')
            .head(self.top_n_drivers)
        )
        
        # 創建 (year, driver) → is_top_driver 的映射
        top_driver_set = set(zip(top_drivers_per_year['year'], top_drivers_per_year['driver']))
        
        # 應用到原始數據
        df['is_top_driver'] = df.apply(
            lambda row: int((row['year'], row['driver']) in top_driver_set),
            axis=1
        )
        
        # 調試輸出：顯示每年的頂尖車手
        for year in sorted(df['year'].unique()):
            year_top_drivers = top_drivers_per_year[top_drivers_per_year['year'] == year]['driver'].tolist()
            print(f"  [is_top_driver] {year}: {year_top_drivers}")
        
        return df
    
    def add_v39_features(self, df: pd.DataFrame, track_name: str) -> pd.DataFrame:
        """添加 v3.9 特徵（17個 - 動態 is_top_driver）"""
        df = df.copy()
        
        # ========== v3.3 交互特徵 (3) ==========
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        # ========== v3.4 速度特徵 (3) ==========
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        apex_speeds = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']]
        df['speed_consistency'] = apex_speeds.std(axis=1) / (df['max_speed'] + 1e-6)
        
        # ========== v3.5 有效特徵 (3) - 保留 ✅ ==========
        # 特徵 15: FP3 相對排名（非線性 - 排名 vs 時間）
        df['fp3_relative_position'] = df['ideal_lap'].rank(method='min')
        
        # 特徵 16: 與最快圈差距（獨立資訊 - 絕對差距）
        df['fp3_gap_to_fastest'] = df['ideal_lap'] - df['ideal_lap'].min()
        
        # ⭐ 特徵 17: 頂尖車手標記（動態計算 - v3.9 改進）
        df = self._calculate_is_top_driver_dynamic(df)
        
        return df
    
    def objective(self, trial: optuna.Trial, X: pd.DataFrame, y: pd.Series) -> float:
        """Optuna 優化目標函數"""
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
        """訓練單一賽道模型（v3.9 動態版本）"""
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
            
            # 步驟 3: 添加 v3.9 特徵（17 個 - 動態 is_top_driver）
            df = self.add_v39_features(df, race_name)
            
            # 清理 NaN/Inf
            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] 特徵工程後無有效數據")
                return None
            
            # 步驟 4: 準備特徵矩陣 (17 個特徵)
            feature_cols = [
                # v3.0 基礎特徵 (8)
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                # v3.3 交互特徵 (3)
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                # v3.4 速度特徵 (3)
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
                # v3.5 有效特徵 (3) ✅
                'fp3_relative_position', 'fp3_gap_to_fastest', 'is_top_driver'
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
                'version': 'v3.9',
                'is_top_driver_method': 'dynamic_season_avg',
                'top_n_drivers': self.top_n_drivers
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
        """訓練所有賽道（2025 賽季 24 場）"""
        tracks = [
            'Australia', 'China', 'Japan', 'Bahrain', 'Saudi Arabia', 'Miami',
            'Emilia Romagna', 'Monaco', 'Spain', 'Canada', 'Austria', 'Great Britain',
            'Belgium', 'Hungary', 'Netherlands', 'Italy', 'Azerbaijan', 'Singapore',
            'United States', 'Mexico', 'Brazil', 'Las Vegas', 'Qatar', 'Abu Dhabi'
        ]
        
        print(f"\n{'='*70}")
        print(f"開始批次訓練 v3.9 - {len(tracks)} 個賽道 (2025 賽季)")
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
        print("v3.9 訓練總結 - 動態 is_top_driver")
        print(f"{'='*70}")
        
        print(f"\n[成功訓練] {len(self.results)}/24 賽道")
        print(f"[總耗時] {duration/60:.1f} 分鐘 ({duration:.0f}秒)")
        print(f"[平均耗時] {duration/len(self.results):.1f} 秒/賽道")
        
        avg_cv_mae = np.mean([r['cv_mae'] for r in self.results.values()])
        avg_train_mae = np.mean([r['train_mae'] for r in self.results.values()])
        avg_r2 = np.mean([r['train_r2'] for r in self.results.values()])
        
        print(f"\n[整體表現]")
        print(f"  平均 CV MAE: {avg_cv_mae:.3f}s")
        print(f"  平均訓練 MAE: {avg_train_mae:.3f}s")
        print(f"  平均 R²: {avg_r2:.4f}")
        
        print(f"\n[各賽道表現]")
        sorted_tracks = sorted(self.results.items(), key=lambda x: x[1]['cv_mae'])
        
        for track, result in sorted_tracks:
            print(f"  {track:20s}: CV MAE {result['cv_mae']:.3f}s, "
                  f"訓練 MAE {result['train_mae']:.3f}s, "
                  f"R² {result['train_r2']:.4f}, "
                  f"{result['sample_count']} 樣本")
    
    def save_results(self):
        """保存訓練結果"""
        output_file = Path("v3.9_training_results.json")
        
        serializable_results = {
            'metadata': {
                'version': 'v3.9',
                'feature_count': 17,
                'is_top_driver_method': 'dynamic_season_avg',
                'top_n_drivers': self.top_n_drivers,
                'improvement': 'Replaced hardcoded driver list with dynamic calculation',
                'training_date': datetime.now().isoformat(),
                'tracks_trained': len(self.results)
            },
            'results': {}
        }
        
        for track, result in self.results.items():
            serializable_results['results'][track] = {
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
    parser = argparse.ArgumentParser(
        description='v3.9 批次訓練器 - 動態 is_top_driver 特徵',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
v3.9 改進：
  ✨ 動態計算 is_top_driver (基於賽季平均 ideal_lap 排名)
  ✅ 無需每年手動更新車手名單
  ✅ 自動適應車手實力變化

範例:
  python batch_train_all_tracks_v3.9.py
  python batch_train_all_tracks_v3.9.py --trials 300 --top-n 10
  python batch_train_all_tracks_v3.9.py --trials 1000 --workers 4
        """
    )
    parser.add_argument('--trials', type=int, default=500, 
                       help='Optuna trials per track (預設: 500)')
    parser.add_argument('--cv-folds', type=int, default=3, 
                       help='交叉驗證 folds (預設: 3)')
    parser.add_argument('--workers', type=int, default=1, 
                       help='並行 workers (預設: 1)')
    parser.add_argument('--top-n', type=int, default=8, 
                       help='前 N 名車手視為頂尖 (預設: 8)')
    
    args = parser.parse_args()
    
    trainer = BatchTrainerV3_9(
        trials=args.trials,
        cv_folds=args.cv_folds,
        workers=args.workers,
        top_n_drivers=args.top_n
    )
    
    trainer.train_all_tracks()
    
    print(f"\n{'='*70}")
    print("v3.9 訓練完成！")
    print(f"{'='*70}")
    print(f"\n模型保存位置: models/track_specific_v3.9/")
    print(f"結果檔案: v3.9_training_results.json")
    print(f"\n下一步：執行 python compare_v38_v39_performance.py 對比性能差異")


if __name__ == '__main__':
    main()
