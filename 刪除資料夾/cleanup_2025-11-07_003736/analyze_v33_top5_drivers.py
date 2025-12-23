#!/usr/bin/env python3
"""
分析 v3.3 2025 驗證中每場比賽 Top 5 車手的預測準確性
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')


class V33Top5Analyzer:
    """v3.3 Top 5 車手預測分析器"""
    
    def __init__(self):
        self.models_dir = Path("models/track_specific_v3.3")
        self.json_dir = Path("json/predictionJSON")
        
        # 2025 賽事映射（與 v3.3 驗證結果一致）
        self.race_mapping = {
            3: "Japan",
            4: "Bahrain",
            5: "Saudi Arabia",
            8: "Monaco",
            10: "Canada",
            12: "Great Britain",
            14: "Hungary",
            15: "Netherlands",
            16: "Italy",
            17: "Azerbaijan",
            18: "Singapore",
            20: "Mexico"
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
        
        except Exception:
            return None
    
    def add_v33_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加 v3.3 交互特徵"""
        df = df.copy()
        
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        return df
    
    def extract_features_from_json(self, json_file: Path) -> pd.DataFrame:
        """從 JSON 提取特徵"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        fp3_data = data.get('practice_sessions', {}).get('FP3', {}).get('driver_data', {})
        q_results = data.get('qualifying', {}).get('results', {})
        
        if not fp3_data or not q_results:
            return pd.DataFrame()
        
        features_list = []
        
        for driver, driver_fp3 in fp3_data.items():
            if driver not in q_results:
                continue
            
            ideal_s1 = self.parse_time_to_seconds(driver_fp3.get('sector1_best'))
            ideal_s2 = self.parse_time_to_seconds(driver_fp3.get('sector2_best'))
            ideal_s3 = self.parse_time_to_seconds(driver_fp3.get('sector3_best'))
            ideal_lap = self.parse_time_to_seconds(driver_fp3.get('best_lap_time'))
            max_speed = driver_fp3.get('speed_trap_max', 0)
            q_time = self.parse_time_to_seconds(q_results[driver].get('best_time'))
            
            if any(x is None for x in [ideal_s1, ideal_s2, ideal_s3, ideal_lap, q_time]):
                continue
            
            features_list.append({
                'driver': driver,
                'ideal_s1': ideal_s1,
                'ideal_s2': ideal_s2,
                'ideal_s3': ideal_s3,
                'ideal_lap': ideal_lap,
                'low_speed_apex': 0,
                'mid_speed_apex': 0,
                'high_speed_apex': 0,
                'max_speed': max_speed,
                'actual_q_time': q_time
            })
        
        return pd.DataFrame(features_list)
    
    def find_2025_race_data(self, race_number: int) -> list:
        """尋找賽事數據"""
        pattern = f"fp_q_data_2025_{race_number}_*.json"
        return sorted(self.json_dir.glob(pattern), reverse=True)
    
    def analyze_race_top5(self, race_number: int, race_name: str) -> dict:
        """分析單場比賽 Top 5"""
        model_file = self.models_dir / f"{race_name}.pkl"
        if not model_file.exists():
            return None
        
        data_files = self.find_2025_race_data(race_number)
        if not data_files:
            return None
        
        try:
            # 載入模型
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            
            # 提取特徵
            df = self.extract_features_from_json(data_files[0])
            if df.empty:
                return None
            
            df = self.add_v33_interaction_features(df)
            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                return None
            
            # 準備 v3.3 特徵（11 個）
            feature_cols = [
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio'
            ]
            
            X = df[feature_cols]
            y_true = df['actual_q_time'].values
            drivers = df['driver'].values
            
            # 預測
            y_pred = model.predict(X)
            
            # 計算名次
            true_ranks = np.argsort(np.argsort(y_true)) + 1
            pred_ranks = np.argsort(np.argsort(y_pred)) + 1
            
            # 提取 Top 5
            top5_idx = np.argsort(y_true)[:5]
            
            top5_data = []
            for actual_pos, idx in enumerate(top5_idx, 1):
                top5_data.append({
                    'driver': drivers[idx],
                    'actual_position': actual_pos,
                    'predicted_position': int(pred_ranks[idx]),
                    'position_diff': int(pred_ranks[idx] - actual_pos),
                    'actual_time': float(y_true[idx]),
                    'predicted_time': float(y_pred[idx]),
                    'time_diff': float(y_pred[idx] - y_true[idx])
                })
            
            return {
                'race_number': race_number,
                'race_name': race_name,
                'top5': top5_data
            }
        
        except Exception as e:
            print(f"Error processing {race_name}: {e}")
            return None
    
    def generate_report(self):
        """生成完整報告"""
        print("="*100)
        print("v3.3 2025 驗證 - Top 5 車手預測準確性分析")
        print("="*100)
        
        all_results = []
        
        for race_num, race_name in self.race_mapping.items():
            result = self.analyze_race_top5(race_num, race_name)
            if result:
                all_results.append(result)
        
        # 逐場打印
        for result in all_results:
            race_name = result['race_name']
            print(f"\n{'='*100}")
            print(f"🏁 {race_name} (Race #{result['race_number']})")
            print(f"{'='*100}")
            print(f"{'實際':<6} {'預測':<6} {'名次差':<8} {'車手':<8} {'實際時間':<12} {'預測時間':<12} {'時間差':<12} {'評價':<10}")
            print("-"*100)
            
            for driver_data in result['top5']:
                actual_pos = driver_data['actual_position']
                pred_pos = driver_data['predicted_position']
                pos_diff = driver_data['position_diff']
                driver = driver_data['driver']
                actual_time = driver_data['actual_time']
                pred_time = driver_data['predicted_time']
                time_diff = driver_data['time_diff']
                
                # 評價
                if pos_diff == 0:
                    evaluation = "✅ 完美"
                elif abs(pos_diff) <= 2:
                    evaluation = "✅ 優秀"
                elif abs(pos_diff) <= 5:
                    evaluation = "⚠️ 可接受"
                else:
                    evaluation = "❌ 偏差大"
                
                print(f"P{actual_pos:<5} P{pred_pos:<5} {pos_diff:+8d} {driver:<8s} {actual_time:11.3f}s {pred_time:11.3f}s {time_diff:+11.3f}s {evaluation:<10}")
        
        # 統計分析
        print("\n\n" + "="*100)
        print("📊 統計摘要")
        print("="*100)
        
        all_position_diffs = []
        all_time_diffs = []
        perfect_predictions = 0
        excellent_predictions = 0
        acceptable_predictions = 0
        poor_predictions = 0
        
        for result in all_results:
            for driver_data in result['top5']:
                pos_diff = abs(driver_data['position_diff'])
                time_diff = abs(driver_data['time_diff'])
                
                all_position_diffs.append(pos_diff)
                all_time_diffs.append(time_diff)
                
                if pos_diff == 0:
                    perfect_predictions += 1
                elif pos_diff <= 2:
                    excellent_predictions += 1
                elif pos_diff <= 5:
                    acceptable_predictions += 1
                else:
                    poor_predictions += 1
        
        total_predictions = len(all_position_diffs)
        
        print(f"\n總預測數: {total_predictions} 位車手 ({len(all_results)} 場比賽 × 5 名)")
        print(f"\n名次預測準確性:")
        print(f"  ✅ 完美預測 (名次完全正確): {perfect_predictions} ({perfect_predictions/total_predictions:.1%})")
        print(f"  ✅ 優秀預測 (±2 名內): {excellent_predictions} ({excellent_predictions/total_predictions:.1%})")
        print(f"  ⚠️  可接受預測 (±5 名內): {acceptable_predictions} ({acceptable_predictions/total_predictions:.1%})")
        print(f"  ❌ 偏差較大 (>5 名): {poor_predictions} ({poor_predictions/total_predictions:.1%})")
        
        print(f"\n平均名次誤差: {np.mean(all_position_diffs):.2f} 名")
        print(f"平均時間誤差: {np.mean(all_time_diffs):.3f} 秒")
        print(f"最大名次誤差: {np.max(all_position_diffs)} 名")
        print(f"最大時間誤差: {np.max(all_time_diffs):.3f} 秒")
        
        # 按賽道統計
        print("\n\n" + "="*100)
        print("📊 各賽道 Top 5 預測表現")
        print("="*100)
        print(f"{'賽道':<20} {'完美預測':<12} {'優秀預測':<12} {'平均名次誤差':<15} {'平均時間誤差':<15}")
        print("-"*100)
        
        for result in all_results:
            race_name = result['race_name']
            perfect = sum(1 for d in result['top5'] if d['position_diff'] == 0)
            excellent = sum(1 for d in result['top5'] if abs(d['position_diff']) <= 2)
            avg_pos_diff = np.mean([abs(d['position_diff']) for d in result['top5']])
            avg_time_diff = np.mean([abs(d['time_diff']) for d in result['top5']])
            
            print(f"{race_name:<20} {perfect}/5 ({perfect*20:.0f}%) {excellent:>6}/5 ({excellent*20:.0f}%) {avg_pos_diff:>14.2f} 名 {avg_time_diff:>14.3f}s")
        
        print("\n" + "="*100)


def main():
    analyzer = V33Top5Analyzer()
    analyzer.generate_report()


if __name__ == "__main__":
    main()
