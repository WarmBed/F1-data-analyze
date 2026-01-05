#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FP2→Q 車隊燃油校正效果評估腳本

評估方案 B（車隊 FP2 燃油習慣校正）的改善效果

作者: GitHub Copilot
日期: 2026-01-04
"""

import json
import os
import re
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
import statistics


def parse_timedelta_to_seconds(time_str: str) -> Optional[float]:
    """將 timedelta 字串轉換為秒數"""
    if not time_str or time_str == 'NaT':
        return None
    
    match = re.search(r'(\d+):(\d+):(\d+\.?\d*)', time_str)
    if match:
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    
    return None


def load_training_data(filepath: str) -> List[dict]:
    """載入訓練數據"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def load_team_habits(filepath: str) -> Dict[str, dict]:
    """載入車隊燃油習慣"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('team_habits', {})


def extract_fp2_q_pairs_for_evaluation(data: List[dict]) -> List[dict]:
    """提取 FP2→Q 配對數據用於評估"""
    pairs = []
    
    for race in data:
        year = race['metadata']['year']
        race_name = race['metadata']['race']
        
        fp2_data = race.get('practice_sessions', {}).get('FP2', {}).get('driver_data', {})
        q_results = race.get('qualifying', {}).get('results', {})
        
        for driver, fp2_info in fp2_data.items():
            if driver not in q_results:
                continue
            
            fp2_time = fp2_info.get('best_lap_time')
            if fp2_time is None or fp2_time <= 0 or fp2_time > 120:
                continue
            
            tire_age = fp2_info.get('tire_age_avg')
            if tire_age is None or not isinstance(tire_age, (int, float)):
                tire_age = 10
            
            team = fp2_info.get('team', 'Unknown')
            
            q_info = q_results[driver]
            q_time_str = q_info.get('best_time')
            q_time = parse_timedelta_to_seconds(q_time_str)
            
            if q_time is None or q_time <= 0:
                continue
            
            improvement = fp2_time - q_time
            
            if improvement < -1 or improvement > 10:
                continue
            
            pairs.append({
                'year': year,
                'race': race_name,
                'driver': driver,
                'team': team,
                'fp2_time': fp2_time,
                'q_time': q_time,
                'improvement': improvement,
                'tire_age_avg': tire_age,
                'is_quali_sim': tire_age <= 3
            })
    
    return pairs


def evaluate_correction_methods(pairs: List[dict], team_habits: Dict[str, dict]) -> Dict[str, dict]:
    """評估不同校正方法的效果"""
    
    # 物理常數
    FUEL_COEF = 0.032  # s/kg
    DEFAULT_FUEL_DIFF = 58  # kg (假設 FP2: 70kg, Q: 12kg)
    
    results = {
        'no_correction': {'errors': [], 'predictions': []},  # 無校正
        'fixed_correction': {'errors': [], 'predictions': []},  # 固定 58kg 校正
        'team_correction': {'errors': [], 'predictions': []},  # 車隊特定校正
        'team_correction_qs_only': {'errors': [], 'predictions': []}  # 車隊校正 (僅 Quali Sim)
    }
    
    for pair in pairs:
        team = pair['team']
        fp2_time = pair['fp2_time']
        q_time = pair['q_time']
        actual_improvement = pair['improvement']
        is_quali_sim = pair['is_quali_sim']
        
        # === 方法 1: 無校正 ===
        # 直接使用 FP2 時間作為 Q 預測
        pred_no_correction = fp2_time
        error_no_correction = abs(pred_no_correction - q_time)
        results['no_correction']['errors'].append(error_no_correction)
        results['no_correction']['predictions'].append({
            'actual': q_time,
            'predicted': pred_no_correction,
            'error': error_no_correction
        })
        
        # === 方法 2: 固定校正 ===
        # 假設固定 58kg 燃油差異
        fixed_correction = DEFAULT_FUEL_DIFF * FUEL_COEF  # 1.856s
        pred_fixed = fp2_time - fixed_correction
        error_fixed = abs(pred_fixed - q_time)
        results['fixed_correction']['errors'].append(error_fixed)
        results['fixed_correction']['predictions'].append({
            'actual': q_time,
            'predicted': pred_fixed,
            'error': error_fixed
        })
        
        # === 方法 3: 車隊特定校正 ===
        if team in team_habits:
            team_correction = team_habits[team].get('fuel_correction_seconds', fixed_correction)
        else:
            team_correction = fixed_correction
        
        pred_team = fp2_time - team_correction
        error_team = abs(pred_team - q_time)
        results['team_correction']['errors'].append(error_team)
        results['team_correction']['predictions'].append({
            'actual': q_time,
            'predicted': pred_team,
            'error': error_team
        })
        
        # === 方法 4: 車隊校正 (僅 Quali Sim 圈) ===
        if is_quali_sim:
            results['team_correction_qs_only']['errors'].append(error_team)
            results['team_correction_qs_only']['predictions'].append({
                'actual': q_time,
                'predicted': pred_team,
                'error': error_team
            })
    
    # 計算統計
    summary = {}
    for method, data in results.items():
        errors = data['errors']
        if errors:
            summary[method] = {
                'sample_count': len(errors),
                'mae': round(statistics.mean(errors), 3),
                'median_error': round(statistics.median(errors), 3),
                'std_error': round(statistics.stdev(errors), 3) if len(errors) > 1 else 0,
                'min_error': round(min(errors), 3),
                'max_error': round(max(errors), 3),
                'p90_error': round(sorted(errors)[int(len(errors) * 0.9)], 3)
            }
    
    return summary


def evaluate_by_race(pairs: List[dict], team_habits: Dict[str, dict]) -> Dict[str, dict]:
    """按賽事評估校正效果"""
    
    FUEL_COEF = 0.032
    DEFAULT_FUEL_DIFF = 58
    
    race_results = defaultdict(lambda: {'fixed': [], 'team': []})
    
    for pair in pairs:
        team = pair['team']
        fp2_time = pair['fp2_time']
        q_time = pair['q_time']
        year = pair['year']
        race = pair['race']
        race_key = f"{year}_{race}"
        
        # 固定校正
        fixed_correction = DEFAULT_FUEL_DIFF * FUEL_COEF
        pred_fixed = fp2_time - fixed_correction
        error_fixed = abs(pred_fixed - q_time)
        
        # 車隊校正
        if team in team_habits:
            team_correction = team_habits[team].get('fuel_correction_seconds', fixed_correction)
        else:
            team_correction = fixed_correction
        
        pred_team = fp2_time - team_correction
        error_team = abs(pred_team - q_time)
        
        race_results[race_key]['fixed'].append(error_fixed)
        race_results[race_key]['team'].append(error_team)
    
    # 計算每場比賽的改善
    improvements = []
    for race_key, data in race_results.items():
        fixed_mae = statistics.mean(data['fixed'])
        team_mae = statistics.mean(data['team'])
        improvement = fixed_mae - team_mae
        improvements.append({
            'race': race_key,
            'fixed_mae': round(fixed_mae, 3),
            'team_mae': round(team_mae, 3),
            'improvement': round(improvement, 3),
            'sample_count': len(data['fixed'])
        })
    
    # 按改善幅度排序
    improvements.sort(key=lambda x: x['improvement'], reverse=True)
    
    return improvements


def print_evaluation_report(summary: Dict[str, dict], race_improvements: List[dict]):
    """列印評估報告"""
    print("\n" + "=" * 100)
    print("FP2→Q 車隊燃油校正效果評估報告")
    print("=" * 100)
    
    print("\n【整體校正方法比較】")
    print(f"\n{'方法':<25} {'樣本數':>8} {'MAE':>10} {'中位數':>10} {'P90':>10} {'最大誤差':>10}")
    print("-" * 100)
    
    method_names = {
        'no_correction': '無校正 (直接使用 FP2)',
        'fixed_correction': '固定校正 (58kg)',
        'team_correction': '車隊特定校正',
        'team_correction_qs_only': '車隊校正 (僅 Quali Sim)'
    }
    
    for method, stats in summary.items():
        name = method_names.get(method, method)
        print(f"{name:<25} {stats['sample_count']:>8} {stats['mae']:>9.3f}s "
              f"{stats['median_error']:>9.3f}s {stats['p90_error']:>9.3f}s {stats['max_error']:>9.3f}s")
    
    print("-" * 100)
    
    # 計算改善幅度
    if 'fixed_correction' in summary and 'team_correction' in summary:
        fixed_mae = summary['fixed_correction']['mae']
        team_mae = summary['team_correction']['mae']
        improvement = fixed_mae - team_mae
        improvement_pct = (improvement / fixed_mae) * 100 if fixed_mae > 0 else 0
        
        print(f"\n【車隊校正 vs 固定校正 改善分析】")
        print(f"  固定校正 MAE: {fixed_mae:.3f}s")
        print(f"  車隊校正 MAE: {team_mae:.3f}s")
        print(f"  改善幅度: {improvement:.3f}s ({improvement_pct:.1f}%)")
    
    if 'team_correction_qs_only' in summary:
        qs_mae = summary['team_correction_qs_only']['mae']
        print(f"  僅 Quali Sim 圈 MAE: {qs_mae:.3f}s")
    
    # 按賽事分析
    print(f"\n【按賽事改善分析 (Top 10 改善最大)】")
    print(f"\n{'賽事':<30} {'固定MAE':>10} {'車隊MAE':>10} {'改善':>10} {'樣本':>6}")
    print("-" * 80)
    
    for race in race_improvements[:10]:
        print(f"{race['race']:<30} {race['fixed_mae']:>9.3f}s "
              f"{race['team_mae']:>9.3f}s {race['improvement']:>9.3f}s {race['sample_count']:>6}")
    
    print(f"\n【按賽事改善分析 (Bottom 5 改善最小/退步)】")
    print(f"\n{'賽事':<30} {'固定MAE':>10} {'車隊MAE':>10} {'改善':>10} {'樣本':>6}")
    print("-" * 80)
    
    for race in race_improvements[-5:]:
        print(f"{race['race']:<30} {race['fixed_mae']:>9.3f}s "
              f"{race['team_mae']:>9.3f}s {race['improvement']:>9.3f}s {race['sample_count']:>6}")


def save_evaluation_report(summary: Dict[str, dict], race_improvements: List[dict], output_path: str):
    """儲存評估報告為 JSON"""
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'description': 'FP2→Q 車隊燃油校正效果評估'
        },
        'method_comparison': summary,
        'race_improvements': race_improvements,
        'summary': {
            'improvement_seconds': round(
                summary['fixed_correction']['mae'] - summary['team_correction']['mae'], 3
            ) if 'fixed_correction' in summary and 'team_correction' in summary else 0,
            'improvement_percent': round(
                (summary['fixed_correction']['mae'] - summary['team_correction']['mae']) 
                / summary['fixed_correction']['mae'] * 100, 1
            ) if 'fixed_correction' in summary and 'team_correction' in summary else 0
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 評估報告已儲存: {output_path}")


def main():
    """主程式"""
    # 路徑設定
    training_data_path = 'training_data/fp2_q_training_data_2022_2025.json'
    team_habits_path = 'training_data/team_fuel_habits.json'
    output_path = 'training_data/fuel_correction_evaluation.json'
    
    print("載入數據...")
    data = load_training_data(training_data_path)
    team_habits = load_team_habits(team_habits_path)
    
    print(f"載入 {len(data)} 場比賽數據")
    print(f"載入 {len(team_habits)} 個車隊燃油習慣")
    
    # 提取評估配對
    pairs = extract_fp2_q_pairs_for_evaluation(data)
    print(f"提取 {len(pairs)} 個有效 FP2→Q 配對")
    
    # 評估不同方法
    summary = evaluate_correction_methods(pairs, team_habits)
    
    # 按賽事評估
    race_improvements = evaluate_by_race(pairs, team_habits)
    
    # 列印報告
    print_evaluation_report(summary, race_improvements)
    
    # 儲存報告
    save_evaluation_report(summary, race_improvements, output_path)


if __name__ == '__main__':
    main()
