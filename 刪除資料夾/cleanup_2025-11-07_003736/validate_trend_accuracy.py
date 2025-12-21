"""
趨勢驗證腳本 - 評估預測的相對排名準確性
包含 Spearman 相關係數、Top-5 準確率、分組準確率
"""
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path

def load_prediction_results(csv_file):
    """載入預測結果 CSV"""
    if not Path(csv_file).exists():
        print(f"[錯誤] 找不到檔案: {csv_file}")
        return None
    
    df = pd.read_csv(csv_file)
    return df

def calculate_spearman(df):
    """計算 Spearman 等級相關係數"""
    # 基於實際 Q 時間排名
    df['actual_rank'] = df['actual_q'].rank(method='min')
    # 基於預測 Q 時間排名
    df['predicted_rank'] = df['predicted_q'].rank(method='min')
    
    # 計算 Spearman 相關係數
    correlation, p_value = spearmanr(df['actual_rank'], df['predicted_rank'])
    
    return {
        'correlation': correlation,
        'p_value': p_value,
        'interpretation': interpret_spearman(correlation)
    }

def interpret_spearman(rho):
    """解釋 Spearman 係數"""
    if rho >= 0.9:
        return "極強相關"
    elif rho >= 0.8:
        return "強相關"
    elif rho >= 0.7:
        return "中等相關"
    elif rho >= 0.5:
        return "弱相關"
    else:
        return "幾乎無相關"

def calculate_top_k_accuracy(df, k=5):
    """計算 Top-K 預測準確率"""
    # 實際 Top-K 車手
    actual_top_k = set(df.nsmallest(k, 'actual_q')['driver'].tolist())
    # 預測 Top-K 車手
    predicted_top_k = set(df.nsmallest(k, 'predicted_q')['driver'].tolist())
    
    # 交集數量
    correct = len(actual_top_k & predicted_top_k)
    
    return {
        'k': k,
        'correct': correct,
        'total': k,
        'accuracy': correct / k,
        'actual_top_k': sorted(actual_top_k),
        'predicted_top_k': sorted(predicted_top_k),
        'correctly_predicted': sorted(actual_top_k & predicted_top_k),
        'missed': sorted(actual_top_k - predicted_top_k),
        'false_positives': sorted(predicted_top_k - actual_top_k)
    }

def classify_drivers(df, method='quantile'):
    """將車手分為三組：頂尖/中游/墊底"""
    if method == 'quantile':
        # 基於 Q 時間四分位數
        q33 = df['actual_q'].quantile(0.33)
        q67 = df['actual_q'].quantile(0.67)
        
        def classify(q_time):
            if q_time <= q33:
                return 'Top'
            elif q_time <= q67:
                return 'Mid'
            else:
                return 'Bottom'
        
        df['actual_group'] = df['actual_q'].apply(classify)
        df['predicted_group'] = df['predicted_q'].apply(classify)
    
    elif method == 'fixed':
        # 固定分組：1-7 頂尖, 8-14 中游, 15-20 墊底
        def classify_by_position(pos):
            if pos <= 7:
                return 'Top'
            elif pos <= 14:
                return 'Mid'
            else:
                return 'Bottom'
        
        df['actual_group'] = df['position'].apply(classify_by_position)
        # 預測排名
        df['predicted_pos'] = df['predicted_q'].rank(method='min')
        df['predicted_group'] = df['predicted_pos'].apply(classify_by_position)
    
    return df

def calculate_group_accuracy(df):
    """計算分組準確率"""
    df = classify_drivers(df, method='quantile')
    
    # 整體準確率
    correct = (df['actual_group'] == df['predicted_group']).sum()
    total = len(df)
    overall_accuracy = correct / total
    
    # 每組準確率
    group_stats = {}
    for group in ['Top', 'Mid', 'Bottom']:
        group_df = df[df['actual_group'] == group]
        if len(group_df) > 0:
            correct_in_group = (group_df['actual_group'] == group_df['predicted_group']).sum()
            group_stats[group] = {
                'total': len(group_df),
                'correct': correct_in_group,
                'accuracy': correct_in_group / len(group_df),
                'drivers': group_df['driver'].tolist()
            }
    
    return {
        'overall_accuracy': overall_accuracy,
        'overall_correct': correct,
        'overall_total': total,
        'group_stats': group_stats
    }

