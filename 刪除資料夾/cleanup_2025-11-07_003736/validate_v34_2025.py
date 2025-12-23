#!/usr/bin/env python3
"""
v3.4 模型 2025 賽季驗證腳本
基於 validate_2025_direct.py 架構，添加 v3.4 特徵支持
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


class V34TwentyFiveValidator:
    """v3.4 模型 2025 驗證器"""
    
    def __init__(self, models_dir: str = "models/track_specific_v3.4"):
        self.models_dir = Path(models_dir)
        self.json_dir = Path("json/predictionJSON")
        self.results = {}
        
        # 2025 賽事映射（race_number -> race_name）
        self.race_mapping = {
            1: "Australia",
            2: "China", 
            3: "Japan",
            4: "Bahrain",
            5: "Saudi Arabia",
            6: "Miami",
            7: "Emilia Romagna",  # Imola
            8: "Monaco",
            9: "Spain",
            10: "Canada",
            11: "Austria",
            12: "Great Britain",
            13: "Belgium",
            14: "Hungary",
            15: "Netherlands",
            16: "Italy",
            17: "Azerbaijan",
            18: "Singapore",
            19: "United States",
            20: "Mexico",
            21: "Brazil",
            22: "Las Vegas",
            23: "Qatar",
            24: "Abu Dhabi"
        }
    
    def parse_time_to_seconds(self, time_str) -> float:
        """將時間字串轉換為秒數"""
        if time_str is None or time_str == '' or time_str == 'N/A':
            return None
        
        try:
            if isinstance(time_str, (int, float)):
                return float(time_str)
            
            time_str = str(time_str).strip()
            
            # 格式: "0 days 00:01:23.456000"
            if 'days' in time_str:
                parts = time_str.split()
                time_part = parts[-1]
                h, m, s = time_part.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s)
            
            # 格式: "1:23.456"
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:
                    return int(parts[0]) * 60 + float(parts[1])
                elif len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            
            return float(time_str)
        
        except Exception as e:
            print(f"    [WARNING] 無法解析時間 '{time_str}': {e}")
            return None
    
    def add_v34_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加 v3.4 所有交互特徵（v3.3 + v3.4 新增）"""
        df = df.copy()
        
        # v3.3 特徵
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        # v3.4 新增特徵（速度交互）
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        
        # speed_consistency = std(apex speeds) / max_speed
        apex_speeds = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']]
        df['speed_consistency'] = apex_speeds.std(axis=1) / (df['max_speed'] + 1e-6)
        
        return df
    
    def extract_features_from_json(self, json_file: Path) -> pd.DataFrame:
        """從 JSON 直接提取特徵"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取 FP3 和排位賽數據
        fp3_data = data.get('practice_sessions', {}).get('FP3', {}).get('driver_data', {})
        q_results = data.get('qualifying', {}).get('results', {})
        
        if not fp3_data or not q_results:
            return pd.DataFrame()
        
        features_list = []
        
        for driver, driver_fp3 in fp3_data.items():
            if driver not in q_results:
                continue
            
            # 提取 FP3 特徵（2025 使用不同鍵名）
            ideal_s1_raw = driver_fp3.get('sector1_best')
            ideal_s2_raw = driver_fp3.get('sector2_best')
            ideal_s3_raw = driver_fp3.get('sector3_best')
            ideal_lap_raw = driver_fp3.get('best_lap_time')
            
            # 轉換為秒數
            ideal_s1 = self.parse_time_to_seconds(ideal_s1_raw)
            ideal_s2 = self.parse_time_to_seconds(ideal_s2_raw)
            ideal_s3 = self.parse_time_to_seconds(ideal_s3_raw)
            ideal_lap = self.parse_time_to_seconds(ideal_lap_raw)
            
            # 提取彎角速度
            low_speed = 0
            mid_speed = 0
            high_speed = 0
            max_speed = driver_fp3.get('speed_trap_max', 0)
            
            # 提取排位賽時間
            q_time_raw = q_results[driver].get('best_time')
            q_time = self.parse_time_to_seconds(q_time_raw)
            
            # 檢查數據完整性
            if any(x is None for x in [ideal_s1, ideal_s2, ideal_s3, ideal_lap, q_time]):
                continue
            
            features_list.append({
                'driver': driver,
                'ideal_s1': ideal_s1,
                'ideal_s2': ideal_s2,
                'ideal_s3': ideal_s3,
                'ideal_lap': ideal_lap,
                'low_speed_apex': low_speed,
                'mid_speed_apex': mid_speed,
                'high_speed_apex': high_speed,
                'max_speed': max_speed,
                'actual_q_time': q_time
            })
        
        return pd.DataFrame(features_list)
    
    def find_2025_race_data(self, race_number: int) -> list:
        """尋找指定賽事編號的 2025 數據"""
        pattern = f"fp_q_data_2025_{race_number}_*.json"
        data_files = list(self.json_dir.glob(pattern))
        
        # 嘗試無前導零
        if not data_files:
            pattern_no_zero = f"fp_q_data_2025_{race_number}_*.json"
            data_files = list(self.json_dir.glob(pattern_no_zero))
        
        return sorted(data_files, reverse=True)  # 最新的先
    
    def predict_race(self, race_number: int, race_name: str) -> dict:
        """預測單場賽事"""
        print(f"\n[{race_number:2d}] {race_name}")
        
        # 檢查模型
        model_file = self.models_dir / f"{race_name}.pkl"
        if not model_file.exists():
            print(f"  [SKIP] No v3.4 model found")
            return None
        
        # 載入模型
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        # 尋找數據
        data_files = self.find_2025_race_data(race_number)
        if not data_files:
            print(f"  [SKIP] No 2025 data found")
            return None
        
        print(f"  [INFO] Using data: {data_files[0].name}")
        
        try:
            # 從 JSON 提取特徵
            df = self.extract_features_from_json(data_files[0])
            
            if df.empty:
                print(f"  [SKIP] 數據提取失敗或為空")
                return None
            
            print(f"  [INFO] 成功載入 {len(df)} 位車手數據")
            
            # 添加 v3.4 交互特徵
            df = self.add_v34_interaction_features(df)
            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] 清理後無有效數據")
                return None
            
            # 準備 v3.4 特徵（14 個）
            feature_cols = [
                # 基礎特徵（8 個）
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                # v3.3 交互特徵（3 個）
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                # v3.4 新增特徵（3 個）
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency'
            ]
            
            X = df[feature_cols]
            y_true = df['actual_q_time'].values
            drivers = df['driver'].values
            
            # 預測
            y_pred = model.predict(X)
            
            # 計算指標
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)
            spearman_corr, _ = spearmanr(y_true, y_pred)
            
            # Top N 準確率
            def top_n_accuracy(y_true, y_pred, n):
                n = min(n, len(y_true))
                true_top_n = set(np.argsort(y_true)[:n])
                pred_top_n = set(np.argsort(y_pred)[:n])
                return len(true_top_n & pred_top_n) / n
            
            top3 = top_n_accuracy(y_true, y_pred, 3)
            top10 = top_n_accuracy(y_true, y_pred, 10)
            
            # 名次計算
            true_ranks = np.argsort(np.argsort(y_true)) + 1
            pred_ranks = np.argsort(np.argsort(y_pred)) + 1
            rank_diff = np.abs(true_ranks - pred_ranks)
            
            print(f"\n  [Performance Metrics]")
            print(f"    R²: {r2:.4f}")
            print(f"    MAE: {mae:.3f}s")
            print(f"    Spearman: {spearman_corr:.3f}")
            print(f"    Top 3 accuracy: {top3:.1%}")
            print(f"    Top 10 accuracy: {top10:.1%}")
            print(f"    Avg rank error: {rank_diff.mean():.1f} pos")
            
            # Top 10 Comparison
            print(f"\n  [Top 10 Comparison]")
            print(f"  {'Rank':>4} {'Driver':>8} {'Actual':>10} {'Predicted':>10} {'TimeDiff':>10} {'PredRank':>8} {'RankDiff':>8}")
            print(f"  {'-'*75}")
            
            top10_idx = np.argsort(y_true)[:min(10, len(y_true))]
            for i, idx in enumerate(top10_idx, 1):
                driver = drivers[idx]
                true_time = y_true[idx]
                pred_time = y_pred[idx]
                time_diff = pred_time - true_time
                pred_rank = pred_ranks[idx]
                rank_diff_val = pred_rank - i
                
                print(f"  {i:4d} {driver:>8s} {true_time:10.3f}s {pred_time:10.3f}s {time_diff:+10.3f}s {pred_rank:8d} {rank_diff_val:+8d}")
            
            return {
                'race_number': race_number,
                'race_name': race_name,
                'n_drivers': len(df),
                'r2': float(r2),
                'mae': float(mae),
                'spearman': float(spearman_corr),
                'top3_accuracy': float(top3),
                'top10_accuracy': float(top10),
                'mean_rank_error': float(rank_diff.mean()),
                'max_rank_error': int(rank_diff.max())
            }
        
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validate_all_2025_races(self):
        """驗證所有 2025 賽事"""
        print("\n" + "="*70)
        print("v3.4 模型 2025 賽季預測驗證")
        print("="*70)
        
        successful = []
        failed = []
        
        for race_num, race_name in self.race_mapping.items():
            result = self.predict_race(race_num, race_name)
            
            if result:
                successful.append(result)
                self.results[race_name] = result
            else:
                failed.append((race_num, race_name))
        
        # Summary Statistics
        print(f"\n\n{'='*70}")
        print("v3.4 - 2025 Season Prediction Validation Summary")
        print(f"{'='*70}")
        
        print(f"\nSuccessful predictions: {len(successful)}/{len(self.race_mapping)} races")
        
        if successful:
            avg_spearman = np.mean([r['spearman'] for r in successful])
            avg_mae = np.mean([r['mae'] for r in successful])
            avg_top3 = np.mean([r['top3_accuracy'] for r in successful])
            avg_top10 = np.mean([r['top10_accuracy'] for r in successful])
            avg_rank_error = np.mean([r['mean_rank_error'] for r in successful])
            
            print(f"\n[Overall Performance]")
            print(f"  Avg Spearman: {avg_spearman:.3f}")
            print(f"  Avg MAE: {avg_mae:.3f}s")
            print(f"  Avg Top 3 accuracy: {avg_top3:.1%}")
            print(f"  Avg Top 10 accuracy: {avg_top10:.1%}")
            print(f"  Avg rank error: {avg_rank_error:.1f} pos")
            
            # 最佳/最差賽道
            print(f"\n[Top 5 Best Predictions (by Spearman)]")
            sorted_by_spearman = sorted(successful, key=lambda x: x['spearman'], reverse=True)
            for i, r in enumerate(sorted_by_spearman[:5], 1):
                print(f"  {i}. {r['race_name']:20s} Spearman={r['spearman']:6.3f}  MAE={r['mae']:5.3f}s")
            
            print(f"\n[Bottom 5 Worst Predictions (by Spearman)]")
            for i, r in enumerate(sorted_by_spearman[-5:][::-1], 1):
                print(f"  {i}. {r['race_name']:20s} Spearman={r['spearman']:6.3f}  MAE={r['mae']:5.3f}s")
        
        if failed:
            print(f"\n[Failed Predictions]")
            for race_num, race_name in failed:
                print(f"  [{race_num:2d}] {race_name}")
        
        # 保存結果
        output = {
            'metadata': {
                'version': 'v3.4',
                'validation_year': 2025,
                'successful_predictions': len(successful),
                'failed_predictions': len(failed)
            },
            'summary': {
                'avg_spearman': float(avg_spearman) if successful else None,
                'avg_mae': float(avg_mae) if successful else None,
                'avg_top3_accuracy': float(avg_top3) if successful else None,
                'avg_top10_accuracy': float(avg_top10) if successful else None,
                'avg_rank_error': float(avg_rank_error) if successful else None
            },
            'race_results': {r['race_name']: {
                'race_number': r['race_number'],
                'n_drivers': r['n_drivers'],
                'r2': r['r2'],
                'mae': r['mae'],
                'spearman': r['spearman'],
                'top3_accuracy': r['top3_accuracy'],
                'top10_accuracy': r['top10_accuracy'],
                'mean_rank_error': r['mean_rank_error']
            } for r in successful}
        }
        
        output_file = 'v3.4_2025_validation_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 結果已保存至: {output_file}")
        
        return self.results


def main():
    """主程式"""
    validator = V34TwentyFiveValidator()
    results = validator.validate_all_2025_races()
    
    print("\n" + "="*70)
    print("v3.4 2025 驗證完成！")
    print("="*70)


if __name__ == "__main__":
    main()
