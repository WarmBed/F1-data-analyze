#!/usr/bin/env python3
"""
v3.5 vs v3.6 精細化 Top5 比較腳本

精細化指標:
1. Driver Match Rate (車手匹配率): 預測 Top5 車手在實際 Top5 中的比例
2. Position Match Rate (位置匹配率): 預測 Top5 車手在正確位置的比例

參考: V3.5_TOP5_PREDICTION_ANALYSIS_REPORT.md
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from scipy.stats import spearmanr


class RefinedTop5Comparator:
    """精細化 Top5 比較器"""
    
    def __init__(self):
        self.v35_results = None
        self.v36_results = None
        self.comparison_results = {}
        
        # 2025 賽事映射
        self.race_mapping = {
            1: "Australia", 2: "China", 3: "Japan", 4: "Bahrain",
            5: "Saudi Arabia", 6: "Miami", 7: "Emilia Romagna", 8: "Monaco",
            9: "Spain", 10: "Canada", 11: "Austria", 12: "Great Britain",
            13: "Belgium", 14: "Hungary", 15: "Netherlands", 16: "Italy",
            17: "Azerbaijan", 18: "Singapore", 19: "United States", 20: "Mexico",
            21: "Brazil", 22: "Las Vegas", 23: "Qatar", 24: "Abu Dhabi"
        }
    
    def load_v35_results(self, json_file: str = "v3.5_2025_validation_results.json"):
        """載入 v3.5 驗證結果"""
        json_path = Path(json_file)
        
        if not json_path.exists():
            print(f"⚠️  找不到 v3.5 結果檔案: {json_file}")
            print("⚠️  請先執行 validate_v35_2025.py 生成結果")
            return False
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.v35_results = json.load(f)
        
        print(f"✓ 載入 v3.5 結果: {len(self.v35_results)} 場賽事")
        return True
    
    def load_v36_results(self, json_file: str = "v3.6_2025_predictions.json"):
        """載入 v3.6 預測結果"""
        json_path = Path(json_file)
        
        if not json_path.exists():
            print(f"⚠️  找不到 v3.6 結果檔案: {json_file}")
            print("⚠️  需要修改 generate_v36_2025_with_cornering.py 保存 JSON 格式")
            return False
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.v36_results = json.load(f)
        
        print(f"✓ 載入 v3.6 結果: {len(self.v36_results)} 場賽事")
        return True
    
    def calculate_refined_top5_metrics(
        self, 
        predictions: List[Dict]
    ) -> Tuple[float, float, int, int]:
        """
        計算精細化 Top5 指標
        
        Returns:
            (driver_match_rate, position_match_rate, driver_correct_count, position_correct_count)
        """
        # 轉換為 DataFrame
        df = pd.DataFrame(predictions)
        
        # 確保有排名欄位
        if 'actual_rank' not in df.columns:
            df['actual_rank'] = df['actual_q_time'].rank()
        if 'predicted_rank' not in df.columns:
            df['predicted_rank'] = df['predicted_time'].rank()
        
        # 實際 Top5 車手
        actual_top5 = set(df.nsmallest(5, 'actual_rank')['driver'].values)
        
        # 預測 Top5 車手
        predicted_top5_df = df.nsmallest(5, 'predicted_rank')
        predicted_top5 = set(predicted_top5_df['driver'].values)
        
        # 1. Driver Match Rate: 預測 Top5 中有幾個車手確實在實際 Top5
        driver_correct_count = len(actual_top5 & predicted_top5)
        driver_match_rate = driver_correct_count / 5.0
        
        # 2. Position Match Rate: 預測 Top5 中有幾個車手在正確位置
        position_correct_count = 0
        
        for idx, row in predicted_top5_df.iterrows():
            predicted_pos = int(row['predicted_rank'])
            actual_pos = int(row['actual_rank'])
            
            # 只計算 Top5 位置（1-5）
            if predicted_pos <= 5 and actual_pos == predicted_pos:
                position_correct_count += 1
        
        position_match_rate = position_correct_count / 5.0
        
        return driver_match_rate, position_match_rate, driver_correct_count, position_correct_count
    
    def compare_single_track(self, race_num: str, track_name: str) -> Dict:
        """比較單一賽道的 v3.5 vs v3.6"""
        
        # 檢查兩個版本是否都有數據
        if race_num not in self.v35_results:
            return None
        
        if track_name not in self.v36_results:
            return None
        
        v35_data = self.v35_results[race_num]
        v36_data = self.v36_results[track_name]
        
        # 計算 v3.5 指標
        v35_driver_match, v35_position_match, v35_driver_count, v35_position_count = \
            self.calculate_refined_top5_metrics(v35_data['predictions'])
        
        # 計算 v3.6 指標
        v36_driver_match, v36_position_match, v36_driver_count, v36_position_count = \
            self.calculate_refined_top5_metrics(v36_data['predictions'])
        
        return {
            'track': track_name,
            'v35': {
                'mae': v35_data['mae'],
                'spearman': v35_data['spearman'],
                'driver_match_rate': v35_driver_match,
                'position_match_rate': v35_position_match,
                'driver_correct': v35_driver_count,
                'position_correct': v35_position_count
            },
            'v36': {
                'mae': v36_data['mae'],
                'spearman': v36_data.get('spearman', v36_data.get('correlation', 0.0)),
                'driver_match_rate': v36_driver_match,
                'position_match_rate': v36_position_match,
                'driver_correct': v36_driver_count,
                'position_correct': v36_position_count
            }
        }
    
    def compare_all_tracks(self):
        """比較所有賽道"""
        print("\n" + "=" * 80)
        print("v3.5 vs v3.6 精細化 Top5 比較")
        print("=" * 80)
        
        valid_count = 0
        
        for race_num_str, v35_data in self.v35_results.items():
            race_num = int(race_num_str)
            track_name = v35_data['track']
            
            result = self.compare_single_track(race_num_str, track_name)
            
            if result:
                self.comparison_results[track_name] = result
                valid_count += 1
                
                print(f"\n[{track_name}]")
                print(f"  v3.5: Driver Match {result['v35']['driver_match_rate']*100:.0f}%, "
                      f"Position Match {result['v35']['position_match_rate']*100:.0f}%, "
                      f"Spearman {result['v35']['spearman']:.3f}")
                print(f"  v3.6: Driver Match {result['v36']['driver_match_rate']*100:.0f}%, "
                      f"Position Match {result['v36']['position_match_rate']*100:.0f}%, "
                      f"Spearman {result['v36']['spearman']:.3f}")
        
        print(f"\n✓ 成功比較 {valid_count} 場賽事")
    
    def generate_summary(self):
        """生成比較總結"""
        if not self.comparison_results:
            print("\n⚠️  沒有比較結果")
            return
        
        print("\n" + "=" * 80)
        print("比較總結")
        print("=" * 80)
        
        # 計算平均值
        v35_driver_match_avg = np.mean([r['v35']['driver_match_rate'] for r in self.comparison_results.values()])
        v35_position_match_avg = np.mean([r['v35']['position_match_rate'] for r in self.comparison_results.values()])
        v35_mae_avg = np.mean([r['v35']['mae'] for r in self.comparison_results.values()])
        v35_spearman_avg = np.mean([r['v35']['spearman'] for r in self.comparison_results.values()])
        
        v36_driver_match_avg = np.mean([r['v36']['driver_match_rate'] for r in self.comparison_results.values()])
        v36_position_match_avg = np.mean([r['v36']['position_match_rate'] for r in self.comparison_results.values()])
        v36_mae_avg = np.mean([r['v36']['mae'] for r in self.comparison_results.values()])
        v36_spearman_avg = np.mean([r['v36']['spearman'] for r in self.comparison_results.values()])
        
        print(f"\n[v3.5 整體表現] ({len(self.comparison_results)} 場)")
        print(f"  Driver Match Rate: {v35_driver_match_avg*100:.1f}%")
        print(f"  Position Match Rate: {v35_position_match_avg*100:.1f}%")
        print(f"  平均 MAE: {v35_mae_avg:.3f}s")
        print(f"  平均 Spearman: {v35_spearman_avg:.3f}")
        
        print(f"\n[v3.6 整體表現] ({len(self.comparison_results)} 場)")
        print(f"  Driver Match Rate: {v36_driver_match_avg*100:.1f}%")
        print(f"  Position Match Rate: {v36_position_match_avg*100:.1f}%")
        print(f"  平均 MAE: {v36_mae_avg:.3f}s")
        print(f"  平均 Spearman: {v36_spearman_avg:.3f}")
        
        # 改進幅度
        driver_improvement = (v36_driver_match_avg - v35_driver_match_avg) / v35_driver_match_avg * 100
        position_improvement = (v36_position_match_avg - v35_position_match_avg) / v35_position_match_avg * 100
        mae_improvement = (v35_mae_avg - v36_mae_avg) / v35_mae_avg * 100
        spearman_improvement = (v36_spearman_avg - v35_spearman_avg) / v35_spearman_avg * 100
        
        print(f"\n[v3.6 相對改進]")
        print(f"  Driver Match Rate: {driver_improvement:+.1f}%")
        print(f"  Position Match Rate: {position_improvement:+.1f}%")
        print(f"  MAE: {mae_improvement:+.1f}%")
        print(f"  Spearman: {spearman_improvement:+.1f}%")
        
        # Top 5 最佳改進賽道
        print(f"\n[Top 5 Driver Match 最佳改進賽道]")
        sorted_tracks = sorted(
            self.comparison_results.items(),
            key=lambda x: x[1]['v36']['driver_match_rate'] - x[1]['v35']['driver_match_rate'],
            reverse=True
        )[:5]
        
        for i, (track, result) in enumerate(sorted_tracks, 1):
            improvement = (result['v36']['driver_match_rate'] - result['v35']['driver_match_rate']) * 100
            print(f"  {i}. {track:20s}: {improvement:+.0f}% "
                  f"(v3.5: {result['v35']['driver_match_rate']*100:.0f}% → "
                  f"v3.6: {result['v36']['driver_match_rate']*100:.0f}%)")
        
        # Top 5 Position Match 最佳改進賽道
        print(f"\n[Top 5 Position Match 最佳改進賽道]")
        sorted_tracks_pos = sorted(
            self.comparison_results.items(),
            key=lambda x: x[1]['v36']['position_match_rate'] - x[1]['v35']['position_match_rate'],
            reverse=True
        )[:5]
        
        for i, (track, result) in enumerate(sorted_tracks_pos, 1):
            improvement = (result['v36']['position_match_rate'] - result['v35']['position_match_rate']) * 100
            print(f"  {i}. {track:20s}: {improvement:+.0f}% "
                  f"(v3.5: {result['v35']['position_match_rate']*100:.0f}% → "
                  f"v3.6: {result['v36']['position_match_rate']*100:.0f}%)")
        
        # 問題賽道分析
        print(f"\n[問題賽道: Great Britain & Canada]")
        for track in ['Great Britain', 'Canada']:
            if track in self.comparison_results:
                result = self.comparison_results[track]
                print(f"\n  {track}:")
                print(f"    v3.5: Driver {result['v35']['driver_match_rate']*100:.0f}%, "
                      f"Position {result['v35']['position_match_rate']*100:.0f}%, "
                      f"MAE {result['v35']['mae']:.3f}s")
                print(f"    v3.6: Driver {result['v36']['driver_match_rate']*100:.0f}%, "
                      f"Position {result['v36']['position_match_rate']*100:.0f}%, "
                      f"MAE {result['v36']['mae']:.3f}s")
    
    def generate_detailed_report(self):
        """生成詳細 Markdown 報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"V3.5_VS_V3.6_REFINED_TOP5_COMPARISON_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# v3.5 vs v3.6 精細化 Top5 比較報告\n\n")
            f.write(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 評估指標說明\n\n")
            f.write("### 1. Driver Match Rate (車手匹配率)\n")
            f.write("- **定義**: 預測 Top5 車手中，有多少人確實在實際 Top5 內\n")
            f.write("- **計算**: (預測 Top5 ∩ 實際 Top5) / 5\n")
            f.write("- **範例**: 預測 [VER, NOR, HAM, RUS, PIA]，實際 [VER, NOR, PIA, LEC, SAI]\n")
            f.write("  - 匹配車手: VER, NOR, PIA (3人)\n")
            f.write("  - Driver Match Rate = 3/5 = 60%\n\n")
            
            f.write("### 2. Position Match Rate (位置匹配率)\n")
            f.write("- **定義**: 預測 Top5 車手中，有多少人在正確的位置\n")
            f.write("- **計算**: (預測位置 == 實際位置) / 5\n")
            f.write("- **範例**: 預測 [VER(1), NOR(2), HAM(3), RUS(4), PIA(5)]\n")
            f.write("          實際 [VER(1), PIA(2), NOR(3), LEC(4), RUS(5)]\n")
            f.write("  - 位置正確: VER(1), RUS(5) (2人)\n")
            f.write("  - Position Match Rate = 2/5 = 40%\n\n")
            
            f.write("---\n\n")
            f.write("## 整體比較\n\n")
            
            # 整體統計表格
            v35_driver_match_avg = np.mean([r['v35']['driver_match_rate'] for r in self.comparison_results.values()])
            v35_position_match_avg = np.mean([r['v35']['position_match_rate'] for r in self.comparison_results.values()])
            v35_mae_avg = np.mean([r['v35']['mae'] for r in self.comparison_results.values()])
            v35_spearman_avg = np.mean([r['v35']['spearman'] for r in self.comparison_results.values()])
            
            v36_driver_match_avg = np.mean([r['v36']['driver_match_rate'] for r in self.comparison_results.values()])
            v36_position_match_avg = np.mean([r['v36']['position_match_rate'] for r in self.comparison_results.values()])
            v36_mae_avg = np.mean([r['v36']['mae'] for r in self.comparison_results.values()])
            v36_spearman_avg = np.mean([r['v36']['spearman'] for r in self.comparison_results.values()])
            
            f.write("| 指標 | v3.5 | v3.6 | 改進幅度 |\n")
            f.write("|------|------|------|----------|\n")
            f.write(f"| **Driver Match Rate** | {v35_driver_match_avg*100:.1f}% | {v36_driver_match_avg*100:.1f}% | {(v36_driver_match_avg-v35_driver_match_avg)*100:+.1f}% |\n")
            f.write(f"| **Position Match Rate** | {v35_position_match_avg*100:.1f}% | {v36_position_match_avg*100:.1f}% | {(v36_position_match_avg-v35_position_match_avg)*100:+.1f}% |\n")
            f.write(f"| **平均 MAE** | {v35_mae_avg:.3f}s | {v36_mae_avg:.3f}s | {(v36_mae_avg-v35_mae_avg):+.3f}s |\n")
            f.write(f"| **平均 Spearman** | {v35_spearman_avg:.3f} | {v36_spearman_avg:.3f} | {(v36_spearman_avg-v35_spearman_avg):+.3f} |\n")
            f.write(f"| **分析賽事數** | {len(self.comparison_results)} | {len(self.comparison_results)} | - |\n\n")
            
            # 逐賽道詳細比較
            f.write("## 逐賽道詳細比較\n\n")
            f.write("| 賽道 | v3.5 Driver | v3.5 Position | v3.6 Driver | v3.6 Position | Driver 改進 | Position 改進 |\n")
            f.write("|------|-------------|---------------|-------------|---------------|-------------|---------------|\n")
            
            for track in sorted(self.comparison_results.keys()):
                result = self.comparison_results[track]
                v35_d = result['v35']['driver_match_rate'] * 100
                v35_p = result['v35']['position_match_rate'] * 100
                v36_d = result['v36']['driver_match_rate'] * 100
                v36_p = result['v36']['position_match_rate'] * 100
                
                f.write(f"| {track} | {v35_d:.0f}% | {v35_p:.0f}% | {v36_d:.0f}% | {v36_p:.0f}% | ")
                f.write(f"{v36_d-v35_d:+.0f}% | {v36_p-v35_p:+.0f}% |\n")
            
            f.write("\n")
        
        print(f"\n✓ 詳細報告已生成: {report_file}")
        return report_file
    
    def save_results(self):
        """保存比較結果為 JSON"""
        output_file = "v35_v36_refined_comparison.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.comparison_results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 比較結果已保存: {output_file}")