def analyze_gap_accuracy(df):
    """分析車手間距離比例準確性"""
    # 計算實際與預測的前五名內部差距
    top5_actual = df.nsmallest(5, 'actual_q')
    top5_predicted = df.nsmallest(5, 'predicted_q')
    
    # 實際 P1-P5 圈速範圍
    actual_p1_p5_gap = top5_actual['actual_q'].max() - top5_actual['actual_q'].min()
    # 預測 P1-P5 圈速範圍
    predicted_p1_p5_gap = top5_predicted['predicted_q'].max() - top5_predicted['predicted_q'].min()
    
    # 實際 P1 vs P20 差距
    p1_actual = df['actual_q'].min()
    p20_actual = df['actual_q'].max()
    actual_p1_p20_gap = p20_actual - p1_actual
    
    # 預測 P1 vs P20 差距
    p1_predicted = df['predicted_q'].min()
    p20_predicted = df['predicted_q'].max()
    predicted_p1_p20_gap = p20_predicted - p1_predicted
    
    return {
        'top5_gap': {
            'actual': actual_p1_p5_gap,
            'predicted': predicted_p1_p5_gap,
            'difference': abs(actual_p1_p5_gap - predicted_p1_p5_gap),
            'relative_error': abs(actual_p1_p5_gap - predicted_p1_p5_gap) / actual_p1_p5_gap
        },
        'full_field_gap': {
            'actual': actual_p1_p20_gap,
            'predicted': predicted_p1_p20_gap,
            'difference': abs(actual_p1_p20_gap - predicted_p1_p20_gap),
            'relative_error': abs(actual_p1_p20_gap - predicted_p1_p20_gap) / actual_p1_p20_gap
        }
    }

