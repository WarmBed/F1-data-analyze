#!/usr/bin/env python3
"""
v3.8 vs v3.8.1 詳細性能對比報告

功能:
1. 比較 v3.8 (17特徵) vs v3.8.1 (19特徵) 的性能
2. 生成每個賽道的預測 vs 實際排名對比
3. 生成每位駕駛員的預測時間 vs 實際時間對比
4. 輸出完整 Markdown 報告
"""
import json
import pickle
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.stats import spearmanr


class DetailedComparisonReporter:
    """詳細比較報告生成器"""
    
    def __init__(self):
        self.v38_dir = Path("models/track_specific_v3.8")
        self.v381_dir = Path("models/track_specific_v3.8.1")
        self.v38_results = None
        self.v381_results = None
        self.comparison_data = []
        
    def load_results(self):
        """載入訓練結果"""
        v38_file = Path("v3.8_training_results.json")
        v381_file = Path("v3.8.1_training_results.json")
        
        if not v38_file.exists():
            print(f"[警告] 找不到 {v38_file}")
            return False
        
        if not v381_file.exists():
            print(f"[警告] 找不到 {v381_file}")
            return False
        
        with open(v38_file, 'r', encoding='utf-8') as f:
            self.v38_results = json.load(f)
        
        with open(v381_file, 'r', encoding='utf-8') as f:
            self.v381_results = json.load(f)
        
        return True
    
    def load_model(self, version: str, track: str):
        """載入模型數據"""
        model_dir = Path(f"models/track_specific_{version}")
        model_file = model_dir / f"{track}.pkl"
        
        if not model_file.exists():
            return None
        
        with open(model_file, 'rb') as f:
            return pickle.load(f)
    
    def load_test_data(self, track: str):
        """載入測試數據（2024年數據）"""
        # 從訓練器載入原始數據
        import sys
        sys.path.append(str(Path.cwd()))
        from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3
        
        trainer = TrackSpecificTrainerV3()
        df = trainer.prepare_data_for_track(track, 2022, 2024)
        
        if df is None or df.empty:
            return None
        
        # 分割測試集（2024年數據）
        test_df = df[df['year'] == 2024].copy()
        
        return test_df
    
    def predict_with_model(self, model_data, test_df, version: str):
        """使用模型進行預測"""
        if model_data is None or test_df is None or test_df.empty:
            return None
        
        model = model_data['model']
        feature_names = model_data['feature_names']
        
        # 準備特徵
        X_test = test_df[feature_names].copy()
        y_test = test_df['actual_q_time'].values
        
        # 預測
        y_pred = model.predict(X_test)
        
        # 計算排名
        test_df['pred_time'] = y_pred
        test_df['pred_rank'] = test_df['pred_time'].rank(method='min').astype(int)
        test_df['actual_rank'] = test_df['actual_q_time'].rank(method='min').astype(int)
        test_df['rank_diff'] = test_df['pred_rank'] - test_df['actual_rank']
        
        return test_df[['driver', 'actual_q_time', 'pred_time', 'actual_rank', 'pred_rank', 'rank_diff']]
    
    def calculate_metrics(self, pred_df):
        """計算評估指標"""
        if pred_df is None or pred_df.empty:
            return None
        
        mae = np.mean(np.abs(pred_df['pred_time'] - pred_df['actual_q_time']))
        rmse = np.sqrt(np.mean((pred_df['pred_time'] - pred_df['actual_q_time'])**2))
        
        # Spearman 排名相關係數
        spearman_corr, spearman_p = spearmanr(pred_df['actual_rank'], pred_df['pred_rank'])
        
        # 排名準確度
        exact_rank = (pred_df['rank_diff'] == 0).sum() / len(pred_df)
        within_1 = (np.abs(pred_df['rank_diff']) <= 1).sum() / len(pred_df)
        within_2 = (np.abs(pred_df['rank_diff']) <= 2).sum() / len(pred_df)
        
        # Top5 準確度
        top5_actual = set(pred_df.nsmallest(5, 'actual_rank')['driver'])
        top5_pred = set(pred_df.nsmallest(5, 'pred_rank')['driver'])
        top5_accuracy = len(top5_actual & top5_pred) / 5
        
        return {
            'mae': mae,
            'rmse': rmse,
            'spearman_corr': spearman_corr,
            'spearman_p': spearman_p,
            'exact_rank': exact_rank,
            'within_1': within_1,
            'within_2': within_2,
            'top5_accuracy': top5_accuracy,
        }
    
    def compare_tracks(self):
        """比較所有賽道"""
        # 獲取共同賽道
        v38_tracks = set(self.v38_results.get('results', {}).keys())
        v381_tracks = set(self.v381_results.get('results', {}).keys())
        common_tracks = v38_tracks & v381_tracks
        
        if not common_tracks:
            print("[錯誤] 沒有共同訓練的賽道")
            return []
        
        print(f"\n[共同賽道] {len(common_tracks)} 個")
        print(f"  {', '.join(sorted(common_tracks))}")
        
        comparison_results = []
        
        for track in sorted(common_tracks):
            print(f"\n[處理] {track}...")
            
            # 載入模型
            v38_model = self.load_model("v3.8", track)
            v381_model = self.load_model("v3.8.1", track)
            
            if v38_model is None or v381_model is None:
                print(f"  [跳過] 缺少模型檔案")
                continue
            
            # 載入測試數據
            test_df = self.load_test_data(track)
            
            if test_df is None or test_df.empty:
                print(f"  [跳過] 無測試數據")
                continue
            
            # v3.8 預測
            v38_pred = self.predict_with_model(v38_model, test_df.copy(), "v3.8")
            v38_metrics = self.calculate_metrics(v38_pred)
            
            # v3.8.1 預測
            v381_pred = self.predict_with_model(v381_model, test_df.copy(), "v3.8.1")
            v381_metrics = self.calculate_metrics(v381_pred)
            
            if v38_metrics and v381_metrics:
                comparison_results.append({
                    'track': track,
                    'v38_pred': v38_pred,
                    'v381_pred': v381_pred,
                    'v38_metrics': v38_metrics,
                    'v381_metrics': v381_metrics,
                })
                
                print(f"  ✅ v3.8  MAE: {v38_metrics['mae']:.3f}s, Top5: {v38_metrics['top5_accuracy']:.1%}")
                print(f"  ✅ v3.8.1 MAE: {v381_metrics['mae']:.3f}s, Top5: {v381_metrics['top5_accuracy']:.1%}")
        
        return comparison_results
    
    def generate_markdown_report(self, comparison_results):
        """生成 Markdown 報告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md = []
        md.append("# v3.8 vs v3.8.1 詳細性能對比報告")
        md.append("")
        md.append(f"**生成時間**: {timestamp}")
        md.append("")
        md.append("---")
        md.append("")
        
        # ========== 總體性能摘要 ==========
        md.append("## 📊 總體性能摘要")
        md.append("")
        
        # 計算平均值
        v38_mae_avg = np.mean([r['v38_metrics']['mae'] for r in comparison_results])
        v381_mae_avg = np.mean([r['v381_metrics']['mae'] for r in comparison_results])
        v38_top5_avg = np.mean([r['v38_metrics']['top5_accuracy'] for r in comparison_results])
        v381_top5_avg = np.mean([r['v381_metrics']['top5_accuracy'] for r in comparison_results])
        v38_spearman_avg = np.mean([r['v38_metrics']['spearman_corr'] for r in comparison_results])
        v381_spearman_avg = np.mean([r['v381_metrics']['spearman_corr'] for r in comparison_results])
        
        mae_improvement = ((v381_mae_avg - v38_mae_avg) / v38_mae_avg) * 100
        top5_improvement = ((v381_top5_avg - v38_top5_avg) / v38_top5_avg) * 100
        spearman_improvement = ((v381_spearman_avg - v38_spearman_avg) / v38_spearman_avg) * 100
        
        md.append("| 指標 | v3.8 (17特徵) | v3.8.1 (19特徵) | 改善 |")
        md.append("|------|---------------|-----------------|------|")
        md.append(f"| **平均 MAE** | {v38_mae_avg:.3f}s | {v381_mae_avg:.3f}s | {mae_improvement:+.2f}% |")
        md.append(f"| **平均 Top5 準確度** | {v38_top5_avg:.1%} | {v381_top5_avg:.1%} | {top5_improvement:+.2f}% |")
        md.append(f"| **平均 Spearman 相關** | {v38_spearman_avg:.3f} | {v381_spearman_avg:.3f} | {spearman_improvement:+.2f}% |")
        md.append("")
        
        # ========== 逐賽道性能對比 ==========
        md.append("## 🏁 逐賽道性能對比")
        md.append("")
        
        md.append("| 賽道 | v3.8 MAE | v3.8.1 MAE | 改善 | v3.8 Top5 | v3.8.1 Top5 | 改善 | v3.8 Spearman | v3.8.1 Spearman |")
        md.append("|------|----------|------------|------|-----------|-------------|------|---------------|-----------------|")
        
        for result in comparison_results:
            track = result['track']
            v38_m = result['v38_metrics']
            v381_m = result['v381_metrics']
            
            mae_diff = ((v381_m['mae'] - v38_m['mae']) / v38_m['mae']) * 100
            top5_diff = ((v381_m['top5_accuracy'] - v38_m['top5_accuracy']) / v38_m['top5_accuracy']) * 100 if v38_m['top5_accuracy'] > 0 else 0
            
            md.append(f"| {track} | {v38_m['mae']:.3f}s | {v381_m['mae']:.3f}s | {mae_diff:+.1f}% | {v38_m['top5_accuracy']:.0%} | {v381_m['top5_accuracy']:.0%} | {top5_diff:+.1f}% | {v38_m['spearman_corr']:.3f} | {v381_m['spearman_corr']:.3f} |")
        
        md.append("")
        
        # ========== 逐賽道詳細預測結果 ==========
        md.append("## 📋 逐賽道詳細預測結果")
        md.append("")
        
        for result in comparison_results:
            track = result['track']
            v38_pred = result['v38_pred']
            v381_pred = result['v381_pred']
            
            md.append(f"### {track}")
            md.append("")
            
            # 合併兩版本的預測結果
            merged = v38_pred.merge(
                v381_pred[['driver', 'pred_time', 'pred_rank', 'rank_diff']],
                on='driver',
                suffixes=('_v38', '_v381')
            )
            
            # 按實際排名排序
            merged = merged.sort_values('actual_rank').reset_index(drop=True)
            
            md.append("| 駕駛員 | 實際時間 | 實際排名 | v3.8 預測時間 | v3.8 預測排名 | v3.8 誤差 | v3.8.1 預測時間 | v3.8.1 預測排名 | v3.8.1 誤差 |")
            md.append("|--------|----------|----------|---------------|---------------|----------|-----------------|-----------------|-------------|")
            
            for _, row in merged.iterrows():
                actual_time = row['actual_q_time']
                actual_rank = row['actual_rank']
                
                v38_pred_time = row['pred_time_v38']
                v38_pred_rank = row['pred_rank_v38']
                v38_rank_diff = row['rank_diff_v38']
                v38_time_diff = v38_pred_time - actual_time
                
                v381_pred_time = row['pred_time_v381']
                v381_pred_rank = row['pred_rank_v381']
                v381_rank_diff = row['rank_diff_v381']
                v381_time_diff = v381_pred_time - actual_time
                
                md.append(f"| {row['driver']} | {actual_time:.2f}s | {actual_rank} | {v38_pred_time:.2f}s | {v38_pred_rank} | {v38_rank_diff:+d} ({v38_time_diff:+.2f}s) | {v381_pred_time:.2f}s | {v381_pred_rank} | {v381_rank_diff:+d} ({v381_time_diff:+.2f}s) |")
            
            md.append("")
        
        # ========== 排名準確度分析 ==========
        md.append("## 🎯 排名準確度分析")
        md.append("")
        
        md.append("| 賽道 | v3.8 精確 | v3.8 ±1 | v3.8 ±2 | v3.8.1 精確 | v3.8.1 ±1 | v3.8.1 ±2 |")
        md.append("|------|-----------|---------|---------|-------------|-----------|-----------|")
        
        for result in comparison_results:
            track = result['track']
            v38_m = result['v38_metrics']
            v381_m = result['v381_metrics']
            
            md.append(f"| {track} | {v38_m['exact_rank']:.0%} | {v38_m['within_1']:.0%} | {v38_m['within_2']:.0%} | {v381_m['exact_rank']:.0%} | {v381_m['within_1']:.0%} | {v381_m['within_2']:.0%} |")
        
        md.append("")
        
        # ========== 特徵重要性對比 ==========
        md.append("## 🔍 特徵重要性對比")
        md.append("")
        
        # 使用第一個賽道作為範例
        sample_track = comparison_results[0]['track']
        v38_result = self.v38_results['results'][sample_track]
        v381_result = self.v381_results['results'][sample_track]
        
        v38_importance = v38_result.get('feature_importance', {})
        v381_importance = v381_result.get('feature_importance', {})
        
        md.append(f"**範例賽道**: {sample_track}")
        md.append("")
        
        md.append("### v3.8 Top 10 特徵")
        md.append("")
        md.append("| 排名 | 特徵 | 重要性 |")
        md.append("|------|------|--------|")
        
        top_v38 = sorted(v38_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (feat, imp) in enumerate(top_v38, 1):
            md.append(f"| {i} | {feat} | {imp*100:.2f}% |")
        
        md.append("")
        
        md.append("### v3.8.1 Top 10 特徵")
        md.append("")
        md.append("| 排名 | 特徵 | 重要性 |")
        md.append("|------|------|--------|")
        
        top_v381 = sorted(v381_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (feat, imp) in enumerate(top_v381, 1):
            marker = "✨" if feat in ['driver_historical_track_performance', 'driver_track_performance_gap'] else ""
            md.append(f"| {i} | {feat} {marker} | {imp*100:.2f}% |")
        
        md.append("")
        
        # ========== 結論 ==========
        md.append("## 📝 結論")
        md.append("")
        
        if mae_improvement < 0:
            md.append(f"✅ **v3.8.1 MAE 改善**: 從 {v38_mae_avg:.3f}s 降至 {v381_mae_avg:.3f}s ({mae_improvement:.2f}%)")
        else:
            md.append(f"⚠️ **v3.8.1 MAE 變化**: 從 {v38_mae_avg:.3f}s 變為 {v381_mae_avg:.3f}s ({mae_improvement:+.2f}%)")
        
        if top5_improvement > 0:
            md.append(f"✅ **v3.8.1 Top5 準確度提升**: 從 {v38_top5_avg:.1%} 提升至 {v381_top5_avg:.1%} ({top5_improvement:+.2f}%)")
        else:
            md.append(f"⚠️ **v3.8.1 Top5 準確度變化**: 從 {v38_top5_avg:.1%} 變為 {v381_top5_avg:.1%} ({top5_improvement:+.2f}%)")
        
        md.append("")
        md.append("### 新增特徵效果")
        md.append("")
        
        # 檢查新特徵的重要性
        new_feature_importance = {
            'driver_historical_track_performance': v381_importance.get('driver_historical_track_performance', 0),
            'driver_track_performance_gap': v381_importance.get('driver_track_performance_gap', 0),
        }
        
        for feat, imp in new_feature_importance.items():
            rank = sorted(v381_importance.items(), key=lambda x: x[1], reverse=True)
            rank_position = [i for i, (f, _) in enumerate(rank, 1) if f == feat][0]
            md.append(f"- **{feat}**: {imp*100:.2f}% (第 {rank_position} 名)")
        
        md.append("")
        md.append("---")
        md.append("")
        md.append("*報告生成器: compare_v38_v381_detailed_report.py*")
        
        return "\n".join(md)
    
    def run(self):
        """執行完整比較流程"""
        print("="*80)
        print("v3.8 vs v3.8.1 詳細性能對比報告生成器")
        print("="*80)
        
        # 載入訓練結果
        if not self.load_results():
            return
        
        # 比較賽道
        comparison_results = self.compare_tracks()
        
        if not comparison_results:
            print("\n[錯誤] 沒有可比較的結果")
            return
        
        # 生成報告
        print("\n[生成報告]")
        markdown_report = self.generate_markdown_report(comparison_results)
        
        # 保存報告
        report_file = Path("v38_v381_detailed_comparison_report.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"✅ 報告已保存: {report_file}")
        print("\n" + "="*80)


def main():
    reporter = DetailedComparisonReporter()
    reporter.run()


if __name__ == '__main__':
    main()
