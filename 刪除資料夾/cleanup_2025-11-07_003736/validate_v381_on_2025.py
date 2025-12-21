#!/usr/bin/env python3
"""
v3.8.1 模型 2025 賽季驗證腳本
基於 v3.5 架構，添加 v3.8.1 的 2 個歷史特徵
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')


class V381TwentyFiveValidator:
    """v3.8.1 模型 2025 驗證器"""
    
    def __init__(self, models_dir: str = "models/track_specific_v3.8.1"):
        self.models_dir = Path(models_dir)
        self.json_dir = Path("json/predictionJSON")
        self.results = {}
        
        # 2025 賽事映射（與 v3.5 一致）
        self.race_mapping = {
            1: "Australia", 2: "China", 3: "Japan", 4: "Bahrain",
            5: "Saudi Arabia", 6: "Miami", 7: "Emilia Romagna", 8: "Monaco",
            9: "Spain", 10: "Canada", 11: "Austria", 12: "Great Britain",
            13: "Belgium", 14: "Hungary", 15: "Netherlands", 16: "Italy",
            17: "Azerbaijan", 18: "Singapore", 19: "United States", 20: "Mexico",
            21: "Brazil", 22: "Las Vegas", 23: "Qatar", 24: "Abu Dhabi"
        }
        
        # v3.8.1 訓練完成的賽道列表（從訓練結果檢查）
        self.trained_tracks = [
            "Japan", "Bahrain", "Monaco", "Italy", "Mexico",
            "Abu Dhabi", "Great Britain", "Canada", "Singapore", "Netherlands"
        ]
        
        # 載入 2022-2024 訓練數據用於計算歷史特徵
        self.historical_data = self._load_historical_data()
    
    def _load_historical_data(self) -> pd.DataFrame:
        """載入 2022-2024 訓練數據用於計算歷史基準"""
        print("\n[載入歷史數據] 讀取 2022-2024 訓練數據...")
        
        all_data = []
        
        for track in self.trained_tracks:
            for year in [2022, 2023, 2024]:
                # 搜索該賽道的 JSON 檔案（正確格式：fp_q_data_{year}_{track}_{timestamp}.json）
                json_files = list(self.json_dir.glob(f"fp_q_data_{year}_{track}_*.json"))
                
                if not json_files:
                    continue
                
                json_file = json_files[0]
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    q_results = data.get('qualifying', {}).get('results', {})
                    
                    for driver, driver_data in q_results.items():
                        q_time = self.parse_time_to_seconds(driver_data.get('best_time'))
                        
                        if q_time is not None:
                            all_data.append({
                                'year': year,
                                'track': track,
                                'driver': driver,
                                'quali_time': q_time
                            })
                
                except Exception as e:
                    print(f"  [警告] 無法讀取 {json_file.name}: {e}")
                    continue
        
        df = pd.DataFrame(all_data)
        
        if len(df) > 0:
            print(f"  [完成] 載入 {len(df)} 筆歷史排位賽數據")
            print(f"  [範圍] {df['year'].min()}-{df['year'].max()}, {df['track'].nunique()} 賽道, {df['driver'].nunique()} 車手")
        else:
            print(f"  [警告] 無法載入歷史數據，將使用預設值")
        
        return df
    
    def calculate_historical_features(self, driver: str, track: str) -> dict:
        """
        計算歷史特徵（參考 batch_train_all_tracks_v3.8.1.py Lines 149-184）
        
        特徵 18: driver_historical_track_performance (車手在該賽道的歷史平均排位時間)
        
        注意：driver_track_performance_gap 由調用方計算（使用 FP3 時間）
        """
        # 如果沒有歷史數據，使用預設值
        if len(self.historical_data) == 0:
            # 無歷史數據時，使用全局預設值 90 秒（F1 典型排位賽時間）
            return {
                'driver_historical_track_performance': 90.0
            }
        
        # 獲取該車手在該賽道的歷史數據（2022-2024）
        driver_track_history = self.historical_data[
            (self.historical_data['driver'] == driver) &
            (self.historical_data['track'] == track)
        ]
        
        if len(driver_track_history) > 0:
            # 有歷史數據：使用該車手在該賽道的平均時間
            historical_perf = driver_track_history['quali_time'].mean()
        else:
            # 新車手或該賽道無歷史：使用該賽道的整體平均
            track_history = self.historical_data[
                self.historical_data['track'] == track
            ]
            
            if len(track_history) > 0:
                historical_perf = track_history['quali_time'].mean()
            else:
                # 極端情況：該賽道完全無歷史數據，使用全局平均
                historical_perf = self.historical_data['quali_time'].mean()
        
        return {
            'driver_historical_track_performance': historical_perf
        }
    
    def parse_time_to_seconds(self, time_str) -> float:
        """將時間字串轉換為秒數（與 v3.5 一致）"""
        if time_str is None or time_str == '' or time_str == 'N/A':
            return None
        
        try:
            if isinstance(time_str, (int, float)):
                return float(time_str)
            
            time_str = str(time_str).strip()
            
            if 'days' in time_str:
                parts = time_str.split()
                time_part = parts[-1]
                h, m, s = time_part.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s)
            
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:
                    return int(parts[0]) * 60 + float(parts[1])
                elif len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            
            return float(time_str)
        
        except Exception as e:
            return None
    
    def add_v35_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加 v3.5 的交互和速度特徵"""
        df = df.copy()
        
        # ========== v3.3 交互特徵 (3個) ==========
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        # ========== v3.4 速度特徵 (3個) ==========
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        apex_speeds = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']]
        df['speed_consistency'] = apex_speeds.std(axis=1) / (df['max_speed'] + 1e-6)
        
        # ========== v3.5 有效特徵 (3個) ==========
        # 特徵 15: FP3 相對排名
        df['fp3_relative_position'] = df['ideal_lap'].rank(method='min')
        
        # 特徵 16: FP3 與最快的差距
        df['fp3_gap_to_fastest'] = df['ideal_lap'] - df['ideal_lap'].min()
        
        # 特徵 17: 頂尖車手標記
        top_drivers = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']
        df['is_top_driver'] = df['driver'].isin(top_drivers).astype(int)
        
        return df
    
    def add_v381_historical_features(self, df: pd.DataFrame, track_name: str) -> pd.DataFrame:
        """添加 v3.8.1 的 2 個歷史特徵"""
        df = df.copy()
        
        # 為每位車手計算歷史特徵
        historical_features = []
        
        for _, row in df.iterrows():
            driver = row['driver']
            current_fp3_time = row['ideal_lap']  # 使用 FP3 最佳圈速作為代理
            
            hist_feat = self.calculate_historical_features(driver, track_name)
            
            # driver_track_performance_gap: 當前 FP3 時間與歷史平均的差距
            # 在訓練時這是 actual_q_time - historical，但預測時我們用 FP3 時間代替
            hist_feat['driver_track_performance_gap'] = current_fp3_time - hist_feat['driver_historical_track_performance']
            
            historical_features.append(hist_feat)
        
        # 添加到 DataFrame
        hist_df = pd.DataFrame(historical_features)
        df['driver_historical_track_performance'] = hist_df['driver_historical_track_performance'].values
        df['driver_track_performance_gap'] = hist_df['driver_track_performance_gap'].values
        
        return df
    
    def load_cornering_data(self, track_name: str, session: str = 'FP3') -> dict:
        """載入彎角分析數據（與 v3.5 一致）"""
        cornering_file = self.json_dir.parent / f"all_drivers_cornering_analysis_2025_{track_name}_{session}.json"
        
        if not cornering_file.exists():
            return {}
        
        with open(cornering_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取每位車手的彎角速度
        corner_speeds = {}
        
        if 'fastest_lap_analysis' in data:
            drivers_data = data['fastest_lap_analysis'].get('drivers', [])
            
            for driver_info in drivers_data:
                driver = driver_info['driver']
                corners = driver_info.get('corners', {})
                
                # 找出 low/mid/high speed 彎角的 apex_speed
                low_speed = None
                mid_speed = None
                high_speed = None
                
                for corner_name, corner_data in corners.items():
                    if 'low_speed' in corner_name:
                        low_speed = corner_data.get('apex_speed')
                    elif 'mid_speed' in corner_name:
                        mid_speed = corner_data.get('apex_speed')
                    elif 'high_speed' in corner_name:
                        high_speed = corner_data.get('apex_speed')
                
                corner_speeds[driver] = {
                    'low_speed_apex': low_speed,
                    'mid_speed_apex': mid_speed,
                    'high_speed_apex': high_speed
                }
        
        return corner_speeds
    
    def extract_features_from_json(self, json_file: Path, track_name: str) -> pd.DataFrame:
        """從 JSON 提取 19 個特徵（17 基礎 + 2 歷史）"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        practice_sessions = data.get('practice_sessions', {})
        q_results = data.get('qualifying', {}).get('results', {})
        
        # 優先使用 FP3，如果沒有（衝刺賽週末）則使用 FP1
        fp_data = practice_sessions.get('FP3', {}).get('driver_data', {})
        practice_session = 'FP3'
        
        if not fp_data:
            fp_data = practice_sessions.get('FP1', {}).get('driver_data', {})
            practice_session = 'FP1'
            print(f"  [衝刺賽週末] 使用 FP1 代替 FP3")
        
        if not fp_data or not q_results:
            return pd.DataFrame()
        
        # 載入彎角分析數據（衝刺賽週末也有 FP3 彎角分析）
        corner_speeds = self.load_cornering_data(track_name, 'FP3')
        
        features_list = []
        
        for driver, driver_fp_data in fp_data.items():
            if driver not in q_results:
                continue
            
            # 提取練習賽特徵（FP3 或 FP1）
            ideal_s1 = self.parse_time_to_seconds(driver_fp_data.get('sector1_best'))
            ideal_s2 = self.parse_time_to_seconds(driver_fp_data.get('sector2_best'))
            ideal_s3 = self.parse_time_to_seconds(driver_fp_data.get('sector3_best'))
            ideal_lap = self.parse_time_to_seconds(driver_fp_data.get('best_lap_time'))
            
            # 彎角速度（從彎角分析檔案讀取）
            if driver in corner_speeds:
                low_speed_apex = corner_speeds[driver].get('low_speed_apex', 0)
                mid_speed_apex = corner_speeds[driver].get('mid_speed_apex', 0)
                high_speed_apex = corner_speeds[driver].get('high_speed_apex', 0)
            else:
                low_speed_apex = 0
                mid_speed_apex = 0
                high_speed_apex = 0
            
            max_speed = driver_fp_data.get('speed_trap_max', 0)
            
            # 排位賽時間
            q_time = self.parse_time_to_seconds(q_results[driver].get('best_time'))
            
            if any(x is None for x in [ideal_s1, ideal_s2, ideal_s3, ideal_lap, q_time]):
                continue
            
            features_list.append({
                'driver': driver,
                'ideal_s1': ideal_s1,
                'ideal_s2': ideal_s2,
                'ideal_s3': ideal_s3,
                'ideal_lap': ideal_lap,
                'low_speed_apex': low_speed_apex,
                'mid_speed_apex': mid_speed_apex,
                'high_speed_apex': high_speed_apex,
                'max_speed': max_speed,
                'actual_q_time': q_time
            })
        
        if not features_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(features_list)
        
        # 添加 v3.5 的 17 個基礎特徵
        df = self.add_v35_features(df)
        
        # 添加 v3.8.1 的 2 個歷史特徵
        df = self.add_v381_historical_features(df, track_name)
        
        return df
    
    def validate_single_race(self, race_num: int) -> dict:
        """驗證單場比賽"""
        track_name = self.race_mapping.get(race_num)
        if not track_name:
            return None
        
        # 檢查是否有訓練好的模型
        if track_name not in self.trained_tracks:
            return None
        
        print(f"\n{'='*70}")
        print(f"驗證: Race #{race_num} - {track_name}")
        print(f"{'='*70}")
        
        # 檢查模型檔案
        model_file = self.models_dir / f"{track_name}.pkl"
        if not model_file.exists():
            print(f"  [SKIP] 找不到模型檔案")
            return None
        
        # 搜索 2025 JSON 檔案（使用 race_num 而不是 track_name）
        json_files = list(self.json_dir.glob(f"fp_q_data_2025_{race_num}_*.json"))
        
        if not json_files:
            print(f"  [SKIP] 找不到 2025 數據檔案")
            return None
        
        json_file = json_files[0]
        print(f"  [數據] {json_file.name}")
        
        # 提取特徵（19個特徵）
        df = self.extract_features_from_json(json_file, track_name)
        if df.empty:
            print(f"  [SKIP] 無法提取特徵")
            return None
        
        print(f"  [樣本] {len(df)} 位車手")
        
        # 載入模型
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
        
        # v3.8.1 模型包裝在字典中
        if isinstance(model_data, dict):
            model = model_data['model']
        else:
            model = model_data
        
        # 準備特徵矩陣（19個特徵：與訓練時完全一致）
        feature_cols = [
            # v3.0 基礎特徵 (8)
            'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
            'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
            # v3.3 交互特徵 (3)
            's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
            # v3.4 速度特徵 (3)
            'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
            # v3.5 有效特徵 (3)
            'fp3_relative_position', 'fp3_gap_to_fastest', 'is_top_driver',
            # v3.8.1 論文特徵 (2)
            'driver_historical_track_performance', 'driver_track_performance_gap'
        ]
        
        # 檢查所有必要特徵是否存在
        missing_features = [f for f in feature_cols if f not in df.columns]
        if missing_features:
            print(f"  [錯誤] 缺少特徵: {missing_features}")
            return None
        
        X = df[feature_cols]
        y_true = df['actual_q_time']
        
        # 預測
        y_pred = model.predict(X)
        
        # 評估
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        spearman = spearmanr(y_true, y_pred)[0]
        
        print(f"  [結果] MAE: {mae:.3f}s, RMSE: {rmse:.3f}s, R²: {r2:.4f}, Spearman: {spearman:.3f}")
        
        # 排序比較
        df['predicted_time'] = y_pred
        df['error'] = y_pred - y_true
        df['actual_rank'] = df['actual_q_time'].rank()
        df['predicted_rank'] = df['predicted_time'].rank()
        df['rank_diff'] = abs(df['actual_rank'] - df['predicted_rank'])
        
        avg_rank_diff = df['rank_diff'].mean()
        print(f"  [排名] 平均名次誤差: {avg_rank_diff:.2f}")
        
        # Top 3 命中率
        actual_top3 = set(df.nsmallest(3, 'actual_q_time')['driver'])
        predicted_top3 = set(df.nsmallest(3, 'predicted_time')['driver'])
        top3_hits = len(actual_top3 & predicted_top3)
        print(f"  [Top 3] 命中 {top3_hits}/3 位車手")
        
        return {
            'race_num': race_num,
            'track': track_name,
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'spearman': spearman,
            'avg_rank_diff': avg_rank_diff,
            'top3_hit_rate': top3_hits / 3.0,
            'sample_count': len(df),
            'predictions': df[['driver', 'actual_q_time', 'predicted_time', 'error',
                             'actual_rank', 'predicted_rank', 'rank_diff']].to_dict('records')
        }
    
    def validate_all_races(self):
        """驗證所有 2025 賽事"""
        print("\n" + "="*70)
        print("v3.8.1 模型 2025 賽季驗證")
        print("="*70)
        print(f"訓練完成賽道: {len(self.trained_tracks)} 個")
        print(f"賽道列表: {', '.join(self.trained_tracks)}")
        
        valid_count = 0
        
        for race_num in range(1, 25):
            result = self.validate_single_race(race_num)
            if result:
                self.results[race_num] = result
                valid_count += 1
        
        self.generate_summary()
        self.save_results()
        
        print(f"\n[完成] 成功驗證 {valid_count}/{len(self.trained_tracks)} 個訓練完成的賽道")
    
    def generate_summary(self):
        """生成驗證總結"""
        if not self.results:
            print("\n[錯誤] 沒有驗證結果")
            return
        
        print("\n" + "="*70)
        print("v3.8.1 2025 驗證總結")
        print("="*70)
        
        all_mae = [r['mae'] for r in self.results.values()]
        all_rmse = [r['rmse'] for r in self.results.values()]
        all_r2 = [r['r2'] for r in self.results.values()]
        all_spearman = [r['spearman'] for r in self.results.values()]
        all_rank_diff = [r['avg_rank_diff'] for r in self.results.values()]
        all_top3_hit = [r['top3_hit_rate'] for r in self.results.values()]
        
        print(f"\n[整體表現]")
        print(f"  驗證賽事數: {len(self.results)}")
        print(f"  平均 MAE: {np.mean(all_mae):.3f}s (std: {np.std(all_mae):.3f}s)")
        print(f"  平均 RMSE: {np.mean(all_rmse):.3f}s")
        print(f"  平均 R²: {np.mean(all_r2):.4f}")
        print(f"  平均 Spearman: {np.mean(all_spearman):.3f}")
        print(f"  平均名次誤差: {np.mean(all_rank_diff):.2f} 名")
        print(f"  Top 3 命中率: {np.mean(all_top3_hit)*100:.1f}%")
        
        # Top 5 最佳賽道
        print(f"\n[Top 5 最佳預測賽道]")
        sorted_by_mae = sorted(
            self.results.items(),
            key=lambda x: x[1]['mae']
        )[:5]
        
        for i, (race_num, result) in enumerate(sorted_by_mae, 1):
            print(f"  {i}. {result['track']:20s}: MAE {result['mae']:.3f}s, R² {result['r2']:.4f}")
        
        # Top 5 最差賽道
        print(f"\n[Top 5 最差預測賽道]")
        sorted_by_mae_worst = sorted(
            self.results.items(),
            key=lambda x: x[1]['mae'],
            reverse=True
        )[:5]
        
        for i, (race_num, result) in enumerate(sorted_by_mae_worst, 1):
            print(f"  {i}. {result['track']:20s}: MAE {result['mae']:.3f}s, R² {result['r2']:.4f}")
        
        # Great Britain & Canada 分析
        print(f"\n[Great Britain & Canada 表現]")
        for track in ['Great Britain', 'Canada']:
            result = next((r for r in self.results.values() if r['track'] == track), None)
            if result:
                print(f"  {track}:")
                print(f"    MAE: {result['mae']:.3f}s, R²: {result['r2']:.4f}, Spearman: {result['spearman']:.3f}")
                print(f"    平均名次誤差: {result['avg_rank_diff']:.2f} 名")
    
    def save_results(self):
        """保存驗證結果"""
        output_file = Path("v3.8.1_2025_predictions.json")
        
        # 轉換為可序列化格式（與 v3.5 格式一致）
        serializable_results = {}
        for race_num, result in self.results.items():
            # 使用賽道名稱作為 key（與 v3.5 一致）
            track_name = result['track']
            serializable_results[track_name] = {
                'race_num': result['race_num'],
                'track': result['track'],
                'mae': float(result['mae']),
                'rmse': float(result['rmse']),
                'r2': float(result['r2']),
                'spearman': float(result['spearman']),
                'avg_rank_diff': float(result['avg_rank_diff']),
                'top3_hit_rate': float(result['top3_hit_rate']),
                'sample_count': result['sample_count'],
                'predictions': result['predictions']
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[保存結果] {output_file}")
        
        # 同時保存詳細版本（包含 race_num 作為 key）
        detailed_output = Path("v3.8.1_2025_validation_results.json")
        detailed_results = {}
        for race_num, result in self.results.items():
            detailed_results[str(race_num)] = {
                'race_num': result['race_num'],
                'track': result['track'],
                'mae': float(result['mae']),
                'rmse': float(result['rmse']),
                'r2': float(result['r2']),
                'spearman': float(result['spearman']),
                'avg_rank_diff': float(result['avg_rank_diff']),
                'top3_hit_rate': float(result['top3_hit_rate']),
                'sample_count': result['sample_count'],
                'predictions': result['predictions']
            }
        
        with open(detailed_output, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
        print(f"[保存結果] {detailed_output} (詳細版)")


def main():
    validator = V381TwentyFiveValidator()
    validator.validate_all_races()


if __name__ == '__main__':
    main()
