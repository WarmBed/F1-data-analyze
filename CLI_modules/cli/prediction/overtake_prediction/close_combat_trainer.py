#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Close Combat Model Trainer (F85)
=================================

訓練近距離接觸預測模型 (0.2-0.3s)。

輸入:
- data/overtake_prediction/training_samples.csv

輸出:
- models/overtake_prediction/close_combat_xgb_v1.json
- models/overtake_prediction/close_combat_feature_importance.csv
- models/overtake_prediction/close_combat_training_report.json

Author: F1T Team
Date: 2025-12-09
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

try:
    import xgboost as xgb
except ImportError:
    xgb = None


class CloseCombatModelTrainer:
    """
    近距離接觸預測模型訓練器
    
    訓練 XGBoost 分類器預測是否會進入 0.2-0.3s 近距離接觸。
    """
    
    # F85 特徵列表 (13個：F83 的 10個 + 3個新特徵)
    FEATURE_COLUMNS = [
        # F83 原有特徵
        'gap_seconds',
        'gap_delta',
        'is_catching',
        'drs_available',
        'attacker_tyre_compound',
        'defender_tyre_compound',
        'tyre_age_diff',
        'track_status_green',
        'attacker_position',
        'race_progress',
        # F85 新增特徵
        'gap_trend_3lap',
        'min_gap_last_5lap',
        'consecutive_catching_laps',
    ]
    
    TARGET_COLUMN = 'close_combat_happened'
    
    def __init__(self,
                 data_dir: str = None,
                 model_dir: str = None,
                 verbose: bool = True):
        """初始化訓練器"""
        if xgb is None:
            raise ImportError("請安裝 xgboost: pip install xgboost")
        
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        
        self.data_dir = Path(data_dir) if data_dir else project_root / "data" / "overtake_prediction"
        self.model_dir = Path(model_dir) if model_dir else project_root / "models" / "overtake_prediction"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.verbose = verbose
        self.df: Optional[pd.DataFrame] = None
        self.X_train: Optional[np.ndarray] = None
        self.X_test: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None
        self.scaler: Optional[StandardScaler] = None
        self.model: Optional[xgb.XGBClassifier] = None
        self.metrics: Dict[str, float] = {}
    
    def load_data(self) -> bool:
        """載入訓練數據"""
        samples_file = self.data_dir / "training_samples.csv"
        
        if not samples_file.exists():
            print(f"[ERROR] 找不到訓練數據: {samples_file}")
            return False
        
        self.df = pd.read_csv(samples_file)
        
        if self.verbose:
            print(f"[F85] 載入 {len(self.df)} 個訓練樣本")
            print(f"      特徵數: {len(self.FEATURE_COLUMNS)}")
        
        # 檢查必要欄位
        missing_cols = []
        for col in self.FEATURE_COLUMNS + [self.TARGET_COLUMN]:
            if col not in self.df.columns:
                missing_cols.append(col)
        
        if missing_cols:
            print(f"[WARNING] 缺少欄位: {missing_cols}")
            print(f"[INFO] 使用向後兼容模式，為缺失欄位提供默認值")
            
            # 為缺少的新特徵填充預設值
            for col in missing_cols:
                if col == 'gap_trend_3lap':
                    self.df[col] = 0.0
                    if self.verbose:
                        print(f"      - {col}: 預設為 0.0 (無趨勢)")
                        
                elif col == 'min_gap_last_5lap':
                    self.df[col] = self.df.get('gap_seconds', 2.0)
                    if self.verbose:
                        print(f"      - {col}: 使用 gap_seconds 作為默認值")
                        
                elif col == 'consecutive_catching_laps':
                    self.df[col] = 0
                    if self.verbose:
                        print(f"      - {col}: 預設為 0 (無連續追近記錄)")
                        
                elif col == self.TARGET_COLUMN:
                    # 為舊數據生成 close_combat 標籤
                    # 啟發式規則：如果 gap < 0.5s 且發生超車，視為近距離接觸
                    if 'overtake_happened' in self.df.columns and 'gap_seconds' in self.df.columns:
                        self.df[col] = (
                            (self.df['overtake_happened'] == 1) & 
                            (self.df['gap_seconds'] < 0.5)
                        ).astype(int)
                        
                        close_combat_count = self.df[col].sum()
                        print(f"[INFO] 為舊數據自動生成 {close_combat_count} 個 close_combat 標籤")
                        print(f"      規則: overtake_happened=1 且 gap<0.5s")
                    else:
                        print(f"[ERROR] 缺少目標標籤且無法生成: {self.TARGET_COLUMN}")
                        return False
        
        return True
    
    def prepare_features(self, test_size: float = 0.2, random_state: int = 42):
        """準備訓練特徵"""
        X = self.df[self.FEATURE_COLUMNS].values
        y = self.df[self.TARGET_COLUMN].values
        
        # 分割數據
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # 標準化
        self.scaler = StandardScaler()
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_test = self.scaler.transform(self.X_test)
        
        if self.verbose:
            print(f"[F85] 訓練集: {len(self.X_train)} 樣本")
            print(f"      測試集: {len(self.X_test)} 樣本")
            print(f"      正樣本比例: {y.sum() / len(y):.2%}")
    
    def train(self, **xgb_params):
        """訓練模型"""
        default_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'random_state': 42
        }
        default_params.update(xgb_params)
        
        self.model = xgb.XGBClassifier(**default_params)
        
        if self.verbose:
            print("[F85] 開始訓練...")
        
        self.model.fit(self.X_train, self.y_train)
        
        # 評估
        self._evaluate()
        
        if self.verbose:
            print(f"[F85] 訓練完成 - AUC: {self.metrics.get('roc_auc', 0):.4f}")
    
    def _evaluate(self):
        """評估模型"""
        y_pred = self.model.predict(self.X_test)
        y_pred_proba = self.model.predict_proba(self.X_test)[:, 1]
        
        self.metrics = {
            'accuracy': accuracy_score(self.y_test, y_pred),
            'precision': precision_score(self.y_test, y_pred, zero_division=0),
            'recall': recall_score(self.y_test, y_pred, zero_division=0),
            'f1_score': f1_score(self.y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(self.y_test, y_pred_proba),
        }
        
        # 交叉驗證
        cv_scores = cross_val_score(
            self.model, self.X_train, self.y_train,
            cv=5, scoring='roc_auc'
        )
        self.metrics['cv_mean_auc'] = cv_scores.mean()
        self.metrics['cv_std_auc'] = cv_scores.std()
    
    def save_model(self, version: str = "v1"):
        """保存模型"""
        model_file = self.model_dir / f"close_combat_xgb_{version}.json"
        self.model.save_model(str(model_file))
        
        # 保存特徵重要性
        importance_df = pd.DataFrame({
            'feature': self.FEATURE_COLUMNS,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        importance_file = self.model_dir / f"close_combat_feature_importance_{version}.csv"
        importance_df.to_csv(importance_file, index=False)
        
        # 保存訓練報告
        report = {
            'model_type': 'XGBClassifier',
            'version': version,
            'trained_at': datetime.now().isoformat(),
            'features': self.FEATURE_COLUMNS,
            'metrics': self.metrics,
            'sample_count': {
                'total': len(self.df),
                'train': len(self.X_train),
                'test': len(self.X_test),
                'positive': int(self.df[self.TARGET_COLUMN].sum())
            }
        }
        
        report_file = self.model_dir / f"close_combat_training_report_{version}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"[F85] 模型已保存: {model_file.name}")
            print(f"      特徵重要性: {importance_file.name}")
            print(f"      訓練報告: {report_file.name}")
        
        return report


def run_f85_model_training(version: str = "v1", verbose: bool = True) -> Dict[str, Any]:
    """
    執行 F85 近距離接觸預測模型訓練
    
    Args:
        version: 模型版本
        verbose: 是否顯示詳細輸出
    
    Returns:
        訓練報告字典
    """
    try:
        trainer = CloseCombatModelTrainer(verbose=verbose)
        
        if not trainer.load_data():
            return {"success": False, "message": "數據載入失敗"}
        
        trainer.prepare_features()
        trainer.train()
        report = trainer.save_model(version=version)
        
        return {
            "success": True,
            "message": "F85 模型訓練完成",
            "report": report
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"訓練失敗: {str(e)}",
            "error": str(e)
        }


if __name__ == "__main__":
    print("=" * 70)
    print("F85: Close Combat Predictor - Model Training")
    print("=" * 70)
    
    result = run_f85_model_training(version="v1", verbose=True)
    
    if result['success']:
        report = result['report']
        print("\n" + "=" * 70)
        print("訓練結果")
        print("=" * 70)
        print(f"AUC: {report['metrics']['roc_auc']:.4f}")
        print(f"Accuracy: {report['metrics']['accuracy']:.4f}")
        print(f"Precision: {report['metrics']['precision']:.4f}")
        print(f"Recall: {report['metrics']['recall']:.4f}")
    else:
        print(f"\n[ERROR] {result['message']}")
