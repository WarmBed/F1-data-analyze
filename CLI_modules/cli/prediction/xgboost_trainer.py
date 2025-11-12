#!/usr/bin/env python3
"""
F1 XGBoost 訓練器 - 功能 72
用於訓練 FP→Q 和 Q→R 預測模型

遵循反幻覺編碼五原則：
1. 禁止幻覺編碼：所有特徵來自已驗證的 JSON 數據
2. 數據來源透明：每個特徵標註 FastF1 來源
3. 性能保守估算：目標 MAE ≤ 0.30s（與 AWS 持平）
4. 處理異常情況：移除濕地會話、處理缺失值
5. 成本保守估算：無 API 成本（純本地訓練）
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 機器學習庫
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder


class XGBoostTrainer:
    """XGBoost 訓練器 - FP→Q 排位賽預測模型"""
    
    def __init__(self, json_dir: str = "json/predictionJSON", verbose: bool = True):
        """
        初始化訓練器（整合 Function 73 賽道分類）
        
        Args:
            json_dir: JSON 數據目錄
            verbose: 是否顯示詳細輸出
        """
        self.json_dir = json_dir
        self.verbose = verbose
        self.label_encoders = {}  # 保存類別編碼器
        
        # 模型輸出目錄
        self.models_dir = Path("models")
        self.reports_dir = Path("reports")
        self.models_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # 🆕 載入賽道分類（Function 73）
        self.track_classification = self._load_track_classification()
        
        if self.verbose:
            print("\n" + "="*70)
            print("🎯 F1 XGBoost 訓練器 - 功能 72 (Enhanced)")
            print("="*70)
            print(f"📂 數據目錄: {json_dir}")
            print(f"💾 模型輸出: {self.models_dir}/")
            print(f"📊 報告輸出: {self.reports_dir}/")
            if self.track_classification:
                print(f"🏁 賽道分類: 已載入 {len(self.track_classification)} 條賽道")
    
    def _load_track_classification(self) -> Dict:
        """載入 Function 73 的賽道分類結果"""
        try:
            classification_file = Path("json/track_classification_FP3.json")
            if not classification_file.exists():
                if self.verbose:
                    print("⚠️  找不到賽道分類檔案，將不使用賽道特徵")
                return {}
            
            with open(classification_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 建立賽道 → cluster_id 映射
            track_mapping = {}
            for cluster_name, cluster_info in data.get('classification', {}).items():
                cluster_id = cluster_info['cluster_id']
                for track_name in cluster_info['tracks']:
                    track_mapping[track_name] = {
                        'cluster_id': cluster_id,
                        'cluster_name': cluster_name,
                        'features': cluster_info.get('center_features', {})
                    }
            
            return track_mapping
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️  載入賽道分類失敗: {e}")
            return {}
    
    def load_training_data(self, start_year: int = 2018, end_year: int = 2024,
                          exclude_wet: bool = True) -> pd.DataFrame:
        """
        載入訓練數據
        
        Args:
            start_year: 起始年份
            end_year: 結束年份
            exclude_wet: 是否排除濕地會話
            
        Returns:
            DataFrame: 訓練數據
        """
        if self.verbose:
            print(f"\n📦 載入訓練數據...")
            print(f"   年份範圍: {start_year}-{end_year}")
            print(f"   排除濕地: {'是' if exclude_wet else '否'}")
        
        all_data = []
        json_files = list(Path(self.json_dir).glob("fp_q_data_*.json"))
        
        if not json_files:
            raise FileNotFoundError(f"找不到 JSON 檔案於: {self.json_dir}")
        
        if self.verbose:
            print(f"   找到 {len(json_files)} 個 JSON 檔案")
        
        loaded_count = 0
        skipped_wet = 0
        skipped_error = 0
        
        for json_file in sorted(json_files):
            try:
                # 解析檔案名稱 (fp_q_data_2024_Japan_20251030_233253.json)
                parts = json_file.stem.split('_')
                if len(parts) < 4:
                    continue
                
                year = int(parts[3])
                
                # 過濾年份
                if year < start_year or year > end_year:
                    continue
                
                # 讀取 JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 檢查是否為濕地會話（FP3 或 Q 下雨）
                if exclude_wet:
                    fp3_rainfall = data.get('practice_sessions', {}).get('FP3', {}).get('weather', {}).get('rainfall', False)
                    q_rainfall = data.get('qualifying', {}).get('weather', {}).get('rainfall', False)
                    
                    if fp3_rainfall or q_rainfall:
                        skipped_wet += 1
                        continue
                
                # 提取特徵
                race_data = self._extract_features_from_json(data, year, json_file.stem)
                if race_data:
                    all_data.extend(race_data)
                    loaded_count += 1
                
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  讀取失敗: {json_file.name} - {str(e)}")
                skipped_error += 1
                continue
        
        if self.verbose:
            print(f"\n✅ 數據載入完成:")
            print(f"   成功載入: {loaded_count} 場賽事")
            print(f"   跳過濕地: {skipped_wet} 場")
            print(f"   讀取錯誤: {skipped_error} 場")
            print(f"   總數據點: {len(all_data)} 筆車手數據")
        
        if not all_data:
            raise ValueError("沒有可用的訓練數據")
        
        df = pd.DataFrame(all_data)
        return df
    
    def _extract_features_from_json(self, data: Dict, year: int, filename: str) -> List[Dict]:
        """
        從 JSON 提取特徵（反幻覺原則：明確標註數據來源）
        
        Args:
            data: JSON 數據
            year: 年份
            filename: 檔案名稱
            
        Returns:
            List[Dict]: 車手特徵列表
        """
        features_list = []
        
        # 提取賽道信息（來源：FastF1 session metadata）
        metadata = data.get('metadata', {})
        race_name = metadata.get('race', 'Unknown')
        
        # 提取排位賽結果（目標變數）
        q_results = data.get('qualifying', {}).get('results', {})
        if not q_results:
            return features_list
        
        # 提取練習賽數據
        practice_sessions = data.get('practice_sessions', {})
        fp1_data = practice_sessions.get('FP1', {}).get('driver_data', {})
        fp2_data = practice_sessions.get('FP2', {}).get('driver_data', {})
        fp3_data = practice_sessions.get('FP3', {}).get('driver_data', {})
        
        # 提取天氣數據（來源：FastF1 weather_data）
        fp3_weather = practice_sessions.get('FP3', {}).get('weather', {})
        q_weather = data.get('qualifying', {}).get('weather', {})
        
        # 遍歷每位車手
        for driver, q_info in q_results.items():
            try:
                # 排位賽結果（目標變數）
                q_position = q_info.get('position')
                q_best_time = q_info.get('best_time')
                
                if q_position is None or q_best_time is None:
                    continue
                
                # 將時間字符串轉為秒數
                q_time_seconds = self._parse_timedelta_to_seconds(q_best_time)
                if q_time_seconds is None:
                    continue
                
                # 提取車隊信息（來源：FastF1 session.results['TeamName']）
                team = q_info.get('team', 'Unknown')
                
                # 提取練習賽特徵
                fp1_features = self._extract_driver_practice_data(fp1_data.get(driver, {}))
                fp2_features = self._extract_driver_practice_data(fp2_data.get(driver, {}))
                fp3_features = self._extract_driver_practice_data(fp3_data.get(driver, {}))
                
                # 計算衍生特徵（特徵工程優化）
                fp1_best = fp1_features.get('best_lap_time')
                fp2_best = fp2_features.get('best_lap_time')
                fp3_best = fp3_features.get('best_lap_time')
                
                # 進步率特徵（車隊調校能力）
                improvement_fp3_fp1 = None
                improvement_fp3_fp2 = None
                if fp1_best and fp3_best and fp1_best > 0:
                    improvement_fp3_fp1 = (fp1_best - fp3_best) / fp1_best * 100  # 百分比改善
                if fp2_best and fp3_best and fp2_best > 0:
                    improvement_fp3_fp2 = (fp2_best - fp3_best) / fp2_best * 100
                
                # 一致性特徵（扇區穩定性）
                fp3_consistency = None
                fp3_avg = fp3_features.get('avg_lap_time')
                fp3_std = fp3_features.get('lap_time_std')
                if fp3_avg and fp3_std and fp3_avg > 0:
                    fp3_consistency = fp3_std / fp3_avg  # 變異係數
                
                # 扇區平衡（賽車調校品質）
                fp3_sector_balance = None
                fp3_s1 = fp3_features.get('sector1_best')
                fp3_s2 = fp3_features.get('sector2_best')
                fp3_s3 = fp3_features.get('sector3_best')
                if fp3_s1 and fp3_s2 and fp3_s3:
                    fp3_sector_balance = max(fp3_s1, fp3_s2, fp3_s3) / min(fp3_s1, fp3_s2, fp3_s3)
                
                # 溫度變化（影響輪胎表現）
                temp_delta_air = None
                temp_delta_track = None
                fp3_air = fp3_weather.get('air_temp_avg')
                q_air = q_weather.get('air_temp_avg')
                fp3_track = fp3_weather.get('track_temp_avg')
                q_track = q_weather.get('track_temp_avg')
                if fp3_air and q_air:
                    temp_delta_air = q_air - fp3_air
                if fp3_track and q_track:
                    temp_delta_track = q_track - fp3_track
                
                # 🆕 階段 1：全圈分析特徵提取（2025-11-01）
                fp1_fastest = fp1_features.get('fastest_lap')
                fp1_all_mean = fp1_features.get('all_laps_mean')
                fp1_all_std = fp1_features.get('all_laps_std')
                
                fp2_fastest = fp2_features.get('fastest_lap')
                fp2_all_mean = fp2_features.get('all_laps_mean')
                fp2_all_std = fp2_features.get('all_laps_std')
                
                fp3_fastest = fp3_features.get('fastest_lap')
                fp3_all_mean = fp3_features.get('all_laps_mean')
                fp3_all_std = fp3_features.get('all_laps_std')
                fp3_race_sim = fp3_features.get('race_sim_avg')
                fp3_degradation = fp3_features.get('race_sim_degradation')
                
                # 🆕 全圈進步趨勢（FP1→FP2→FP3）
                fp1_to_fp2_improvement = None
                fp2_to_fp3_improvement = None
                if fp1_all_mean and fp2_all_mean and fp1_all_mean > 0:
                    fp1_to_fp2_improvement = (fp1_all_mean - fp2_all_mean) / fp1_all_mean * 100
                if fp2_all_mean and fp3_all_mean and fp2_all_mean > 0:
                    fp2_to_fp3_improvement = (fp2_all_mean - fp3_all_mean) / fp2_all_mean * 100
                
                # 構建特徵字典
                features = {
                    # 基礎資訊
                    'year': year,
                    'race': race_name,
                    'driver': driver,
                    'team': team,
                    
                    # FP3 特徵（最重要 - 最接近排位賽）
                    'fp3_best_lap': fp3_best,
                    'fp3_avg_lap': fp3_avg,
                    'fp3_lap_std': fp3_std,
                    'fp3_sector1': fp3_s1,
                    'fp3_sector2': fp3_s2,
                    'fp3_sector3': fp3_s3,
                    'fp3_speed_trap': fp3_features.get('speed_trap_max'),
                    'fp3_valid_laps': fp3_features.get('valid_laps', 0),
                    
                    # FP1/FP2 參考特徵（保留關鍵指標）
                    'fp1_best_lap': fp1_best,
                    'fp2_best_lap': fp2_best,
                    
                    # 🆕 階段 1：全圈分析特徵（2025-11-01）
                    'fp1_fastest_lap': fp1_fastest,
                    'fp1_all_laps_mean': fp1_all_mean,
                    'fp1_all_laps_std': fp1_all_std,
                    
                    'fp2_fastest_lap': fp2_fastest,
                    'fp2_all_laps_mean': fp2_all_mean,
                    'fp2_all_laps_std': fp2_all_std,
                    
                    'fp3_fastest_lap': fp3_fastest,
                    'fp3_all_laps_mean': fp3_all_mean,
                    'fp3_all_laps_std': fp3_all_std,
                    'fp3_race_sim_avg': fp3_race_sim,
                    'fp3_race_sim_degradation': fp3_degradation,
                    
                    # 🆕 全圈進步趨勢
                    'fp1_to_fp2_improvement': fp1_to_fp2_improvement,
                    'fp2_to_fp3_improvement': fp2_to_fp3_improvement,
                    
                    # 🆕 衍生特徵 - 進步率（反映車隊調校能力）
                    'improvement_fp3_fp1': improvement_fp3_fp1,
                    'improvement_fp3_fp2': improvement_fp3_fp2,
                    
                    # 🆕 衍生特徵 - 一致性（反映車手/賽車穩定性）
                    'fp3_consistency': fp3_consistency,
                    'fp3_sector_balance': fp3_sector_balance,
                    
                    # 天氣特徵（來源：FastF1 weather_data）
                    'fp3_air_temp': fp3_air,
                    'fp3_track_temp': fp3_track,
                    'fp3_humidity': fp3_weather.get('humidity_avg'),
                    'q_air_temp': q_air,
                    'q_track_temp': q_track,
                    'q_humidity': q_weather.get('humidity_avg'),
                    
                    # 🆕 衍生特徵 - 溫度變化（影響輪胎抓地力）
                    'temp_delta_air': temp_delta_air,
                    'temp_delta_track': temp_delta_track,
                    
                    # 目標變數
                    'q_position': q_position,
                    'q_time': q_time_seconds,
                }
                
                features_list.append(features)
                
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  提取車手 {driver} 特徵失敗: {e}")
                continue
        
        return features_list
    
    def _extract_driver_practice_data(self, driver_data: Dict) -> Dict:
        """提取練習賽車手數據"""
        if isinstance(driver_data, str):
            # 數據是字符串格式，需要解析
            # 例如: "@{total_laps=18; valid_laps=13; best_lap_time=90.056; ...}"
            # 這是 PowerShell 輸出格式，需要特殊處理
            return self._parse_powershell_dict(driver_data)
        elif isinstance(driver_data, dict):
            return driver_data
        else:
            return {}
    
    def _parse_powershell_dict(self, ps_string: str) -> Dict:
        """解析 PowerShell 字典字符串"""
        try:
            # 移除 @{} 包裹
            if ps_string.startswith('@{') and ps_string.endswith('}'):
                ps_string = ps_string[2:-1]
            
            # 分割鍵值對
            pairs = ps_string.split('; ')
            result = {}
            
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 嘗試轉換為數值
                    try:
                        if value == 'NaN':
                            result[key] = np.nan
                        elif value.startswith('System.Object'):
                            result[key] = []
                        else:
                            result[key] = float(value)
                    except:
                        result[key] = value
            
            return result
        except Exception as e:
            return {}
    
    def _add_track_classification_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加賽道分類特徵 (Function 73 track classification)
        
        將賽道名稱映射至對應的 cluster_id:
        - Cluster 0: 高速街道賽道 (High-speed street circuits)
        - Cluster 1: 標準高速賽道 (Standard high-speed)
        - Cluster 2: 技術型賽道 (Technical circuits)
        
        Args:
            df: 包含 'race' 欄位的 DataFrame
            
        Returns:
            添加 'track_cluster_id' 欄位的 DataFrame
        """
        if not self.track_classification:
            if self.verbose:
                print("⚠️  警告: 賽道分類數據未載入，跳過特徵添加")
            df['track_cluster_id'] = -1  # 預設值
            return df
        
        def map_track_to_cluster(race_name: str) -> int:
            """映射賽道名稱至 cluster_id"""
            if race_name in self.track_classification:
                return self.track_classification[race_name]['cluster_id']
            else:
                # 處理未映射的賽道，使用 Cluster 1 (標準高速) 作為預設
                if self.verbose:
                    print(f"⚠️  未找到賽道分類: {race_name}，使用預設 Cluster 1")
                return 1
        
        # 映射賽道至 cluster_id
        df['track_cluster_id'] = df['race'].apply(map_track_to_cluster)
        
        if self.verbose:
            print("\n✅ 賽道分類特徵已添加:")
            cluster_counts = df['track_cluster_id'].value_counts().sort_index()
            cluster_names = {0: "高速街道", 1: "標準高速", 2: "技術型"}
            for cluster_id, count in cluster_counts.items():
                cluster_name = cluster_names.get(cluster_id, "未知")
                print(f"   Cluster {cluster_id} ({cluster_name}): {count} 筆數據")
        
        return df
    
    def _parse_timedelta_to_seconds(self, time_str: str) -> Optional[float]:
        """將時間字符串轉為秒數"""
        try:
            if pd.isna(time_str) or time_str is None:
                return None
            
            # 格式: "0 days 00:01:28.197000"
            if 'days' in str(time_str):
                td = pd.Timedelta(time_str)
                return td.total_seconds()
            else:
                # 已經是數字
                return float(time_str)
        except:
            return None
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        準備訓練特徵（遵循 AWS 的 One-hot 編碼方法）
        
        Args:
            df: 原始數據
            
        Returns:
            X: 特徵矩陣
            y: 目標變數（排位賽時間）
        """
        if self.verbose:
            print(f"\n🔧 準備訓練特徵...")
            print(f"   原始數據: {len(df)} 筆")
        
        # 複製數據
        df_processed = df.copy()
        
        # 🆕 優化數據清洗 - 移除極端異常值
        initial_len = len(df_processed)
        
        # 移除圈速異常值（使用 IQR 方法）
        for col in ['fp3_best_lap', 'q_time']:
            if col in df_processed.columns:
                Q1 = df_processed[col].quantile(0.25)
                Q3 = df_processed[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR  # 使用 3*IQR 保留更多數據
                upper_bound = Q3 + 3 * IQR
                df_processed = df_processed[
                    (df_processed[col] >= lower_bound) & 
                    (df_processed[col] <= upper_bound)
                ]
        
        # 移除明顯錯誤的數據（圈速 < 60 秒或 > 150 秒）
        for col in ['fp1_best_lap', 'fp2_best_lap', 'fp3_best_lap', 'q_time']:
            if col in df_processed.columns:
                df_processed = df_processed[
                    (df_processed[col] >= 60) & 
                    (df_processed[col] <= 150)
                ]
        
        # 處理缺失值（僅在數字列）
        numeric_cols = df_processed.select_dtypes(include=[np.number]).columns
        df_processed[numeric_cols] = df_processed[numeric_cols].fillna(df_processed[numeric_cols].median())
        
        outliers_removed = initial_len - len(df_processed)
        if self.verbose:
            print(f"   清理後數據: {len(df_processed)} 筆 (移除 {outliers_removed} 筆異常值)")
        
        # 🆕 添加賽道分類特徵（Function 73）
        if self.track_classification:
            df_processed = self._add_track_classification_features(df_processed)
            # 確保 track_cluster_id 是數值類型並填補缺失值
            df_processed['track_cluster_id'] = df_processed['track_cluster_id'].fillna(1).astype(int)
        
        # 選擇特徵
        # 🎯 功能 75：純 FP3 特徵優化（2025-11-02）
        # 根據 feature_importance 分析，移除 FP1/FP2 雜訊（32.91% 權重但相關性低）
        # 保留 15 個核心特徵，特徵減少 61.5%（39 → 15）
        
        feature_cols = [
            # ✅ FP3 核心特徵（最重要 - feature_importance 65.79%）
            'fp3_best_lap',      # 35.36% - 最重要特徵
            'fp3_fastest_lap',   # 30.43% - 第二重要
            'fp3_avg_lap',       # 平均圈速（穩定性）
            'fp3_sector1', 'fp3_sector2', 'fp3_sector3',  # 賽道細節
            'fp3_speed_trap',    # 直線速度
            'fp3_valid_laps',    # 有效圈數（數據可靠度）
            
            # ✅ FP3 衍生特徵（穩定性指標）
            'fp3_consistency',   # 圈速變異係數
            'fp3_sector_balance', # 扇區平衡
            
            # ✅ 天氣變化（FP3→Q，影響輪胎表現）
            'temp_delta_air',    # 氣溫變化
            'temp_delta_track',  # 賽道溫度變化
            
            # ❌ 已移除特徵（FP1/FP2 雜訊，32.91% 權重）：
            # - 'fp1_best_lap', 'fp2_best_lap' (11.20%)
            # - 'fp1_fastest_lap', 'fp2_fastest_lap' (20.61%)
            # - 'fp1_all_laps_mean', 'fp2_all_laps_mean' (0.06%)
            # - 'fp1_all_laps_std', 'fp2_all_laps_std' (0.16%)
            # - 'fp1_to_fp2_improvement', 'fp2_to_fp3_improvement' (0.04%)
            # - 'improvement_fp3_fp1', 'improvement_fp3_fp2' (0.04%)
            
            # ❌ 已移除特徵（無效特徵）：
            # - 'track_cluster_id' (0.0076% - 賽道分類失敗)
            # - 'fp3_race_sim_avg', 'fp3_race_sim_degradation' (0.03%)
            # - 'fp3_air_temp', 'fp3_track_temp', 'fp3_humidity' (0.21%)
            # - 'q_air_temp', 'q_track_temp', 'q_humidity' (0.61%)
            # - 'fp3_lap_std', 'fp3_all_laps_mean', 'fp3_all_laps_std' (0.09%)
        ]
        
        # 類別特徵（One-hot 編碼 - 與 AWS 相同）
        categorical_cols = ['driver', 'team', 'race']
        
        X = df_processed[feature_cols].copy()
        
        # ✅ 確保所有數值特徵統一為 float 類型（避免 int/str 混雜導致編碼錯誤）
        numeric_feature_cols = [col for col in feature_cols if col in X.columns]
        X[numeric_feature_cols] = X[numeric_feature_cols].astype(float)
        
        # 對類別變數進行 One-hot 編碼
        for col in categorical_cols:
            if col in df_processed.columns:
                # 確保數據類型一致（轉為字符串）
                df_processed[col] = df_processed[col].astype(str)
                
                # 使用 LabelEncoder 以便於預測時使用
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df_processed[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df_processed[col])
                else:
                    df_processed[f'{col}_encoded'] = self.label_encoders[col].transform(df_processed[col])
                
                # 添加到特徵中
                X[f'{col}_encoded'] = df_processed[f'{col}_encoded']
        
        # 目標變數
        y = df_processed['q_time']
        
        if self.verbose:
            print(f"   特徵數量: {X.shape[1]}")
            print(f"   數值特徵: {len(feature_cols)}")
            print(f"   類別特徵: {len(categorical_cols)} (已編碼)")
        
        return X, y
    
    def train_model(self, X: pd.DataFrame, y: pd.Series, 
                   param_grid: Optional[Dict] = None) -> Dict:
        """
        訓練 XGBoost 模型（使用時間序列交叉驗證）
        
        Args:
            X: 特徵矩陣
            y: 目標變數
            param_grid: 超參數網格搜索範圍
            
        Returns:
            Dict: 訓練結果
        """
        if self.verbose:
            print(f"\n🤖 訓練 XGBoost 模型...")
            print(f"   訓練樣本: {len(X)}")
        
        # 優化超參數範圍（擴展搜索空間以提高精度）
        if param_grid is None:
            param_grid = {
                'n_estimators': [200, 300, 500],         # 更多樹以捕捉複雜模式
                'max_depth': [6, 8, 10],                # 更深的樹以學習交互作用
                'learning_rate': [0.01, 0.03, 0.05],    # 更細緻的學習率
                'subsample': [0.7, 0.8, 0.9],           # 降低過擬合風險
                'colsample_bytree': [0.7, 0.8, 0.9],    # 特徵採樣多樣性
                'min_child_weight': [1, 3, 5],          # 控制過擬合
                'gamma': [0, 0.1, 0.2],                 # 增加正則化
            }
        
        # 基礎模型
        base_model = XGBRegressor(
            random_state=42,
            objective='reg:squarederror',
            n_jobs=-1,
            verbosity=2 if self.verbose else 0  # 0=silent, 1=warning, 2=info, 3=debug
        )
        
        # 時間序列分割（避免數據洩漏）
        tscv = TimeSeriesSplit(n_splits=5)
        
        if self.verbose:
            print(f"   交叉驗證: TimeSeriesSplit (n_splits=5)")
            print(f"   超參數搜索範圍: {param_grid}")
        
        # 網格搜索
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=tscv,
            scoring='neg_mean_absolute_error',
            n_jobs=-1,
            verbose=1 if self.verbose else 0
        )
        
        # 訓練
        grid_search.fit(X, y)
        
        # 最佳模型
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_score = -grid_search.best_score_  # 轉回正值MAE
        
        if self.verbose:
            print(f"\n✅ 訓練完成!")
            print(f"   最佳 MAE: {best_score:.3f} 秒")
            print(f"   最佳參數: {best_params}")
        
        # 評估模型
        cv_results = self._evaluate_model_cv(best_model, X, y, tscv)
        
        return {
            'model': best_model,
            'best_params': best_params,
            'best_mae': best_score,
            'cv_results': cv_results,
            'feature_importance': dict(zip(X.columns, best_model.feature_importances_))
        }
    
    def _evaluate_model_cv(self, model, X, y, cv) -> Dict:
        """交叉驗證評估模型"""
        mae_scores = []
        rmse_scores = []
        r2_scores = []
        
        for train_idx, val_idx in cv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            
            mae_scores.append(mean_absolute_error(y_val, y_pred))
            rmse_scores.append(np.sqrt(mean_squared_error(y_val, y_pred)))
            r2_scores.append(r2_score(y_val, y_pred))
        
        return {
            'mae_mean': np.mean(mae_scores),
            'mae_std': np.std(mae_scores),
            'rmse_mean': np.mean(rmse_scores),
            'r2_mean': np.mean(r2_scores),
            'fold_maes': mae_scores
        }
    
    def save_model_and_report(self, train_results: Dict, model_name: str = "xgboost_fp_q_baseline") -> Dict:
        """
        保存模型和性能報告
        
        Args:
            train_results: 訓練結果
            model_name: 模型名稱
            
        Returns:
            Dict: 保存結果
        """
        if self.verbose:
            print(f"\n💾 保存模型和報告...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存模型
        model_path = self.models_dir / f"{model_name}_{timestamp}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': train_results['model'],
                'label_encoders': self.label_encoders,
                'feature_names': list(train_results['model'].feature_names_in_),
                'timestamp': timestamp
            }, f)
        
        # 同時保存為最新版本
        latest_path = self.models_dir / f"{model_name}.pkl"
        with open(latest_path, 'wb') as f:
            pickle.dump({
                'model': train_results['model'],
                'label_encoders': self.label_encoders,
                'feature_names': list(train_results['model'].feature_names_in_),
                'timestamp': timestamp
            }, f)
        
        # 生成性能報告
        report = {
            'model_info': {
                'name': model_name,
                'timestamp': timestamp,
                'model_path': str(model_path),
                'type': 'XGBoost Regressor'
            },
            'performance': {
                'cv_mae_mean': train_results['cv_results']['mae_mean'],
                'cv_mae_std': train_results['cv_results']['mae_std'],
                'cv_rmse_mean': train_results['cv_results']['rmse_mean'],
                'cv_r2_mean': train_results['cv_results']['r2_mean'],
                'fold_maes': train_results['cv_results']['fold_maes'],
                'target': 'MAE ≤ 0.30s (AWS baseline: 0.297s)',
                'achieved': train_results['cv_results']['mae_mean'] <= 0.30
            },
            'hyperparameters': train_results['best_params'],
            'feature_importance': train_results['feature_importance']
        }
        
        # 保存報告
        report_path = self.reports_dir / f"baseline_model_performance_{timestamp}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        if self.verbose:
            print(f"   ✅ 模型已保存: {model_path}")
            print(f"   ✅ 最新版本: {latest_path}")
            print(f"   ✅ 報告已保存: {report_path}")
            
            # 顯示性能摘要
            print(f"\n📊 性能摘要:")
            print(f"   交叉驗證 MAE: {report['performance']['cv_mae_mean']:.3f} ± {report['performance']['cv_mae_std']:.3f} 秒")
            print(f"   目標達成: {'✅ 是' if report['performance']['achieved'] else '❌ 否'}")
            print(f"   R² Score: {report['performance']['cv_r2_mean']:.3f}")
        
        return {
            'model_path': str(model_path),
            'report_path': str(report_path),
            'report': report
        }


def run_xgboost_training(start_year: int = 2018, end_year: int = 2023,
                        exclude_wet: bool = True, verbose: bool = True) -> Dict:
    """
    執行 XGBoost 訓練流程
    
    Args:
        start_year: 訓練數據起始年份
        end_year: 訓練數據結束年份
        exclude_wet: 是否排除濕地會話
        verbose: 是否顯示詳細輸出
        
    Returns:
        Dict: 訓練結果
    """
    try:
        # 初始化訓練器
        trainer = XGBoostTrainer(verbose=verbose)
        
        # 載入數據
        df = trainer.load_training_data(start_year, end_year, exclude_wet)
        
        # 準備特徵
        X, y = trainer.prepare_features(df)
        
        # 訓練模型
        train_results = trainer.train_model(X, y)
        
        # 保存模型和報告
        save_results = trainer.save_model_and_report(train_results)
        
        return {
            'success': True,
            'message': 'XGBoost 訓練完成',
            'model_path': save_results['model_path'],
            'report_path': save_results['report_path'],
            'performance': train_results['cv_results'],
            'function_id': '72'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'XGBoost 訓練失敗: {str(e)}',
            'error': str(e),
            'function_id': '72'
        }


if __name__ == '__main__':
    # 測試訓練器
    result = run_xgboost_training(
        start_year=2018,
        end_year=2023,
        exclude_wet=True,
        verbose=True
    )
    
    print("\n" + "="*70)
    if result['success']:
        print("✅ 訓練成功!")
        print(f"模型路徑: {result['model_path']}")
        print(f"報告路徑: {result['report_path']}")
    else:
        print("❌ 訓練失敗!")
        print(f"錯誤: {result['message']}")
    print("="*70)
