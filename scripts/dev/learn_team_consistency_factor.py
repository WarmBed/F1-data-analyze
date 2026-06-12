#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
車隊 FP2→Q 一致性因子學習腳本

從 2022-2025 的 FP2→Q 歷史數據學習各車隊的一致性調整因子。

核心邏輯:
1. 計算每個車隊在 FP2 Quali Sim 中的表現與實際 Q 表現的差異
2. 對於表現不穩定的車隊（標準差大），添加正向調整（懲罰）
3. 對於表現穩定的車隊（標準差小），不需要調整

輸出:
  training_data/team_consistency_factors.json

作者: GitHub Copilot
日期: 2026-01-04
"""

import json
import re
import statistics
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ===== 車隊名稱標準化映射 =====
TEAM_NAME_MAPPING = {
    'Alfa Romeo': 'Kick Sauber',
    'Sauber': 'Kick Sauber',
    'Alfa Romeo Racing': 'Kick Sauber',
    'AlphaTauri': 'Racing Bulls',
    'Scuderia AlphaTauri': 'Racing Bulls',
    'RB': 'Racing Bulls',
    'RB F1 Team': 'Racing Bulls',
    'Visa Cash App RB': 'Racing Bulls',
    'Aston Martin Aramco': 'Aston Martin',
    'Aston Martin Aramco Cognizant F1 Team': 'Aston Martin',
    'Red Bull Racing': 'Red Bull Racing',
    'Mercedes': 'Mercedes',
    'Ferrari': 'Ferrari',
    'McLaren': 'McLaren',
    'Alpine': 'Alpine',
    'Williams': 'Williams',
    'Haas F1 Team': 'Haas F1 Team',
    'Aston Martin': 'Aston Martin',
    'Racing Bulls': 'Racing Bulls',
    'Kick Sauber': 'Kick Sauber',
}


def normalize_team_name(team: str) -> str:
    """標準化車隊名稱"""
    team = team.strip()
    if team in TEAM_NAME_MAPPING:
        return TEAM_NAME_MAPPING[team]
    team_lower = team.lower()
    for old_name, new_name in TEAM_NAME_MAPPING.items():
        if old_name.lower() in team_lower or team_lower in old_name.lower():
            return new_name
    return team


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
    print(f"正在載入訓練數據: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"載入 {len(data)} 場比賽數據")
    return data


def extract_fp2_q_prediction_errors(data: List[dict]) -> Dict[str, List[dict]]:
    """
    提取每個車隊的 FP2→Q 預測誤差
    
    對於每個車手:
    1. 獲取 FP2 最佳圈速（優先使用 Quali Sim 圈）
    2. 獲取 Q 賽最佳圈速
    3. 計算差異 (Q - FP2)
    4. 按車隊分組收集這些差異
    
    Returns:
        Dict[str, List[dict]]: 車隊 -> 預測誤差列表
    """
    team_errors = defaultdict(list)
    
    for race in data:
        year = race['metadata']['year']
        race_name = race['metadata']['race']
        
        fp2_data = race.get('practice_sessions', {}).get('FP2', {}).get('driver_data', {})
        q_results = race.get('qualifying', {}).get('results', {})
        
        for driver, fp2_info in fp2_data.items():
            if driver not in q_results:
                continue
            
            # 獲取 FP2 最佳圈速
            fp2_time = fp2_info.get('best_lap_time')
            if fp2_time is None or fp2_time <= 0 or fp2_time > 120:
                continue
            
            # 獲取輪胎壽命（用於識別 Quali Sim）
            tire_age = fp2_info.get('tire_age_avg')
            is_quali_sim = tire_age is not None and tire_age <= 3
            
            # 獲取車隊（標準化名稱）
            team = fp2_info.get('team', 'Unknown')
            team = normalize_team_name(team)
            
            # 獲取 Q 賽最佳圈速
            q_info = q_results[driver]
            q_time_str = q_info.get('best_time')
            q_time = parse_timedelta_to_seconds(q_time_str)
            
            if q_time is None or q_time <= 0 or q_time > 120:
                continue
            
            # 計算差異 (Q - FP2)
            # 正值 = Q 比 FP2 慢（FP2 表現太好）
            # 負值 = Q 比 FP2 快（正常進步）
            delta = q_time - fp2_time
            
            # 年份權重: 近年數據權重更高
            year_weights = {2025: 2.0, 2024: 1.5, 2023: 1.0, 2022: 0.7}
            year_weight = year_weights.get(year, 1.0)
            
            team_errors[team].append({
                'year': year,
                'race': race_name,
                'driver': driver,
                'fp2_time': fp2_time,
                'q_time': q_time,
                'delta': delta,
                'is_quali_sim': is_quali_sim,
                'tire_age': tire_age,
                'year_weight': year_weight
            })
    
    return team_errors


def calculate_team_consistency_factors(team_errors: Dict[str, List[dict]]) -> Dict[str, dict]:
    """
    計算車隊一致性調整因子
    
    對於每個車隊:
    1. 僅使用 Quali Sim 圈的 FP2→Q 差異
    2. 使用年份加權計算平均值和標準差（近年數據權重更高）
    3. 對於表現不一致的車隊（標準差大或平均誤差大）添加調整
    
    調整公式:
    adjusted_prediction = base_prediction + consistency_adjustment
    """
    results = {}
    
    # 收集所有車隊的 Quali Sim 加權標準差和平均值
    all_qs_stds = []
    all_qs_means = []
    
    for team, errors in team_errors.items():
        # 僅使用 Quali Sim 圈的數據
        qs_errors = [e for e in errors if e['is_quali_sim']]
        
        if len(qs_errors) < 10:  # 至少需要 10 個 Quali Sim 樣本
            continue
        
        # 加權平均計算
        total_weight = sum(e['year_weight'] for e in qs_errors)
        weighted_sum = sum(e['delta'] * e['year_weight'] for e in qs_errors)
        qs_mean = weighted_sum / total_weight if total_weight > 0 else 0
        
        # 加權標準差計算
        weighted_var_sum = sum(e['year_weight'] * (e['delta'] - qs_mean) ** 2 for e in qs_errors)
        qs_std = (weighted_var_sum / total_weight) ** 0.5 if total_weight > 0 else 0
        
        all_qs_stds.append(qs_std)
        all_qs_means.append(qs_mean)
        
        # 計算「異常值比例」- 與平均值偏差超過 2 標準差的樣本比例
        if qs_std > 0:
            outlier_count = sum(1 for e in qs_errors if abs(e['delta'] - qs_mean) > 2 * qs_std)
            outlier_ratio = outlier_count / len(qs_errors)
        else:
            outlier_ratio = 0
        
        results[team] = {
            'sample_count': len(errors),
            'quali_sim_count': len(qs_errors),
            'qs_mean_delta': qs_mean,
            'qs_std_delta': qs_std,
            'outlier_ratio': outlier_ratio,
            'min_delta': min(e['delta'] for e in qs_errors),
            'max_delta': max(e['delta'] for e in qs_errors),
        }
    
    # 計算基準值（所有車隊 Quali Sim 數據的中位數）
    baseline_std = statistics.median(all_qs_stds) if all_qs_stds else 1.0
    baseline_mean = statistics.median(all_qs_means) if all_qs_means else 0.0
    
    print(f"\n基準標準差 (Quali Sim 加權): {baseline_std:.3f}s")
    print(f"基準平均差異 (Quali Sim 加權): {baseline_mean:.3f}s")
    
    # 計算每個車隊的調整因子
    for team, info in results.items():
        qs_std = info['qs_std_delta']
        qs_mean = info['qs_mean_delta']
        outlier_ratio = info['outlier_ratio']
        
        # 一致性調整: 變異大的車隊需要調整
        # 只對標準差高於基準的車隊進行調整
        std_excess = max(0, qs_std - baseline_std)
        
        # 偏差調整: 如果 FP2 Quali Sim 總是比 Q 快（mean_delta > baseline），需要調整
        # 這是「除了燃油修正以外」的額外差異
        mean_excess = max(0, qs_mean - baseline_mean)
        
        # 調整強度
        # 標準差調整: 使用額外標準差的 25% (增強調整)
        std_strength = 0.25
        consistency_adjustment = std_excess * std_strength
        
        # 偏差調整: 使用額外偏差的 20% (增強調整)
        bias_strength = 0.20
        bias_adjustment = mean_excess * bias_strength
        
        # 異常值調整: 異常值比例高的車隊需要更多調整
        # 如果異常值比例 > 5%，每多 1% 加 0.05s
        outlier_adjustment = max(0, (outlier_ratio - 0.05)) * 5.0
        
        # 總調整 = 一致性調整 + 偏差調整 + 異常值調整
        # 限制最大調整為 1.0s
        total_adjustment = min(1.0, consistency_adjustment + bias_adjustment + outlier_adjustment)
        
        info['baseline_std'] = baseline_std
        info['baseline_mean'] = baseline_mean
        info['std_excess'] = std_excess
        info['mean_excess'] = mean_excess
        info['consistency_adjustment'] = consistency_adjustment
        info['bias_adjustment'] = bias_adjustment
        info['outlier_adjustment'] = outlier_adjustment
        info['total_adjustment'] = total_adjustment
        
        # 判斷調整類型
        if total_adjustment > 0.3:
            info['adjustment_type'] = 'HIGH'  # 高調整（不穩定車隊）
        elif total_adjustment > 0.1:
            info['adjustment_type'] = 'MEDIUM'  # 中等調整
        else:
            info['adjustment_type'] = 'LOW'  # 低調整（穩定車隊）
    
    return results


def save_consistency_factors(factors: Dict[str, dict], output_path: str):
    """保存一致性因子到 JSON 文件"""
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'fp2_q_training_data_2022_2025.json',
            'description': '車隊 FP2→Q 一致性調整因子（從歷史數據學習）',
            'formula': 'adjusted_prediction = base_prediction + total_adjustment',
        },
        'team_factors': factors
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n一致性因子已保存到: {output_path}")


def main():
    # 載入訓練數據
    training_file = Path(__file__).parent / "training_data" / "fp2_q_training_data_2022_2025.json"
    data = load_training_data(str(training_file))
    
    # 提取 FP2→Q 預測誤差
    print("\n提取 FP2→Q 預測誤差...")
    team_errors = extract_fp2_q_prediction_errors(data)
    
    total_samples = sum(len(errors) for errors in team_errors.values())
    print(f"提取 {total_samples} 個樣本，涵蓋 {len(team_errors)} 個車隊")
    
    # 計算一致性因子
    print("\n計算車隊一致性調整因子...")
    factors = calculate_team_consistency_factors(team_errors)
    
    # 保存結果
    output_path = Path(__file__).parent / "training_data" / "team_consistency_factors.json"
    save_consistency_factors(factors, str(output_path))
    
    # 打印報告
    print("\n" + "=" * 100)
    print("車隊 FP2→Q 一致性調整因子報告 (僅基於 Quali Sim 數據)")
    print("=" * 100)
    print(f"\n{'車隊':<20} {'樣本':>6} {'QS圈':>6} {'QS平均Δ':>10} {'QS標準差':>10} {'調整值':>10} {'類型':>8}")
    print("-" * 90)
    
    # 按調整值排序
    sorted_factors = sorted(factors.items(), key=lambda x: x[1]['total_adjustment'], reverse=True)
    
    for team, info in sorted_factors:
        print(f"{team:<20} {info['sample_count']:>6} {info['quali_sim_count']:>6} "
              f"{info['qs_mean_delta']:>+10.3f} {info['qs_std_delta']:>10.3f} "
              f"{info['total_adjustment']:>+10.3f} {info['adjustment_type']:>8}")
    
    print("-" * 90)
    print("\n說明:")
    print("  - QS平均Δ: Q時間 - FP2 Quali Sim時間 的平均值（正值 = FP2 比 Q 快）")
    print("  - QS標準差: FP2 Quali Sim → Q 表現的變異程度")
    print("  - 調整值: 預測時需要加上的調整秒數（基於歷史一致性）")
    print("  - HIGH: 高調整（>0.3s），MEDIUM: 中等調整（0.1-0.3s），LOW: 低調整（<0.1s）")


if __name__ == "__main__":
    main()
