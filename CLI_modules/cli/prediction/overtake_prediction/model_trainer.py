#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Overtake Model Trainer (F82)
============================

使用收集的超車數據訓練 XGBoost 分類器。

輸入:
- data/overtake_prediction/training_samples.csv

輸出:
- models/overtake_prediction/overtake_xgb_v1.json       - XGBoost 模型
- models/overtake_prediction/feature_importance.csv     - 特徵重要性
- models/overtake_prediction/training_report.json       - 訓練報告

Author: F1T Team
Date: 2025-12-05
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from sklearn.preprocessing import StandardScaler


class OvertakeModelTrainer:
    """
    超車預測模型訓練器
    
    訓練 XGBoost 分類器預測超車事件。
    
    使用方式:
        trainer = OvertakeModelTrainer()
        trainer.load_data()
        trainer.train()
        trainer.save_model()
    """
    
    # 訓練用特徵列表
    FEATURE_COLUMNS = [
        'gap_seconds',           # 間距 (秒)
        'gap_delta',             # 間距變化
        'is_catching',           # 是否追近
        'drs_available',         # DRS 可用
        'attacker_tyre_compound', # 進攻者輪胎
        'defender_tyre_compound', # 防守者輪胎
        'tyre_age_diff',         # 輪胎壽命差
        'track_status_green',    # 綠旗狀態
        'attacker_position',     # 進攻者位置
        'race_progress',         # 比賽進度
    ]
    
    TARGET_COLUMN = 'overtake_happened'
    
    def __init__(self,
                 data_dir: str = None,
                 model_dir: str = None,
                 verbose: bool = True):
        """
        初始化訓練器
        
        Args:
            data_dir: 訓練數據目錄
            model_dir: 模型輸出目錄
            verbose: 是否顯示詳細輸出
        """
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        
        if data_dir is None:
            self.data_dir = project_root / "data" / "overtake_prediction"
        else:
            self.data_dir = Path(data_dir)
        
        if model_dir is None:
            self.model_dir = project_root / "models" / "overtake_prediction"
        else:
            self.model_dir = Path(model_dir)
        
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # 數據
        self.df: Optional[pd.DataFrame] = None
        self.X_train: Optional[np.ndarray] = None
        self.X_test: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None
        self.scaler: Optional[StandardScaler] = None
        
        # 模型
        self.model = None
        self.feature_importance: Optional[pd.DataFrame] = None
        self.training_report: Dict[str, Any] = {}
        
        if self.verbose:
            print(f"[F82] OvertakeModelTrainer 初始化")
            print(f"[F82] 數據目錄: {self.data_dir}")
            print(f"[F82] 模型目錄: {self.model_dir}")
    
    def load_data(self, filepath: str = None) -> pd.DataFrame:
        """
        載入訓練數據
        
        Args:
            filepath: CSV 檔案路徑，None 則使用預設路徑
            
        Returns:
            載入的 DataFrame
        """
        if filepath is None:
            filepath = self.data_dir / "training_samples.csv"
        else:
            filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"訓練數據檔案不存在: {filepath}")
        
        if self.verbose:
            print(f"[F82] 載入訓練數據: {filepath}")
        
        self.df = pd.read_csv(filepath)
        
        if self.verbose:
            print(f"[F82] 載入 {len(self.df)} 筆樣本")
            print(f"[F82] 正樣本: {self.df[self.TARGET_COLUMN].sum()}")
            print(f"[F82] 負樣本: {len(self.df) - self.df[self.TARGET_COLUMN].sum()}")
        
        return self.df
    
    def prepare_data(self, 
                     test_size: float = 0.2,
                     random_state: int = 42,
                     balance: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        準備訓練/測試數據
        
        Args:
            test_size: 測試集比例
            random_state: 隨機種子
            balance: 是否進行類別平衡 (上採樣少數類)
            
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        if self.df is None:
            raise ValueError("請先執行 load_data()")
        
        if self.verbose:
            print(f"[F82] 準備訓練數據...")
        
        # 選擇特徵和標籤
        X = self.df[self.FEATURE_COLUMNS].copy()
        y = self.df[self.TARGET_COLUMN].copy()
        
        # 處理缺失值
        X = X.fillna(0)
        
        # 分割數據
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        if self.verbose:
            print(f"[F82] 訓練集: {len(self.X_train)} 樣本")
            print(f"[F82] 測試集: {len(self.X_test)} 樣本")
        
        # 類別平衡 (SMOTE 替代: 簡單上採樣)
        if balance:
            self._balance_classes()
        
        # 標準化 (可選，XGBoost 不一定需要)
        # self.scaler = StandardScaler()
        # self.X_train = self.scaler.fit_transform(self.X_train)
        # self.X_test = self.scaler.transform(self.X_test)
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def _balance_classes(self):
        """簡單上採樣平衡類別"""
        if self.verbose:
            print(f"[F82] 執行類別平衡...")
        
        # 確保 X_train 是 DataFrame
        if isinstance(self.X_train, pd.DataFrame):
            X_df = self.X_train.copy()
        else:
            X_df = pd.DataFrame(self.X_train, columns=self.FEATURE_COLUMNS)
        
        # 確保 y_train 是 Series
        if isinstance(self.y_train, pd.Series):
            y_series = self.y_train.copy()
        else:
            y_series = pd.Series(self.y_train, name=self.TARGET_COLUMN)
        
        # 合併訓練數據
        train_df = pd.concat([X_df.reset_index(drop=True), y_series.reset_index(drop=True)], axis=1)
        
        # 分離正負樣本
        positive = train_df[train_df[self.TARGET_COLUMN] == 1]
        negative = train_df[train_df[self.TARGET_COLUMN] == 0]
        
        if self.verbose:
            print(f"[F82]   平衡前: 正樣本 {len(positive)}, 負樣本 {len(negative)}")
        
        # 計算目標比例 (1:3 ~ 1:5 較平衡)
        target_ratio = 0.25  # 正樣本佔 25%
        target_positive = int(len(negative) * target_ratio / (1 - target_ratio))
        
        # 上採樣正樣本
        if len(positive) < target_positive:
            positive_upsampled = positive.sample(n=target_positive, replace=True, random_state=42)
        else:
            positive_upsampled = positive
        
        # 合併
        balanced = pd.concat([positive_upsampled, negative]).sample(frac=1, random_state=42)
        
        # 保留 DataFrame 格式以保持特徵名稱
        self.X_train = balanced[self.FEATURE_COLUMNS]
        self.y_train = balanced[self.TARGET_COLUMN].values
        
        if self.verbose:
            print(f"[F82]   平衡後: 正樣本 {sum(self.y_train)}, 負樣本 {len(self.y_train) - sum(self.y_train)}")
    
    def train(self, 
              n_estimators: int = 200,
              max_depth: int = 6,
              learning_rate: float = 0.1,
              scale_pos_weight: float = None) -> Any:
        """
        訓練 XGBoost 模型
        
        Args:
            n_estimators: 樹的數量
            max_depth: 最大深度
            learning_rate: 學習率
            scale_pos_weight: 正樣本權重 (None 則自動計算)
            
        Returns:
            訓練好的模型
        """
        try:
            import xgboost as xgb
        except ImportError:
            raise ImportError("請安裝 xgboost: pip install xgboost")
        
        if self.X_train is None:
            raise ValueError("請先執行 prepare_data()")
        
        if self.verbose:
            print(f"\n[F82] ===== 開始訓練 XGBoost 模型 =====")
            print(f"[F82] 參數: n_estimators={n_estimators}, max_depth={max_depth}, lr={learning_rate}")
        
        # 自動計算正樣本權重
        if scale_pos_weight is None:
            neg_count = sum(self.y_train == 0)
            pos_count = sum(self.y_train == 1)
            scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1
            if self.verbose:
                print(f"[F82] 自動計算 scale_pos_weight: {scale_pos_weight:.2f}")
        
        # 創建模型
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            scale_pos_weight=scale_pos_weight,
            eval_metric='auc',
            random_state=42,
            n_jobs=-1
        )
        
        # 訓練 (關閉 verbose 避免過多輸出)
        start_time = datetime.now()
        if self.verbose:
            print(f"[F82] 訓練中... (這可能需要幾秒鐘)")
        
        self.model.fit(
            self.X_train, self.y_train,
            eval_set=[(self.X_test, self.y_test)],
            verbose=False  # 關閉逐步輸出，避免 VSC 過載
        )
        training_time = (datetime.now() - start_time).total_seconds()
        
        if self.verbose:
            print(f"[F82] 訓練完成! 耗時: {training_time:.2f} 秒")
        
        # 評估
        self._evaluate()
        
        # 特徵重要性
        self._compute_feature_importance()
        
        # 更新訓練報告
        self.training_report.update({
            'model_type': 'XGBClassifier',
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'scale_pos_weight': scale_pos_weight,
            'training_time_seconds': training_time,
            'train_samples': len(self.X_train),
            'test_samples': len(self.X_test),
            'trained_at': datetime.now().isoformat()
        })
        
        return self.model
    
    def _evaluate(self):
        """評估模型效能"""
        if self.model is None:
            return
        
        if self.verbose:
            print(f"\n[F82] ===== 模型評估 =====")
        
        # 預測
        y_pred = self.model.predict(self.X_test)
        y_pred_proba = self.model.predict_proba(self.X_test)[:, 1]
        
        # 計算指標
        metrics = {
            'accuracy': accuracy_score(self.y_test, y_pred),
            'precision': precision_score(self.y_test, y_pred, zero_division=0),
            'recall': recall_score(self.y_test, y_pred, zero_division=0),
            'f1_score': f1_score(self.y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(self.y_test, y_pred_proba)
        }
        
        # 混淆矩陣
        cm = confusion_matrix(self.y_test, y_pred)
        
        if self.verbose:
            print(f"[F82] Accuracy:  {metrics['accuracy']:.4f}")
            print(f"[F82] Precision: {metrics['precision']:.4f}")
            print(f"[F82] Recall:    {metrics['recall']:.4f}")
            print(f"[F82] F1 Score:  {metrics['f1_score']:.4f}")
            print(f"[F82] ROC AUC:   {metrics['roc_auc']:.4f}")
            print(f"\n[F82] 混淆矩陣:")
            print(f"[F82]   TN: {cm[0][0]:5d}  FP: {cm[0][1]:5d}")
            print(f"[F82]   FN: {cm[1][0]:5d}  TP: {cm[1][1]:5d}")
        
        self.training_report['metrics'] = metrics
        self.training_report['confusion_matrix'] = cm.tolist()
    
    def _compute_feature_importance(self):
        """計算特徵重要性"""
        if self.model is None:
            return
        
        importance = self.model.feature_importances_
        self.feature_importance = pd.DataFrame({
            'feature': self.FEATURE_COLUMNS,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        if self.verbose:
            print(f"\n[F82] ===== 特徵重要性 =====")
            for _, row in self.feature_importance.iterrows():
                print(f"[F82]   {row['feature']:30s}: {row['importance']:.4f}")
    
    def cross_validate(self, cv: int = 5) -> Dict[str, float]:
        """
        交叉驗證
        
        Args:
            cv: 折數
            
        Returns:
            交叉驗證分數
        """
        if self.model is None or self.X_train is None:
            raise ValueError("請先訓練模型")
        
        if self.verbose:
            print(f"\n[F82] ===== {cv} 折交叉驗證 =====")
        
        # 合併訓練和測試集
        X_all = np.vstack([self.X_train, self.X_test])
        y_all = np.hstack([self.y_train, self.y_test])
        
        # 交叉驗證
        scores = cross_val_score(self.model, X_all, y_all, cv=cv, scoring='roc_auc')
        
        cv_results = {
            'cv_mean_auc': scores.mean(),
            'cv_std_auc': scores.std(),
            'cv_scores': scores.tolist()
        }
        
        if self.verbose:
            print(f"[F82] 平均 AUC: {cv_results['cv_mean_auc']:.4f} (+/- {cv_results['cv_std_auc']:.4f})")
        
        self.training_report['cross_validation'] = cv_results
        return cv_results
    
    def save_model(self, version: str = "v1") -> Tuple[Path, Path, Path]:
        """
        保存模型和報告
        
        Args:
            version: 模型版本標籤
            
        Returns:
            (模型檔案路徑, 特徵重要性檔案路徑, 報告檔案路徑)
        """
        if self.model is None:
            raise ValueError("請先訓練模型")
        
        # 保存模型
        model_path = self.model_dir / f"overtake_xgb_{version}.json"
        self.model.save_model(str(model_path))
        
        # 保存特徵重要性
        importance_path = self.model_dir / f"feature_importance_{version}.csv"
        if self.feature_importance is not None:
            self.feature_importance.to_csv(importance_path, index=False, encoding='utf-8-sig')
        
        # 保存訓練報告
        report_path = self.model_dir / f"training_report_{version}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.training_report, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"\n[F82] ===== 模型保存完成 =====")
            print(f"[F82] 模型: {model_path}")
            print(f"[F82] 特徵重要性: {importance_path}")
            print(f"[F82] 訓練報告: {report_path}")
        
        return model_path, importance_path, report_path
    
    def get_training_summary(self) -> Dict[str, Any]:
        """獲取訓練摘要"""
        return {
            'data_dir': str(self.data_dir),
            'model_dir': str(self.model_dir),
            'feature_columns': self.FEATURE_COLUMNS,
            'report': self.training_report
        }


# ============================================================================
# CLI 入口點
# ============================================================================
def run_f82_model_training(data_file: str = None,
                           version: str = "v1",
                           verbose: bool = True) -> Dict[str, Any]:
    """
    執行 F82 模型訓練
    
    Args:
        data_file: 訓練數據檔案路徑
        version: 模型版本標籤
        verbose: 是否顯示詳細輸出
        
    Returns:
        訓練報告
    """
    print("=" * 70)
    print("F82: 超車預測模型訓練器")
    print("=" * 70)
    
    trainer = OvertakeModelTrainer(verbose=verbose)
    
    # 載入數據
    trainer.load_data(data_file)
    
    # 準備數據
    trainer.prepare_data(balance=True)
    
    # 訓練模型
    trainer.train(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1
    )
    
    # 交叉驗證
    trainer.cross_validate(cv=5)
    
    # 保存模型
    trainer.save_model(version=version)
    
    summary = trainer.get_training_summary()
    
    print("\n" + "=" * 70)
    print("訓練完成!")
    if 'metrics' in summary['report']:
        print(f"  - ROC AUC: {summary['report']['metrics']['roc_auc']:.4f}")
        print(f"  - F1 Score: {summary['report']['metrics']['f1_score']:.4f}")
    print("=" * 70)
    
    return summary


if __name__ == "__main__":
    # 測試執行
    run_f82_model_training(version="v1")
