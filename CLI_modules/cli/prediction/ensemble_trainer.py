#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function 76: Ensemble Learning Trainer
集成學習訓練器 - XGBoost + LightGBM + CatBoost

策略：
1. 訓練三個基礎模型（XGBoost, LightGBM, CatBoost）
2. 實現兩種集成方法：加權平均 & Stacking
3. 自動選擇最佳集成策略
4. 目標：MAE < 0.80s
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.linear_model import Ridge
import xgboost as xgb
import lightgbm as lgb
import catboost as ctb


class EnsembleTrainer:
    """集成學習訓練器"""
    
    def __init__(self, features_count=15, verbose=True):
        """
        初始化訓練器
        
        Args:
            features_count: 特徵數量（預設 15 個純 FP3 特徵）
            verbose: 是否顯示詳細輸出
        """
        self.features_count = features_count
        self.verbose = verbose
        
        # 基礎模型
        self.xgb_model = None
        self.lgb_model = None
        self.ctb_model = None
        
        # 集成模型
        self.stacking_model = None
        self.ensemble_weights = None
        
        # 性能記錄
        self.performance = {
            'xgboost': {},
            'lightgbm': {},
            'catboost': {},
            'weighted_avg': {},
            'stacking': {},
            'best_method': None
        }
    
    def train_xgboost(self, X_train, y_train, X_val, y_val):
        """訓練 XGBoost 模型（使用 Function 75 的最佳參數）"""
        if self.verbose:
            print("\n[1/3] 訓練 XGBoost 模型...")
        
        # Function 75 的最佳超參數
        params = {
            'n_estimators': 200,
            'max_depth': 7,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0.1,
            'min_child_weight': 3,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42
        }
        
        self.xgb_model = xgb.XGBRegressor(**params)
        self.xgb_model.fit(X_train, y_train)
        
        # 驗證集評估
        y_pred = self.xgb_model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        self.performance['xgboost'] = {
            'mae': mae,
            'r2': r2,
            'rmse': rmse
        }
        
        if self.verbose:
            print(f"  ✅ XGBoost - MAE: {mae:.4f}s, R²: {r2:.4f}")
        
        return self.xgb_model
    
    def train_lightgbm(self, X_train, y_train, X_val, y_val):
        """訓練 LightGBM 模型"""
        if self.verbose:
            print("\n[2/3] 訓練 LightGBM 模型...")
        
        # LightGBM 超參數（對應 XGBoost 設定）
        params = {
            'n_estimators': 200,
            'max_depth': 7,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42,
            'verbose': -1
        }
        
        self.lgb_model = lgb.LGBMRegressor(**params)
        self.lgb_model.fit(X_train, y_train)
        
        # 驗證集評估
        y_pred = self.lgb_model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        self.performance['lightgbm'] = {
            'mae': mae,
            'r2': r2,
            'rmse': rmse
        }
        
        if self.verbose:
            print(f"  ✅ LightGBM - MAE: {mae:.4f}s, R²: {r2:.4f}")
        
        return self.lgb_model
    
    def train_catboost(self, X_train, y_train, X_val, y_val):
        """訓練 CatBoost 模型"""
        if self.verbose:
            print("\n[3/3] 訓練 CatBoost 模型...")
        
        # CatBoost 超參數（對應 XGBoost 設定）
        params = {
            'iterations': 200,
            'depth': 7,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bylevel': 0.8,
            'l2_leaf_reg': 1.0,
            'random_state': 42,
            'verbose': False
        }
        
        self.ctb_model = ctb.CatBoostRegressor(**params)
        self.ctb_model.fit(X_train, y_train)
        
        # 驗證集評估
        y_pred = self.ctb_model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        self.performance['catboost'] = {
            'mae': mae,
            'r2': r2,
            'rmse': rmse
        }
        
        if self.verbose:
            print(f"  ✅ CatBoost - MAE: {mae:.4f}s, R²: {r2:.4f}")
        
        return self.ctb_model
    
    def create_weighted_average(self, X_val, y_val):
        """創建加權平均集成"""
        if self.verbose:
            print("\n[集成策略 1] 創建加權平均集成...")
        
        # 獲取各模型預測
        xgb_pred = self.xgb_model.predict(X_val)
        lgb_pred = self.lgb_model.predict(X_val)
        ctb_pred = self.ctb_model.predict(X_val)
        
        # 基於驗證集 MAE 計算權重（MAE 越小，權重越大）
        xgb_mae = self.performance['xgboost']['mae']
        lgb_mae = self.performance['lightgbm']['mae']
        ctb_mae = self.performance['catboost']['mae']
        
        # 使用倒數作為權重（MAE 越小，權重越大）
        total = (1/xgb_mae) + (1/lgb_mae) + (1/ctb_mae)
        w_xgb = (1/xgb_mae) / total
        w_lgb = (1/lgb_mae) / total
        w_ctb = (1/ctb_mae) / total
        
        self.ensemble_weights = {
            'xgboost': w_xgb,
            'lightgbm': w_lgb,
            'catboost': w_ctb
        }
        
        # 加權平均預測
        y_pred = w_xgb * xgb_pred + w_lgb * lgb_pred + w_ctb * ctb_pred
        
        # 評估
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        self.performance['weighted_avg'] = {
            'mae': mae,
            'r2': r2,
            'rmse': rmse,
            'weights': self.ensemble_weights
        }
        
        if self.verbose:
            print(f"  權重: XGB={w_xgb:.3f}, LGB={w_lgb:.3f}, CTB={w_ctb:.3f}")
            print(f"  ✅ 加權平均 - MAE: {mae:.4f}s, R²: {r2:.4f}")
        
        return mae
    
    def create_stacking(self, X_train, y_train, X_val, y_val):
        """創建 Stacking 集成（使用 Ridge 回歸作為元模型）"""
        if self.verbose:
            print("\n[集成策略 2] 創建 Stacking 集成...")
        
        # 獲取訓練集的基礎模型預測（用於訓練元模型）
        xgb_train_pred = self.xgb_model.predict(X_train)
        lgb_train_pred = self.lgb_model.predict(X_train)
        ctb_train_pred = self.ctb_model.predict(X_train)
        
        # 組合訓練集預測作為元模型特徵
        meta_features_train = np.column_stack([
            xgb_train_pred,
            lgb_train_pred,
            ctb_train_pred
        ])
        
        # 訓練元模型（Ridge 回歸）
        self.stacking_model = Ridge(alpha=1.0, random_state=42)
        self.stacking_model.fit(meta_features_train, y_train)
        
        # 獲取驗證集的基礎模型預測
        xgb_val_pred = self.xgb_model.predict(X_val)
        lgb_val_pred = self.lgb_model.predict(X_val)
        ctb_val_pred = self.ctb_model.predict(X_val)
        
        # 組合驗證集預測
        meta_features_val = np.column_stack([
            xgb_val_pred,
            lgb_val_pred,
            ctb_val_pred
        ])
        
        # 元模型預測
        y_pred = self.stacking_model.predict(meta_features_val)
        
        # 評估
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        # 記錄元模型的係數（相當於權重）
        stacking_weights = {
            'xgboost': float(self.stacking_model.coef_[0]),
            'lightgbm': float(self.stacking_model.coef_[1]),
            'catboost': float(self.stacking_model.coef_[2]),
            'intercept': float(self.stacking_model.intercept_)
        }
        
        self.performance['stacking'] = {
            'mae': mae,
            'r2': r2,
            'rmse': rmse,
            'weights': stacking_weights
        }
        
        if self.verbose:
            print(f"  元模型係數: XGB={stacking_weights['xgboost']:.3f}, "
                  f"LGB={stacking_weights['lightgbm']:.3f}, "
                  f"CTB={stacking_weights['catboost']:.3f}")
            print(f"  ✅ Stacking - MAE: {mae:.4f}s, R²: {r2:.4f}")
        
        return mae
    
    def select_best_method(self):
        """選擇最佳集成方法"""
        # 比較所有方法的 MAE
        methods = {
            'xgboost': self.performance['xgboost']['mae'],
            'lightgbm': self.performance['lightgbm']['mae'],
            'catboost': self.performance['catboost']['mae'],
            'weighted_avg': self.performance['weighted_avg']['mae'],
            'stacking': self.performance['stacking']['mae']
        }
        
        best_method = min(methods, key=methods.get)
        self.performance['best_method'] = best_method
        
        if self.verbose:
            print(f"\n最佳方法: {best_method} (MAE: {methods[best_method]:.4f}s)")
        
        return best_method
    
    def predict(self, X, method='best'):
        """
        使用指定方法進行預測
        
        Args:
            X: 特徵矩陣
            method: 'best', 'xgboost', 'lightgbm', 'catboost', 'weighted_avg', 'stacking'
        """
        if method == 'best':
            method = self.performance['best_method']
        
        if method == 'xgboost':
            return self.xgb_model.predict(X)
        elif method == 'lightgbm':
            return self.lgb_model.predict(X)
        elif method == 'catboost':
            return self.ctb_model.predict(X)
        elif method == 'weighted_avg':
            xgb_pred = self.xgb_model.predict(X)
            lgb_pred = self.lgb_model.predict(X)
            ctb_pred = self.ctb_model.predict(X)
            
            w = self.ensemble_weights
            return w['xgboost'] * xgb_pred + w['lightgbm'] * lgb_pred + w['catboost'] * ctb_pred
        elif method == 'stacking':
            xgb_pred = self.xgb_model.predict(X)
            lgb_pred = self.lgb_model.predict(X)
            ctb_pred = self.ctb_model.predict(X)
            
            meta_features = np.column_stack([xgb_pred, lgb_pred, ctb_pred])
            return self.stacking_model.predict(meta_features)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def save(self, output_dir="models"):
        """保存模型"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存各個模型
        with open(output_path / "xgboost_pure_fp3.pkl", 'wb') as f:
            pickle.dump(self.xgb_model, f)
        
        with open(output_path / "lightgbm_pure_fp3.pkl", 'wb') as f:
            pickle.dump(self.lgb_model, f)
        
        with open(output_path / "catboost_pure_fp3.pkl", 'wb') as f:
            pickle.dump(self.ctb_model, f)
        
        if self.stacking_model is not None:
            with open(output_path / "stacking_meta_model.pkl", 'wb') as f:
                pickle.dump(self.stacking_model, f)
        
        # 保存集成配置
        ensemble_config = {
            'best_method': self.performance['best_method'],
            'ensemble_weights': self.ensemble_weights,
            'performance': self.performance
        }
        
        with open(output_path / "ensemble_config.json", 'w', encoding='utf-8') as f:
            json.dump(ensemble_config, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"\n✅ 模型已保存至: {output_path}")
    
    def load(self, model_dir="models"):
        """載入模型"""
        model_path = Path(model_dir)
        
        with open(model_path / "xgboost_pure_fp3.pkl", 'rb') as f:
            self.xgb_model = pickle.load(f)
        
        with open(model_path / "lightgbm_pure_fp3.pkl", 'rb') as f:
            self.lgb_model = pickle.load(f)
        
        with open(model_path / "catboost_pure_fp3.pkl", 'rb') as f:
            self.ctb_model = pickle.load(f)
        
        if (model_path / "stacking_meta_model.pkl").exists():
            with open(model_path / "stacking_meta_model.pkl", 'rb') as f:
                self.stacking_model = pickle.load(f)
        
        with open(model_path / "ensemble_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.performance = config['performance']
            self.ensemble_weights = config['ensemble_weights']
        
        if self.verbose:
            print(f"✅ 模型已載入: {model_path}")
