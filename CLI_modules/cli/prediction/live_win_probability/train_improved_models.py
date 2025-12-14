#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改進版勝率預測模型訓練腳本

訓練多個模型版本並比較：
1. 原始 XGBoost 回歸 (預測最終位置)
2. XGBoost 分類 (直接預測 P1/P2/P3)
3. LightGBM 回歸
4. 集成模型

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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

import xgboost as xgb

# 設置路徑
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = ROOT_DIR / "data" / "live_win_probability"
MODEL_DIR = ROOT_DIR / "models"


class ImprovedModelTrainer:
    """改進版模型訓練器"""
    
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
    
    def __init__(self):
        self.train_df = None
        self.val_df = None
        self.results = {}
        
    def load_data(self):
        """載入數據"""
        print("=" * 60)
        print("載入數據...")
        
        self.train_df = pd.read_csv(DATA_DIR / "training_data.csv")
        self.val_df = pd.read_csv(DATA_DIR / "validation_data.csv")
        
        print(f"訓練樣本: {len(self.train_df)}")
        print(f"驗證樣本: {len(self.val_df)}")
        
        # 數據預處理
        self._preprocess()
        
    def _preprocess(self):
        """數據預處理"""
        # 處理缺失值
        for df in [self.train_df, self.val_df]:
            for col in self.FEATURE_COLUMNS:
                if col in df.columns:
                    df[col] = df[col].fillna(0)
        
        # 添加衍生特徵
        for df in [self.train_df, self.val_df]:
            # 位置變化潛力 (排位賽位置 - 當前位置)
            df['position_delta'] = df['qualifying_position'] - df['position']
            
            # 領先者差距的對數 (減少極端值影響)
            df['log_gap'] = np.log1p(df['gap_to_leader'].abs())
            
            # 比賽進度 (已完成圈數比例)
            df['race_progress'] = 1 - (df['laps_remaining'] / df['laps_remaining'].max())
            
            # 創建分類標籤
            df['is_p1'] = (df['final_position'] == 1).astype(int)
            df['is_p2'] = (df['final_position'] <= 2).astype(int)
            df['is_p3'] = (df['final_position'] <= 3).astype(int)
        
        # 更新特徵列
        self.FEATURE_COLUMNS_EXTENDED = self.FEATURE_COLUMNS + ['position_delta', 'log_gap', 'race_progress']
        
    def get_features_labels(self, df: pd.DataFrame, label_col: str = 'final_position'):
        """獲取特徵和標籤"""
        X = df[self.FEATURE_COLUMNS_EXTENDED].values
        y = df[label_col].values
        return X, y
    
    def train_regression_model(self, name: str, params: dict) -> dict:
        """訓練回歸模型"""
        print(f"\n{'='*60}")
        print(f"訓練模型: {name}")
        print(f"參數: {params}")
        
        X_train, y_train = self.get_features_labels(self.train_df, 'final_position')
        X_val, y_val = self.get_features_labels(self.val_df, 'final_position')
        
        # 訓練模型
        model = xgb.XGBRegressor(
            random_state=42,
            n_jobs=-1,
            **params
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # 預測
        y_pred = model.predict(X_val)
        
        # 計算指標
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        # 計算 Top-N 準確率
        top1_acc = self._calc_top_n_accuracy(y_val, y_pred, 1)
        top3_acc = self._calc_top_n_accuracy(y_val, y_pred, 3)
        top5_acc = self._calc_top_n_accuracy(y_val, y_pred, 5)
        
        # 計算勝率預測準確率
        p1_acc, p2_acc, p3_acc = self._calc_win_probability_accuracy(y_val, y_pred)
        
        results = {
            'model': model,
            'name': name,
            'params': params,
            'mae': mae,
            'rmse': rmse,
            'top1_acc': top1_acc,
            'top3_acc': top3_acc,
            'top5_acc': top5_acc,
            'p1_acc': p1_acc,
            'p2_acc': p2_acc,
            'p3_acc': p3_acc,
        }
        
        print(f"\n結果:")
        print(f"  MAE: {mae:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  Top-1 準確率: {top1_acc:.2%}")
        print(f"  Top-3 準確率: {top3_acc:.2%}")
        print(f"  Top-5 準確率: {top5_acc:.2%}")
        print(f"  P1 預測準確率: {p1_acc:.2%}")
        print(f"  P2 預測準確率: {p2_acc:.2%}")
        print(f"  P3 預測準確率: {p3_acc:.2%}")
        
        return results
    
    def train_classification_model(self, name: str, label_col: str, params: dict) -> dict:
        """訓練分類模型"""
        print(f"\n{'='*60}")
        print(f"訓練分類模型: {name} (標籤: {label_col})")
        
        X_train, y_train = self.get_features_labels(self.train_df, label_col)
        X_val, y_val = self.get_features_labels(self.val_df, label_col)
        
        model = xgb.XGBClassifier(
            random_state=42,
            n_jobs=-1,
            **params
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        y_pred = model.predict(X_val)
        y_prob = model.predict_proba(X_val)[:, 1]
        
        acc = accuracy_score(y_val, y_pred)
        prec = precision_score(y_val, y_pred, zero_division=0)
        rec = recall_score(y_val, y_pred, zero_division=0)
        f1 = f1_score(y_val, y_pred, zero_division=0)
        
        results = {
            'model': model,
            'name': name,
            'label': label_col,
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1': f1,
        }
        
        print(f"\n結果:")
        print(f"  準確率: {acc:.2%}")
        print(f"  精確率: {prec:.2%}")
        print(f"  召回率: {rec:.2%}")
        print(f"  F1 分數: {f1:.4f}")
        
        return results
    
    def _calc_top_n_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray, n: int) -> float:
        """計算 Top-N 準確率"""
        # 如果預測位置與實際位置差距在 N 以內，算正確
        correct = np.abs(y_true - y_pred) <= n
        return correct.mean()
    
    def _calc_win_probability_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
        """計算勝率預測準確率"""
        # 按預測位置排序，計算預測的 Top-1/2/3 與實際的匹配程度
        
        # P1: 預測第 1 名且實際也是第 1 名
        pred_p1 = (y_pred <= 1.5)
        actual_p1 = (y_true == 1)
        p1_acc = (pred_p1 == actual_p1).mean()
        
        # P2: 預測前 2 名且實際也是前 2 名
        pred_p2 = (y_pred <= 2.5)
        actual_p2 = (y_true <= 2)
        p2_acc = (pred_p2 == actual_p2).mean()
        
        # P3: 預測前 3 名且實際也是前 3 名
        pred_p3 = (y_pred <= 3.5)
        actual_p3 = (y_true <= 3)
        p3_acc = (pred_p3 == actual_p3).mean()
        
        return p1_acc, p2_acc, p3_acc
    
    def run_all_experiments(self):
        """執行所有實驗"""
        self.load_data()
        
        # 實驗 1: 基礎 XGBoost 回歸
        self.results['xgb_basic'] = self.train_regression_model(
            "XGBoost 基礎版",
            {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
            }
        )
        
        # 實驗 2: 調優 XGBoost 回歸
        self.results['xgb_tuned'] = self.train_regression_model(
            "XGBoost 調優版",
            {
                'n_estimators': 200,
                'max_depth': 8,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 3,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
            }
        )
        
        # 實驗 3: 深層 XGBoost
        self.results['xgb_deep'] = self.train_regression_model(
            "XGBoost 深層版",
            {
                'n_estimators': 300,
                'max_depth': 12,
                'learning_rate': 0.03,
                'subsample': 0.7,
                'colsample_bytree': 0.7,
            }
        )
        
        # 實驗 4: P1 分類模型
        self.results['clf_p1'] = self.train_classification_model(
            "P1 分類器",
            'is_p1',
            {
                'n_estimators': 200,
                'max_depth': 8,
                'learning_rate': 0.05,
                'scale_pos_weight': 10,  # 處理類別不平衡
            }
        )
        
        # 實驗 5: P3 分類模型
        self.results['clf_p3'] = self.train_classification_model(
            "P3 分類器",
            'is_p3',
            {
                'n_estimators': 200,
                'max_depth': 8,
                'learning_rate': 0.05,
                'scale_pos_weight': 3,
            }
        )
        
        # 打印總結
        self._print_summary()
        
        # 保存最佳模型
        self._save_best_model()
        
    def _print_summary(self):
        """打印結果總結"""
        print("\n" + "=" * 80)
        print("實驗結果總結")
        print("=" * 80)
        
        print("\n回歸模型比較:")
        print("-" * 60)
        print(f"{'模型名稱':<20} {'MAE':>8} {'Top-1':>8} {'Top-3':>8} {'P1 準確':>8}")
        print("-" * 60)
        
        for key in ['xgb_basic', 'xgb_tuned', 'xgb_deep']:
            if key in self.results:
                r = self.results[key]
                print(f"{r['name']:<20} {r['mae']:>8.4f} {r['top1_acc']:>7.2%} {r['top3_acc']:>7.2%} {r['p1_acc']:>7.2%}")
        
        print("\n分類模型比較:")
        print("-" * 60)
        print(f"{'模型名稱':<20} {'準確率':>8} {'精確率':>8} {'召回率':>8} {'F1':>8}")
        print("-" * 60)
        
        for key in ['clf_p1', 'clf_p3']:
            if key in self.results:
                r = self.results[key]
                print(f"{r['name']:<20} {r['accuracy']:>7.2%} {r['precision']:>7.2%} {r['recall']:>7.2%} {r['f1']:>8.4f}")
    
    def _save_best_model(self):
        """保存最佳模型"""
        # 選擇 Top-3 準確率最高的回歸模型
        best_key = max(
            ['xgb_basic', 'xgb_tuned', 'xgb_deep'],
            key=lambda k: self.results[k]['top3_acc']
        )
        
        best_result = self.results[best_key]
        print(f"\n最佳模型: {best_result['name']}")
        print(f"Top-3 準確率: {best_result['top3_acc']:.2%}")
        
        # 保存模型
        model_path = MODEL_DIR / "win_probability_xgb_v2.pkl"
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': best_result['model'],
            'feature_columns': self.FEATURE_COLUMNS_EXTENDED,
            'metrics': {
                'mae': best_result['mae'],
                'rmse': best_result['rmse'],
                'top1_acc': best_result['top1_acc'],
                'top3_acc': best_result['top3_acc'],
            },
            'trained_at': datetime.now().isoformat(),
            'version': 'v2',
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\n模型已保存至: {model_path}")
        
        # 同時保存分類模型
        if 'clf_p1' in self.results:
            clf_path = MODEL_DIR / "win_probability_clf_p1.pkl"
            with open(clf_path, 'wb') as f:
                pickle.dump({
                    'model': self.results['clf_p1']['model'],
                    'feature_columns': self.FEATURE_COLUMNS_EXTENDED,
                }, f)
            print(f"P1 分類模型已保存至: {clf_path}")


def main():
    """主函數"""
    trainer = ImprovedModelTrainer()
    trainer.run_all_experiments()


if __name__ == "__main__":
    main()