def main():
    comparator = RefinedTop5Comparator()
    
    # 載入 v3.5 結果
    if not comparator.load_v35_results():
        print("\n⚠️  請先執行以下命令生成 v3.5 結果:")
        print("   python validate_v35_2025.py")
        return
    
    # 載入 v3.6 結果
    if not comparator.load_v36_results():
        print("\n⚠️  v3.6 結果檔案不存在")
        print("⚠️  需要修改 generate_v36_2025_with_cornering.py 保存 JSON 格式")
        print("\n提示: 在 generate_v36_2025_with_cornering.py 的 main() 函數末尾添加:")
        print("```python")
        print("# 保存 JSON 格式")
        print("json_results = {}")
        print("for track, result in results.items():")
        print("    df = result['data']")
        print("    json_results[track] = {")
        print("        'mae': result['mae'],")
        print("        'correlation': result['correlation'],")
        print("        'top5_correct': result['top5_correct'],")
        print("        'predictions': df[['driver', 'actual_q_time', 'predicted_q_time',")
        print("                          'actual_position', 'predicted_position']].to_dict('records')")
        print("    }")
        print("")
        print("with open('v3.6_2025_predictions.json', 'w', encoding='utf-8') as f:")
        print("    json.dump(json_results, f, indent=2, ensure_ascii=False)")
        print("```")
        return
    
    # 進行比較
    comparator.compare_all_tracks()
    
    # 生成總結
    comparator.generate_summary()
    
    # 生成詳細報告
    comparator.generate_detailed_report()
    
    # 保存結果
    comparator.save_results()
    
    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
