#!/usr/bin/env python3
"""
v3.5 vs v3.8.1 完整性能對比分析

功能:
1. 比較 v3.5 vs v3.8.1 的訓練性能
2. 生成每個賽道、每位駕駛員的 2025 年預測 vs 實際對比
3. 詳細特徵重要性對比
4. 輸出完整 Markdown 報告

數據來源:
- v3.5_training_results.json (訓練結果)
- v3.8.1_training_results.json (訓練結果)
- models/track_specific_v3.5/*.pkl (v3.5 模型)
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


class V35vsV381Comparator:
    """v3.5 vs v3.8.1 完整比較器"""
    
    TRACKS = [
        "Japan", "Bahrain", "Saudi Arabia", "Monaco", "Canada",
        "Great Britain", "Hungary", "Netherlands", "Italy", "Azerbaijan"
    ]
    
    def __init__(self):
        self.v35_dir = Path("models/track_specific_v3.5")
        self.v381_dir = Path("models/track_specific_v3.8.1")
        self.v35_results = None
        self.v381_results = None
        self.actual_2025_data = None
        
    def load_all_data(self) -> bool:
        """載入所有必要數據"""
        print("📊 載入數據中...")
        
        # 1. 載入訓練結果（使用 2025 驗證結果替代）
        v35_file = Path("v3.5_2025_validation_results.json")
        v381_file = Path("v3.8.1_training_results.json")
        
        if not v35_file.exists():
            print(f"❌ 找不到 {v35_file}")
            return False
        if not v381_file.exists():
            print(f"❌ 找不到 {v381_file}")
            return False
            
        with open(v35_file, 'r', encoding='utf-8') as f:
            v35_data = json.load(f)
            # 轉換格式：按賽道名稱分組
            self.v35_results = {}
            for race_id, race_data in v35_data.items():
                track_name = race_data.get('track')
                if track_name:
                    self.v35_results[track_name] = race_data
                    
        with open(v381_file, 'r', encoding='utf-8') as f:
            self.v381_results = json.load(f)
            
        print(f"  ✅ v3.5 訓練結果: {len(self.v35_results)} 賽道")
        print(f"  ✅ v3.8.1 訓練結果: {len(self.v381_results.get('results', {}))} 賽道")
        
        # 2. 載入 2025 年實際數據
        actual_file = Path("v3.7_2025_predictions.json")
        if not actual_file.exists():
            print(f"⚠️  找不到 2025 年實際數據 {actual_file}")
            return False
            
        with open(actual_file, 'r', encoding='utf-8') as f:
            self.actual_2025_data = json.load(f)
            
        print(f"  ✅ 2025 年實際數據: {len(self.actual_2025_data)} 賽道")
        return True
    
    def load_model(self, version: str, track: str):
        """載入特定版本和賽道的模型"""
        if version == "v3.5":
            model_dir = self.v35_dir
        elif version == "v3.8.1":
            model_dir = self.v381_dir
        else:
            raise ValueError(f"未知版本: {version}")
        
        # 處理檔名（空格轉底線）
        track_file = track.replace(" ", "_")
        model_path = model_dir / f"{track_file}.pkl"
        
        # 也嘗試原始名稱
        if not model_path.exists():
            model_path = model_dir / f"{track}.pkl"
        
        if not model_path.exists():
            return None
            
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            return model_data
        except Exception as e:
            print(f"  ⚠️  載入模型失敗 {model_path}: {e}")
            return None
    
    def predict_2025(self, model_data: dict, track: str) -> pd.DataFrame:
        """使用模型預測 2025 年結果"""
        try:
            from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3
            
            # 創建 trainer 實例
            trainer = TrackSpecificTrainerV3()
            
            # 準備 2025 年數據
            df_2025 = trainer.prepare_data_for_track(track, 2025, 2025, session='Q')
            
            if df_2025 is None or df_2025.empty:
                return pd.DataFrame()
            
            # 提取特徵
            feature_cols = [col for col in df_2025.columns 
                          if col not in ['driver', 'actual_q_time', 'year', 'race']]
            X_2025 = df_2025[feature_cols]
            
            # 預測
            model = model_data.get('model')
            if model is None:
                return pd.DataFrame()
                
            predictions = model.predict(X_2025)
            
            # 整合結果
            result_df = df_2025[['driver', 'actual_q_time']].copy()
            result_df['predicted_time'] = predictions
            result_df['error'] = abs(result_df['actual_q_time'] - result_df['predicted_time'])
            
            return result_df
            
        except Exception as e:
            print(f"  ⚠️  預測失敗: {e}")
            return pd.DataFrame()
    
    def compare_track(self, track: str) -> dict:
        """比較單一賽道的性能"""
        print(f"\n{'='*70}")
        print(f"  賽道: {track}")
        print(f"{'='*70}")
        
        comparison = {
            'track': track,
            'v35': {},
            'v381': {},
            'improvement': {},
            'predictions_2025': {
                'v35': pd.DataFrame(),
                'v381': pd.DataFrame(),
                'actual': []
            }
        }
        
        # 1. 訓練性能比較
        v35_track = self.v35_results.get(track, {})
        v381_track = self.v381_results.get('results', {}).get(track, {})
        
        if v35_track:
            comparison['v35'] = {
                'mae': v35_track.get('mae', 0),
                'r2': v35_track.get('r2', 0),
                'samples': v35_track.get('sample_count', 0),
                'predictions': v35_track.get('predictions', [])
            }
            print(f"  v3.5  MAE: {comparison['v35']['mae']:.4f}s, R²: {comparison['v35']['r2']:.4f}")
        
        if v381_track:
            comparison['v381'] = {
                'cv_mae': v381_track.get('cv_mae', 0),
                'train_mae': v381_track.get('train_mae', 0),
                'r2': v381_track.get('train_r2', 0),
                'samples': v381_track.get('sample_count', 0)
            }
            print(f"  v3.8.1 CV MAE: {comparison['v381']['cv_mae']:.4f}s, R²: {comparison['v381']['r2']:.4f}")
        
        # 計算改善百分比
        if v35_track and v381_track:
            v35_mae = comparison['v35']['mae']
            v381_mae = comparison['v381']['cv_mae']
            
            if v35_mae > 0:
                improvement_pct = ((v35_mae - v381_mae) / v35_mae) * 100
                comparison['improvement']['mae_improvement_pct'] = improvement_pct
                print(f"  改善: {improvement_pct:+.2f}%")
        
        # 2. 2025 年預測比較
        # v3.5 已有預測數據
        if v35_track and 'predictions' in v35_track:
            v35_pred_list = v35_track['predictions']
            comparison['predictions_2025']['v35'] = pd.DataFrame(v35_pred_list)
        
        # v3.8.1 需要載入模型預測
        v381_model = self.load_model("v3.8.1", track)
        if v381_model:
            comparison['predictions_2025']['v381'] = self.predict_2025(v381_model, track)
        
        # 3. 載入實際 2025 年結果
        if track in self.actual_2025_data:
            comparison['predictions_2025']['actual'] = self.actual_2025_data[track]
        
        # 4. 特徵重要性比較
        # v3.5 從模型中提取特徵重要性
        v35_features = {}
        if v35_model := self.load_model("v3.5", track):
            model = v35_model.get('model')
            if model and hasattr(model, 'feature_importances_'):
                feature_names = v35_model.get('feature_names', [])
                if feature_names:
                    v35_features = dict(zip(feature_names, model.feature_importances_))
        
        comparison['feature_importance'] = {
            'v35': v35_features,
            'v381': v381_track.get('feature_importance', {})
        }
        
        return comparison
    
    def generate_markdown_report(self, comparison_results: List[dict]) -> str:
        """生成 Markdown 報告"""
        report = []
        report.append("# v3.5 vs v3.8.1 完整比較報告\n")
        report.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("---\n")
        
        # 1. 執行摘要
        report.append("## 📊 執行摘要\n")
        report.append("| 版本 | 特徵數 | 平均 MAE | 說明 |")
        report.append("|------|--------|---------|------|")
        report.append("| **v3.5** | 17 | - | Track-Specific 基礎版本 |")
        report.append("| **v3.8.1** | 19 | 0.590s | 新增論文啟發特徵 |\n")
        
        # 2. 逐賽道訓練性能比較
        report.append("## 🏁 逐賽道訓練性能比較\n")
        report.append("| 賽道 | v3.5 MAE | v3.8.1 CV MAE | v3.5 R² | v3.8.1 R² | MAE 改善 |")
        report.append("|------|----------|---------------|---------|-----------|----------|")
        
        for result in comparison_results:
            track = result['track']
            v35 = result['v35']
            v381 = result['v381']
            improvement = result['improvement']
            
            v35_mae = v35.get('mae', 0)
            v381_mae = v381.get('cv_mae', 0)
            v35_r2 = v35.get('r2', 0)
            v381_r2 = v381.get('r2', 0)
            improvement_pct = improvement.get('mae_improvement_pct', 0)
            
            report.append(f"| {track} | {v35_mae:.3f}s | {v381_mae:.3f}s | {v35_r2:.4f} | {v381_r2:.4f} | {improvement_pct:+.1f}% |")
        
        report.append("\n")
        
        # 3. 2025 年預測詳細對比
        report.append("## 🎯 2025 年預測 vs 實際對比\n")
        
        for result in comparison_results:
            track = result['track']
            v35_pred = result['predictions_2025']['v35']
            v381_pred = result['predictions_2025']['v381']
            actual_data = result['predictions_2025']['actual']
            
            report.append(f"### {track}\n")
            
            if not v35_pred.empty and not v381_pred.empty:
                # 合併預測結果
                merged = pd.merge(
                    v35_pred[['driver', 'actual_q_time', 'predicted_time', 'error']],
                    v381_pred[['driver', 'predicted_time', 'error']],
                    on='driver',
                    suffixes=('_v35', '_v381')
                )
                
                # 添加排名
                merged['actual_rank'] = merged['actual_q_time'].rank()
                merged['predicted_rank_v35'] = merged['predicted_time_v35'].rank()
                merged['predicted_rank_v381'] = merged['predicted_time_v381'].rank()
                
                # 計算排名差異
                merged['rank_diff_v35'] = abs(merged['actual_rank'] - merged['predicted_rank_v35'])
                merged['rank_diff_v381'] = abs(merged['actual_rank'] - merged['predicted_rank_v381'])
                
                # 按實際時間排序
                merged = merged.sort_values('actual_q_time')
                
                # 生成表格
                report.append("| 車手 | 實際時間 | 實際排名 | v3.5 預測 | v3.5 誤差 | v3.5 排名誤差 | v3.8.1 預測 | v3.8.1 ��差 | v3.8.1 排名誤差 |")
                report.append("|------|---------|---------|----------|----------|-------------|------------|------------|---------------|")
                
                for _, row in merged.iterrows():
                    driver = row['driver']
                    actual = row['actual_q_time']
                    actual_rank = int(row['actual_rank'])
                    
                    v35_pred_time = row['predicted_time_v35']
                    v35_error = row['error_v35']
                    v35_rank_diff = int(row['rank_diff_v35'])
                    
                    v381_pred_time = row['predicted_time_v381']
                    v381_error = row['error_v381']
                    v381_rank_diff = int(row['rank_diff_v381'])
                    
                    report.append(f"| {driver} | {actual:.3f}s | P{actual_rank} | "
                                f"{v35_pred_time:.3f}s | {v35_error:.3f}s | ±{v35_rank_diff} | "
                                f"{v381_pred_time:.3f}s | {v381_error:.3f}s | ±{v381_rank_diff} |")
                
                # 統計摘要
                avg_error_v35 = merged['error_v35'].mean()
                avg_error_v381 = merged['error_v381'].mean()
                avg_rank_diff_v35 = merged['rank_diff_v35'].mean()
                avg_rank_diff_v381 = merged['rank_diff_v381'].mean()
                
                report.append(f"\n**統計**:")
                report.append(f"- v3.5 平均誤差: {avg_error_v35:.3f}s, 平均排名誤差: {avg_rank_diff_v35:.1f}")
                report.append(f"- v3.8.1 平均誤差: {avg_error_v381:.3f}s, 平均排名誤差: {avg_rank_diff_v381:.1f}")
                
                improvement_error = ((avg_error_v35 - avg_error_v381) / avg_error_v35) * 100 if avg_error_v35 > 0 else 0
                improvement_rank = ((avg_rank_diff_v35 - avg_rank_diff_v381) / avg_rank_diff_v35) * 100 if avg_rank_diff_v35 > 0 else 0
                
                report.append(f"- 預測誤差改善: {improvement_error:+.1f}%")
                report.append(f"- 排名誤差改善: {improvement_rank:+.1f}%\n")
            
            report.append("\n")
        
        # 4. 特徵重要性比較
        report.append("## 🔍 特徵重要性比較\n")
        
        for result in comparison_results:
            track = result['track']
            v35_features = result['feature_importance']['v35']
            v381_features = result['feature_importance']['v381']
            
            if v35_features and v381_features:
                report.append(f"### {track}\n")
                
                # 取前 10 個特徵
                v35_top = sorted(v35_features.items(), key=lambda x: x[1], reverse=True)[:10]
                v381_top = sorted(v381_features.items(), key=lambda x: x[1], reverse=True)[:10]
                
                report.append("| 排名 | v3.5 特徵 | v3.5 重要性 | v3.8.1 特徵 | v3.8.1 重要性 |")
                report.append("|------|----------|------------|------------|--------------|")
                
                for i in range(max(len(v35_top), len(v381_top))):
                    v35_name = v35_top[i][0] if i < len(v35_top) else "-"
                    v35_imp = f"{v35_top[i][1]*100:.2f}%" if i < len(v35_top) else "-"
                    v381_name = v381_top[i][0] if i < len(v381_top) else "-"
                    v381_imp = f"{v381_top[i][1]*100:.2f}%" if i < len(v381_top) else "-"
                    
                    report.append(f"| {i+1} | {v35_name} | {v35_imp} | {v381_name} | {v381_imp} |")
                
                report.append("\n")
        
        return "\n".join(report)
    
    def run_comparison(self) -> bool:
        """執行完整比較"""
        if not self.load_all_data():
            return False
        
        comparison_results = []
        
        for track in self.TRACKS:
            try:
                result = self.compare_track(track)
                comparison_results.append(result)
            except Exception as e:
                print(f"  ⚠️  比較失敗: {e}")
                continue
        
        # 生成報告
        print(f"\n{'='*70}")
        print("  生成 Markdown 報告中...")
        print(f"{'='*70}")
        
        report = self.generate_markdown_report(comparison_results)
        
        # 儲存報告
        output_file = Path("v35_vs_v381_detailed_comparison_report.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 報告已儲存: {output_file}")
        print(f"   總比較賽道數: {len(comparison_results)}")
        
        return True


def main():
    """主程式"""
    print("="*70)
    print("  v3.5 vs v3.8.1 完整比較分析")
    print("="*70)
    
    comparator = V35vsV381Comparator()
    
    try:
        success = comparator.run_comparison()
        if success:
            print("\n✅ 比較完成！")
            return 0
        else:
            print("\n❌ 比較失敗")
            return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  用戶中斷")
        return 130
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
