#!/usr/bin/env python3
"""
F1 賽道特定模型訓練器 v3.0 - 基於物理特徵的 FP3→Q 預測

設計原則：
1. 使用當前週末的客觀物理數據（不依賴歷史車手特徵）
2. 每個賽道自動學習特徵權重
3. 物理意義明確（Ideal lap + 彎角速度 + 最高速）

特徵架構：
- Ideal Lap: S1/S2/S3 最佳時間
- Corner Speed: 低速/中速/高速彎 apex 速度
- Top Speed: 速度陷阱最高速度

遵循反幻覺編碼五原則：
- 原則 0：禁止幻覺編碼，所有方法調用前先驗證
- 原則 1：複用現有 JSON 數據結構
- 原則 2：使用 UniversalDataLoader 架構模式
- 原則 3：所有字串使用 tr()（未來）
- 原則 4：print 輸出會導向 logger
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

# 機器學習庫
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder


class TrackSpecificTrainerV3:
    """賽道特定模型訓練器 v3.0 - 基於物理特徵"""
    
    def __init__(self, json_dir: str = "json", verbose: bool = True):
        """
        初始化訓練器
        
        Args:
            json_dir: JSON 數據目錄
            verbose: 是否顯示詳細輸出
        """
        self.json_dir = Path(json_dir)
        self.verbose = verbose
        
        # 模型輸出目錄
        self.models_dir = Path("models/track_specific_v3")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 數據存儲
        self.track_data = {}  # {track_name: DataFrame}
        self.track_models = {}  # {track_name: model}
        self.track_performance = {}  # {track_name: metrics}
        
        if self.verbose:
            print("\n" + "="*70)
            print("F1 賽道特定模型訓練器 v3.0 - 物理特徵系統")
            print("="*70)
            print(f"數據目錄: {self.json_dir}")
            print(f"模型輸出: {self.models_dir}/")
            print("\n特徵系統:")
            print("  1. Ideal Lap (S1/S2/S3)")
            print("  2. Corner Speed (Low/Mid/High)")
            print("  3. Top Speed (Speed Trap)")
    
    def load_training_data_v3(self, track_name: str, start_year: int = 2022, 
                             end_year: int = 2024) -> pd.DataFrame:
        """
        載入訓練數據（v3.0 物理特徵版本）
        
        Args:
            track_name: 賽道名稱
            start_year: 起始年份
            end_year: 結束年份
        
        Returns:
            DataFrame: 包含物理特徵和目標的訓練數據
        """
        if self.verbose:
            print(f"\n[載入數據] {track_name} ({start_year}-{end_year})")
        
        all_data = []
        
        for year in range(start_year, end_year + 1):
            # 載入 FP3→Q 數據
            fp_q_file = list(self.json_dir.glob(f"predictionJSON/fp_q_data_{year}_{track_name}_*.json"))
            if not fp_q_file:
                if self.verbose:
                    print(f"  [SKIP] {year} - 找不到 FP3→Q 數據")
                continue
            
            # 載入彎角數據 - 支援 Sprint fallback
            corner_file = self.json_dir / f"all_drivers_cornering_analysis_{year}_{track_name}_FP3.json"
            if not corner_file.exists():
                # Sprint Weekend Fallback: 嘗試使用 Sprint 數據
                sprint_file = self.json_dir / f"all_drivers_cornering_analysis_{year}_{track_name}_Sprint.json"
                if sprint_file.exists():
                    corner_file = sprint_file
                    if self.verbose:
                        print(f"  [INFO] 使用 Sprint 數據替代 FP3")
                else:
                    if self.verbose:
                        print(f"  [SKIP] {year} - 找不到彎角數據（FP3 或 Sprint）")
                    continue
            
            # 讀取數據
            with open(fp_q_file[0], 'r', encoding='utf-8') as f:
                fp_q_data = json.load(f)
            
            with open(corner_file, 'r', encoding='utf-8') as f:
                corner_data = json.load(f)
            
            # 提取特徵
            year_data = self._extract_features_v3(fp_q_data, corner_data, year)
            
            if year_data:
                all_data.extend(year_data)
                if self.verbose:
                    print(f"  [OK] {year} - {len(year_data)} 樣本")
        
        if not all_data:
            if self.verbose:
                print(f"  [ERROR] 沒有可用數據")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        
        if self.verbose:
            print(f"\n[統計] 總樣本數: {len(df)}")
            print(f"[統計] 特徵數量: {len(df.columns) - 2}")  # 排除 driver, actual_q_time
        
        return df
    
    def _extract_features_v3(self, fp_q_data: Dict, corner_data: Dict, year: int) -> List[Dict]:
        """
        提取物理特徵（v3.0）
        
        Args:
            fp_q_data: FP3→Q 數據
            corner_data: 彎角數據
            year: 年份
        
        Returns:
            特徵列表
        """
        features_list = []
        
        # 獲取練習賽和排位賽數據 - 支援 Sprint Weekend (FP1 替代 FP3)
        practice_sessions = fp_q_data.get('practice_sessions', {})
        fp3_drivers = practice_sessions.get('FP3', {}).get('driver_data', {})
        
        # Sprint Weekend Fallback: 如果沒有 FP3，使用 FP1
        if not fp3_drivers:
            fp3_drivers = practice_sessions.get('FP1', {}).get('driver_data', {})
        
        q_results = fp_q_data.get('qualifying', {}).get('results', {})
        
        # 獲取彎角數據
        corner_drivers = {d['driver']: d for d in corner_data.get('fastest_lap_analysis', {}).get('drivers', [])}

        # 有些 JSON 會把 selected_corners 設為 null 或非 dict，增加防禦性處理
        try:
            raw_selected = corner_data.get('selected_corners', {})
        except Exception:
            raw_selected = {}

        if isinstance(raw_selected, dict):
            selected_corners = raw_selected
        else:
            selected_corners = {}

        # 獲取彎道編號（使用安全取值）
        low_corner_num = (selected_corners.get('low_speed') or {}).get('corner_number')
        mid_corner_num = (selected_corners.get('mid_speed') or {}).get('corner_number')
        high_corner_num = (selected_corners.get('high_speed') or {}).get('corner_number')
        
        for driver in fp3_drivers.keys():
            if driver not in q_results or driver not in corner_drivers:
                continue
            
            fp3_data = fp3_drivers[driver]
            q_data = q_results[driver]
            corner_driver_data = corner_drivers[driver]
            
            # 提取 Q 時間（目標變數）
            q_time_str = str(q_data['best_time'])
            if 'days' in q_time_str:
                time_parts = q_time_str.split(' ')[-1]
                h, m, s = time_parts.split(':')
                actual_q_time = int(h) * 3600 + int(m) * 60 + float(s)
            else:
                continue
            
            # 構建特徵向量（增加健壯型轉換以避免字串 / None 值）
            def _to_float(v):
                try:
                    return float(v)
                except Exception:
                    return np.nan

            features = {
                'year': year,
                'driver': driver,

                # 1. Ideal Lap 特徵
                'ideal_s1': _to_float(fp3_data.get('sector1_best', np.nan)),
                'ideal_s2': _to_float(fp3_data.get('sector2_best', np.nan)),
                'ideal_s3': _to_float(fp3_data.get('sector3_best', np.nan)),
                'ideal_lap': _to_float(fp3_data.get('best_lap_time', np.nan)),

                # 2. 彎角速度特徵
                'low_speed_apex': 0.0,
                'mid_speed_apex': 0.0,
                'high_speed_apex': 0.0,

                # 3. 速度陷阱
                'max_speed': _to_float(fp3_data.get('speed_trap_max', np.nan)),

                # 目標變數
                'actual_q_time': actual_q_time
            }
            
            # 提取彎角速度
            corners_dict = corner_driver_data.get('corners', {})
            corner_speeds_available = []
            
            if low_corner_num:
                corner_key = f"low_speed_corner_{low_corner_num}"
                if corner_key in corners_dict:
                    features['low_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
                    corner_speeds_available.append('low')
            
            if mid_corner_num:
                corner_key = f"mid_speed_corner_{mid_corner_num}"
                if corner_key in corners_dict:
                    features['mid_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
                    corner_speeds_available.append('mid')
            
            if high_corner_num:
                corner_key = f"high_speed_corner_{high_corner_num}"
                if corner_key in corners_dict:
                    features['high_speed_apex'] = corners_dict[corner_key].get('apex_speed', 0.0)
                    corner_speeds_available.append('high')
            
            # 驗證數據完整性
            # 要求基礎遙測數據完整，且至少有一個彎角速度數據
            if all(not np.isnan(features[k]) for k in ['ideal_s1', 'ideal_s2', 'ideal_s3', 'max_speed']):
                # 檢查可用的彎角速度是否都 > 0
                valid_corners = True
                for corner_type in corner_speeds_available:
                    speed_key = f'{corner_type}_speed_apex'
                    if features.get(speed_key, 0.0) <= 0:
                        valid_corners = False
                        break
                
                # 至少需要一個有效的彎角數據
                if valid_corners and len(corner_speeds_available) > 0:
                    features_list.append(features)
        
        return features_list
    
    def train_track_model_v3(self, track_name: str, 
                           start_year: int = 2022, 
                           end_year: int = 2024) -> Dict[str, Any]:
        """
        訓練賽道特定模型（v3.0）
        
        Args:
            track_name: 賽道名稱
            start_year: 訓練起始年份
            end_year: 訓練結束年份
        
        Returns:
            訓練結果
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"[訓練] {track_name} 模型 (v3.0 物理特徵)")
            print(f"{'='*70}")
        
        # 載入數據
        df = self.load_training_data_v3(track_name, start_year, end_year)
        
        if df.empty:
            return {
                'success': False,
                'message': f'{track_name} 沒有可用的訓練數據'
            }
        
        # 準備特徵和目標
        feature_cols = [
            'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
            'low_speed_apex', 'mid_speed_apex', 'high_speed_apex',
            'max_speed'
        ]
        
        X = df[feature_cols]
        y = df['actual_q_time']
        
        # 分割訓練/測試集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 訓練 XGBoost 模型
        model = XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            min_child_weight=3,
            gamma=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # 評估
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_r2 = r2_score(y_test, y_pred_test)
        
        # 儲存模型
        self.track_models[track_name] = model
        
        # 儲存效能指標
        self.track_performance[track_name] = {
            'samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'train_mae': train_mae,
            'test_mae': test_mae,
            'test_r2': test_r2,
            'features': feature_cols,
            'feature_importances': dict(zip(feature_cols, model.feature_importances_))
        }
        
        if self.verbose:
            print(f"\n[結果]")
            print(f"  訓練樣本: {len(X_train)}, 測試樣本: {len(X_test)}")
            print(f"  訓練 MAE: {train_mae:.3f}s")
            print(f"  測試 MAE: {test_mae:.3f}s")
            print(f"  測試 R²: {test_r2:.4f}")
            
            print(f"\n[特徵重要性]")
            importances = sorted(
                self.track_performance[track_name]['feature_importances'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for feat, imp in importances:
                print(f"  {feat}: {imp:.4f}")
        
        return {
            'success': True,
            'track': track_name,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'test_r2': test_r2
        }
    
    def save_model(self, track_name: str):
        """儲存模型"""
        if track_name not in self.track_models:
            print(f"[ERROR] 找不到 {track_name} 的模型")
            return
        
        model_file = self.models_dir / f"{track_name}.pkl"
        
        with open(model_file, 'wb') as f:
            pickle.dump({
                'model': self.track_models[track_name],
                'performance': self.track_performance[track_name],
                'track': track_name,
                'version': 'v3.0',
                'train_date': datetime.now().isoformat()
            }, f)
        
        if self.verbose:
            print(f"\n[儲存] 模型已儲存: {model_file}")


def main():
    """測試訓練器"""
    trainer = TrackSpecificTrainerV3(verbose=True)
    
    # 訓練 Mexico 模型
    result = trainer.train_track_model_v3('Mexico', 2022, 2024)
    
    if result['success']:
        # 儲存模型
        trainer.save_model('Mexico')
        print("\n[完成] 訓練成功！")
    else:
        print(f"\n[失敗] {result.get('message')}")


if __name__ == '__main__':
    main()
