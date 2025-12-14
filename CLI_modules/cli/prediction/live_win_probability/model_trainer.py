#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Win Probability - XGBoost Model Trainer

此模組負責訓練 XGBoost 回歸模型，預測最終名次並轉換為勝率。

模型架構:
- 輸入: 18 個特徵 (即時 + 歷史)
- 輸出: 最終名次預測 (1-21)
- 轉換: 使用 softmax-like 方式計算 P1/P2/P3 機率

特徵重要性分析:
- position: 當前位置是最重要的預測因子
- gap_to_leader: 與領先者差距
- laps_remaining: 剩餘圈數（越少，預測越準確）
- pit_count: 進站次數
- tyre_compound/age: 輪胎策略

作者: F1T Dev Team
日期: 2025-01
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import pickle
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        mean_absolute_error, 
        mean_squared_error, 
        accuracy_score,
        classification_report
    )
except ImportError as e:
    raise ImportError(
        "Required packages not installed. Run: pip install xgboost scikit-learn pandas numpy"
    ) from e

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WinProbabilityModelTrainer:
    """
    XGBoost 模型訓練器
    
    使用方法:
    ```python
    trainer = WinProbabilityModelTrainer()
    trainer.load_data("data/live_win_probability/training_data.csv")
    trainer.train()
    trainer.save_model("models/win_probability_v1.pkl")
    ```
    """
    
    # 特徵列定義
    FEATURE_COLUMNS = [
        'position',
        'gap_to_leader',
        'gap_to_ahead',
        'lap_time',
        'best_lap_time',
        'tyre_compound',
        'tyre_age',
        'pit_count',
        'laps_remaining',
        'track_status',
        'air_temp',
        'rainfall',
        'driver_win_rate',
        'driver_podium_rate',
        'team_rating',
        'circuit_overtake_rate',
        'circuit_sc_rate',
        'qualifying_position',
    ]
    
    # 標籤列
    LABEL_COLUMN = 'final_position'
    
    def __init__(self, random_state: int = 42):
        """
        初始化訓練器
        
        Args:
            random_state: 隨機種子
        """
        self.random_state = random_state
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_importance: Optional[Dict[str, float]] = None
        self.train_data: Optional[pd.DataFrame] = None
        self.val_data: Optional[pd.DataFrame] = None
        self.training_metrics: Dict[str, Any] = {}
        
    def load_data(
        self, 
        train_path: str,
        val_path: Optional[str] = None,
        test_size: float = 0.2
    ) -> Tuple[int, int]:
        """
        載入訓練數據
        
        Args:
            train_path: 訓練數據 CSV 路徑
            val_path: 驗證數據 CSV 路徑（可選）
            test_size: 若無驗證數據，從訓練數據分割的比例
            
        Returns:
            (訓練樣本數, 驗證樣本數)
        """
        logger.info(f"Loading training data from: {train_path}")
        self.train_data = pd.read_csv(train_path)
        logger.info(f"Loaded {len(self.train_data)} training samples")
        
        if val_path and os.path.exists(val_path):
            logger.info(f"Loading validation data from: {val_path}")
            self.val_data = pd.read_csv(val_path)
            logger.info(f"Loaded {len(self.val_data)} validation samples")
        else:
            # 從訓練數據分割驗證集
            logger.info(f"Splitting {test_size*100:.0f}% data for validation")
            self.train_data, self.val_data = train_test_split(
                self.train_data, 
                test_size=test_size, 
                random_state=self.random_state
            )
            
        return len(self.train_data), len(self.val_data)
    
    def _prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        準備特徵和標籤
        
        Args:
            df: 數據 DataFrame
            
        Returns:
            (X, y) 特徵和標籤陣列
        """
        # 選擇特徵列
        X = df[self.FEATURE_COLUMNS].copy()
        
        # 處理缺失值
        X = X.fillna(0)
        
        # 處理無限值
        X = X.replace([np.inf, -np.inf], 0)
        
        # 標籤
        y = df[self.LABEL_COLUMN].values
        
        return X.values, y
    
    def train(
        self,
        n_estimators: int = 200,
        max_depth: int = 8,
        learning_rate: float = 0.1,
        early_stopping_rounds: int = 20,
        verbose: bool = True
    ) -> Dict[str, float]:
        """
        訓練 XGBoost 模型
        
        Args:
            n_estimators: 樹的數量
            max_depth: 樹的最大深度
            learning_rate: 學習率
            early_stopping_rounds: 早停輪數
            verbose: 是否顯示訓練進度
            
        Returns:
            訓練指標字典
        """
        if self.train_data is None:
            raise ValueError("No training data loaded. Call load_data() first.")
            
        logger.info("Preparing training data...")
        X_train, y_train = self._prepare_features(self.train_data)
        X_val, y_val = self._prepare_features(self.val_data)
        
        logger.info(f"Training set: {X_train.shape[0]} samples, {X_train.shape[1]} features")
        logger.info(f"Validation set: {X_val.shape[0]} samples")
        
        # 初始化 XGBoost 回歸模型
        # 降低 verbosity 避免過多輸出導致 VS Code 終端當機
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            objective='reg:squarederror',
            random_state=self.random_state,
            n_jobs=-1,
            verbosity=0,  # 完全關閉 XGBoost 內部輸出
        )
        
        logger.info("Training XGBoost model...")
        
        # 訓練模型
        # 使用 eval_set 但減少輸出頻率，避免終端緩衝區溢出
        # verbose=True 會每輪輸出，改為每 50 輪輸出一次
        eval_result = {}
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=50 if verbose else 0  # 每 50 輪輸出一次，而非每輪
        )
        
        # 計算訓練指標
        y_train_pred = self.model.predict(X_train)
        y_val_pred = self.model.predict(X_val)
        
        # 回歸指標
        train_mae = mean_absolute_error(y_train, y_train_pred)
        val_mae = mean_absolute_error(y_val, y_val_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
        
        # 分類指標（四捨五入到最近整數位置）
        y_train_class = np.clip(np.round(y_train_pred), 1, 21).astype(int)
        y_val_class = np.clip(np.round(y_val_pred), 1, 21).astype(int)
        train_acc = accuracy_score(y_train, y_train_class)
        val_acc = accuracy_score(y_val, y_val_class)
        
        # Top-3 準確率（預測前 3 名是否包含實際前 3 名）
        top3_train = self._calculate_top_n_accuracy(y_train, y_train_pred, n=3)
        top3_val = self._calculate_top_n_accuracy(y_val, y_val_pred, n=3)
        
        self.training_metrics = {
            'train_mae': train_mae,
            'val_mae': val_mae,
            'train_rmse': train_rmse,
            'val_rmse': val_rmse,
            'train_exact_accuracy': train_acc,
            'val_exact_accuracy': val_acc,
            'train_top3_accuracy': top3_train,
            'val_top3_accuracy': top3_val,
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'feature_count': len(self.FEATURE_COLUMNS),
            'train_samples': len(self.train_data),
            'val_samples': len(self.val_data),
        }
        
        # 特徵重要性
        self.feature_importance = dict(zip(
            self.FEATURE_COLUMNS,
            self.model.feature_importances_
        ))
        
        logger.info(f"Training complete!")
        logger.info(f"  Train MAE: {train_mae:.3f}, Val MAE: {val_mae:.3f}")
        logger.info(f"  Train RMSE: {train_rmse:.3f}, Val RMSE: {val_rmse:.3f}")
        logger.info(f"  Train Exact Acc: {train_acc:.2%}, Val Exact Acc: {val_acc:.2%}")
        logger.info(f"  Train Top-3 Acc: {top3_train:.2%}, Val Top-3 Acc: {top3_val:.2%}")
        
        return self.training_metrics
    
    def _calculate_top_n_accuracy(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        n: int = 3
    ) -> float:
        """
        計算 Top-N 準確率
        
        檢查預測中位置 <= n 的車手，是否實際也在 Top-n
        
        Args:
            y_true: 實際位置
            y_pred: 預測位置
            n: Top-N 的 N 值
            
        Returns:
            Top-N 準確率
        """
        # 找出真實 top-n
        true_top_n = set(np.where(y_true <= n)[0])
        
        # 找出預測 top-n（取預測值最小的 n 個）
        pred_top_n_indices = np.argsort(y_pred)[:len(true_top_n)]
        pred_top_n = set(pred_top_n_indices)
        
        # 計算重疊率
        if len(true_top_n) == 0:
            return 0.0
        overlap = len(true_top_n & pred_top_n)
        return overlap / len(true_top_n)
    
    def predict_probabilities(
        self, 
        features: np.ndarray,
        top_n: int = 3
    ) -> np.ndarray:
        """
        預測 Top-N 機率
        
        將回歸預測轉換為機率分布。
        使用 softmax-like 公式：P(i) = exp(-pred[i]) / sum(exp(-pred[j]))
        
        Args:
            features: 特徵陣列 (n_samples, n_features)
            top_n: 返回 Top-N 機率
            
        Returns:
            機率陣列 (n_samples, top_n)，分別為 P1, P2, P3 機率
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
            
        # 獲取預測位置
        pred_positions = self.model.predict(features)
        
        # 轉換為機率（使用負值的 softmax，因為位置越低越好）
        # pred_positions 越低，機率越高
        min_pred = np.min(pred_positions)
        max_pred = np.max(pred_positions)
        
        # 歸一化到 [0, 1]
        normalized = (pred_positions - min_pred) / (max_pred - min_pred + 1e-8)
        
        # 計算勝率（位置越低，勝率越高）
        win_scores = 1 - normalized
        
        # 轉換為機率分布
        exp_scores = np.exp(win_scores * 5)  # 乘以係數增加區分度
        probabilities = exp_scores / exp_scores.sum()
        
        # 對於單一預測，返回 top_n 機率
        if features.ndim == 1 or features.shape[0] == 1:
            # 基於預測位置估算 P1, P2, P3 機率
            pred_pos = pred_positions[0] if features.ndim == 2 else pred_positions
            
            # 使用 sigmoid 函數估算機率
            # P1 機率：位置越接近 1，機率越高
            p1 = 1 / (1 + np.exp((pred_pos - 1) * 2))
            p2 = 1 / (1 + np.exp((pred_pos - 2) * 2))
            p3 = 1 / (1 + np.exp((pred_pos - 3) * 2))
            
            return np.array([p1, p2, p3])
        
        # 批量預測
        results = []
        for pred_pos in pred_positions:
            p1 = 1 / (1 + np.exp((pred_pos - 1) * 2))
            p2 = 1 / (1 + np.exp((pred_pos - 2) * 2))
            p3 = 1 / (1 + np.exp((pred_pos - 3) * 2))
            results.append([p1, p2, p3])
            
        return np.array(results)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        獲取特徵重要性
        
        Returns:
            {feature_name: importance} 字典，按重要性排序
        """
        if self.feature_importance is None:
            raise ValueError("Model not trained. Call train() first.")
            
        # 按重要性排序
        sorted_importance = dict(sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return sorted_importance
    
    def save_model(self, model_path: str) -> None:
        """
        保存模型
        
        Args:
            model_path: 模型保存路徑 (.pkl 或 .json)
        """
        if self.model is None:
            raise ValueError("No model to save. Call train() first.")
            
        # 確保目錄存在
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 保存完整模型資訊
        model_data = {
            'model': self.model,
            'feature_columns': self.FEATURE_COLUMNS,
            'feature_importance': self.feature_importance,
            'training_metrics': self.training_metrics,
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
        }
        
        if model_path.endswith('.json'):
            # 保存為 JSON（僅參數）
            self.model.save_model(model_path)
            # 另外保存 metadata
            meta_path = model_path.replace('.json', '_metadata.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'feature_columns': self.FEATURE_COLUMNS,
                    'feature_importance': self.feature_importance,
                    'training_metrics': self.training_metrics,
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                }, f, indent=2)
        else:
            # 保存為 pickle
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
        logger.info(f"Model saved to: {model_path}")
    
    def load_model(self, model_path: str) -> None:
        """
        載入模型
        
        Args:
            model_path: 模型路徑
        """
        if model_path.endswith('.json'):
            self.model = xgb.XGBRegressor()
            self.model.load_model(model_path)
            # 載入 metadata
            meta_path = model_path.replace('.json', '_metadata.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    self.feature_importance = metadata.get('feature_importance')
                    self.training_metrics = metadata.get('training_metrics', {})
        else:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.feature_importance = model_data.get('feature_importance')
                self.training_metrics = model_data.get('training_metrics', {})
                
        logger.info(f"Model loaded from: {model_path}")


def main():
    """訓練模型的主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train Win Probability Model')
    parser.add_argument('--train', type=str, default='data/live_win_probability/training_data.csv',
                        help='Training data path')
    parser.add_argument('--val', type=str, default='data/live_win_probability/validation_data.csv',
                        help='Validation data path')
    parser.add_argument('--output', type=str, default='models/win_probability_xgb_v1.pkl',
                        help='Output model path')
    parser.add_argument('--n-estimators', type=int, default=200, help='Number of trees')
    parser.add_argument('--max-depth', type=int, default=8, help='Max tree depth')
    parser.add_argument('--learning-rate', type=float, default=0.1, help='Learning rate')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Live Win Probability - Model Training")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 初始化訓練器
    trainer = WinProbabilityModelTrainer()
    
    # 載入數據
    print("[1/4] Loading data...")
    n_train, n_val = trainer.load_data(args.train, args.val)
    print(f"  Training samples: {n_train}")
    print(f"  Validation samples: {n_val}")
    print()
    
    # 訓練模型
    print("[2/4] Training model...")
    metrics = trainer.train(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        verbose=True
    )
    print()
    
    # 顯示特徵重要性
    print("[3/4] Feature Importance:")
    importance = trainer.get_feature_importance()
    for i, (feature, imp) in enumerate(importance.items()):
        print(f"  {i+1:2d}. {feature:25s}: {imp:.4f}")
    print()
    
    # 保存模型
    print("[4/4] Saving model...")
    trainer.save_model(args.output)
    
    print()
    print("=" * 60)
    print("Training Summary")
    print("=" * 60)
    print(f"  Validation MAE: {metrics['val_mae']:.3f} positions")
    print(f"  Validation RMSE: {metrics['val_rmse']:.3f} positions")
    print(f"  Exact Position Accuracy: {metrics['val_exact_accuracy']:.2%}")
    print(f"  Top-3 Prediction Accuracy: {metrics['val_top3_accuracy']:.2%}")
    print(f"  Model saved to: {args.output}")
    print()


if __name__ == "__main__":
    main()
