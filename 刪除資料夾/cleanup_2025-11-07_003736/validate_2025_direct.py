#!/usr/bin/env python3
"""
2025 賽季預測驗證腳本（v3.3）- 直接處理 JSON

直接讀取 2025 FP3→Q JSON 數據，不依賴 TrainerV3 的載入方法
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score


class V3_3_2025Validator_Direct:
    """v3.3 模型 2025 賽季驗證器（直接處理 JSON）"""
    
    def __init__(self):
        self.models_dir = Path("models/track_specific_v3.3")
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
        
        self.results = {}
    
    def parse_time_to_seconds(self, time_value):
        """將時間轉換為秒數（支援多種格式）"""
        if time_value is None:
            return None
        
        # 如果已經是數字，直接返回
        if isinstance(time_value, (int, float)):
            return float(time_value)
        
        # 如果是字串，解析 timedelta 格式 '0 days 00:01:26.983000'
        if isinstance(time_value, str):
            try:
                # 移除 'days' 部分
                if 'days' in time_value:
                    parts = time_value.split('days')
                    time_part = parts[1].strip()
                else:
                    time_part = time_value.strip()
                
                # 解析 HH:MM:SS.ffffff
                time_components = time_part.split(':')
                hours = int(time_components[0])
                minutes = int(time_components[1])
                seconds = float(time_components[2])
                
                total_seconds = hours * 3600 + minutes * 60 + seconds
                return total_seconds
            except:
                return None
        
        return None
    
    def add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加 v3.3 交互特徵"""
        df = df.copy()
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
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
            ideal_s1_raw = driver_fp3.get('sector1_best')  # 2025 格式
            ideal_s2_raw = driver_fp3.get('sector2_best')  # 2025 格式
            ideal_s3_raw = driver_fp3.get('sector3_best')  # 2025 格式
            ideal_lap_raw = driver_fp3.get('best_lap_time')  # 2025 格式
            
            # 轉換為秒數
            ideal_s1 = self.parse_time_to_seconds(ideal_s1_raw)
            ideal_s2 = self.parse_time_to_seconds(ideal_s2_raw)
            ideal_s3 = self.parse_time_to_seconds(ideal_s3_raw)
            ideal_lap = self.parse_time_to_seconds(ideal_lap_raw)
            
            # 提取彎角速度（通常在 cornering 數據中，這裡先用 0）
            low_speed = 0
            mid_speed = 0
            high_speed = 0
            max_speed = driver_fp3.get('speed_trap_max', 0)
            
            # 提取排位賽時間（2025 使用 best_time）
            q_time_raw = q_results[driver].get('best_time')  # 2025 格式
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
        files = list(self.json_dir.glob(pattern))
        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def predict_race(self, race_number: int, race_name: str) -> dict:
        """預測單場比賽"""
        print(f"\n{'='*70}")
        print(f"賽事 {race_number}: {race_name}")
        print(f"{'='*70}")
        
        # Check model
        model_file = self.models_dir / f"{race_name}.pkl"
        if not model_file.exists():
            print(f"  [SKIP] No v3.3 model found")
            return None
        
        # 載入模型
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        # Find data
        data_files = self.find_2025_race_data(race_number)
        if not data_files:
            print(f"  [SKIP] No 2025 data found")
            return None
        
        print(f"  [INFO] Using data: {data_files[0].name}")
        
        try:
            # 直接從 JSON 提取特徵
            df = self.extract_features_from_json(data_files[0])
            
            if df.empty:
                print(f"  [SKIP] 數據提取失敗或為空")
                return None
            
            print(f"  [INFO] 成功載入 {len(df)} 位車手數據")
            
            # 添加交互特徵
            df = self.add_interaction_features(df)
            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] 清理後無有效數據")
                return None
            
            # 準備特徵
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
            print(f"    R2: {r2:.4f}")
            print(f"    MAE (time): {mae:.3f}s")
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
        print("v3.3 模型 2025 賽季預測驗證（直接處理 JSON）")
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
        print("2025 Season Prediction Validation Summary")
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
            print(f"  Avg MAE (time): {avg_mae:.3f}s")
            print(f"  Avg Top 3 accuracy: {avg_top3:.1%}")
            print(f"  Avg Top 10 accuracy: {avg_top10:.1%}")
            print(f"  Avg rank error: {avg_rank_error:.1f} pos")
            
            # Top 5 Best Predictions
            sorted_by_spearman = sorted(successful, key=lambda x: x['spearman'], reverse=True)
            print(f"\n[Top 5 Best Predictions] (by Spearman)")
            print(f"  {'Track':20s} {'Spearman':>10s} {'MAE':>8s} {'Top3':>8s} {'RankErr':>10s}")
            print(f"  {'-'*62}")
            for r in sorted_by_spearman[:5]:
                print(f"  {r['race_name']:20s} {r['spearman']:10.3f} {r['mae']:8.3f}s {r['top3_accuracy']:7.1%} {r['mean_rank_error']:9.1f}pos")
            
            # Bottom 5 Worst
            print(f"\n[Bottom 5 Worst Predictions]")
            print(f"  {'Track':20s} {'Spearman':>10s} {'MAE':>8s} {'Top3':>8s} {'RankErr':>10s}")
            print(f"  {'-'*62}")
            for r in sorted_by_spearman[-5:]:
                print(f"  {r['race_name']:20s} {r['spearman']:10.3f} {r['mae']:8.3f}s {r['top3_accuracy']:7.1%} {r['mean_rank_error']:9.1f}pos")
        
        if failed:
            print(f"\n[Skipped Races] ({len(failed)} races)")
            for race_num, race_name in failed:
                reason = "No model" if not (self.models_dir / f"{race_name}.pkl").exists() else "No data"
                print(f"  {race_num:2d}. {race_name:20s} ({reason})")
        
        # 保存結果
        output = {
            'metadata': {
                'version': 'v3.3',
                'validation_year': 2025,
                'timestamp': datetime.now().isoformat(),
                'total_races': len(self.race_mapping),
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
            'race_results': self.results
        }
        
        output_file = Path('v3.3_2025_validation_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n[保存] 結果已保存: {output_file}")
        print("\n✅ 2025 賽季驗證完成！")


def main():
    """主函數"""
    validator = V3_3_2025Validator_Direct()
    validator.validate_all_2025_races()


if __name__ == "__main__":
    main()
