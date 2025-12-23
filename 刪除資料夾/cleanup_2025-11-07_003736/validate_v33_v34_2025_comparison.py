#!/usr/bin/env python3
"""
對比 v3.3 vs v3.4 在 2025 賽季的預測表現
使用 validate_2025_direct.py 的 JSON 解析邏輯
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error


class CompareV33V34_2025:
    """對比 v3.3 vs v3.4 在 2025 的表現"""
    
    def __init__(self):
        self.models_v33_dir = Path("models/track_specific_v3.3")
        self.models_v34_dir = Path("models/track_specific_v3.4")
        self.json_dir = Path("json/predictionJSON")
        
        # 2025 賽季賽事映射
        self.race_mapping = {
            1: "Australia", 2: "China", 3: "Japan", 4: "Bahrain", 5: "Saudi Arabia",
            6: "Miami", 7: "Emilia Romagna", 8: "Monaco", 9: "Spain", 10: "Canada",
            11: "Austria", 12: "Great Britain", 13: "Belgium", 14: "Hungary",
            15: "Netherlands", 16: "Italy", 17: "Azerbaijan", 18: "Singapore",
            19: "United States", 20: "Mexico", 21: "Brazil", 22: "Las Vegas",
            23: "Qatar", 24: "Abu Dhabi"
        }
        
        self.results_v33 = {}
        self.results_v34 = {}
    
    def parse_time_to_seconds(self, time_value):
        """將時間轉換為秒數"""
        if time_value is None:
            return None
        
        if isinstance(time_value, (int, float)):
            return float(time_value)
        
        if isinstance(time_value, str):
            try:
                if 'days' in time_value:
                    parts = time_value.split('days')
                    time_part = parts[1].strip()
                else:
                    time_part = time_value.strip()
                
                time_components = time_part.split(':')
                hours = int(time_components[0])
                minutes = int(time_components[1])
                seconds = float(time_components[2])
                
                return hours * 3600 + minutes * 60 + seconds
            except:
                return None
        
        return None
    
    def add_v33_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加 v3.3 交互特徵（11 特徵）"""
        df = df.copy()
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        return df
    
    def add_v34_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加 v3.4 所有交互特徵（14 特徵）"""
        df = self.add_v33_features(df)
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        apex_std = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']].std(axis=1)
        df['speed_consistency'] = apex_std / (df['max_speed'] + 1e-6)
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
            
            # FP3 特徵（2025 格式）
            ideal_s1 = self.parse_time_to_seconds(driver_fp3.get('sector1_best'))
            ideal_s2 = self.parse_time_to_seconds(driver_fp3.get('sector2_best'))
            ideal_s3 = self.parse_time_to_seconds(driver_fp3.get('sector3_best'))
            ideal_lap = self.parse_time_to_seconds(driver_fp3.get('best_lap_time'))
            
            # 彎角速度
            corner_data = driver_fp3.get('corner_data', {})
            low_speed_apex = corner_data.get('low_speed', {}).get('avg_speed')
            mid_speed_apex = corner_data.get('mid_speed', {}).get('avg_speed')
            high_speed_apex = corner_data.get('high_speed', {}).get('avg_speed')
            max_speed = driver_fp3.get('max_speed')
            
            # 實際排位結果
            q_position = q_results[driver].get('position')
            q_time = self.parse_time_to_seconds(q_results[driver].get('time'))
            
            if None in [ideal_s1, ideal_s2, ideal_s3, ideal_lap, q_position, q_time]:
                continue
            
            features_list.append({
                'driver': driver,
                'position': q_position,
                'actual_q_time': q_time,
                'ideal_s1': ideal_s1,
                'ideal_s2': ideal_s2,
                'ideal_s3': ideal_s3,
                'ideal_lap': ideal_lap,
                'low_speed_apex': low_speed_apex or 0,
                'mid_speed_apex': mid_speed_apex or 0,
                'high_speed_apex': high_speed_apex or 0,
                'max_speed': max_speed or 0
            })
        
        if not features_list:
            return pd.DataFrame()
        
        return pd.DataFrame(features_list)
    
    def validate_race(self, race_number: int, model_version: str):
        """驗證單一賽事"""
        race_name = self.race_mapping.get(race_number)
        if not race_name:
            return None
        
        # 找 JSON 檔案
        pattern = f"race_{race_number}_*_*.json"
        json_files = list(self.json_dir.glob(pattern))
        
        if not json_files:
            return None
        
        json_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        # 提取特徵
        df = self.extract_features_from_json(json_file)
        
        if df.empty:
            return None
        
        # 添加交互特徵並準備特徵集
        if model_version == 'v3.3':
            df = self.add_v33_features(df)
            feature_cols = [
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio'
            ]
            model_path = self.models_v33_dir / f"{race_name}.pkl"
        else:  # v3.4
            df = self.add_v34_features(df)
            feature_cols = [
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency'
            ]
            model_path = self.models_v34_dir / f"{race_name}.pkl"
        
        # 清理數據
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        
        if df.empty or not model_path.exists():
            return None
        
        # 載入模型並預測
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        X = df[feature_cols]
        y_actual = df['actual_q_time']
        y_pred = model.predict(X)
        
        # 評估
        mae = mean_absolute_error(y_actual, y_pred)
        spearman, _ = spearmanr(y_actual, y_pred)
        
        return {
            'race': race_name,
            'race_number': race_number,
            'mae': float(mae),
            'spearman': float(spearman),
            'n_samples': len(df)
        }
    
    def run_comparison(self):
        """執行完整對比"""
        print("="*80)
        print("v3.3 vs v3.4 - 2025 賽季預測對比")
        print("="*80)
        
        for race_num in range(1, 25):
            race_name = self.race_mapping.get(race_num, f"Race {race_num}")
            
            # v3.3 驗證
            result_v33 = self.validate_race(race_num, 'v3.3')
            if result_v33:
                self.results_v33[race_name] = result_v33
            
            # v3.4 驗證
            result_v34 = self.validate_race(race_num, 'v3.4')
            if result_v34:
                self.results_v34[race_name] = result_v34
            
            # 即時顯示對比
            if result_v33 and result_v34:
                print(f"\n{'='*80}")
                print(f"Race {race_num}: {race_name}")
                print(f"{'='*80}")
                
                print(f"\nv3.3: MAE {result_v33['mae']:.3f}s, Spearman {result_v33['spearman']:.3f}")
                print(f"v3.4: MAE {result_v34['mae']:.3f}s, Spearman {result_v34['spearman']:.3f}")
                
                mae_change = result_v34['mae'] - result_v33['mae']
                spearman_change = result_v34['spearman'] - result_v33['spearman']
                
                mae_symbol = "✅" if mae_change < 0 else "❌"
                spearman_symbol = "✅" if spearman_change > 0 else "❌"
                
                print(f"\n變化:")
                print(f"  MAE:      {mae_change:+.3f}s {mae_symbol}")
                print(f"  Spearman: {spearman_change:+.3f} {spearman_symbol}")
        
        # 生成總結
        self.print_summary()
    
    def print_summary(self):
        """列印總結"""
        print(f"\n{'='*80}")
        print("總結分析")
        print(f"{'='*80}")
        
        common_races = set(self.results_v33.keys()) & set(self.results_v34.keys())
        
        if not common_races:
            print("\n❌ 沒有共同的驗證結果")
            return
        
        print(f"\n共同驗證賽道數: {len(common_races)}")
        
        # Great Britain 專項對比
        if "Great Britain" in common_races:
            print(f"\n{'='*80}")
            print("🎯 Great Britain 專項對比（重點）")
            print(f"{'='*80}")
            
            gb_v33 = self.results_v33["Great Britain"]
            gb_v34 = self.results_v34["Great Britain"]
            
            print(f"\nv3.3 (11 特徵):")
            print(f"  MAE:      {gb_v33['mae']:.3f}s")
            print(f"  Spearman: {gb_v33['spearman']:.3f}")
            
            print(f"\nv3.4 (14 特徵 + max_speed 交互):")
            print(f"  MAE:      {gb_v34['mae']:.3f}s")
            print(f"  Spearman: {gb_v34['spearman']:.3f}")
            
            mae_improvement = (gb_v33['mae'] - gb_v34['mae']) / gb_v33['mae'] * 100
            spearman_improvement = gb_v34['spearman'] - gb_v33['spearman']
            
            print(f"\n改進幅度:")
            print(f"  MAE:      {mae_improvement:+.1f}% ({gb_v34['mae'] - gb_v33['mae']:+.3f}s)")
            print(f"  Spearman: {spearman_improvement:+.3f}")
            
            # 判定
            if gb_v34['mae'] < gb_v33['mae'] and gb_v34['spearman'] > gb_v33['spearman']:
                print("\n✅✅✅ v3.4 全面改進 Great Britain 預測！")
            elif gb_v34['mae'] < gb_v33['mae']:
                print("\n✅ v3.4 改進 MAE，但 Spearman 未改善")
            elif gb_v34['spearman'] > gb_v33['spearman']:
                print("\n✅ v3.4 改進 Spearman，但 MAE 未改善")
            else:
                print("\n❌ v3.4 未能改進 Great Britain 預測")
                print("⚠️  添加 max_speed 交互特徵無效，需要其他方案")
        
        # 整體統計
        print(f"\n{'='*80}")
        print("整體統計對比")
        print(f"{'='*80}")
        
        mae_v33 = [self.results_v33[r]['mae'] for r in common_races]
        mae_v34 = [self.results_v34[r]['mae'] for r in common_races]
        spearman_v33 = [self.results_v33[r]['spearman'] for r in common_races]
        spearman_v34 = [self.results_v34[r]['spearman'] for r in common_races]
        
        print(f"\nv3.3: 平均 MAE {np.mean(mae_v33):.3f}s, 平均 Spearman {np.mean(spearman_v33):.3f}")
        print(f"v3.4: 平均 MAE {np.mean(mae_v34):.3f}s, 平均 Spearman {np.mean(spearman_v34):.3f}")
        
        # 改進統計
        mae_improved = sum(1 for r in common_races if self.results_v34[r]['mae'] < self.results_v33[r]['mae'])
        spearman_improved = sum(1 for r in common_races if self.results_v34[r]['spearman'] > self.results_v33[r]['spearman'])
        
        print(f"\nMAE 改進賽道數:      {mae_improved}/{len(common_races)} ({mae_improved/len(common_races)*100:.1f}%)")
        print(f"Spearman 改進賽道數: {spearman_improved}/{len(common_races)} ({spearman_improved/len(common_races)*100:.1f}%)")
        
        # 顯示改進/退步最多的賽道
        changes = []
        for race in common_races:
            mae_change = self.results_v34[race]['mae'] - self.results_v33[race]['mae']
            spearman_change = self.results_v34[race]['spearman'] - self.results_v33[race]['spearman']
            changes.append((race, mae_change, spearman_change))
        
        print(f"\nTop 5 改進最多（MAE 降幅最大）:")
        changes_sorted = sorted(changes, key=lambda x: x[1])
        for i, (race, mae_change, spearman_change) in enumerate(changes_sorted[:5], 1):
            print(f"  {i}. {race:20s} MAE {mae_change:+.3f}s, Spearman {spearman_change:+.3f}")
        
        print(f"\nTop 5 退步最多（MAE 增幅最大）:")
        for i, (race, mae_change, spearman_change) in enumerate(changes_sorted[-5:][::-1], 1):
            print(f"  {i}. {race:20s} MAE {mae_change:+.3f}s, Spearman {spearman_change:+.3f}")


def main():
    comparator = CompareV33V34_2025()
    comparator.run_comparison()


if __name__ == "__main__":
    main()
