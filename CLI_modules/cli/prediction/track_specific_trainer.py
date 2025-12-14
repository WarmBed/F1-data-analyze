#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 賽道特定模型訓練器 - Function 77
為每個賽道訓練獨立的排位時間預測模型

設計原則：
1. 每個賽道訓練獨立的 XGBoost 模型
2. 保留所有現有特徵 + 新增賽道歷史特徵
3. 支援低樣本賽道（最低 20 樣本 = 1 年數據）
4. 單一檔案儲存（每賽道獨立 .pkl）
5. 即時更新機制（每場賽事後可重新訓練）

遵循反幻覺編碼五原則：
- 原則 0：禁止幻覺編碼，所有方法調用前先驗證
- 原則 1：複用 xgboost_trainer.py 的數據載入邏輯
- 原則 2：使用 UniversalDataLoader 架構模式
- 原則 3：所有字串使用 tr()（未來）
- 原則 4：print 輸出會導向 logger
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


class TrackSpecificTrainer:
    """賽道特定模型訓練器 - 為每個賽道訓練獨立模型"""
    
    # 原型驗證賽道（10 個主要賽道）
    PROTOTYPE_TRACKS = [
        'Bahrain', 'Monaco', 'Spain', 'Silverstone', 'Singapore',
        'Mexico', 'USA', 'Brazil', 'Japan', 'Abu Dhabi'
    ]
    
    def __init__(self, json_dir: str = "json/predictionJSON", verbose: bool = True):
        """
        初始化賽道特定訓練器
        
        Args:
            json_dir: JSON 數據目錄
            verbose: 是否顯示詳細輸出
        """
        self.json_dir = Path(json_dir)
        self.verbose = verbose
        self.label_encoders = {}  # 類別編碼器
        
        # 模型輸出目錄
        self.models_dir = Path("models/track_specific")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 數據存儲
        self.track_data = {}  # {track_name: DataFrame}
        self.track_models = {}  # {track_name: model}
        self.track_performance = {}  # {track_name: metrics}
        
        # 賽道歷史統計
        self.track_history = defaultdict(lambda: defaultdict(list))
        
        # Function 78 車手特徵（FP3→Q 歷史關係）
        self.driver_fp3_q_features = {}  # {track_name: {driver: features}}
        
        if self.verbose:
            print("\n" + "="*70)
            print("F1 賽道特定模型訓練器 - Function 77 (v2.0 + Function 78)")
            print("="*70)
            print(f"數據目錄: {self.json_dir}")
            print(f"模型輸出: {self.models_dir}/")
            print(f"原型賽道: {len(self.PROTOTYPE_TRACKS)} 個")
    
    def load_training_data(self, start_year: int = 2018, end_year: int = 2024,
                          exclude_wet: bool = True) -> Dict[str, pd.DataFrame]:
        """
        載入訓練數據並按賽道分組
        
        Args:
            start_year: 起始年份
            end_year: 結束年份
            exclude_wet: 是否排除濕地會話
        
        Returns:
            Dict[track_name, DataFrame]: 每個賽道的訓練數據
        """
        if self.verbose:
            print(f"\n[載入數據] 年份範圍: {start_year}-{end_year}")
        
        all_data = []
        file_count = 0
        error_count = 0
        
        # 掃描所有 JSON 檔案
        for year in range(start_year, end_year + 1):
            pattern = f"fp_q_data_{year}_*.json"
            json_files = list(self.json_dir.glob(pattern))
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 新格式 JSON 結構:
                    # {
                    #   "metadata": {year, race, ...},
                    #   "practice_sessions": {FP1, FP2, FP3},
                    #   "qualifying": {session_info, weather, results},
                    #   "drivers": [list of driver codes]
                    # }
                    
                    metadata = data.get('metadata', {})
                    practice_sessions = data.get('practice_sessions', {})
                    qualifying = data.get('qualifying', {})
                    
                    # 檢查必要數據
                    if not practice_sessions.get('FP3') or not qualifying.get('results'):
                        error_count += 1
                        continue
                    
                    # 提取賽道名稱
                    track_name = metadata.get('race', 'Unknown')
                    if track_name == 'Unknown':
                        error_count += 1
                        continue
                    
                    # 提取 FP3 和排位賽數據
                    fp3_data = practice_sessions['FP3'].get('driver_data', {})
                    q_results = qualifying['results']
                    
                    # 提取每位車手的數據
                    for driver_code in q_results.keys():
                        if driver_code not in fp3_data:
                            continue  # 沒有 FP3 數據，跳過
                        
                        row = self._extract_features(
                            fp3_driver_data=fp3_data[driver_code],
                            q_driver_data=q_results[driver_code],
                            metadata=metadata,
                            driver_code=driver_code
                        )
                        if row is not None:
                            all_data.append(row)
                    
                    file_count += 1
                    
                except Exception as e:
                    if self.verbose:
                        print(f"[錯誤] 載入 {json_file.name} 失敗: {e}")
                    error_count += 1
                    continue
        
        if self.verbose:
            print(f"[完成] 載入 {file_count} 個檔案，共 {len(all_data)} 筆數據（{error_count} 個錯誤）")
        
        # 轉換為 DataFrame
        df = pd.DataFrame(all_data)
        
        if len(df) == 0:
            print("[警告] 沒有載入任何數據！")
            return {}
        
        # 按賽道分組
        track_groups = df.groupby('race')
        
        for track_name, track_df in track_groups:
            self.track_data[track_name] = track_df.reset_index(drop=True)
            
            if self.verbose:
                print(f"  - {track_name}: {len(track_df)} 樣本")
        
        # 計算賽道歷史統計
        self._calculate_track_history(df)
        
        return self.track_data
    
    def _extract_features(self, fp3_driver_data: Dict, q_driver_data: Dict,
                         metadata: Dict, driver_code: str) -> Optional[Dict]:
        """
        提取特徵（適配新 JSON 格式）
        
        Args:
            fp3_driver_data: FP3 車手數據
            q_driver_data: 排位賽車手數據
            metadata: 元數據
            driver_code: 車手代碼
        
        Returns:
            特徵字典或 None
        """
        try:
            # 目標變數：排位賽最佳時間
            q_time_str = q_driver_data.get('best_time')
            if not q_time_str:
                return None
            
            # 解析時間字串（格式："0 days 00:01:15.123000"）
            if isinstance(q_time_str, str) and 'days' in q_time_str:
                time_parts = q_time_str.split()[-1]  # "00:01:15.123000"
                h, m, s = time_parts.split(':')
                q_time = float(h) * 3600 + float(m) * 60 + float(s)
            else:
                q_time = float(q_time_str)
            
            # 基礎驗證
            if q_time < 50 or q_time > 150:  # 排位時間應在 50-150 秒範圍
                return None
            
            # === 提取 FP3 特徵（新格式）===
            # 新格式範例:
            # {
            #   "best_lap_time": 91.062,
            #   "avg_lap_time": 114.326,
            #   "lap_time_std": 19.078,
            #   "sector1_best": 29.054,
            #   "sector2_best": 39.019,
            #   "sector3_best": 22.857,
            #   "speed_trap_max": 316.0,
            #   "total_laps": 16,
            #   ...
            # }
            
            features = {
                # 目標變數
                'q_time': q_time,
                
                # 元數據
                'year': metadata.get('year', 0),
                'race': metadata.get('race', 'Unknown'),
                'driver': driver_code,
                
                # FP3 基礎特徵
                'fp3_best': fp3_driver_data.get('best_lap_time', 0.0),
                'fp3_mean': fp3_driver_data.get('avg_lap_time', 0.0),
                'fp3_std': fp3_driver_data.get('lap_time_std', 0.0),
                'fp3_laps': fp3_driver_data.get('valid_laps', 0),
                
                # FP3 分段時間
                'fp3_sector1': fp3_driver_data.get('sector1_best', 0.0),
                'fp3_sector2': fp3_driver_data.get('sector2_best', 0.0),
                'fp3_sector3': fp3_driver_data.get('sector3_best', 0.0),
                
                # FP3 速度陷阱（新格式只有一個 speed_trap_max）
                'fp3_speed_st': fp3_driver_data.get('speed_trap_max', 0.0),
                'fp3_speed_i1': 0.0,  # 新格式沒有這些細分
                'fp3_speed_i2': 0.0,
                'fp3_speed_fl': 0.0,
                
                # 賽道特徵（從 metadata 提取，若無則設為 0）
                'track_length': metadata.get('track_length', 0.0),
                'turns_count': metadata.get('turns_count', 0),
                'track_cluster': metadata.get('track_cluster', 0),
                
                # 天氣特徵（新格式可能沒有，暫時設為 0）
                'air_temp': metadata.get('air_temp', 0.0),
                'track_temp': metadata.get('track_temp', 0.0),
                'humidity': metadata.get('humidity', 0.0),
                'pressure': metadata.get('pressure', 0.0),
                'wind_speed': metadata.get('wind_speed', 0.0),
            }
            
            # 基礎驗證：FP3 最佳時間應該合理
            if features['fp3_best'] < 50 or features['fp3_best'] > 200:
                return None
            
            return features
            
        except Exception as e:
            if self.verbose:
                print(f"[特徵提取錯誤] {driver_code}: {e}")
            return None
    
    def _parse_time(self, time_value: Any) -> float:
        """解析時間值"""
        if time_value is None or time_value == 'NO TIME':
            return 0.0
        
        if isinstance(time_value, (int, float)):
            return float(time_value)
        
        if isinstance(time_value, str):
            if 'days' in time_value:
                time_parts = time_value.split()[-1]
                h, m, s = time_parts.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
            try:
                return float(time_value)
            except:
                return 0.0
        
        return 0.0
    
    def _calculate_track_history(self, df: pd.DataFrame):
        """
        計算賽道歷史統計（用於新增特徵）
        
        為每個賽道的每位車手計算：
        - 歷史平均排位時間
        - 歷史最佳排位時間
        - 出賽次數
        """
        if self.verbose:
            print("\n[計算賽道歷史統計]")
        
        for track_name in df['race'].unique():
            track_df = df[df['race'] == track_name]
            
            for driver in track_df['driver'].unique():
                driver_track_df = track_df[track_df['driver'] == driver]
                q_times = driver_track_df['q_time'].tolist()
                
                self.track_history[track_name][driver] = {
                    'avg_q_time': np.mean(q_times),
                    'best_q_time': np.min(q_times),
                    'appearances': len(q_times)
                }
        
        if self.verbose:
            total_stats = sum(len(drivers) for drivers in self.track_history.values())
            print(f"  已計算 {len(self.track_history)} 個賽道，共 {total_stats} 筆車手統計")
    
    def load_driver_fp3_q_features(self, track_name: str):
        """
        載入 Function 78 生成的車手 FP3→Q 特徵
        
        Args:
            track_name: 賽道名稱
        """
        feature_file = Path("json") / f"driver_fp3_q_features_{track_name}.json"
        
        if not feature_file.exists():
            if self.verbose:
                print(f"  [提示] 找不到 Function 78 特徵檔案: {feature_file.name}")
                print(f"  [提示] 執行 'python scripts/extract_driver_fp3_q_features.py' 生成特徵")
            return False
        
        try:
            with open(feature_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('success') and data.get('function_id') == "78":
                self.driver_fp3_q_features[track_name] = data.get('features', {})
                if self.verbose:
                    driver_count = len(self.driver_fp3_q_features[track_name])
                    print(f"  [Function 78] 載入 {driver_count} 名車手的 FP3→Q 特徵")
                return True
        except Exception as e:
            if self.verbose:
                print(f"  [錯誤] 載入 Function 78 特徵失敗: {e}")
        
        return False
    
    def add_track_history_features(self, df: pd.DataFrame, track_name: str) -> pd.DataFrame:
        """
        為數據集新增賽道歷史特徵（v2.0 - 包含 Function 78 特徵）
        
        Args:
            df: 原始數據
            track_name: 賽道名稱
        
        Returns:
            新增特徵後的數據
        """
        df = df.copy()
        
        # === 原有特徵（v1.0）===
        # 初始化新特徵欄位
        df['driver_avg_q_time_this_track'] = 0.0
        df['driver_best_q_time_this_track'] = 0.0
        df['driver_appearances_this_track'] = 0
        
        # 填入歷史數據
        for idx, row in df.iterrows():
            driver = row['driver']
            history = self.track_history.get(track_name, {}).get(driver, {})
            
            df.at[idx, 'driver_avg_q_time_this_track'] = history.get('avg_q_time', 0.0)
            df.at[idx, 'driver_best_q_time_this_track'] = history.get('best_q_time', 0.0)
            df.at[idx, 'driver_appearances_this_track'] = history.get('appearances', 0)
        
        # === Function 78 特徵（v2.0）===
        # 嘗試載入 FP3→Q 特徵
        if track_name not in self.driver_fp3_q_features:
            self.load_driver_fp3_q_features(track_name)
        
        # 如果成功載入 Function 78 特徵，則添加到數據中
        if track_name in self.driver_fp3_q_features:
            fp3_q_features = self.driver_fp3_q_features[track_name]
            
            # 初始化 4 個新特徵欄位
            df['driver_avg_fp3_to_q_delta'] = 0.0
            df['driver_fp3_to_q_std'] = 0.0
            df['driver_track_appearances_f78'] = 0
            df['driver_best_delta'] = 0.0
            
            # 填入 Function 78 特徵
            for idx, row in df.iterrows():
                driver = row['driver']
                if driver in fp3_q_features:
                    features = fp3_q_features[driver]
                    df.at[idx, 'driver_avg_fp3_to_q_delta'] = features.get('driver_avg_fp3_to_q_delta', 0.0)
                    df.at[idx, 'driver_fp3_to_q_std'] = features.get('driver_fp3_to_q_std', 0.0)
                    df.at[idx, 'driver_track_appearances_f78'] = features.get('driver_track_appearances', 0)
                    df.at[idx, 'driver_best_delta'] = features.get('driver_best_delta', 0.0)
        
        return df
    
    def train_track_model(self, track_name: str, 
                         test_size: float = 0.2,
                         random_state: int = 42) -> Dict:
        """
        訓練單一賽道的模型
        
        Args:
            track_name: 賽道名稱
            test_size: 測試集比例
            random_state: 隨機種子
        
        Returns:
            訓練結果字典
        """
        if track_name not in self.track_data:
            return {'success': False, 'message': f'找不到賽道數據: {track_name}'}
        
        df = self.track_data[track_name].copy()
        
        if self.verbose:
            print(f"\n[訓練模型] {track_name} ({len(df)} 樣本)")
        
        # 檢查最低樣本需求
        if len(df) < 20:
            msg = f"樣本不足: {len(df)} < 20（最低需求 1 年數據）"
            if self.verbose:
                print(f"  [跳過] {msg}")
            return {'success': False, 'message': msg}
        
        # 新增賽道歷史特徵
        df = self.add_track_history_features(df, track_name)
        
        # 準備特徵和目標
        feature_cols = [col for col in df.columns if col not in 
                       ['q_time', 'year', 'race', 'driver']]
        
        X = df[feature_cols]
        y = df['q_time']
        
        # 處理類別特徵（如果有）
        # 注意：在單一賽道內，race 是常數，已移除
        
        # 分割訓練/測試集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # 訓練 XGBoost 模型（優化超參數以減少過擬合）
        model = XGBRegressor(
            n_estimators=50,      # 減少樹數量 (200→50)
            max_depth=3,          # 降低樹深度 (6→3)
            learning_rate=0.1,    # 提高學習率 (0.05→0.1)
            min_child_weight=3,   # 增加正則化（新增）
            gamma=0.1,            # 增加剪枝（新增）
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
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
            'features': feature_cols
        }
        
        if self.verbose:
            print(f"  訓練樣本: {len(X_train)}, 測試樣本: {len(X_test)}")
            print(f"  訓練 MAE: {train_mae:.3f}s")
            print(f"  測試 MAE: {test_mae:.3f}s")
            print(f"  測試 R2: {test_r2:.4f}")
        
        return {
            'success': True,
            'track': track_name,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'test_r2': test_r2
        }
    
    def train_prototype_tracks(self) -> Dict:
        """
        訓練 10 個原型賽道
        
        Returns:
            訓練結果摘要
        """
        if self.verbose:
            print("\n" + "="*70)
            print("開始訓練原型賽道（10 個主要賽道）")
            print("="*70)
        
        results = {
            'successful': [],
            'failed': [],
            'overall_mae': [],
            'overall_r2': []
        }
        
        for track_name in self.PROTOTYPE_TRACKS:
            result = self.train_track_model(track_name)
            
            if result['success']:
                results['successful'].append(track_name)
                results['overall_mae'].append(result['test_mae'])
                results['overall_r2'].append(result['test_r2'])
            else:
                results['failed'].append({
                    'track': track_name,
                    'reason': result.get('message', 'Unknown')
                })
        
        # 計算總體統計
        if results['overall_mae']:
            results['mean_mae'] = np.mean(results['overall_mae'])
            results['median_mae'] = np.median(results['overall_mae'])
            results['mean_r2'] = np.mean(results['overall_r2'])
        
        if self.verbose:
            print("\n" + "="*70)
            print("原型訓練結果摘要")
            print("="*70)
            print(f"成功: {len(results['successful'])}/{len(self.PROTOTYPE_TRACKS)} 個賽道")
            if results['overall_mae']:
                print(f"平均 MAE: {results['mean_mae']:.3f}s")
                print(f"中位數 MAE: {results['median_mae']:.3f}s")
                print(f"平均 R2: {results['mean_r2']:.4f}")
            
            if results['failed']:
                print(f"\n失敗 {len(results['failed'])} 個賽道:")
                for failed in results['failed']:
                    print(f"  - {failed['track']}: {failed['reason']}")
        
        return results
    
    def save_models(self, prefix: str = "prototype"):
        """
        儲存所有訓練好的模型
        
        Args:
            prefix: 檔案名稱前綴
        """
        if self.verbose:
            print(f"\n[儲存模型] 共 {len(self.track_models)} 個模型")
        
        for track_name, model in self.track_models.items():
            # 清理賽道名稱（移除特殊字元）
            safe_track_name = track_name.replace(' ', '_').replace('/', '_')
            
            model_file = self.models_dir / f"{safe_track_name}.pkl"
            
            with open(model_file, 'wb') as f:
                pickle.dump({
                    'model': model,
                    'track_name': track_name,
                    'performance': self.track_performance.get(track_name, {}),
                    'train_date': datetime.now().isoformat()
                }, f)
            
            if self.verbose:
                print(f"  已儲存: {model_file.name}")
        
        # 儲存訓練摘要
        summary_file = self.models_dir / f"{prefix}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'train_date': datetime.now().isoformat(),
                'tracks': list(self.track_models.keys()),
                'performance': self.track_performance
            }, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"  已儲存訓練摘要: {summary_file.name}")
    
    def load_model(self, track_name: str) -> Optional[XGBRegressor]:
        """
        載入指定賽道的模型
        
        Args:
            track_name: 賽道名稱
        
        Returns:
            模型或 None
        """
        safe_track_name = track_name.replace(' ', '_').replace('/', '_')
        model_file = self.models_dir / f"{safe_track_name}.pkl"
        
        if not model_file.exists():
            if self.verbose:
                print(f"[警告] 找不到模型檔案: {model_file}")
            return None
        
        try:
            with open(model_file, 'rb') as f:
                data = pickle.load(f)
            return data['model']
        except Exception as e:
            if self.verbose:
                print(f"[錯誤] 載入模型失敗: {e}")
            return None
    
    def predict(self, track_name: str, features: pd.DataFrame) -> Optional[np.ndarray]:
        """
        使用賽道特定模型進行預測
        
        Args:
            track_name: 賽道名稱
            features: 特徵數據
        
        Returns:
            預測結果或 None
        """
        # 從記憶體載入模型
        if track_name in self.track_models:
            model = self.track_models[track_name]
        else:
            # 從檔案載入模型
            model = self.load_model(track_name)
            if model is None:
                return None
        
        return model.predict(features)
    
    def predict_2025_qualifying(self, track_name: str, year: int = 2025) -> Dict[str, Any]:
        """
        預測 2025 年排位賽結果
        
        Args:
            track_name: 賽道名稱
            year: 預測年份（默認 2025）
        
        Returns:
            包含預測結果和實際結果的對比
        """
        from scipy.stats import spearmanr
        
        if self.verbose:
            print(f"\n[預測模式] {year} {track_name} 排位賽")
        
        # 載入模型
        model = self.load_model(track_name)
        if model is None:
            return {
                'success': False,
                'message': f'找不到 {track_name} 的訓練模型'
            }
        
        # 載入 2025 FP3 數據
        # 注意：2025 檔案使用賽事編號（例如 _20_ 表示 Mexico）
        import glob
        
        # Mexico 是第 20 場賽事
        race_number = 20  # TODO: 根據賽道名稱動態獲取
        files = glob.glob(str(self.json_dir / f"fp_q_data_{year}_{race_number}_*.json"))
        
        if not files:
            return {
                'success': False,
                'message': f'找不到 {year} 年 {track_name} (賽事 {race_number}) 的數據檔案'
            }
        
        # 讀取最新的 2025 數據
        latest_file = sorted(files)[-1]
        if self.verbose:
            print(f"  載入數據: {Path(latest_file).name}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data_2025 = json.load(f)
        
        # 提取 FP3 和排位賽數據
        fp3_data = data_2025.get('practice_sessions', {}).get('FP3', {}).get('driver_data', {})
        q_results = data_2025.get('qualifying', {}).get('results', {})
        
        if not fp3_data or not q_results:
            return {
                'success': False,
                'message': 'FP3 或排位賽數據不完整'
            }
        
        # 載入 Function 78 特徵
        self.load_driver_fp3_q_features(track_name)
        
        # 準備預測特徵
        prediction_data = []
        for driver in fp3_data.keys():
            if driver not in q_results:
                continue
            
            driver_fp3 = fp3_data[driver]
            
            # 基礎特徵
            row = {
                'driver': driver,
                'fp3_best': driver_fp3.get('best_lap_time', np.nan),
                'fp3_mean': driver_fp3.get('avg_lap_time', np.nan),
                'fp3_std': driver_fp3.get('lap_time_std', np.nan),
                'fp3_laps': driver_fp3.get('valid_laps', 0),
                'fp3_sector1': driver_fp3.get('sector1_best', np.nan),
                'fp3_sector2': driver_fp3.get('sector2_best', np.nan),
                'fp3_sector3': driver_fp3.get('sector3_best', np.nan),
                'fp3_speed_st': driver_fp3.get('speed_trap_max', np.nan),
                'fp3_speed_i1': driver_fp3.get('speed_trap_max', np.nan),  # 簡化
                'fp3_speed_i2': driver_fp3.get('speed_trap_max', np.nan),
                'fp3_speed_fl': driver_fp3.get('speed_trap_max', np.nan),
            }
            
            # 賽道特徵（使用固定值）
            row.update({
                'track_length': 4.304,  # Mexico 賽道長度
                'turns_count': 17,
                'track_cluster': 1,  # 高海拔賽道
            })
            
            # 天氣特徵
            weather = data_2025.get('practice_sessions', {}).get('FP3', {}).get('weather', {})
            row.update({
                'air_temp': weather.get('air_temp_avg', 25.0),
                'track_temp': weather.get('track_temp_avg', 40.0),
                'humidity': weather.get('humidity_avg', 30.0),
                'pressure': 1015.0,  # 默認值
                'wind_speed': 5.0,
            })
            
            # 車手歷史特徵（使用默認值）
            row.update({
                'driver_avg_q_time_this_track': 77.0,
                'driver_best_q_time_this_track': 76.0,
                'driver_appearances_this_track': 5,
            })
            
            # Function 78 特徵
            if driver in self.driver_fp3_q_features.get(track_name, {}):
                f78_features = self.driver_fp3_q_features[track_name][driver]
                row.update({
                    'driver_avg_fp3_to_q_delta': f78_features.get('driver_avg_fp3_to_q_delta', 0.0),
                    'driver_fp3_to_q_std': f78_features.get('driver_fp3_to_q_std', 0.5),
                    'driver_track_appearances_f78': f78_features.get('driver_track_appearances', 5),
                    'driver_best_delta': f78_features.get('driver_best_delta', 0.0),
                })
            else:
                row.update({
                    'driver_avg_fp3_to_q_delta': 0.0,
                    'driver_fp3_to_q_std': 0.5,
                    'driver_track_appearances_f78': 0,
                    'driver_best_delta': 0.0,
                })
            
            # 實際排位賽時間
            q_time_str = str(q_results[driver]['best_time'])
            if 'days' in q_time_str:
                time_parts = q_time_str.split(' ')[-1]
                h, m, s = time_parts.split(':')
                actual_q_time = int(h) * 3600 + int(m) * 60 + float(s)
            else:
                actual_q_time = np.nan
            
            row['actual_q_time'] = actual_q_time
            row['actual_position'] = q_results[driver]['position']
            
            prediction_data.append(row)
        
        df_pred = pd.DataFrame(prediction_data)
        
        # 執行預測
        feature_cols = [col for col in df_pred.columns if col not in 
                       ['driver', 'actual_q_time', 'actual_position']]
        X_pred = df_pred[feature_cols]
        
        predictions = model.predict(X_pred)
        df_pred['predicted_q_time'] = predictions
        
        # 計算評估指標
        actual_times = df_pred['actual_q_time'].values
        pred_times = df_pred['predicted_q_time'].values
        
        mae = mean_absolute_error(actual_times, pred_times)
        r2 = r2_score(actual_times, pred_times)
        
        # 計算 Spearman 相關（名次預測準確度）
        df_pred['predicted_position'] = df_pred['predicted_q_time'].rank()
        spearman_corr, _ = spearmanr(df_pred['actual_position'], df_pred['predicted_position'])
        
        # 排序並顯示結果
        df_pred = df_pred.sort_values('predicted_position')
        
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"預測結果 vs 實際結果")
            print(f"{'='*70}")
            print(f"{'名次':<4} {'車手':<6} {'預測時間':<10} {'實際時間':<10} {'實際名次':<6} {'誤差':<8}")
            print(f"{'-'*70}")
            
            for idx, row in df_pred.iterrows():
                pred_pos = int(row['predicted_position'])
                actual_pos = int(row['actual_position'])
                error = row['predicted_q_time'] - row['actual_q_time']
                
                print(f"{pred_pos:<4} {row['driver']:<6} {row['predicted_q_time']:>8.3f}s  "
                      f"{row['actual_q_time']:>8.3f}s  {actual_pos:<6} {error:>+7.3f}s")
            
            print(f"\n{'='*70}")
            print(f"評估指標:")
            print(f"  MAE (時間誤差): {mae:.4f}s")
            print(f"  R² Score: {r2:.4f}")
            print(f"  Spearman (名次相關): {spearman_corr:.4f}")
            print(f"{'='*70}")
        
        return {
            'success': True,
            'track': track_name,
            'year': year,
            'mae': mae,
            'r2': r2,
            'spearman': spearman_corr,
            'predictions': df_pred[['driver', 'predicted_q_time', 'actual_q_time', 
                                   'predicted_position', 'actual_position']].to_dict('records')
        }


def main():
    """主程式 - 訓練原型賽道模型"""
    trainer = TrackSpecificTrainer(verbose=True)
    
    # 載入訓練數據
    track_data = trainer.load_training_data(
        start_year=2018,
        end_year=2024,
        exclude_wet=True
    )
    
    print(f"\n載入完成，共 {len(track_data)} 個賽道")
    
    # 訓練原型賽道
    results = trainer.train_prototype_tracks()
    
    # 儲存模型
    trainer.save_models(prefix="prototype")
    
    print("\n訓練完成！")
    return results


if __name__ == "__main__":
    main()
