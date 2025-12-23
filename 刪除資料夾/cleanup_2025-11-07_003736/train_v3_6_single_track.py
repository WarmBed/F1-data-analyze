#!/usr/bin/env python3
"""
v3.6 單賽道訓練器 - Optuna 超參數深度調優版本

核心特性：
1. 每個賽道獨立訓練 500 次 Optuna 試驗
2. 自動尋找賽道特定的最佳超參數配置
3. 交叉驗證確保小樣本穩定性
4. 保存模型和調優歷史

使用方法：
    python train_v3_6_single_track.py --track Monaco --trials 500
"""
import sys
import json
import pickle
import argparse
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional

import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import xgboost as xgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr

# 禁用警告
warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

# 導入現有訓練器用於數據載入
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class TrackExpertTrainer:
    """v3.6 單賽道專家訓練器"""
    
    def __init__(self, track_name: str, n_trials: int = 500, verbose: bool = True):
        self.track_name = track_name
        self.n_trials = n_trials
        self.verbose = verbose
        
        # 使用 v3.5 的數據載入器
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        
        # 目錄設置
        self.models_dir = Path("models/v3.6")
        self.studies_dir = Path("optuna_studies")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.studies_dir.mkdir(parents=True, exist_ok=True)
        
        # 訓練數據
        self.X_train = None
        self.y_train = None
        self.feature_names = None
        self.n_samples = 0
        
        # 最佳模型
        self.best_model = None
        self.best_params = None
        self.best_score = float('inf')
        
        # 調優歷史
        self.study = None
        
    def load_data(self) -> bool:
        """載入賽道訓練數據"""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"📊 載入 {self.track_name} 訓練數據")
            print(f"{'='*60}")
        
        try:
            # 使用 TrackSpecificTrainerV3 的數據載入方法
            data = self.base_trainer.load_training_data_v3(
                track_name=self.track_name,
                start_year=2022,
                end_year=2024
            )
            
            if data is None or len(data) == 0:
                print(f"  ❌ {self.track_name} 無訓練數據")
                return False
            
            # 提取特徵和目標 (v3.0 使用 actual_q_time 作為目標)
            feature_cols = [col for col in data.columns if col not in ['actual_q_time', 'driver', 'year', 'race']]
            self.X_train = data[feature_cols].values
            self.y_train = data['actual_q_time'].values
            self.feature_names = feature_cols
            self.n_samples = len(data)
            
            if self.verbose:
                print(f"  ✅ 訓練樣本數: {self.n_samples}")
                print(f"  ✅ 特徵數量: {len(self.feature_names)}")
                print(f"  ✅ 目標範圍: {self.y_train.min():.3f}s - {self.y_train.max():.3f}s")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 載入數據失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def objective(self, trial: optuna.Trial) -> float:
        """
        Optuna 優化目標函數
        
        返回交叉驗證的平均 MAE（越小越好）
        """
        # 定義超參數搜索空間
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 500),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 7),
            'gamma': trial.suggest_float('gamma', 0, 0.5),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 1.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 1.0),
            'random_state': 42,
            'n_jobs': -1
        }
        
        # 創建模型
        model = xgb.XGBRegressor(**params)
        
        # 交叉驗證（處理小樣本）
        cv_folds = min(5, max(3, self.n_samples // 4))
        kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        
        # 計算交叉驗證分數
        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=kf,
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )
        
        # 返回平均 MAE
        mae = -scores.mean()
        return mae
    
    def optimize(self) -> Dict:
        """
        執行 Optuna 超參數調優
        
        返回最佳參數和調優統計
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🔍 開始超參數調優 (試驗次數: {self.n_trials})")
            print(f"{'='*60}")
        
        # 創建 Optuna study
        study_name = f"{self.track_name}_v3.6"
        storage_path = self.studies_dir / f"{self.track_name}_study.db"
        
        self.study = optuna.create_study(
            study_name=study_name,
            direction='minimize',
            storage=f'sqlite:///{storage_path}',
            load_if_exists=True,
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=20, n_warmup_steps=10)
        )
        
        # 執行優化
        if self.verbose:
            self.study.optimize(
                self.objective,
                n_trials=self.n_trials,
                show_progress_bar=True,
                n_jobs=1  # 避免嵌套並行
            )
        else:
            self.study.optimize(
                self.objective,
                n_trials=self.n_trials,
                show_progress_bar=False,
                n_jobs=1
            )
        
        # 保存最佳參數
        self.best_params = self.study.best_params
        self.best_score = self.study.best_value
        
        if self.verbose:
            print(f"\n  ✅ 調優完成!")
            print(f"  📈 最佳 MAE: {self.best_score:.4f}s")
            print(f"\n  🎯 最佳參數:")
            for key, value in self.best_params.items():
                print(f"     {key:20s}: {value}")
        
        # 返回調優統計
        stats = {
            'track': self.track_name,
            'n_trials': len(self.study.trials),
            'best_mae': self.best_score,
            'best_params': self.best_params,
            'n_samples': self.n_samples,
            'cv_folds': min(5, max(3, self.n_samples // 4)),
            'timestamp': datetime.now().isoformat()
        }
        
        return stats
    
    def train_final_model(self) -> xgb.XGBRegressor:
        """
        使用最佳參數訓練最終模型
        
        返回訓練好的模型
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🚀 訓練最終模型")
            print(f"{'='*60}")
        
        # 使用最佳參數創建模型
        final_params = self.best_params.copy()
        final_params['random_state'] = 42
        final_params['n_jobs'] = -1
        
        self.best_model = xgb.XGBRegressor(**final_params)
        
        # 訓練模型
        self.best_model.fit(self.X_train, self.y_train)
        
        # 計算訓練集性能
        y_pred = self.best_model.predict(self.X_train)
        train_mae = mean_absolute_error(self.y_train, y_pred)
        train_r2 = r2_score(self.y_train, y_pred)
        
        # 計算 Spearman 相關性
        spearman_corr, _ = spearmanr(self.y_train, y_pred)
        
        if self.verbose:
            print(f"  ✅ 訓練完成!")
            print(f"  📊 訓練集性能:")
            print(f"     MAE:      {train_mae:.4f}s")
            print(f"     R²:       {train_r2:.4f}")
            print(f"     Spearman: {spearman_corr:.4f}")
        
        return self.best_model
    
    def save_model(self) -> str:
        """
        保存訓練好的模型
        
        返回模型檔案路徑
        """
        if self.best_model is None:
            raise ValueError("模型尚未訓練，請先調用 train_final_model()")
        
        # 保存模型
        model_path = self.models_dir / f"{self.track_name}.pkl"
        
        model_data = {
            'model': self.best_model,
            'feature_names': self.feature_names,
            'best_params': self.best_params,
            'best_cv_mae': self.best_score,
            'n_samples': self.n_samples,
            'track_name': self.track_name,
            'version': 'v3.6',
            'timestamp': datetime.now().isoformat()
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        if self.verbose:
            print(f"\n  💾 模型已保存: {model_path}")
        
        return str(model_path)
    
    def get_feature_importance(self) -> pd.DataFrame:
        """獲取特徵重要性"""
        if self.best_model is None:
            return None
        
        importance = self.best_model.feature_importances_
        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        })
        df = df.sort_values('importance', ascending=False)
        
        return df
    
    def train_complete_pipeline(self) -> Dict:
        """
        完整訓練流程
        
        返回訓練結果統計
        """
        start_time = datetime.now()
        
        # 1. 載入數據
        if not self.load_data():
            return {'success': False, 'error': '數據載入失敗'}
        
        # 2. 超參數調優
        optim_stats = self.optimize()
        
        # 3. 訓練最終模型
        self.train_final_model()
        
        # 4. 保存模型
        model_path = self.save_model()
        
        # 5. 特徵重要性
        feature_importance = self.get_feature_importance()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 整理結果
        result = {
            'success': True,
            'track': self.track_name,
            'model_path': model_path,
            'best_cv_mae': self.best_score,
            'best_params': self.best_params,
            'n_samples': self.n_samples,
            'n_trials': self.n_trials,
            'duration_seconds': duration,
            'top_features': feature_importance.head(5).to_dict('records') if feature_importance is not None else None,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"✅ {self.track_name} 訓練完成!")
            print(f"{'='*60}")
            print(f"  ⏱️  訓練時間: {duration:.1f}s")
            print(f"  📈 最佳 CV MAE: {self.best_score:.4f}s")
            print(f"  📊 訓練樣本: {self.n_samples}")
            print(f"  🔍 調優試驗: {self.n_trials}")
            
            if feature_importance is not None:
                print(f"\n  🎯 Top 5 重要特徵:")
                for i, row in feature_importance.head(5).iterrows():
                    print(f"     {i+1}. {row['feature']:30s}: {row['importance']*100:5.2f}%")
        
        return result


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='v3.6 單賽道訓練器')
    parser.add_argument('--track', type=str, required=True, help='賽道名稱 (e.g., Monaco)')
    parser.add_argument('--trials', type=int, default=500, help='Optuna 試驗次數 (默認: 500)')
    parser.add_argument('--quiet', action='store_true', help='靜默模式')
    
    args = parser.parse_args()
    
    # 創建訓練器
    trainer = TrackExpertTrainer(
        track_name=args.track,
        n_trials=args.trials,
        verbose=not args.quiet
    )
    
    # 執行訓練
    result = trainer.train_complete_pipeline()
    
    # 保存結果
    if result['success']:
        result_file = Path(f"train_result_{args.track}_v3.6.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n  📄 結果已保存: {result_file}")
        return 0
    else:
        print(f"\n  ❌ 訓練失敗: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
