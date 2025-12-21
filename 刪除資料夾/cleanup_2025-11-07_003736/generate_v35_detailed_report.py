#!/usr/bin/env python3
"""
v3.5 詳細分析報告生成器

生成內容:
1. 每場賽事的完整預測結果（所有車手）
2. 預測排名 vs 實際排名對比
3. 時間差異分析
4. 特徵重要性分析
5. 模型參數詳情
"""

import json
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from scipy.stats import spearmanr


class V35DetailedReportGenerator:
    """v3.5 詳細報告生成器"""
    
    def __init__(self):
        self.results_data = None
        self.models_dir = Path("models/track_specific_v3.5")
        self.race_mapping = {
            3: "Japan", 4: "Bahrain", 5: "Saudi Arabia", 8: "Monaco",
            10: "Canada", 12: "Great Britain", 14: "Hungary", 
            15: "Netherlands", 16: "Italy", 17: "Azerbaijan",
            18: "Singapore", 20: "Mexico"
        }
        
    def load_results(self, json_file: str = "v3.5_2025_validation_results.json"):
        """載入 v3.5 驗證結果"""
        json_path = Path(json_file)
        
        if not json_path.exists():
            print(f"⚠️  找不到結果檔案: {json_file}")
            return False
        
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # 轉換為列表格式
        if isinstance(raw_data, dict):
            self.results_data = []
            for race_num_str, race_data in raw_data.items():
                race_data['race_number'] = int(race_num_str)
                self.results_data.append(race_data)
        else:
            self.results_data = raw_data
        
        print(f"✓ 載入 {len(self.results_data)} 場賽事結果")
        return True
    
    def load_model_info(self, track_name: str) -> Dict:
        """載入模型資訊（特徵重要性、參數等）"""
        model_file = self.models_dir / f"{track_name}.pkl"
        
        if not model_file.exists():
            return None
        
        try:
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            
            # 獲取特徵重要性
            if hasattr(model, 'feature_importances_'):
                feature_importance = model.feature_importances_
                
                # v3.5 的 20 個特徵名稱
                feature_names = [
                    'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                    'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 
                    'max_speed',
                    's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                    'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
                    'track_avg_improvement_rate', 'adjusted_ideal_lap',
                    'fp3_relative_position', 'fp3_gap_to_fastest',
                    'is_top_driver', 'driver_historical_improvement'
                ]
                
                # 按重要性排序
                importance_dict = dict(zip(feature_names, feature_importance))
                sorted_importance = sorted(importance_dict.items(), 
                                          key=lambda x: x[1], reverse=True)
                
                return {
                    'feature_importance': sorted_importance,
                    'params': model.get_params() if hasattr(model, 'get_params') else {},
                    'n_features': len(feature_names)
                }
            
        except Exception as e:
            print(f"⚠️  載入模型失敗 {track_name}: {e}")
            return None
        
        return None
    
    def generate_race_detail_section(self, race_data: Dict) -> List[str]:
        """生成單場賽事詳細分析"""
        section = []
        
        race_num = race_data['race_number']
        track_name = race_data.get('track_name', self.race_mapping.get(race_num, f"Race {race_num}"))
        
        section.append(f"## Race #{race_num} - {track_name}\n")
        
        # 整體統計
        section.append("### 📊 整體統計\n")
        section.append(f"- **參賽車手數**: {race_data.get('sample_count', len(race_data['predictions']))}")
        section.append(f"- **MAE (平均絕對誤差)**: {race_data.get('mae', 0):.3f}s")
        section.append(f"- **R² (決定係數)**: {race_data.get('r2', 0):.4f}")
        section.append(f"- **Spearman 相關性**: {race_data.get('spearman', 0):.3f}")
        section.append(f"- **平均排名誤差**: {race_data.get('avg_rank_diff', 0):.2f} 位")
        section.append(f"- **Top5 正確預測**: {race_data.get('top5_correct', 0)}/5 ({race_data.get('top5_correct', 0)*20}%)\n")
        
        # 車手預測詳細表格
        section.append("### 🏎️ 車手預測詳細結果\n")
        section.append("| 排名 | 車手 | 實際圈速 | 預測圈速 | 時間差異 | 實際排名 | 預測排名 | 排名差異 |")
        section.append("|------|------|----------|----------|----------|----------|----------|----------|")
        
        # 按實際排名排序
        predictions = sorted(race_data['predictions'], key=lambda x: x['actual_rank'])
        
        for i, pred in enumerate(predictions, 1):
            driver = pred['driver']
            actual_time = pred['actual_q_time']
            pred_time = pred['predicted_time']
            time_diff = pred_time - actual_time
            actual_rank = int(pred['actual_rank'])
            pred_rank = int(pred['predicted_rank'])
            rank_diff = abs(pred_rank - actual_rank)
            
            # 時間差異顏色標記（用文字表示）
            time_marker = "✅" if abs(time_diff) < 0.5 else ("⚠️" if abs(time_diff) < 2.0 else "❌")
            rank_marker = "✅" if rank_diff == 0 else ("⚠️" if rank_diff <= 2 else "❌")
            
            section.append(
                f"| {i} | {driver} | {actual_time:.3f}s | {pred_time:.3f}s | "
                f"{time_marker} {time_diff:+.3f}s | {actual_rank} | {pred_rank} | "
                f"{rank_marker} {rank_diff} |"
            )
        
        section.append("\n**圖例**: ✅ 優秀 | ⚠️ 尚可 | ❌ 需改進\n")
        
        # Top5 分析
        section.append("### 🏆 Top5 預測分析\n")
        
        actual_top5 = sorted(predictions, key=lambda x: x['actual_rank'])[:5]
        pred_top5 = sorted(predictions, key=lambda x: x['predicted_rank'])[:5]
        
        section.append("**實際 Top5**:")
        for i, p in enumerate(actual_top5, 1):
            section.append(f"{i}. {p['driver']} - {p['actual_q_time']:.3f}s")
        
        section.append("\n**預測 Top5**:")
        for i, p in enumerate(pred_top5, 1):
            actual_rank = int(p['actual_rank'])
            marker = "✅" if actual_rank <= 5 else "❌"
            section.append(f"{i}. {p['driver']} - {p['predicted_time']:.3f}s {marker} (實際第{actual_rank})")
        
        section.append("")
        
        # 預測準確性分析
        section.append("### 📈 預測準確性分析\n")
        
        # 計算各個誤差區間的車手數
        time_diffs = [abs(p['predicted_time'] - p['actual_q_time']) for p in predictions]
        excellent = sum(1 for d in time_diffs if d < 0.5)
        good = sum(1 for d in time_diffs if 0.5 <= d < 2.0)
        poor = sum(1 for d in time_diffs if d >= 2.0)
        
        total = len(predictions)
        section.append(f"- **優秀預測** (誤差 < 0.5s): {excellent}/{total} ({excellent/total*100:.1f}%)")
        section.append(f"- **良好預測** (0.5s ≤ 誤差 < 2.0s): {good}/{total} ({good/total*100:.1f}%)")
        section.append(f"- **待改進** (誤差 ≥ 2.0s): {poor}/{total} ({poor/total*100:.1f}%)\n")
        
        # 最佳/最差預測
        best_pred = min(predictions, key=lambda x: abs(x['predicted_time'] - x['actual_q_time']))
        worst_pred = max(predictions, key=lambda x: abs(x['predicted_time'] - x['actual_q_time']))
        
        section.append(f"- **最佳預測**: {best_pred['driver']} (誤差 {abs(best_pred['predicted_time'] - best_pred['actual_q_time']):.3f}s)")
        section.append(f"- **最差預測**: {worst_pred['driver']} (誤差 {abs(worst_pred['predicted_time'] - worst_pred['actual_q_time']):.3f}s)\n")
        
        # 特徵重要性
        model_info = self.load_model_info(track_name)
        if model_info:
            section.append("### 🔍 特徵重要性分析\n")
            section.append("**Top 10 最重要特徵**:\n")
            section.append("| 排名 | 特徵名稱 | 重要性 | 佔比 |")
            section.append("|------|----------|--------|------|")
            
            total_importance = sum(imp for _, imp in model_info['feature_importance'])
            
            for rank, (feat_name, importance) in enumerate(model_info['feature_importance'][:10], 1):
                percentage = (importance / total_importance * 100) if total_importance > 0 else 0
                
                # 特徵名稱中文化
                feat_name_zh = self._translate_feature_name(feat_name)
                
                section.append(f"| {rank} | {feat_name_zh} | {importance:.4f} | {percentage:.2f}% |")
            
            section.append("\n**完整特徵重要性**:\n")
            section.append("| 特徵名稱 | 重要性 | 佔比 |")
            section.append("|----------|--------|------|")
            
            for feat_name, importance in model_info['feature_importance']:
                percentage = (importance / total_importance * 100) if total_importance > 0 else 0
                feat_name_zh = self._translate_feature_name(feat_name)
                section.append(f"| {feat_name_zh} | {importance:.4f} | {percentage:.2f}% |")
            
            section.append("")
        
        section.append("---\n")
        
        return section
    
    def _translate_feature_name(self, feat_name: str) -> str:
        """將特徵名稱翻譯為中文"""
        translations = {
            'ideal_s1': 'S1 理想時間',
            'ideal_s2': 'S2 理想時間',
            'ideal_s3': 'S3 理想時間',
            'ideal_lap': '單圈理想時間',
            'low_speed_apex': '低速彎頂點速度',
            'mid_speed_apex': '中速彎頂點速度',
            'high_speed_apex': '高速彎頂點速度',
            'max_speed': '最高速度',
            's1_s2_ratio': 'S1/S2 比率',
            'sector_cv': '扇區變異係數',
            's2_lap_ratio': 'S2/單圈 比率',
            'max_speed_lap_ratio': '最高速/單圈 比率',
            'max_speed_s2_ratio': '最高速/S2 比率',
            'speed_consistency': '速度一致性',
            'track_avg_improvement_rate': '賽道平均進步率',
            'adjusted_ideal_lap': '調整後理想圈速',
            'fp3_relative_position': 'FP3 相對位置',
            'fp3_gap_to_fastest': 'FP3 與最快差距',
            'is_top_driver': '是否頂尖車手',
            'driver_historical_improvement': '車手歷史進步率'
        }
        return translations.get(feat_name, feat_name)
    
    def generate_overall_summary(self) -> List[str]:
        """生成整體總結"""
        section = []
        
        section.append("# v3.5 模型 2025 賽季詳細分析報告\n")
        section.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        section.append("**模型版本**: v3.5 (20 特徵 + 固定 XGBoost 參數)\n")
        
        section.append("## 📋 報告說明\n")
        section.append("本報告提供 v3.5 模型在 2025 賽季的完整預測分析，包含：")
        section.append("1. 每場賽事所有車手的預測結果")
        section.append("2. 實際排名與預測排名的詳細對比")
        section.append("3. 時間差異分析（秒數級別）")
        section.append("4. 特徵重要性分析（各賽道模型）")
        section.append("5. Top5 預測準確性評估\n")
        
        section.append("---\n")
        
        # 整體統計
        section.append("## 🌍 整體賽季統計\n")
        
        total_races = len(self.results_data)
        total_predictions = sum(len(r['predictions']) for r in self.results_data)
        avg_mae = np.mean([r['mae'] for r in self.results_data])
        avg_r2 = np.mean([r['r2'] for r in self.results_data])
        avg_spearman = np.mean([r['spearman'] for r in self.results_data 
                                if not np.isnan(r.get('spearman', np.nan))])
        avg_top5 = np.mean([r.get('top5_correct', 0) for r in self.results_data])
        
        section.append(f"- **分析賽事數**: {total_races}")
        section.append(f"- **總預測次數**: {total_predictions}")
        section.append(f"- **平均 MAE**: {avg_mae:.3f}s")
        section.append(f"- **平均 R²**: {avg_r2:.4f}")
        section.append(f"- **平均 Spearman**: {avg_spearman:.3f}")
        section.append(f"- **平均 Top5 準確數**: {avg_top5:.2f}/5 ({avg_top5*20:.1f}%)\n")
        
        # 各賽道表現排行
        section.append("### 🏁 各賽道表現排行\n")
        section.append("**按 MAE 排序（越低越好）**:\n")
        section.append("| 排名 | 賽道 | MAE | R² | Spearman | Top5 |")
        section.append("|------|------|-----|----|-----------|----|")
        
        sorted_by_mae = sorted(self.results_data, key=lambda x: x['mae'])
        for rank, race in enumerate(sorted_by_mae, 1):
            track = race.get('track_name', self.race_mapping.get(race['race_number'], f"Race {race['race_number']}"))
            section.append(
                f"| {rank} | {track} | {race['mae']:.3f}s | {race['r2']:.4f} | "
                f"{race.get('spearman', 0):.3f} | {race.get('top5_correct', 0)}/5 |"
            )
        
        section.append("\n**按 Top5 準確率排序（越高越好）**:\n")
        section.append("| 排名 | 賽道 | Top5 準確 | MAE | Spearman |")
        section.append("|------|------|-----------|-----|----------|")
        
        sorted_by_top5 = sorted(self.results_data, 
                                key=lambda x: x.get('top5_correct', 0), 
                                reverse=True)
        for rank, race in enumerate(sorted_by_top5, 1):
            track = race.get('track_name', self.race_mapping.get(race['race_number'], f"Race {race['race_number']}"))
            section.append(
                f"| {rank} | {track} | {race.get('top5_correct', 0)}/5 ({race.get('top5_correct', 0)*20}%) | "
                f"{race['mae']:.3f}s | {race.get('spearman', 0):.3f} |"
            )
        
        section.append("\n---\n")
        
        return section
    
    def generate_full_report(self, output_file: str = None) -> str:
        """生成完整報告"""
        if not self.results_data:
            print("⚠️  請先載入結果數據")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not output_file:
            output_file = f"V3.5_DETAILED_2025_REPORT_{timestamp}.md"
        
        report = []
        
        # 整體總結
        report.extend(self.generate_overall_summary())
        
        # 每場賽事詳細分析
        for race_data in sorted(self.results_data, key=lambda x: x['race_number']):
            report.extend(self.generate_race_detail_section(race_data))
        
        # 模型架構說明
        report.append("## 🔧 v3.5 模型架構說明\n")
        report.append("### 特徵工程（20 個特徵）\n")
        report.append("**基礎特徵 (8)**:")
        report.append("- 理想圈速: S1, S2, S3, 單圈")
        report.append("- 彎道速度: 低速/中速/高速彎頂點")
        report.append("- 最高速度\n")
        
        report.append("**交互特徵 (3)**:")
        report.append("- S1/S2 比率")
        report.append("- 扇區變異係數")
        report.append("- S2/單圈 比率\n")
        
        report.append("**速度特徵 (3)**:")
        report.append("- 最高速/單圈 比率")
        report.append("- 最高速/S2 比率")
        report.append("- 速度一致性\n")
        
        report.append("**改進率特徵 (6)**:")
        report.append("- 賽道平均進步率")
        report.append("- 調整後理想圈速")
        report.append("- FP3 相對位置")
        report.append("- FP3 與最快差距")
        report.append("- 是否頂尖車手標記")
        report.append("- 車手歷史進步率\n")
        
        report.append("### XGBoost 參數（固定）\n")
        report.append("```python")
        report.append("n_estimators = 100")
        report.append("max_depth = 4")
        report.append("learning_rate = 0.1")
        report.append("subsample = 0.8")
        report.append("colsample_bytree = 0.8")
        report.append("```\n")
        
        report.append("---\n")
        report.append(f"\n**報告生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n**數據來源**: v3.5_2025_validation_results.json")
        
        report_text = "\n".join(report)
        
        # 保存報告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"\n✓ 詳細報告已保存: {output_file}")
        print(f"  - 總字數: {len(report_text):,} 字元")
        print(f"  - 總行數: {len(report):,} 行")
        
        return output_file


def main():
    """主程式"""
    print("="*70)
    print("v3.5 詳細分析報告生成器")
    print("="*70)
    
    generator = V35DetailedReportGenerator()
    
    # 載入結果
    print("\n載入 v3.5 驗證結果...")
    if not generator.load_results():
        return
    
    # 生成報告
    print("\n生成詳細報告...")
    print("  - 包含所有賽事車手預測")
    print("  - 包含排名與時間差異")
    print("  - 包含特徵重要性分析")
    
    output_file = generator.generate_full_report()
    
    print("\n" + "="*70)
    print("完成！")
    print("="*70)
    print(f"\n📄 報告檔案: {output_file}")
    print("📊 內容包含:")
    print("  ✓ 整體賽季統計")
    print("  ✓ 每場賽事詳細分析")
    print("  ✓ 所有車手預測結果")
    print("  ✓ 特徵重要性分析")
    print("  ✓ Top5 準確性評估")


if __name__ == "__main__":
    main()
