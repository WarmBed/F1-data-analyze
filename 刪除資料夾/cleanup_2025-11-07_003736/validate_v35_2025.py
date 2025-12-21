#!/usr/bin/env python3
"""
v3.5 模型 2025 賽季驗證腳本
基於 validate_v34_2025.py 架構，添加 v3.5 的 6 個改進率特徵
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')


class V35TwentyFiveValidator:
    """v3.5 模型 2025 驗證器"""
    
    def __init__(self, models_dir: str = "models/track_specific_v3.5"):
        self.models_dir = Path(models_dir)
        self.json_dir = Path("json/predictionJSON")
        self.results = {}
        
        # 2025 賽事映射
        self.race_mapping = {
            1: "Australia", 2: "China", 3: "Japan", 4: "Bahrain",
            5: "Saudi Arabia", 6: "Miami", 7: "Emilia Romagna", 8: "Monaco",
            9: "Spain", 10: "Canada", 11: "Austria", 12: "Great Britain",
            13: "Belgium", 14: "Hungary", 15: "Netherlands", 16: "Italy",
            17: "Azerbaijan", 18: "Singapore", 19: "United States", 20: "Mexico",
            21: "Brazil", 22: "Las Vegas", 23: "Qatar", 24: "Abu Dhabi"
        }
        
        # 賽道改進率（從訓練結果）
        self.track_improvement_rates = self._get_improvement_rates()
        
        # 頂尖車手列表
        self.top_drivers = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']
    
    def _get_improvement_rates(self) -> dict:
        """賽道改進率字典"""
        return {
            'Japan': 0.0136, 'Bahrain': 0.0189, 'Monaco': 0.0159,
            'Italy': 0.0074, 'Mexico': 0.0063, 'Abu Dhabi': 0.0104,
            'Great Britain': 0.015,  # 使用預設值（2022異常已移除）
            'Canada': 0.0362,  # 3.62% from analysis
            'Singapore': 0.0266, 'Netherlands': 0.0768, 'Saudi Arabia': 0.0035,
            'Miami': 0.0119, 'Azerbaijan': 0.0091, 'United States': 0.0131,
            'Las Vegas': 0.0121, 'Hungary': 0.0874, 'Belgium': 0.0515,
            'Australia': 0.0097, 'Spain': 0.0159, 'China': 0.015,
            'Austria': 0.015, 'Brazil': 0.012, 'Qatar': 0.012,
            'Emilia Romagna': 0.012
        }
    
    def parse_time_to_seconds(self, time_str) -> float:
        """將時間字串轉換為秒數"""
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
    
    def add_v35_features(self, df: pd.DataFrame, track_name: str) -> pd.DataFrame:
        """添加 v3.5 所有特徵（20個）"""
        df = df.copy()
        
        # ========== v3.3 交互特徵 ==========
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        # ========== v3.4 速度特徵 ==========
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        apex_speeds = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']]
        df['speed_consistency'] = apex_speeds.std(axis=1) / (df['max_speed'] + 1e-6)
        
        # ========== v3.5 改進率特徵 (新增) ==========
        
        # 特徵 15: 賽道平均改進率
        track_rate = self.track_improvement_rates.get(track_name, 0.015)
        df['track_avg_improvement_rate'] = track_rate
        
        # 特徵 16: 修正後的 ideal lap
        df['adjusted_ideal_lap'] = df['ideal_lap'] * (1 - track_rate)
        
        # 特徵 17: FP3 相對排名
        df['fp3_relative_position'] = df['ideal_lap'].rank(method='min')
        
        # 特徵 18: FP3 與最快的差距
        df['fp3_gap_to_fastest'] = df['ideal_lap'] - df['ideal_lap'].min()
        
        # 特徵 19: 頂尖車手標記
        df['is_top_driver'] = df['driver'].isin(self.top_drivers).astype(int)
        
        # 特徵 20: 車手歷史改進能力（簡化版）
        df['driver_historical_improvement'] = df['is_top_driver'] * 0.002
        
        return df
    
    def load_cornering_data(self, track_name: str, session: str = 'FP3') -> dict:
        """載入彎角分析數據"""
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
        """從 JSON 直接提取特徵（修正版：正確讀取彎角數據，支援衝刺賽週末）"""
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
        
        # 添加 v3.5 特徵
        df = self.add_v35_features(df, track_name)
        
        return df
    
    def validate_single_race(self, race_num: int) -> dict:
        """驗證單場比賽"""
        track_name = self.race_mapping.get(race_num)
        if not track_name:
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
        
        # 提取特徵
        df = self.extract_features_from_json(json_file, track_name)
        if df.empty:
            print(f"  [SKIP] 無法提取特徵")
            return None
        
        print(f"  [樣本] {len(df)} 位車手")
        
        # 載入模型
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        # 準備特徵矩陣（20個特徵）
        feature_cols = [
            'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
            'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
            's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
            'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
            'track_avg_improvement_rate', 'adjusted_ideal_lap',
            'fp3_relative_position', 'fp3_gap_to_fastest',
            'is_top_driver', 'driver_historical_improvement'
        ]
        
        X = df[feature_cols]
        y_true = df['actual_q_time']
        
        # 預測
        y_pred = model.predict(X)
        
        # 評估
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        spearman = spearmanr(y_true, y_pred)[0]
        
        print(f"  [結果] MAE: {mae:.3f}s, R²: {r2:.4f}, Spearman: {spearman:.3f}")
        
        # 排序比較
        df['predicted_time'] = y_pred
        df['actual_rank'] = df['actual_q_time'].rank()
        df['predicted_rank'] = df['predicted_time'].rank()
        df['rank_diff'] = abs(df['actual_rank'] - df['predicted_rank'])
        
        avg_rank_diff = df['rank_diff'].mean()
        print(f"  [排名] 平均名次誤差: {avg_rank_diff:.2f}")
        
        return {
            'race_num': race_num,
            'track': track_name,
            'mae': mae,
            'r2': r2,
            'spearman': spearman,
            'avg_rank_diff': avg_rank_diff,
            'sample_count': len(df),
            'predictions': df[['driver', 'actual_q_time', 'predicted_time', 
                             'actual_rank', 'predicted_rank', 'rank_diff']].to_dict('records')
        }
    
    def validate_all_races(self):
        """驗證所有 2025 賽事"""
        print("\n" + "="*70)
        print("v3.5 模型 2025 賽季驗證")
        print("="*70)
        
        valid_count = 0
        
        for race_num in range(1, 25):
            result = self.validate_single_race(race_num)
            if result:
                self.results[race_num] = result
                valid_count += 1
        
        self.generate_summary()
        self.save_results()
        
        print(f"\n[完成] 成功驗證 {valid_count}/24 場比賽")
    
    def generate_summary(self):
        """生成驗證總結"""
        if not self.results:
            print("\n[錯誤] 沒有驗證結果")
            return
        
        print("\n" + "="*70)
        print("v3.5 2025 驗證總結")
        print("="*70)
        
        all_mae = [r['mae'] for r in self.results.values()]
        all_spearman = [r['spearman'] for r in self.results.values()]
        all_rank_diff = [r['avg_rank_diff'] for r in self.results.values()]
        
        print(f"\n[整體表現]")
        print(f"  驗證賽事數: {len(self.results)}")
        print(f"  平均 MAE: {np.mean(all_mae):.3f}s (std: {np.std(all_mae):.3f}s)")
        print(f"  平均 Spearman: {np.mean(all_spearman):.3f}")
        print(f"  平均名次誤差: {np.mean(all_rank_diff):.2f} 名")
        
        # Top 5 最佳賽道
        print(f"\n[Top 5 最佳預測賽道]")
        sorted_by_spearman = sorted(
            self.results.items(),
            key=lambda x: x[1]['spearman'],
            reverse=True
        )[:5]
        
        for i, (race_num, result) in enumerate(sorted_by_spearman, 1):
            print(f"  {i}. {result['track']:20s}: Spearman {result['spearman']:.3f}, MAE {result['mae']:.3f}s")
        
        # Top 5 最差賽道
        print(f"\n[Top 5 最差預測賽道]")
        sorted_by_spearman_worst = sorted(
            self.results.items(),
            key=lambda x: x[1]['spearman']
        )[:5]
        
        for i, (race_num, result) in enumerate(sorted_by_spearman_worst, 1):
            print(f"  {i}. {result['track']:20s}: Spearman {result['spearman']:.3f}, MAE {result['mae']:.3f}s")
        
        # Great Britain & Canada 分析
        print(f"\n[Great Britain & Canada 表現]")
        for track in ['Great Britain', 'Canada']:
            result = next((r for r in self.results.values() if r['track'] == track), None)
            if result:
                print(f"  {track}:")
                print(f"    MAE: {result['mae']:.3f}s, Spearman: {result['spearman']:.3f}")
                print(f"    平均名次誤差: {result['avg_rank_diff']:.2f} 名")
    
    def save_results(self):
        """保存驗證結果"""
        output_file = Path("v3.5_2025_validation_results.json")
        
        # 轉換為可序列化格式
        serializable_results = {}
        for race_num, result in self.results.items():
            serializable_results[str(race_num)] = {
                'race_num': result['race_num'],
                'track': result['track'],
                'mae': float(result['mae']),
                'r2': float(result['r2']),
                'spearman': float(result['spearman']),
                'avg_rank_diff': float(result['avg_rank_diff']),
                'sample_count': result['sample_count'],
                'predictions': result['predictions']
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[保存結果] {output_file}")


def main():
    validator = V35TwentyFiveValidator()
    validator.validate_all_races()


if __name__ == '__main__':
    main()