def generate_trend_report(df, track_name='Unknown'):
    """生成完整的趨勢驗證報告"""
    print("="*80)
    print(f"{track_name} 趨勢驗證報告")
    print("="*80)
    
    # 1. Spearman 相關係數
    print("\n[指標 1] Spearman 等級相關係數")
    print("-"*80)
    spearman_results = calculate_spearman(df)
    print(f"  相關係數 (ρ): {spearman_results['correlation']:.4f}")
    print(f"  P 值: {spearman_results['p_value']:.6f}")
    print(f"  解釋: {spearman_results['interpretation']}")
    
    # 成功標準
    if spearman_results['correlation'] >= 0.8:
        print(f"  [通過] 達到目標 ≥ 0.8")
    else:
        print(f"  [未達標] 目標 ≥ 0.8，實際 {spearman_results['correlation']:.4f}")
    
    # 2. Top-K 準確率
    print("\n[指標 2] Top-K 預測準確率")
    print("-"*80)
    
    for k in [3, 5, 10]:
        topk_results = calculate_top_k_accuracy(df, k=k)
        print(f"\n  Top-{k} 準確率: {topk_results['accuracy']*100:.1f}% ({topk_results['correct']}/{topk_results['total']})")
        print(f"    實際 Top-{k}: {', '.join(topk_results['actual_top_k'])}")
        print(f"    預測 Top-{k}: {', '.join(topk_results['predicted_top_k'])}")
        print(f"    正確預測: {', '.join(topk_results['correctly_predicted'])}")
        if topk_results['missed']:
            print(f"    遺漏: {', '.join(topk_results['missed'])}")
        if topk_results['false_positives']:
            print(f"    誤判: {', '.join(topk_results['false_positives'])}")
    
    # 3. 分組準確率
    print("\n[指標 3] 分組準確率 (頂尖/中游/墊底)")
    print("-"*80)
    group_results = calculate_group_accuracy(df)
    print(f"\n  整體準確率: {group_results['overall_accuracy']*100:.1f}% ({group_results['overall_correct']}/{group_results['overall_total']})")
    
    for group_name in ['Top', 'Mid', 'Bottom']:
        if group_name in group_results['group_stats']:
            stats = group_results['group_stats'][group_name]
            print(f"\n  {group_name} 組:")
            print(f"    準確率: {stats['accuracy']*100:.1f}% ({stats['correct']}/{stats['total']})")
            print(f"    車手: {', '.join(stats['drivers'])}")
    
    # 4. 差距準確性
    print("\n[指標 4] 車手間差距準確性")
    print("-"*80)
    gap_results = analyze_gap_accuracy(df)
    
    print(f"\n  Top 5 內部差距:")
    print(f"    實際: {gap_results['top5_gap']['actual']:.3f}s")
    print(f"    預測: {gap_results['top5_gap']['predicted']:.3f}s")
    print(f"    誤差: {gap_results['top5_gap']['difference']:.3f}s ({gap_results['top5_gap']['relative_error']*100:.1f}%)")
    
    print(f"\n  全場差距 (P1 vs P20):")
    print(f"    實際: {gap_results['full_field_gap']['actual']:.3f}s")
    print(f"    預測: {gap_results['full_field_gap']['predicted']:.3f}s")
    print(f"    誤差: {gap_results['full_field_gap']['difference']:.3f}s ({gap_results['full_field_gap']['relative_error']*100:.1f}%)")
    
    # 5. 總評
    print("\n[總評]")
    print("-"*80)
    
    score = 0
    max_score = 4
    
    # Spearman ≥ 0.8
    if spearman_results['correlation'] >= 0.8:
        score += 1
        print(f"  [通過] Spearman 相關 ≥ 0.8 ({spearman_results['correlation']:.4f})")
    else:
        print(f"  [未通過] Spearman 相關 < 0.8 ({spearman_results['correlation']:.4f})")
    
    # Top-5 準確率 ≥ 60%
    top5_acc = calculate_top_k_accuracy(df, k=5)['accuracy']
    if top5_acc >= 0.6:
        score += 1
        print(f"  [通過] Top-5 準確率 ≥ 60% ({top5_acc*100:.1f}%)")
    else:
        print(f"  [未通過] Top-5 準確率 < 60% ({top5_acc*100:.1f}%)")
    
    # 分組準確率 ≥ 70%
    if group_results['overall_accuracy'] >= 0.7:
        score += 1
        print(f"  [通過] 分組準確率 ≥ 70% ({group_results['overall_accuracy']*100:.1f}%)")
    else:
        print(f"  [未通過] 分組準確率 < 70% ({group_results['overall_accuracy']*100:.1f}%)")
    
    # 差距相對誤差 ≤ 20%
    if gap_results['top5_gap']['relative_error'] <= 0.2:
        score += 1
        print(f"  [通過] Top 5 差距誤差 ≤ 20% ({gap_results['top5_gap']['relative_error']*100:.1f}%)")
    else:
        print(f"  [未通過] Top 5 差距誤差 > 20% ({gap_results['top5_gap']['relative_error']*100:.1f}%)")
    
    print(f"\n  總評分: {score}/{max_score}")
    
    if score == max_score:
        print(f"  評級: 優秀 (Excellent)")
    elif score >= 3:
        print(f"  評級: 良好 (Good)")
    elif score >= 2:
        print(f"  評級: 及格 (Pass)")
    else:
        print(f"  評級: 需改進 (Needs Improvement)")
    
    print("\n" + "="*80)
    
    return {
        'spearman': spearman_results,
        'topk': {k: calculate_top_k_accuracy(df, k) for k in [3, 5, 10]},
        'group': group_results,
        'gap': gap_results,
        'score': score,
        'max_score': max_score
    }

def main():
    """主函數"""
    # 載入墨西哥預測結果
    csv_file = 'reports/mexico_2025_prediction_results.csv'
    df = load_prediction_results(csv_file)
    
    if df is None:
        return
    
    # 生成趨勢報告
    results = generate_trend_report(df, track_name='2025 墨西哥站')
    
    # 保存詳細結果到 JSON
    import json
    output_file = 'reports/mexico_2025_trend_analysis.json'
    
    # 轉換為可 JSON 序列化的格式
    json_results = {
        'spearman': {
            'correlation': float(results['spearman']['correlation']),
            'p_value': float(results['spearman']['p_value']),
            'interpretation': results['spearman']['interpretation']
        },
        'topk': {
            str(k): {
                'accuracy': float(v['accuracy']),
                'correct': int(v['correct']),
                'total': int(v['total']),
                'actual_top_k': v['actual_top_k'],
                'predicted_top_k': v['predicted_top_k']
            } for k, v in results['topk'].items()
        },
        'group': {
            'overall_accuracy': float(results['group']['overall_accuracy']),
            'overall_correct': int(results['group']['overall_correct']),
            'overall_total': int(results['group']['overall_total'])
        },
        'gap': results['gap'],
        'score': int(results['score']),
        'max_score': int(results['max_score'])
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] 詳細結果已保存至: {output_file}")

if __name__ == '__main__':
    main()
