"""
v3.4 vs v3.5 Top 5 預測詳細對比分析

分析每場比賽的 Top 5 車手預測：
1. Top 5 準確率（預測前 5 中有幾個實際是前 5）
2. 排名誤差（預測排名 vs 實際排名）
3. 時間誤差（預測時間 vs 實際時間）
4. 車手級別分析（VER, HAM, LEC, NOR, PIA 等頂尖車手）
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

# 賽事名稱映射
RACE_MAPPING = {
    3: "Japan",
    4: "Bahrain", 
    5: "Saudi Arabia",
    8: "Monaco",
    10: "Canada",
    12: "Great Britain",
    14: "Hungary",
    15: "Netherlands",
    16: "Italy",
    17: "Azerbaijan",
    18: "Singapore",
    20: "Mexico"
}

def load_validation_results(version: str) -> Dict:
    """載入驗證結果 JSON"""
    if version == "v3.4":
        file_path = Path("v3.4_2025_validation_results.json")
    else:
        file_path = Path("v3.5_2025_validation_results.json")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_top5_predictions(predictions: List[Dict]) -> Tuple[List[str], List[str], List[float], List[float]]:
    """
    提取 Top 5 預測
    
    Returns:
        actual_top5_drivers: 實際 Top 5 車手
        predicted_top5_drivers: 預測 Top 5 車手
        actual_top5_times: 實際 Top 5 時間
        predicted_top5_times: 預測 Top 5 時間
    """
    # 按實際排名排序
    sorted_by_actual = sorted(predictions, key=lambda x: x['actual_rank'])
    actual_top5 = sorted_by_actual[:5]
    
    # 按預測排名排序
    sorted_by_predicted = sorted(predictions, key=lambda x: x['predicted_rank'])
    predicted_top5 = sorted_by_predicted[:5]
    
    actual_top5_drivers = [p['driver'] for p in actual_top5]
    predicted_top5_drivers = [p['driver'] for p in predicted_top5]
    actual_top5_times = [p['actual_q_time'] for p in actual_top5]
    predicted_top5_times = [p['predicted_time'] for p in predicted_top5]
    
    return actual_top5_drivers, predicted_top5_drivers, actual_top5_times, predicted_top5_times

def calculate_top5_accuracy(actual_top5: List[str], predicted_top5: List[str]) -> Tuple[int, List[str]]:
    """
    計算 Top 5 準確率
    
    Returns:
        correct_count: 預測正確的車手數量
        correct_drivers: 預測正確的車手列表
    """
    correct_drivers = [driver for driver in predicted_top5 if driver in actual_top5]
    return len(correct_drivers), correct_drivers

def analyze_top5_per_race(race_data: Dict, version: str) -> Dict:
    """分析單場比賽的 Top 5 預測"""
    # v3.4 只有摘要統計，沒有詳細預測
    if version == 'v3.4':
        return {
            'version': version,
            'has_details': False,
            'mae': race_data['mae'],
            'spearman': race_data['spearman'],
            'top3_accuracy': race_data.get('top3_accuracy', None),
            'top10_accuracy': race_data.get('top10_accuracy', None),
            'mean_rank_error': race_data.get('mean_rank_error', None)
        }
    
    # v3.5 有詳細預測
    predictions = race_data['predictions']
    
    # 提取 Top 5
    actual_top5_drivers, predicted_top5_drivers, actual_top5_times, predicted_top5_times = \
        extract_top5_predictions(predictions)
    
    # 計算準確率
    correct_count, correct_drivers = calculate_top5_accuracy(actual_top5_drivers, predicted_top5_drivers)
    
    # 計算每位車手的誤差
    driver_errors = {}
    for pred in predictions:
        driver = pred['driver']
        if driver in actual_top5_drivers or driver in predicted_top5_drivers:
            driver_errors[driver] = {
                'actual_rank': pred['actual_rank'],
                'predicted_rank': pred['predicted_rank'],
                'rank_error': abs(pred['rank_diff']),
                'actual_time': pred['actual_q_time'],
                'predicted_time': pred['predicted_time'],
                'time_error': abs(pred['predicted_time'] - pred['actual_q_time'])
            }
    
    return {
        'version': version,
        'has_details': True,
        'actual_top5': actual_top5_drivers,
        'predicted_top5': predicted_top5_drivers,
        'correct_count': correct_count,
        'correct_drivers': correct_drivers,
        'accuracy': correct_count / 5.0,
        'driver_errors': driver_errors,
        'mae': race_data['mae'],
        'spearman': race_data['spearman']
    }

def compare_top5_both_versions(race_num: int, v34_results: Dict, v35_results: Dict) -> Dict:
    """對比 v3.4 和 v3.5 的 Top 5 預測"""
    race_name = RACE_MAPPING[race_num]
    
    # v3.4 分析
    if race_name in v34_results['race_results']:
        v34_analysis = analyze_top5_per_race(v34_results['race_results'][race_name], 'v3.4')
    else:
        v34_analysis = None
    
    # v3.5 分析
    if str(race_num) in v35_results:
        v35_analysis = analyze_top5_per_race(v35_results[str(race_num)], 'v3.5')
    else:
        v35_analysis = None
    
    return {
        'race_num': race_num,
        'race_name': race_name,
        'v3.4': v34_analysis,
        'v3.5': v35_analysis
    }

def print_race_top5_comparison(comparison: Dict):
    """打印單場比賽的 Top 5 對比"""
    race_name = comparison['race_name']
    v34 = comparison['v3.4']
    v35 = comparison['v3.5']
    
    print(f"\n{'='*100}")
    print(f"🏁 {race_name} (Race {comparison['race_num']})")
    print(f"{'='*100}")
    
    if v34 and v35 and v35.get('has_details'):
        # 性能指標對比
        print(f"\n📊 整體性能對比：")
        print(f"  v3.4: Spearman {v34['spearman']:.3f}, MAE {v34['mae']:.3f}s, Top3 準確率 {v34.get('top3_accuracy', 0)*100:.0f}%")
        print(f"  v3.5: Spearman {v35['spearman']:.3f}, MAE {v35['mae']:.3f}s")
        
        # Top 5 準確率對比
        print(f"\n🎯 Top 5 準確率：")
        print(f"  v3.5: {v35['correct_count']}/5 ({v35['accuracy']*100:.0f}%)")
        print(f"  (v3.4 無詳細車手預測數據，只有 Top3 準確率: {v34.get('top3_accuracy', 0)*100:.0f}%)")
        
        # 實際 Top 5
        print(f"\n✅ 實際 Top 5：")
        print(f"  {', '.join(v35['actual_top5'])}")
        
        # v3.5 預測 Top 5
        print(f"\n🟢 v3.5 預測 Top 5：")
        v35_pred_str = ', '.join([
            f"**{d}**" if d in v35['actual_top5'] else d 
            for d in v35['predicted_top5']
        ])
        print(f"  {v35_pred_str}")
        print(f"  正確: {', '.join(v35['correct_drivers'])}")
        
        # 詳細車手對比（只顯示實際或預測 Top 5 的車手）
        print(f"\n📋 Top 5 車手詳細分析（v3.5）：")
        print(f"{'車手':<8} {'實際排名':<10} {'v3.5 預測':<12} {'排名誤差':<12} {'時間誤差':<12}")
        print(f"{'-'*60}")
        
        for driver in v35['actual_top5']:
            v35_data = v35['driver_errors'].get(driver, {})
            
            actual_rank = v35_data.get('actual_rank', '?')
            v35_pred = v35_data.get('predicted_rank', '?')
            v35_rank_err = v35_data.get('rank_error', '?')
            v35_time_err = v35_data.get('time_error', 0)
            
            # 標記誤差
            if isinstance(v35_rank_err, (int, float)):
                if v35_rank_err == 0:
                    rank_mark = "✅完美"
                elif v35_rank_err <= 2:
                    rank_mark = "✅"
                elif v35_rank_err <= 5:
                    rank_mark = "⚠️"
                else:
                    rank_mark = "❌"
            else:
                rank_mark = ""
            
            print(f"{driver:<8} {actual_rank:<10.0f} {v35_pred:<12.1f} {str(v35_rank_err):<12} {v35_time_err:<11.3f}s")
        
        # 預測 Top 5 但實際不在的車手
        wrong_predictions = [d for d in v35['predicted_top5'] if d not in v35['actual_top5']]
        if wrong_predictions:
            print(f"\n❌ 預測進 Top 5 但實際不在的車手：")
            for driver in wrong_predictions:
                v35_data = v35['driver_errors'].get(driver, {})
                actual_rank = v35_data.get('actual_rank', '?')
                predicted_rank = v35_data.get('predicted_rank', '?')
                print(f"  {driver}: 預測排名 {predicted_rank:.1f}, 實際排名 {actual_rank:.0f}")
        
        # 時間預測詳細對比（僅實際 Top 5）
        print(f"\n⏱️  時間預測詳細（實際 Top 5）：")
        print(f"{'車手':<8} {'實際時間':<12} {'v3.5 預測':<12} {'誤差':<12} {'誤差%':<10}")
        print(f"{'-'*60}")
        
        for driver in v35['actual_top5']:
            v35_data = v35['driver_errors'].get(driver, {})
            
            actual_time = v35_data.get('actual_time', 0)
            v35_pred_time = v35_data.get('predicted_time', 0)
            v35_time_err = v35_data.get('time_error', 0)
            error_pct = (v35_time_err / actual_time * 100) if actual_time > 0 else 0
            
            print(f"{driver:<8} {actual_time:<12.3f} {v35_pred_time:<12.3f} {v35_time_err:<11.3f}s {error_pct:<9.2f}%")
    
    elif v35:
        # 只有 v3.5
        print(f"\n⚠️  只有 v3.5 驗證結果")
        print(f"\n📊 性能：Spearman {v35['spearman']:.3f}, MAE {v35['mae']:.3f}s")
        print(f"🎯 Top 5 準確率: {v35['correct_count']}/5 ({v35['accuracy']*100:.0f}%)")
        print(f"✅ 實際: {', '.join(v35['actual_top5'])}")
        print(f"🟢 預測: {', '.join(v35['predicted_top5'])}")
        print(f"✓ 正確: {', '.join(v35['correct_drivers'])}")
    
    elif v34:
        # 只有 v3.4
        print(f"\n⚠️  只有 v3.4 驗證結果")
        print(f"\n📊 性能：Spearman {v34['spearman']:.3f}, MAE {v34['mae']:.3f}s")
        print(f"🎯 Top 5 準確率: {v34['correct_count']}/5 ({v34['accuracy']*100:.0f}%)")
        print(f"✅ 實際: {', '.join(v34['actual_top5'])}")
        print(f"🔵 預測: {', '.join(v34['predicted_top5'])}")
        print(f"✓ 正確: {', '.join(v34['correct_drivers'])}")

def generate_summary_statistics(all_comparisons: List[Dict]) -> Dict:
    """生成統計摘要"""
    v34_top3_accuracies = []
    v35_accuracies = []
    v35_correct_total = 0
    
    for comp in all_comparisons:
        if comp['v3.4'] and comp['v3.4'].get('top3_accuracy') is not None:
            v34_top3_accuracies.append(comp['v3.4']['top3_accuracy'])
        if comp['v3.5'] and comp['v3.5'].get('has_details'):
            v35_accuracies.append(comp['v3.5']['accuracy'])
            v35_correct_total += comp['v3.5']['correct_count']
    
    return {
        'v3.4_avg_top3_accuracy': sum(v34_top3_accuracies) / len(v34_top3_accuracies) if v34_top3_accuracies else 0,
        'v3.5_avg_accuracy': sum(v35_accuracies) / len(v35_accuracies) if v35_accuracies else 0,
        'v3.5_total_correct': v35_correct_total,
        'v3.4_race_count': len(v34_top3_accuracies),
        'v3.5_race_count': len(v35_accuracies)
    }

def main():
    """主程式"""
    print("="*100)
    print("🏎️  v3.4 vs v3.5 Top 5 預測詳細對比分析")
    print("="*100)
    
    # 載入驗證結果
    print("\n📂 載入驗證結果...")
    v34_results = load_validation_results('v3.4')
    v35_results = load_validation_results('v3.5')
    
    # 分析所有共同賽事
    all_comparisons = []
    
    # 優先分析問題賽道
    priority_races = [12, 14, 10]  # Great Britain, Hungary, Canada
    other_races = [num for num in RACE_MAPPING.keys() if num not in priority_races]
    
    print("\n🔴 問題賽道優先分析：Great Britain, Hungary, Canada")
    for race_num in priority_races:
        comparison = compare_top5_both_versions(race_num, v34_results, v35_results)
        all_comparisons.append(comparison)
        print_race_top5_comparison(comparison)
    
    print("\n\n🟢 其他賽道分析：")
    for race_num in other_races[:7]:  # 前 7 個其他賽道
        comparison = compare_top5_both_versions(race_num, v34_results, v35_results)
        all_comparisons.append(comparison)
        print_race_top5_comparison(comparison)
    
    # 統計摘要
    print(f"\n{'='*100}")
    print("📊 統計摘要")
    print(f"{'='*100}")
    
    stats = generate_summary_statistics(all_comparisons)
    
    print(f"\n🎯 Top 5 整體準確率：")
    print(f"  v3.4: Top3 平均 {stats['v3.4_avg_top3_accuracy']*100:.1f}% ({stats['v3.4_race_count']} 場比賽)")
    print(f"        (v3.4 只有 Top3 統計，無詳細車手預測)")
    print(f"  v3.5: Top5 平均 {stats['v3.5_avg_accuracy']*100:.1f}% ({stats['v3.5_race_count']} 場比賽)")
    print(f"        總計 {stats['v3.5_total_correct']}/{stats['v3.5_race_count']*5} 車手預測正確")
    
    print(f"\n� 說明：v3.4 原驗證腳本只記錄 Top3 準確率，v3.5 有完整車手預測數據")
    
    # 重點發現
    print(f"\n💡 重點發現：")
    
    # 找出 v3.5 表現最好和最差的賽事
    v35_races = [(c['race_name'], c['v3.5']['accuracy'], c['v3.5']['spearman']) 
                 for c in all_comparisons if c['v3.5']]
    v35_races_sorted = sorted(v35_races, key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 v3.5 Top 5 表現最佳：")
    for race, acc, spear in v35_races_sorted[:3]:
        print(f"  {race}: {acc*100:.0f}% 準確率, Spearman {spear:.3f}")
    
    print(f"\n⚠️  v3.5 Top 5 表現最差：")
    for race, acc, spear in v35_races_sorted[-3:]:
        print(f"  {race}: {acc*100:.0f}% 準確率, Spearman {spear:.3f}")

if __name__ == "__main__":
    main()
