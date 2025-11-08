#!/usr/bin/env python3
"""
v3.5 vs v3.7 精細化 Top5 比較腳本

v3.7 架構: v3.5 的 20 特徵 + v3.6 的 Optuna 優化 (500 trials)

精細化指標:
1. Driver Match Rate (車手匹配率): 預測 Top5 車手在實際 Top5 中的比例
2. Position Match Rate (位置匹配率): 預測 Top5 車手在正確位置的比例
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
        self.v37_results = None
        self.comparison_results = {}
        
        # 2025 賽事映射（對應 v3.7 支援的 10 個賽道）
        self.race_mapping = {
            1: "Bahrain",
            2: "Saudi Arabia", 
            3: "Japan",
            6: "Monaco",
            9: "Canada",
            11: "Great Britain",
            13: "Hungary",
            14: "Netherlands",
            15: "Italy",
            16: "Azerbaijan"
        }
    
    def load_v35_results(self, json_file: str = "v3.5_2025_validation_results.json"):
        """載入 v3.5 驗證結果"""
        json_path = Path(json_file)
        
        if not json_path.exists():
            print(f"⚠️  找不到 v3.5 結果檔案: {json_file}")
            return False
        
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # v3.5 結果是字典格式 {race_num: race_data}，轉換為列表
        if isinstance(raw_data, dict):
            self.v35_results = []
            for race_num_str, race_data in raw_data.items():
                race_data['race_number'] = int(race_num_str)
                self.v35_results.append(race_data)
        else:
            self.v35_results = raw_data
        
        print(f"✓ 載入 v3.5 結果: {len(self.v35_results)} 場賽事")
        return True
    
    def load_v37_results(self, json_file: str = "v3.7_2025_predictions.json"):
        """載入 v3.7 預測結果"""
        json_path = Path(json_file)
        
        if not json_path.exists():
            print(f"⚠️  找不到 v3.7 結果檔案: {json_file}")
            return False
        
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # v3.7 結果是字典格式 {track_name: race_data}，轉換為列表
        if isinstance(raw_data, dict):
            self.v37_results = []
            for track_name, race_data in raw_data.items():
                # 確保 race_number 欄位存在
                if 'race_num' in race_data:
                    race_data['race_number'] = race_data['race_num']
                if 'track' in race_data:
                    race_data['track_name'] = race_data['track']
                self.v37_results.append(race_data)
        else:
            self.v37_results = raw_data
        
        print(f"✓ 載入 v3.7 結果: {len(self.v37_results)} 場賽事")
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
        
        for _, row in predicted_top5_df.iterrows():
            driver = row['driver']
            pred_pos = int(row['predicted_rank'])
            
            # 獲取實際排名
            actual_row = df[df['driver'] == driver]
            if not actual_row.empty:
                actual_pos = int(actual_row.iloc[0]['actual_rank'])
                
                # 檢查是否在相同位置
                if pred_pos == actual_pos:
                    position_correct_count += 1
        
        position_match_rate = position_correct_count / 5.0
        
        return driver_match_rate, position_match_rate, driver_correct_count, position_correct_count
    
    def compare_single_track(self, race_num: int, track_name: str) -> Dict:
        """比較單個賽道的 v3.5 和 v3.7 表現"""
        
        # 獲取 v3.5 結果
        v35_race = None
        for race in self.v35_results:
            if race.get('race_number') == race_num or race.get('track_name') == track_name:
                v35_race = race
                break
        
        # 獲取 v3.7 結果
        v37_race = None
        for race in self.v37_results:
            if race.get('race_number') == race_num or race.get('track_name') == track_name:
                v37_race = race
                break
        
        if not v35_race or not v37_race:
            return None
        
        # 計算 v3.5 指標
        v35_driver_rate, v35_pos_rate, v35_driver_count, v35_pos_count = \
            self.calculate_refined_top5_metrics(v35_race['predictions'])
        
        # 計算 v3.7 指標
        v37_driver_rate, v37_pos_rate, v37_driver_count, v37_pos_count = \
            self.calculate_refined_top5_metrics(v37_race['predictions'])
        
        return {
            'track_name': track_name,
            'race_number': race_num,
            'v35': {
                'driver_match_rate': v35_driver_rate,
                'position_match_rate': v35_pos_rate,
                'driver_count': v35_driver_count,
                'position_count': v35_pos_count,
                'mae': v35_race.get('mae', 0),
                'spearman': v35_race.get('spearman', 0)
            },
            'v37': {
                'driver_match_rate': v37_driver_rate,
                'position_match_rate': v37_pos_rate,
                'driver_count': v37_driver_count,
                'position_count': v37_pos_count,
                'mae': v37_race.get('mae', 0),
                'spearman': v37_race.get('spearman', 0)
            },
            'improvement': {
                'driver_match': v37_driver_rate - v35_driver_rate,
                'position_match': v37_pos_rate - v35_pos_rate,
                'mae': v35_race.get('mae', 0) - v37_race.get('mae', 0),
                'spearman': v37_race.get('spearman', 0) - v35_race.get('spearman', 0)
            }
        }
    
    def compare_all_tracks(self) -> Dict:
        """比較所有賽道"""
        results = []
        
        for race_num, track_name in self.race_mapping.items():
            print(f"比較 Race #{race_num} - {track_name}...")
            
            comparison = self.compare_single_track(race_num, track_name)
            if comparison:
                results.append(comparison)
        
        # 計算整體統計
        v35_driver_rates = [r['v35']['driver_match_rate'] for r in results]
        v35_pos_rates = [r['v35']['position_match_rate'] for r in results]
        v35_maes = [r['v35']['mae'] for r in results]
        v35_spearmans = [r['v35']['spearman'] for r in results if not np.isnan(r['v35']['spearman'])]
        
        v37_driver_rates = [r['v37']['driver_match_rate'] for r in results]
        v37_pos_rates = [r['v37']['position_match_rate'] for r in results]
        v37_maes = [r['v37']['mae'] for r in results]
        v37_spearmans = [r['v37']['spearman'] for r in results if not np.isnan(r['v37']['spearman'])]
        
        summary = {
            'total_races': len(results),
            'v35_summary': {
                'avg_driver_match_rate': np.mean(v35_driver_rates),
                'avg_position_match_rate': np.mean(v35_pos_rates),
                'avg_mae': np.mean(v35_maes),
                'avg_spearman': np.mean(v35_spearmans) if v35_spearmans else 0
            },
            'v37_summary': {
                'avg_driver_match_rate': np.mean(v37_driver_rates),
                'avg_position_match_rate': np.mean(v37_pos_rates),
                'avg_mae': np.mean(v37_maes),
                'avg_spearman': np.mean(v37_spearmans) if v37_spearmans else 0
            },
            'overall_improvement': {
                'driver_match': np.mean(v37_driver_rates) - np.mean(v35_driver_rates),
                'position_match': np.mean(v37_pos_rates) - np.mean(v35_pos_rates),
                'mae': np.mean(v35_maes) - np.mean(v37_maes),
                'spearman': (np.mean(v37_spearmans) if v37_spearmans else 0) - 
                            (np.mean(v35_spearmans) if v35_spearmans else 0)
            },
            'track_results': results
        }
        
        self.comparison_results = summary
        return summary
    
    def generate_detailed_report(self, output_file: str = None) -> str:
        """生成詳細比較報告"""
        if not self.comparison_results:
            print("⚠️  請先執行 compare_all_tracks()")
            return None
        
        summary = self.comparison_results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not output_file:
            output_file = f"V3.5_VS_V3.7_REFINED_TOP5_COMPARISON_{timestamp}.md"
        
        report = []
        report.append("# v3.5 vs v3.7 精細化 Top5 比較報告\n")
        report.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("**v3.7 架構**: v3.5 的 20 特徵 + v3.6 的 Optuna 優化 (500 trials)\n")
        
        # 評估指標說明
        report.append("## 評估指標說明\n")
        report.append("### 1. Driver Match Rate (車手匹配率)")
        report.append("- **定義**: 預測 Top5 車手中，有多少人確實在實際 Top5 內")
        report.append("- **計算**: (預測 Top5 ∩ 實際 Top5) / 5")
        report.append("- **範例**: 預測 [VER, NOR, HAM, RUS, PIA]，實際 [VER, NOR, PIA, LEC, SAI]")
        report.append("  - 匹配車手: VER, NOR, PIA (3人)")
        report.append("  - Driver Match Rate = 3/5 = 60%\n")
        
        report.append("### 2. Position Match Rate (位置匹配率)")
        report.append("- **定義**: 預測 Top5 車手中，有多少人在正確的位置")
        report.append("- **計算**: (預測位置 == 實際位置) / 5")
        report.append("- **範例**: 預測 [VER(1), NOR(2), HAM(3), RUS(4), PIA(5)]")
        report.append("          實際 [VER(1), PIA(2), NOR(3), LEC(4), RUS(5)]")
        report.append("  - 位置正確: VER(1), RUS(5) (2人)")
        report.append("  - Position Match Rate = 2/5 = 40%\n")
        
        report.append("---\n")
        
        # 整體比較
        report.append("## 整體比較\n")
        v35_sum = summary['v35_summary']
        v37_sum = summary['v37_summary']
        improve = summary['overall_improvement']
        
        report.append("| 指標 | v3.5 | v3.7 | 改進幅度 |")
        report.append("|------|------|------|----------|")
        report.append(f"| **Driver Match Rate** | {v35_sum['avg_driver_match_rate']:.1%} | {v37_sum['avg_driver_match_rate']:.1%} | {improve['driver_match']:+.1%} |")
        report.append(f"| **Position Match Rate** | {v35_sum['avg_position_match_rate']:.1%} | {v37_sum['avg_position_match_rate']:.1%} | {improve['position_match']:+.1%} |")
        report.append(f"| **平均 MAE** | {v35_sum['avg_mae']:.3f}s | {v37_sum['avg_mae']:.3f}s | {improve['mae']:+.3f}s |")
        report.append(f"| **平均 Spearman** | {v35_sum['avg_spearman']:.3f} | {v37_sum['avg_spearman']:.3f} | {improve['spearman']:+.3f} |")
        report.append(f"| **分析賽事數** | {summary['total_races']} | {summary['total_races']} | - |\n")
        
        # 逐賽道詳細比較
        report.append("## 逐賽道詳細比較\n")
        report.append("| 賽道 | v3.5 Driver | v3.5 Position | v3.7 Driver | v3.7 Position | Driver 改進 | Position 改進 |")
        report.append("|------|-------------|---------------|-------------|---------------|-------------|---------------|")
        
        for result in sorted(summary['track_results'], key=lambda x: x['track_name']):
            track = result['track_name']
            v35 = result['v35']
            v37 = result['v37']
            imp = result['improvement']
            
            report.append(
                f"| {track} | {v35['driver_match_rate']:.0%} | {v35['position_match_rate']:.0%} | "
                f"{v37['driver_match_rate']:.0%} | {v37['position_match_rate']:.0%} | "
                f"{imp['driver_match']:+.0%} | {imp['position_match']:+.0%} |"
            )
        
        report.append("\n---\n")
        
        # MAE 和 Spearman 比較
        report.append("## MAE 和 Spearman 相關性比較\n")
        report.append("| 賽道 | v3.5 MAE | v3.7 MAE | MAE 改進 | v3.5 Spearman | v3.7 Spearman | Spearman 改進 |")
        report.append("|------|----------|----------|----------|---------------|---------------|---------------|")
        
        for result in sorted(summary['track_results'], key=lambda x: x['track_name']):
            track = result['track_name']
            v35 = result['v35']
            v37 = result['v37']
            imp = result['improvement']
            
            v35_sp_str = f"{v35['spearman']:.3f}" if not np.isnan(v35['spearman']) else "N/A"
            v37_sp_str = f"{v37['spearman']:.3f}" if not np.isnan(v37['spearman']) else "N/A"
            sp_imp_str = f"{imp['spearman']:+.3f}" if not np.isnan(imp['spearman']) else "N/A"
            
            report.append(
                f"| {track} | {v35['mae']:.3f}s | {v37['mae']:.3f}s | {imp['mae']:+.3f}s | "
                f"{v35_sp_str} | {v37_sp_str} | {sp_imp_str} |"
            )
        
        report.append("\n---\n")
        
        # 關鍵發現
        report.append("## 關鍵發現\n")
        
        # 計算改進/退步的賽道數量
        driver_improved = sum(1 for r in summary['track_results'] if r['improvement']['driver_match'] > 0)
        driver_declined = sum(1 for r in summary['track_results'] if r['improvement']['driver_match'] < 0)
        
        pos_improved = sum(1 for r in summary['track_results'] if r['improvement']['position_match'] > 0)
        pos_declined = sum(1 for r in summary['track_results'] if r['improvement']['position_match'] < 0)
        
        report.append(f"### 整體表現")
        report.append(f"- **Driver Match Rate**: v3.7 {'改進' if improve['driver_match'] > 0 else '退步'} {abs(improve['driver_match']):.1%}")
        report.append(f"  - 改進賽道: {driver_improved}/{summary['total_races']}")
        report.append(f"  - 退步賽道: {driver_declined}/{summary['total_races']}")
        report.append(f"- **Position Match Rate**: v3.7 {'改進' if improve['position_match'] > 0 else '退步'} {abs(improve['position_match']):.1%}")
        report.append(f"  - 改進賽道: {pos_improved}/{summary['total_races']}")
        report.append(f"  - 退步賽道: {pos_declined}/{summary['total_races']}")
        report.append(f"- **MAE**: v3.7 {'改善' if improve['mae'] > 0 else '惡化'} {abs(improve['mae']):.3f}s")
        report.append(f"- **Spearman**: v3.7 {'改善' if improve['spearman'] > 0 else '惡化'} {abs(improve['spearman']):.3f}\n")
        
        # 最佳/最差改進
        best_driver_improve = max(summary['track_results'], key=lambda x: x['improvement']['driver_match'])
        worst_driver_improve = min(summary['track_results'], key=lambda x: x['improvement']['driver_match'])
        
        report.append("### 最佳改進賽道")
        report.append(f"- **{best_driver_improve['track_name']}**: Driver Match +{best_driver_improve['improvement']['driver_match']:.0%}")
        report.append(f"  - v3.5: {best_driver_improve['v35']['driver_match_rate']:.0%} → v3.7: {best_driver_improve['v37']['driver_match_rate']:.0%}\n")
        
        report.append("### 最大退步賽道")
        report.append(f"- **{worst_driver_improve['track_name']}**: Driver Match {worst_driver_improve['improvement']['driver_match']:.0%}")
        report.append(f"  - v3.5: {worst_driver_improve['v35']['driver_match_rate']:.0%} → v3.7: {worst_driver_improve['v37']['driver_match_rate']:.0%}\n")
        
        # 結論
        report.append("## 結論\n")
        
        if improve['driver_match'] > 0:
            report.append(f"✅ **v3.7 優於 v3.5**: Optuna 優化成功提升 Driver Match Rate {abs(improve['driver_match']):.1%}")
        else:
            report.append(f"❌ **v3.7 未能超越 v3.5**: Driver Match Rate 下降 {abs(improve['driver_match']):.1%}")
        
        if improve['mae'] > 0:
            report.append(f"✅ **MAE 改善**: v3.7 MAE 降低 {improve['mae']:.3f}s")
        else:
            report.append(f"⚠️  **MAE 惡化**: v3.7 MAE 增加 {abs(improve['mae']):.3f}s")
        
        report_text = "\n".join(report)
        
        # 保存報告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"\n✓ 報告已保存: {output_file}")
        
        return report_text
    
    def save_comparison_json(self, output_file: str = None):
        """保存比較結果為 JSON"""
        if not self.comparison_results:
            print("⚠️  請先執行 compare_all_tracks()")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not output_file:
            output_file = f"v35_vs_v37_comparison_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.comparison_results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON 結果已保存: {output_file}")


def main():
    """主程式"""
    print("="*70)
    print("v3.5 vs v3.7 精細化 Top5 比較")
    print("="*70)
    
    comparator = RefinedTop5Comparator()
    
    # 載入結果
    if not comparator.load_v35_results():
        return
    
    if not comparator.load_v37_results():
        return
    
    # 執行比較
    print("\n" + "="*70)
    print("執行逐賽道比較...")
    print("="*70)
    
    summary = comparator.compare_all_tracks()
    
    # 顯示整體結果
    print("\n" + "="*70)
    print("整體比較結果")
    print("="*70)
    
    v35_sum = summary['v35_summary']
    v37_sum = summary['v37_summary']
    improve = summary['overall_improvement']
    
    print(f"\n{'指標':<25} | {'v3.5':<12} | {'v3.7':<12} | {'改進':<12}")
    print("-" * 70)
    print(f"{'Driver Match Rate':<25} | {v35_sum['avg_driver_match_rate']:>11.1%} | {v37_sum['avg_driver_match_rate']:>11.1%} | {improve['driver_match']:>+11.1%}")
    print(f"{'Position Match Rate':<25} | {v35_sum['avg_position_match_rate']:>11.1%} | {v37_sum['avg_position_match_rate']:>11.1%} | {improve['position_match']:>+11.1%}")
    print(f"{'平均 MAE':<25} | {v35_sum['avg_mae']:>10.3f}s | {v37_sum['avg_mae']:>10.3f}s | {improve['mae']:>+10.3f}s")
    print(f"{'平均 Spearman':<25} | {v35_sum['avg_spearman']:>11.3f} | {v37_sum['avg_spearman']:>11.3f} | {improve['spearman']:>+11.3f}")
    
    # 生成報告
    print("\n" + "="*70)
    print("生成詳細報告...")
    print("="*70)
    
    comparator.generate_detailed_report()
    comparator.save_comparison_json()
    
    print("\n" + "="*70)
    print("完成！")
    print("="*70)


if __name__ == "__main__":
    main()
