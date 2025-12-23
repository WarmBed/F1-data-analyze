#!/usr/bin/env python3
"""
2025 賽季預測驗證腳本（v3.3）

目標：
1. 載入所有 2025 年 FP3→Q 數據（數字編號格式）
2. 使用 v3.3 模型預測排位賽結果
3. 對比預測名次 vs 實際名次
4. 計算 Spearman 相關性、MAE、Top N 準確率
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score
import sys

sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class V3_3_2025Validator:
    """v3.3 模型 2025 賽季驗證器"""
    
    def __init__(self):
        self.models_dir = Path("models/track_specific_v3.3")
        self.json_dir = Path("json")
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        
        # 2025 賽季賽事映射（數字 → 賽道名稱）
        self.race_mapping = {
            1: "Australia",
            2: "China", 
            3: "Japan",
            4: "Bahrain",
            5: "Saudi Arabia",
            6: "Miami",
            7: "Emilia Romagna",
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
        
        self.results = {}
    
    def add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加 v3.3 交互特徵"""
        df = df.copy()
        
        # 交互特徵 1: S1/S2 比率
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        
        # 交互特徵 2: Sector 變異係數
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        
        # 交互特徵 3: S2/Lap 比率
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        return df
    
    def find_2025_race_data(self, race_number: int) -> list:
        """尋找指定賽事編號的 2025 數據"""
        pattern = f"fp_q_data_2025_{race_number}_*.json"
        files = list(self.json_dir.glob(f"predictionJSON/{pattern}"))
        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)  # 最新的在前
    
    def predict_race(self, race_number: int, race_name: str) -> dict:
        """預測單場比賽"""
        print(f"\n{'='*70}")
        print(f"賽事 {race_number}: {race_name}")
        print(f"{'='*70}")
        
        # 檢查模型是否存在
        model_file = self.models_dir / f"{race_name}.pkl"
        if not model_file.exists():
            print(f"  [SKIP] 找不到 v3.3 模型")
            return None
        
        # 載入模型
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        # 尋找 2025 數據
        data_files = self.find_2025_race_data(race_number)
        if not data_files:
            print(f"  [SKIP] 找不到 2025 數據")
            return None
        
        print(f"  [INFO] 使用數據: {data_files[0].name}")
        
        try:
            # 載入數據（使用 v3 trainer 的方法，但指定 2025 年）
            df = self.base_trainer.load_training_data_v3(race_name, start_year=2025, end_year=2025)
            
            if df.empty:
                print(f"  [SKIP] 數據載入失敗或為空")
                return None
            
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
            drivers = df['driver'].values if 'driver' in df.columns else [f"Driver_{i}" for i in range(len(df))]
            
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
            
            # 名次對比
            true_ranks = np.argsort(np.argsort(y_true)) + 1
            pred_ranks = np.argsort(np.argsort(y_pred)) + 1
            rank_diff = np.abs(true_ranks - pred_ranks)
            
            print(f"\n  [效能指標]")
            print(f"    R²: {r2:.4f}")
            print(f"    MAE (時間): {mae:.3f}秒")
            print(f"    Spearman 相關性: {spearman_corr:.3f}")
            print(f"    Top 3 準確率: {top3:.1%}")
            print(f"    Top 10 準確率: {top10:.1%}")
            print(f"    平均名次誤差: {rank_diff.mean():.1f} 位")
            
            # 顯示前 10 名對比
            print(f"\n  [前 10 名對比]")
            print(f"  {'排名':>4} {'車手':>8} {'實際時間':>10} {'預測時間':>10} {'誤差':>8} {'預測排名':>8} {'名次差':>8}")
            print(f"  {'-'*68}")
            
            top10_idx = np.argsort(y_true)[:min(10, len(y_true))]
            for i, idx in enumerate(top10_idx, 1):
                driver = drivers[idx]
                true_time = y_true[idx]
                pred_time = y_pred[idx]
                time_diff = pred_time - true_time
                true_rank = true_ranks[idx]
                pred_rank = pred_ranks[idx]
                rank_diff_val = pred_rank - true_rank
                
                print(f"  {i:4d} {driver:>8s} {true_time:10.3f}s {pred_time:10.3f}s {time_diff:+8.3f}s {pred_rank:8d} {rank_diff_val:+8d}")
            
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
                'max_rank_error': int(rank_diff.max()),
                'predictions': {
                    'drivers': drivers.tolist(),
                    'true_times': y_true.tolist(),
                    'pred_times': y_pred.tolist(),
                    'true_ranks': true_ranks.tolist(),
                    'pred_ranks': pred_ranks.tolist()
                }
            }
        
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validate_all_2025_races(self):
        """驗證所有 2025 賽事"""
        print("\n" + "="*70)
        print("v3.3 模型 2025 賽季預測驗證")
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
        
        # 統計總結
        print(f"\n\n{'='*70}")
        print("2025 賽季預測驗證總結")
        print(f"{'='*70}")
        
        print(f"\n成功預測: {len(successful)}/{len(self.race_mapping)} 場比賽")
        
        if successful:
            avg_spearman = np.mean([r['spearman'] for r in successful])
            avg_mae = np.mean([r['mae'] for r in successful])
            avg_top3 = np.mean([r['top3_accuracy'] for r in successful])
            avg_top10 = np.mean([r['top10_accuracy'] for r in successful])
            avg_rank_error = np.mean([r['mean_rank_error'] for r in successful])
            
            print(f"\n[整體效能]")
            print(f"  平均 Spearman 相關性: {avg_spearman:.3f}")
            print(f"  平均 MAE (時間): {avg_mae:.3f}秒")
            print(f"  平均 Top 3 準確率: {avg_top3:.1%}")
            print(f"  平均 Top 10 準確率: {avg_top10:.1%}")
            print(f"  平均名次誤差: {avg_rank_error:.1f} 位")
            
            # Top 5 最佳預測
            sorted_by_spearman = sorted(successful, key=lambda x: x['spearman'], reverse=True)
            print(f"\n[Top 5 最準確預測]（依 Spearman 排序）")
            print(f"  {'賽道':20s} {'Spearman':>10s} {'MAE':>8s} {'Top3':>8s} {'名次誤差':>10s}")
            print(f"  {'-'*60}")
            for r in sorted_by_spearman[:5]:
                print(f"  {r['race_name']:20s} {r['spearman']:10.3f} {r['mae']:8.3f}s {r['top3_accuracy']:7.1%} {r['mean_rank_error']:9.1f}位")
            
            # Bottom 5 待改進
            print(f"\n[Bottom 5 待改進預測]")
            print(f"  {'賽道':20s} {'Spearman':>10s} {'MAE':>8s} {'Top3':>8s} {'名次誤差':>10s}")
            print(f"  {'-'*60}")
            for r in sorted_by_spearman[-5:]:
                print(f"  {r['race_name']:20s} {r['spearman']:10.3f} {r['mae']:8.3f}s {r['top3_accuracy']:7.1%} {r['mean_rank_error']:9.1f}位")
        
        if failed:
            print(f"\n[跳過的比賽] ({len(failed)} 場)")
            for race_num, race_name in failed:
                print(f"  {race_num:2d}. {race_name}")
        
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
    validator = V3_3_2025Validator()
    validator.validate_all_2025_races()


if __name__ == "__main__":
    main()
