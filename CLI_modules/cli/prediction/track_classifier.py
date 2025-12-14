#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
賽道分類訓練器 - 功能 73（重構版）

用途：按賽道類別訓練獨立的 XGBoost 模型
創建時間：2025-11-02
相關文檔：docs/develop task/CLI develop task/AI分析FP,Q,R-精簡版.md

遵循反幻覺編碼五原則：
1. 禁止幻覺編碼：複用 XGBoostTrainer 已驗證的代碼
2. 數據來源透明：基於 track_categories.py 的分類
3. 性能保守估算：目標 MAE 0.60-0.70s（改善 25-30%）
4. 處理異常情況：未分類賽道預設為 mixed
5. 成本保守估算：無額外 API 成本
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# XGBoost
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 本地模組
from .track_categories import (
    get_track_category, 
    get_all_categories, 
    get_tracks_in_category,
    get_category_statistics
)
from .xgboost_trainer import XGBoostTrainer


class TrackSpecificTrainer:
    """賽道分類訓練器 - 為每個賽道類別訓練獨立模型"""
    
    def __init__(self, json_dir: str = "json/predictionJSON", verbose: bool = True):
        """
        初始化賽道分類訓練器
        
        Args:
            json_dir: JSON 數據目錄
            verbose: 是否顯示詳細輸出
        """
        self.json_dir = json_dir
        self.verbose = verbose
        self.models = {}  # {category: trained_model}
        self.best_params = {}  # {category: best_params}
        self.performance = {}  # {category: performance_metrics}
        
        # 目錄設定
        self.models_dir = Path("models")
        self.reports_dir = Path("reports")
        self.models_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # 基礎訓練器（用於數據載入和預處理）
        self.base_trainer = XGBoostTrainer(json_dir=json_dir, verbose=False)
        
        if self.verbose:
            print("\n" + "="*70)
            print("🏁 賽道分類訓練器 - 功能 73 (方案 1)")
            print("="*70)
            print(f"📂 數據目錄: {json_dir}")
            print(f"💾 模型輸出: {self.models_dir}/")
            print(f"📊 報告輸出: {self.reports_dir}/")
            
            # 顯示賽道分類統計
            stats = get_category_statistics()
            print(f"\n🏎️  賽道分類統計:")
            for category, count in stats.items():
                print(f"   {category:12s}: {count:2d} 個賽道")
    
    def train_all_categories(self, start_year: int = 2018, end_year: int = 2023,
                            exclude_wet: bool = True, 
                            use_fast_params: bool = False) -> Dict:
        """
        為每個賽道類別訓練獨立模型
        
        Args:
            start_year: 起始年份
            end_year: 結束年份（訓練數據，2024 保留為驗證）
            exclude_wet: 是否排除濕地會話
            use_fast_params: 是否使用快速參數（測試用）
            
        Returns:
            Dict: 訓練結果摘要
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"🚀 開始訓練賽道分類模型")
            print(f"{'='*70}")
            print(f"   訓練年份: {start_year}-{end_year}")
            print(f"   排除濕地: {'是' if exclude_wet else '否'}")
        
        # Step 1: 載入完整訓練數據
        if self.verbose:
            print(f"\n📂 載入訓練數據...")
        
        df = self.base_trainer.load_training_data(
            start_year=start_year,
            end_year=end_year,
            exclude_wet=exclude_wet
        )
        
        if df.empty:
            print("❌ 錯誤：無法載入訓練數據")
            return {}
        
        if self.verbose:
            print(f"   ✅ 載入 {len(df)} 筆訓練樣本")
        
        # Step 2: 添加賽道類別欄位
        df['track_category'] = df['race'].apply(get_track_category)
        
        if self.verbose:
            print(f"\n賽道分類分佈:")
            category_counts = df['track_category'].value_counts()
            for category, count in category_counts.items():
                print(f"   {category:12s}: {count:4d} 筆 ({count/len(df)*100:.1f}%)")
        
        # Step 2.5: 預先 fit label encoders（使用全部數據）
        # 這樣可以避免在分類訓練時遇到未見過的標籤
        if self.verbose:
            print(f"\n預處理類別編碼器...")
        
        categorical_cols = ['driver', 'team', 'race']
        for col in categorical_cols:
            if col in df.columns:
                from sklearn.preprocessing import LabelEncoder
                encoder = LabelEncoder()
                encoder.fit(df[col].astype(str))
                self.base_trainer.label_encoders[col] = encoder
        
        if self.verbose:
            print(f"   已初始化 {len(categorical_cols)} 個類別編碼器")
        
        # Step 3: 為每個類別訓練模型
        training_results = {}
        
        for category in get_all_categories():
            if self.verbose:
                print(f"\n{'='*70}")
                print(f"🏎️  訓練 {category.upper()} 類別模型")
                print(f"{'='*70}")
            
            # 篩選該類別數據
            category_df = df[df['track_category'] == category].copy()
            
            if len(category_df) < 20:
                print(f"   ⚠️  {category} 樣本數不足 ({len(category_df)} < 20)，跳過")
                continue
            
            # 訓練該類別模型
            result = self._train_single_category(
                category=category,
                df=category_df,
                use_fast_params=use_fast_params
            )
            
            training_results[category] = result
        
        # Step 4: 生成訓練摘要
        summary = self._generate_training_summary(training_results, df)
        
        if self.verbose:
            self._print_training_summary(summary)
        
        return summary
    
    def _train_single_category(self, category: str, df: pd.DataFrame, 
                              use_fast_params: bool = False) -> Dict:
        """
        訓練單一類別模型
        
        Args:
            category: 賽道類別
            df: 該類別的訓練數據
            use_fast_params: 是否使用快速參數
            
        Returns:
            Dict: 訓練結果
        """
        if self.verbose:
            print(f"   樣本數: {len(df)}")
            print(f"   賽道數: {df['race'].nunique()}")
            print(f"   年份範圍: {df['year'].min()}-{df['year'].max()}")
        
        # 準備特徵和標籤
        X, y = self.base_trainer.prepare_features(df)
        
        if self.verbose:
            print(f"   特徵數: {len(X.columns)}")
        
        # 設定超參數
        if use_fast_params:
            # 快速測試參數
            params = {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 3,
                'gamma': 0.1,
                'random_state': 42,
                'objective': 'reg:squarederror',
                'n_jobs': -1
            }
        else:
            # 使用 Function 73 的最佳參數作為基準
            params = {
                'n_estimators': 300,
                'max_depth': 8,
                'learning_rate': 0.03,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 3,
                'gamma': 0.1,
                'random_state': 42,
                'objective': 'reg:squarederror',
                'n_jobs': -1
            }
        
        # 創建並訓練模型
        model = XGBRegressor(**params)
        
        # 時間序列交叉驗證
        tscv = TimeSeriesSplit(n_splits=5)
        cv_results = self._evaluate_model_cv(model, X, y, tscv)
        
        # 用全部數據訓練最終模型
        model.fit(X, y)
        
        # 保存模型和參數
        self.models[category] = model
        self.best_params[category] = params
        self.performance[category] = cv_results
        
        # 保存到檔案
        model_path = self.models_dir / f"xgboost_{category}.pkl"
        joblib.dump(model, model_path)
        
        if self.verbose:
            print(f"\n   ✅ 訓練完成")
            print(f"      MAE: {cv_results['mae_mean']:.3f}s ± {cv_results['mae_std']:.3f}s")
            print(f"      R²:  {cv_results['r2_mean']:.3f}")
            print(f"      💾 已保存: {model_path}")
        
        return {
            'mae_mean': cv_results['mae_mean'],
            'mae_std': cv_results['mae_std'],
            'r2_mean': cv_results['r2_mean'],
            'params': params,
            'samples': len(df),
            'tracks': df['race'].nunique(),
            'model_path': str(model_path)
        }
    
    def _evaluate_model_cv(self, model, X, y, cv) -> Dict:
        """交叉驗證評估模型（複用 XGBoostTrainer 邏輯）"""
        mae_scores = []
        rmse_scores = []
        r2_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(cv.split(X), 1):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            
            mae = mean_absolute_error(y_val, y_pred)
            rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            r2 = r2_score(y_val, y_pred)
            
            mae_scores.append(mae)
            rmse_scores.append(rmse)
            r2_scores.append(r2)
            
            if self.verbose:
                print(f"   Fold {fold}: MAE={mae:.3f}s, R²={r2:.3f}")
        
        return {
            'mae_mean': np.mean(mae_scores),
            'mae_std': np.std(mae_scores),
            'rmse_mean': np.mean(rmse_scores),
            'r2_mean': np.mean(r2_scores),
            'fold_maes': mae_scores
        }
    
    def predict(self, race: str, features: pd.DataFrame) -> np.ndarray:
        """
        根據賽道類別選擇對應模型進行預測
        
        Args:
            race: 賽事名稱
            features: 特徵數據
            
        Returns:
            np.ndarray: 預測結果
        """
        category = get_track_category(race)
        
        if category not in self.models:
            # 如果該類別模型不存在，嘗試載入
            model_path = self.models_dir / f"xgboost_{category}.pkl"
            if model_path.exists():
                self.models[category] = joblib.load(model_path)
            else:
                raise ValueError(f"找不到 {category} 類別的模型: {model_path}")
        
        model = self.models[category]
        return model.predict(features)
    
    def evaluate_by_category(self, test_df: pd.DataFrame) -> Dict:
        """
        按類別評估測試集性能
        
        Args:
            test_df: 測試數據（應包含 2024 數據）
            
        Returns:
            Dict: 各類別性能指標
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"📊 按類別評估性能（測試集）")
            print(f"{'='*70}")
        
        # 添加賽道類別
        test_df['track_category'] = test_df['race'].apply(get_track_category)
        
        results = {}
        
        for category in get_all_categories():
            category_df = test_df[test_df['track_category'] == category]
            
            if len(category_df) == 0:
                if self.verbose:
                    print(f"\n{category:12s}: 無測試樣本")
                continue
            
            # 準備特徵
            X, y = self.base_trainer.prepare_features(category_df)
            
            # 預測
            y_pred = self.predict(category_df['race'].iloc[0], X)
            
            # 計算指標
            mae = mean_absolute_error(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            r2 = r2_score(y, y_pred)
            
            results[category] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'samples': len(category_df),
                'races': category_df['race'].unique().tolist()
            }
            
            if self.verbose:
                print(f"\n{category.upper():12s}:")
                print(f"   樣本數: {len(category_df)}")
                print(f"   MAE: {mae:.3f}s")
                print(f"   RMSE: {rmse:.3f}s")
                print(f"   R²: {r2:.3f}")
        
        return results
    
    def _generate_training_summary(self, training_results: Dict, full_df: pd.DataFrame) -> Dict:
        """生成訓練摘要報告"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'training_period': f"{full_df['year'].min()}-{full_df['year'].max()}",
            'total_samples': len(full_df),
            'categories': {},
            'overall': {}
        }
        
        # 各類別結果
        total_mae_weighted = 0
        total_samples = 0
        
        for category, result in training_results.items():
            summary['categories'][category] = result
            total_mae_weighted += result['mae_mean'] * result['samples']
            total_samples += result['samples']
        
        # 整體加權 MAE
        if total_samples > 0:
            summary['overall']['weighted_mae'] = total_mae_weighted / total_samples
            summary['overall']['total_samples'] = total_samples
        
        return summary
    
    def _print_training_summary(self, summary: Dict):
        """列印訓練摘要"""
        print(f"\n{'='*70}")
        print(f"📈 訓練摘要報告")
        print(f"{'='*70}")
        print(f"訓練時間: {summary['timestamp']}")
        print(f"訓練期間: {summary['training_period']}")
        print(f"總樣本數: {summary['total_samples']}")
        
        print(f"\n各類別性能:")
        print(f"{'類別':<15s} {'樣本數':>8s} {'賽道數':>8s} {'MAE':>10s} {'R²':>8s}")
        print("-" * 70)
        
        for category, result in summary['categories'].items():
            print(f"{category:<15s} {result['samples']:>8d} {result['tracks']:>8d} "
                  f"{result['mae_mean']:>9.3f}s {result['r2_mean']:>8.3f}")
        
        if 'weighted_mae' in summary['overall']:
            print("-" * 70)
            print(f"{'整體加權 MAE':<15s} {summary['overall']['total_samples']:>8d} "
                  f"{'':>8s} {summary['overall']['weighted_mae']:>9.3f}s")
    
    def save_training_report(self, summary: Dict, report_name: str = "track_classification_training") -> str:
        """保存訓練報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"{report_name}_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"\n💾 訓練報告已保存: {report_path}")
        
        return str(report_path)


# 測試代碼
if __name__ == "__main__":
    print("TrackSpecificTrainer 測試")
    print("="*70)
    
    # 創建訓練器
    trainer = TrackSpecificTrainer(verbose=True)
    
    # 測試訓練（使用快速參數）
    print("\n測試：訓練所有類別模型（快速模式）")
    summary = trainer.train_all_categories(
        start_year=2022,  # 只用 2022-2023 測試
        end_year=2023,
        use_fast_params=True
    )
    
    # 保存報告
    trainer.save_training_report(summary)
