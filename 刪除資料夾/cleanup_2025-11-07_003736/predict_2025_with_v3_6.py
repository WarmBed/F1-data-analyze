"""
v3.6 模型 2025 賽季預測腳本
使用訓練好的 v3.6 賽道專家模型對 2025 賽季進行預測並生成 Top5 分析報告
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from scipy.stats import spearmanr

from CLI_modules.cli.trainer.track_specific_trainer_v3 import TrackSpecificTrainerV3


class V36Predictor:
    """v3.6 模型預測器"""
    
    def __init__(self, models_dir: str = "models/v3.6"):
        self.models_dir = models_dir
        self.models = {}
        self.base_trainer = TrackSpecificTrainerV3()
        
    def load_all_models(self) -> Dict[str, dict]:
        """載入所有已訓練的 v3.6 模型"""
        if not os.path.exists(self.models_dir):
            print(f"❌ 模型目錄不存在: {self.models_dir}")
            return {}
        
        model_files = [f for f in os.listdir(self.models_dir) if f.endswith('.pkl')]
        
        for model_file in model_files:
            track_name = model_file.replace('.pkl', '')
            model_path = os.path.join(self.models_dir, model_file)
            
            try:
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                self.models[track_name] = model_data
                print(f"✅ 載入模型: {track_name}")
            except Exception as e:
                print(f"❌ 載入失敗 {track_name}: {e}")
        
        print(f"\n📊 已載入 {len(self.models)} 個模型")
        return self.models
    
    def predict_race(self, year: int, race: str, session: str = 'R') -> Tuple[pd.DataFrame, Dict]:
        """
        預測單場賽事
        
        Returns:
            predictions_df: 包含預測結果的 DataFrame
            metrics: 評估指標字典
        """
        # 檢查模型是否存在
        if race not in self.models:
            print(f"❌ {race} 模型不存在")
            return None, None
        
        model_data = self.models[race]
        model = model_data['model']
        feature_names = model_data['feature_names']
        
        # 載入 FP3 數據進行預測
        try:
            fp3_data = self.base_trainer.load_training_data_v3(
                track_name=race,
                start_year=year,
                end_year=year
            )
            
            if fp3_data.empty:
                print(f"❌ {race} {year} 無 FP3 數據")
                return None, None
            
            # 提取特徵
            X_pred = fp3_data[feature_names].values
            drivers = fp3_data['driver'].values
            
            # 預測
            y_pred = model.predict(X_pred)
            
            # 創建預測 DataFrame
            predictions_df = pd.DataFrame({
                'driver': drivers,
                'predicted_time': y_pred,
                'predicted_rank': pd.Series(y_pred).rank().values
            })
            
            # 如果有實際結果，計算誤差
            if 'actual_q_time' in fp3_data.columns:
                predictions_df['actual_time'] = fp3_data['actual_q_time'].values
                predictions_df['actual_rank'] = fp3_data['actual_q_time'].rank().values
                predictions_df['time_error'] = predictions_df['predicted_time'] - predictions_df['actual_time']
                predictions_df['time_error_pct'] = (predictions_df['time_error'] / predictions_df['actual_time'] * 100).abs()
                predictions_df['rank_error'] = (predictions_df['predicted_rank'] - predictions_df['actual_rank']).abs()
                
                # 計算評估指標
                mae = predictions_df['time_error'].abs().mean()
                spearman, _ = spearmanr(predictions_df['actual_rank'], predictions_df['predicted_rank'])
                
                # Top5 準確率
                actual_top5 = set(predictions_df.nsmallest(5, 'actual_time')['driver'])
                predicted_top5 = set(predictions_df.nsmallest(5, 'predicted_time')['driver'])
                top5_correct = len(actual_top5 & predicted_top5)
                top5_accuracy = top5_correct / 5 * 100
                
                metrics = {
                    'mae': mae,
                    'spearman': spearman,
                    'top5_accuracy': top5_accuracy,
                    'top5_correct': top5_correct,
                    'has_actual': True
                }
            else:
                metrics = {'has_actual': False}
            
            # 排序
            predictions_df = predictions_df.sort_values('predicted_time')
            
            return predictions_df, metrics
            
        except Exception as e:
            print(f"❌ 預測失敗 {race}: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def predict_all_2025_races(self) -> Dict:
        """預測 2025 所有賽事"""
        races_2025 = [
            'Bahrain', 'Saudi_Arabia', 'Japan', 'Monaco', 'Canada',
            'Great_Britain', 'Hungary', 'Netherlands', 'Italy', 'Azerbaijan'
        ]
        
        results = {}
        
        for race in races_2025:
            if race not in self.models:
                print(f"\n⏭️  跳過 {race} (模型不存在)")
                continue
            
            print(f"\n{'='*60}")
            print(f"🏁 預測 {race}")
            print('='*60)
            
            predictions_df, metrics = self.predict_race(2025, race, 'R')
            
            if predictions_df is not None:
                results[race] = {
                    'predictions': predictions_df,
                    'metrics': metrics
                }
                
                # 顯示 Top5 預測
                print("\n🏆 預測 Top 5:")
                top5 = predictions_df.head(5)
                for idx, row in top5.iterrows():
                    actual_str = ""
                    if 'actual_time' in row:
                        actual_str = f" | 實際: {row['actual_time']:.3f}s (第{int(row['actual_rank'])})"
                    print(f"  {int(row['predicted_rank'])}. {row['driver']}: {row['predicted_time']:.3f}s{actual_str}")
                
                # 顯示評估指標
                if metrics['has_actual']:
                    print(f"\n📊 評估指標:")
                    print(f"  MAE: {metrics['mae']:.3f}s")
                    print(f"  Spearman: {metrics['spearman']:.3f}")
                    print(f"  Top5 準確率: {metrics['top5_accuracy']:.1f}% ({metrics['top5_correct']}/5)")
        
        return results
    
    def generate_report(self, results: Dict, output_path: str = None):
        """生成詳細分析報告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"V3.6_2025_TOP5_ANALYSIS_REPORT_{timestamp}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# v3.6 2025 賽季 Top5 預測分析報告\n\n")
            f.write(f"**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**模型版本**: v3.6 (Optuna 優化賽道專家模型)\n")
            f.write(f"**分析賽事**: {len(results)} 場\n\n")
            f.write("---\n\n")
            
            # 整體統計
            f.write("## 📊 整體統計\n\n")
            
            races_with_actual = {k: v for k, v in results.items() if v['metrics']['has_actual']}
            
            if races_with_actual:
                total_correct = sum(v['metrics']['top5_correct'] for v in races_with_actual.values())
                total_possible = len(races_with_actual) * 5
                overall_accuracy = total_correct / total_possible * 100
                
                avg_mae = np.mean([v['metrics']['mae'] for v in races_with_actual.values()])
                avg_spearman = np.mean([v['metrics']['spearman'] for v in races_with_actual.values()])
                
                f.write("| 指標 | 數值 |\n")
                f.write("|------|------|\n")
                f.write(f"| **Top5 準確率** | **{overall_accuracy:.1f}%** ({total_correct}/{total_possible}) |\n")
                f.write(f"| **平均 MAE** | {avg_mae:.3f}s |\n")
                f.write(f"| **平均 Spearman** | {avg_spearman:.3f} |\n")
                f.write(f"| **分析賽事** | {len(races_with_actual)} 場 |\n\n")
            
            # 各賽道詳細分析
            f.write("## 🏎️ 各賽道詳細分析\n\n")
            
            for race, data in sorted(results.items()):
                f.write(f"### {race}\n\n")
                
                predictions = data['predictions']
                metrics = data['metrics']
                
                # Top5 預測 vs 實際
                f.write("**預測 Top5:**\n\n")
                f.write("| 排名 | 車手 | 預測時間 | 實際時間 | 實際排名 | 時間誤差 | 誤差% |\n")
                f.write("|------|------|----------|----------|----------|----------|-------|\n")
                
                top5_pred = predictions.head(5)
                for _, row in top5_pred.iterrows():
                    if 'actual_time' in row:
                        f.write(f"| {int(row['predicted_rank'])} | {row['driver']} | "
                               f"{row['predicted_time']:.3f}s | {row['actual_time']:.3f}s | "
                               f"{int(row['actual_rank'])} | {row['time_error']:.3f}s | "
                               f"{row['time_error_pct']:.2f}% |\n")
                    else:
                        f.write(f"| {int(row['predicted_rank'])} | {row['driver']} | "
                               f"{row['predicted_time']:.3f}s | - | - | - | - |\n")
                
                # 評估指標
                if metrics['has_actual']:
                    f.write(f"\n**評估指標:**\n\n")
                    f.write(f"- MAE: {metrics['mae']:.3f}s\n")
                    f.write(f"- Spearman: {metrics['spearman']:.3f}\n")
                    f.write(f"- Top5 準確率: {metrics['top5_accuracy']:.1f}% ({metrics['top5_correct']}/5)\n")
                
                f.write("\n---\n\n")
            
            # v3.5 比較（如果有舊報告）
            f.write("## 📈 v3.5 vs v3.6 比較\n\n")
            f.write("*需要載入 v3.5 結果進行比較*\n\n")
        
        print(f"\n✅ 報告已生成: {output_path}")
        return output_path


def main():
    """主程式"""
    print("="*60)
    print("🏎️  v3.6 2025 賽季預測器")
    print("="*60)
    
    # 創建預測器
    predictor = V36Predictor()
    
    # 載入模型
    print("\n📦 載入訓練好的模型...")
    predictor.load_all_models()
    
    if not predictor.models:
        print("❌ 沒有可用的模型，請先完成訓練")
        return
    
    # 預測 2025 賽季
    print("\n🔮 開始預測 2025 賽季...")
    results = predictor.predict_all_2025_races()
    
    # 生成報告
    print("\n📝 生成分析報告...")
    report_path = predictor.generate_report(results)
    
    print("\n" + "="*60)
    print("✅ 預測完成!")
    print("="*60)
    print(f"📄 報告: {report_path}")


if __name__ == "__main__":
    main()
