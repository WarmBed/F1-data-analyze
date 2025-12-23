#!/usr/bin/env python3
"""
v3.8 vs v3.8.1 完整性能對比分析

功能:
1. 比較 v3.8 (17特徵) vs v3.8.1 (19特徵) 的訓練性能
2. 生成每個賽道、每位駕駛員的 2025 年預測 vs 實際對比
3. 詳細特徵重要性對比
4. 輸出完整 Markdown 報告

數據來源:
- v3.8_training_results.json (訓練結果)
- v3.8.1_training_results.json (訓練結果)
- models/track_specific_v3.8/*.pkl (v3.8 模型)
- models/track_specific_v3.8.1/*.pkl (v3.8.1 模型)
- v3.7_2025_predictions.json (2025 年實際結果)
"""
import json
import pickle
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from scipy.stats import spearmanr


class V38vsV381Comparator:
    """v3.8 vs v3.8.1 完整比較器"""
    
    TRACKS = [
        "Japan", "Bahrain", "Saudi Arabia", "Monaco", "Canada",
        "Great Britain", "Hungary", "Netherlands", "Italy", "Azerbaijan"
    ]
    
    def __init__(self):
        self.v38_dir = Path("models/track_specific_v3.8")
        self.v381_dir = Path("models/track_specific_v3.8.1")
        self.v38_results = None
        self.v381_results = None
        self.actual_2025_data = None
        
    def load_all_data(self) -> bool:
        """載入所有必要數據"""
        print("📊 載入數據中...")
        
        # 1. 載入訓練結果
        v38_file = Path("v3.8_training_results.json")
        v381_file = Path("v3.8.1_training_results.json")
        
        if not v38_file.exists():
            print(f"❌ 找不到 {v38_file}")
            return False
        
        if not v381_file.exists():
            print(f"❌ 找不到 {v381_file}")
            return False
        
        with open(v38_file, 'r', encoding='utf-8') as f:
            self.v38_results = json.load(f)
        
        with open(v381_file, 'r', encoding='utf-8') as f:
            self.v381_results = json.load(f)
        
        print(f"✅ 訓練結果載入完成")
        
        # 2. 載入 2025 年實際結果
        actual_file = Path("v3.7_2025_predictions.json")
        if not actual_file.exists():
            print(f"⚠️  找不到 2025 年實際數據: {actual_file}")
            return False
        
        with open(actual_file, 'r', encoding='utf-8') as f:
            self.actual_2025_data = json.load(f)
        
        print(f"✅ 2025 年實際數據載入完成")
        
        return True
    
    def load_model(self, version: str, track: str) -> Dict[str, Any]:
        """載入模型"""
        model_dir = Path(f"models/track_specific_{version}")
        
        # 處理賽道名稱中的空格
        track_filename = track.replace(" ", "_")
        model_file = model_dir / f"{track_filename}.pkl"
        
        if not model_file.exists():
            # 嘗試原始名稱
            model_file = model_dir / f"{track}.pkl"
            if not model_file.exists():
                print(f"⚠️  找不到模型: {model_file}")
                return None
        
        with open(model_file, 'rb') as f:
            return pickle.load(f)
    
    def predict_2025(self, model_data: Dict, track: str) -> pd.DataFrame:
        """為 2025 年生成預測"""
        if model_data is None:
            return None
        
        # 從 actual_2025_data 獲取該賽道的實際結果
        if track not in self.actual_2025_data:
            print(f"⚠️  找不到 {track} 的 2025 年數據")
            return None
        
        track_data = self.actual_2025_data[track]
        
        # 需要從特徵數據重建輸入
        # 這裡我們使用 TrackSpecificTrainerV3 來獲取 2025 年的特徵
        try:
            sys.path.append(str(Path.cwd()))
            from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3
            
            trainer = TrackSpecificTrainerV3()
            df = trainer.prepare_data_for_track(track, 2022, 2025)
            
            if df is None or df.empty:
                print(f"⚠️  {track} 無法載入特徵數據")
                return None
            
            # 篩選 2025 年數據
            df_2025 = df[df['year'] == 2025].copy()
            
            if df_2025.empty:
                print(f"⚠️  {track} 沒有 2025 年數據")
                return None
            
            # 使用模型預測
            model = model_data['model']
            feature_names = model_data['feature_names']
            
            X_2025 = df_2025[feature_names]
            y_pred = model.predict(X_2025)
            
            # 構建結果 DataFrame
            result_df = pd.DataFrame({
                'driver': df_2025['driver'].values,
                'actual_q_time': df_2025['actual_q_time'].values,
                'predicted_time': y_pred
            })
            
            # 計算排名
            result_df['actual_rank'] = result_df['actual_q_time'].rank(method='min').astype(int)
            result_df['predicted_rank'] = result_df['predicted_time'].rank(method='min').astype(int)
            result_df['rank_diff'] = abs(result_df['predicted_rank'] - result_df['actual_rank'])
            result_df['time_error'] = abs(result_df['predicted_time'] - result_df['actual_q_time'])
            
            return result_df
            
        except Exception as e:
            print(f"❌ {track} 預測失敗: {str(e)}")
            return None
    
    def compare_track(self, track: str) -> Dict[str, Any]:
        """比較單個賽道的兩個版本"""
        print(f"\n🏁 分析 {track}...")
        
        # 載入模型
        v38_model = self.load_model("v3.8", track)
        v381_model = self.load_model("v3.8.1", track)
        
        if v38_model is None or v381_model is None:
            print(f"⚠️  {track} 模型載入失敗")
            return None
        
        # 生成 2025 年預測
        v38_pred = self.predict_2025(v38_model, track)
        v381_pred = self.predict_2025(v381_model, track)
        
        if v38_pred is None or v381_pred is None:
            print(f"⚠️  {track} 預測生成失敗")
            return None
        
        # 訓練性能對比
        track_key = track.replace(" ", "_")
        v38_train = self.v38_results['results'].get(track_key, {})
        v381_train = self.v381_results['results'].get(track_key, {})
        
        # 計算 2025 預測性能
        v38_mae = v38_pred['time_error'].mean()
        v381_mae = v381_pred['time_error'].mean()
        
        v38_rank_error = v38_pred['rank_diff'].mean()
        v381_rank_error = v381_pred['rank_diff'].mean()
        
        # 特徵重要性對比
        v38_importance = v38_train.get('feature_importance', {})
        v381_importance = v381_train.get('feature_importance', {})
        
        return {
            'track': track,
            'training': {
                'v38': {
                    'cv_mae': v38_train.get('cv_mae'),
                    'train_mae': v38_train.get('train_mae'),
                    'r2': v38_train.get('train_r2')
                },
                'v381': {
                    'cv_mae': v381_train.get('cv_mae'),
                    'train_mae': v381_train.get('train_mae'),
                    'r2': v381_train.get('train_r2')
                }
            },
            'prediction_2025': {
                'v38': {
                    'mae': v38_mae,
                    'rank_error': v38_rank_error,
                    'predictions': v38_pred.to_dict('records')
                },
                'v381': {
                    'mae': v381_mae,
                    'rank_error': v381_rank_error,
                    'predictions': v381_pred.to_dict('records')
                }
            },
            'feature_importance': {
                'v38': v38_importance,
                'v381': v381_importance
            }
        }
    
    def generate_markdown_report(self, comparison_results: List[Dict]) -> str:
        """生成 Markdown 報告"""
        report = []
        
        # 標題
        report.append("# v3.8 vs v3.8.1 完整性能對比報告\n")
        report.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**對比版本**: v3.8 (17特徵) vs v3.8.1 (19特徵)\n")
        report.append("---\n\n")
        
        # 執行摘要
        report.append("## 執行摘要\n\n")
        
        # 統計總體改善
        v38_total_cv_mae = []
        v381_total_cv_mae = []
        v38_total_pred_mae = []
        v381_total_pred_mae = []
        
        for result in comparison_results:
            if result is None:
                continue
            v38_total_cv_mae.append(result['training']['v38']['cv_mae'])
            v381_total_cv_mae.append(result['training']['v381']['cv_mae'])
            v38_total_pred_mae.append(result['prediction_2025']['v38']['mae'])
            v381_total_pred_mae.append(result['prediction_2025']['v381']['mae'])
        
        avg_v38_cv = np.mean(v38_total_cv_mae)
        avg_v381_cv = np.mean(v381_total_cv_mae)
        avg_v38_pred = np.mean(v38_total_pred_mae)
        avg_v381_pred = np.mean(v381_total_pred_mae)
        
        cv_improvement = ((avg_v38_cv - avg_v381_cv) / avg_v38_cv) * 100
        pred_improvement = ((avg_v38_pred - avg_v381_pred) / avg_v38_pred) * 100
        
        report.append("| 指標 | v3.8 | v3.8.1 | 改善 |\n")
        report.append("|------|------|--------|------|\n")
        report.append(f"| **平均 CV MAE** | {avg_v38_cv:.3f}s | {avg_v381_cv:.3f}s | {cv_improvement:+.1f}% |\n")
        report.append(f"| **平均 2025 預測 MAE** | {avg_v38_pred:.3f}s | {avg_v381_pred:.3f}s | {pred_improvement:+.1f}% |\n")
        report.append(f"| **特徵數量** | 17 | 19 | +2 |\n\n")
        
        # 逐賽道分析
        report.append("---\n\n")
        report.append("## 逐賽道詳細分析\n\n")
        
        for result in comparison_results:
            if result is None:
                continue
            
            track = result['track']
            report.append(f"### {track}\n\n")
            
            # 訓練性能對比
            report.append("#### 訓練性能對比\n\n")
            report.append("| 指標 | v3.8 | v3.8.1 | 差異 |\n")
            report.append("|------|------|--------|------|\n")
            
            v38_cv = result['training']['v38']['cv_mae']
            v381_cv = result['training']['v381']['cv_mae']
            cv_diff = v381_cv - v38_cv
            
            v38_r2 = result['training']['v38']['r2']
            v381_r2 = result['training']['v381']['r2']
            r2_diff = v381_r2 - v38_r2
            
            report.append(f"| CV MAE | {v38_cv:.3f}s | {v381_cv:.3f}s | {cv_diff:+.3f}s |\n")
            report.append(f"| R² | {v38_r2:.4f} | {v381_r2:.4f} | {r2_diff:+.4f} |\n\n")
            
            # 2025 預測性能
            report.append("#### 2025 年預測性能\n\n")
            report.append("| 指標 | v3.8 | v3.8.1 | 差異 |\n")
            report.append("|------|------|--------|------|\n")
            
            v38_pred_mae = result['prediction_2025']['v38']['mae']
            v381_pred_mae = result['prediction_2025']['v381']['mae']
            pred_mae_diff = v381_pred_mae - v38_pred_mae
            
            v38_rank_err = result['prediction_2025']['v38']['rank_error']
            v381_rank_err = result['prediction_2025']['v381']['rank_error']
            rank_err_diff = v381_rank_err - v38_rank_err
            
            report.append(f"| 時間誤差 MAE | {v38_pred_mae:.3f}s | {v381_pred_mae:.3f}s | {pred_mae_diff:+.3f}s |\n")
            report.append(f"| 排名誤差 | {v38_rank_err:.2f} | {v381_rank_err:.2f} | {rank_err_diff:+.2f} |\n\n")
            
            # 逐車手預測對比（Top 10）
            report.append("#### 逐車手預測對比\n\n")
            report.append("| 車手 | 實際時間 | 實際排名 | v3.8 預測 | v3.8 排名 | v3.8.1 預測 | v3.8.1 排名 |\n")
            report.append("|------|---------|---------|----------|---------|------------|------------|\n")
            
            v38_preds = {p['driver']: p for p in result['prediction_2025']['v38']['predictions']}
            v381_preds = {p['driver']: p for p in result['prediction_2025']['v381']['predictions']}
            
            # 按實際排名排序
            drivers = sorted(v38_preds.keys(), key=lambda d: v38_preds[d]['actual_rank'])
            
            for driver in drivers[:10]:  # 只顯示 Top 10
                v38_p = v38_preds[driver]
                v381_p = v381_preds[driver]
                
                report.append(f"| {driver} | {v38_p['actual_q_time']:.3f}s | {int(v38_p['actual_rank'])} | ")
                report.append(f"{v38_p['predicted_time']:.3f}s | {int(v38_p['predicted_rank'])} | ")
                report.append(f"{v381_p['predicted_time']:.3f}s | {int(v381_p['predicted_rank'])} |\n")
            
            report.append("\n")
            
            # 特徵重要性對比
            report.append("#### 特徵重要性 Top 5 對比\n\n")
            
            v38_imp = result['feature_importance']['v38']
            v381_imp = result['feature_importance']['v381']
            
            # v3.8 Top 5
            v38_top5 = sorted(v38_imp.items(), key=lambda x: x[1], reverse=True)[:5]
            report.append("**v3.8 Top 5**:\n")
            for i, (feat, imp) in enumerate(v38_top5, 1):
                report.append(f"{i}. {feat}: {imp:.2f}%\n")
            report.append("\n")
            
            # v3.8.1 Top 5
            v381_top5 = sorted(v381_imp.items(), key=lambda x: x[1], reverse=True)[:5]
            report.append("**v3.8.1 Top 5**:\n")
            for i, (feat, imp) in enumerate(v381_top5, 1):
                marker = " ✨" if feat in ['driver_track_performance_gap', 'driver_historical_track_performance'] else ""
                report.append(f"{i}. {feat}: {imp:.2f}%{marker}\n")
            report.append("\n")
            
            # 新特徵表現
            new_features = ['driver_track_performance_gap', 'driver_historical_track_performance']
            new_feat_found = False
            report.append("**新特徵表現**:\n")
            for feat in new_features:
                if feat in v381_imp:
                    new_feat_found = True
                    rank = sorted(v381_imp.items(), key=lambda x: x[1], reverse=True)
                    rank_pos = [f for f, _ in rank].index(feat) + 1
                    report.append(f"- {feat}: {v381_imp[feat]:.2f}% (第 {rank_pos} 名)\n")
            
            if not new_feat_found:
                report.append("- 新特徵未進入主要貢獻者\n")
            
            report.append("\n---\n\n")
        
        return ''.join(report)
    
    def run(self):
        """執行完整比較分析"""
        print("=" * 60)
        print("v3.8 vs v3.8.1 完整性能對比分析")
        print("=" * 60)
        
        # 載入數據
        if not self.load_all_data():
            print("❌ 數據載入失敗")
            return
        
        # 比較所有賽道
        comparison_results = []
        for track in self.TRACKS:
            result = self.compare_track(track)
            comparison_results.append(result)
        
        # 生成報告
        print("\n📝 生成報告中...")
        report = self.generate_markdown_report(comparison_results)
        
        # 儲存報告
        output_file = Path("v38_vs_v381_detailed_comparison_report.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 報告已生成: {output_file}")
        print("=" * 60)


if __name__ == "__main__":
    comparator = V38vsV381Comparator()
    comparator.run()
