#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
車隊 FP2→Q 預測殘差調整因子學習腳本

這個腳本使用更精確的方法來計算調整因子：
1. 模擬 Function 76 的預測邏輯
2. 計算每個車隊的預測殘差
3. 生成殘差調整因子

輸出:
  training_data/team_residual_adjustment.json

作者: GitHub Copilot
日期: 2026-01-04
"""

import json
import re
import statistics
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional


def load_training_data(filepath: str) -> List[dict]:
    """載入訓練數據"""
    print(f"正在載入訓練數據: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"載入 {len(data)} 場比賽數據")
    return data


def parse_timedelta_to_seconds(time_str: str) -> Optional[float]:
    """將 timedelta 字串轉換為秒數"""
    if not time_str:
        return None
    match = re.search(r'(\d+):(\d+):(\d+\.?\d*)', time_str)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return None


def identify_quali_sim_laps(driver_data: dict) -> bool:
    """判斷車手是否有 Quali Sim 圈"""
    # 檢查是否有 tire_age_avg <= 3 的圈
    tire_age = driver_data.get('tire_age_avg')
    return tire_age is not None and tire_age <= 3


def calculate_residual_adjustment(data: List[dict]) -> Dict[str, dict]:
    """
    計算車隊的預測殘差調整因子
    
    邏輯:
    1. 對每個車隊，計算所有 FP2 Quali Sim 圈 vs Q 時間的差異
    2. 「差異」= Q 時間 - FP2 Quali Sim 時間
    3. 如果平均差異是正數，表示 Q 通常比 FP2 慢，需要加大調整
    4. 如果平均差異是負數，表示 Q 通常比 FP2 快，不需要額外調整
    """
    # 車隊名稱標準化映射（合併舊名到新名）
    team_name_mapping = {
        # Alfa Romeo → Kick Sauber (2024 更名)
        'Alfa Romeo': 'Kick Sauber',
        'Alfa Romeo Racing': 'Kick Sauber',
        'Sauber': 'Kick Sauber',
        # AlphaTauri → RB → Racing Bulls (2024 更名)
        'AlphaTauri': 'Racing Bulls',
        'RB': 'Racing Bulls',
        'Scuderia AlphaTauri': 'Racing Bulls',
        # 其他車隊保持原名
    }
    
    team_residuals = defaultdict(list)
    
    # 年份權重
    year_weights = {2025: 2.0, 2024: 1.5, 2023: 1.0, 2022: 0.7}
    
    for race in data:
        year = race['metadata']['year']
        race_name = race['metadata']['race']
        year_weight = year_weights.get(year, 1.0)
        
        fp2 = race.get('practice_sessions', {}).get('FP2', {}).get('driver_data', {})
        q = race.get('qualifying', {}).get('results', {})
        
        for driver, fp2_info in fp2.items():
            team_raw = fp2_info.get('team', 'Unknown')
            # 標準化車隊名稱
            team = team_name_mapping.get(team_raw, team_raw)
            
            # 只處理有 Quali Sim 數據的車手
            if not identify_quali_sim_laps(fp2_info):
                continue
            
            fp2_time = fp2_info.get('best_lap_time', 0)
            if not fp2_time or fp2_time <= 0 or fp2_time > 120:
                continue
            
            if driver not in q:
                continue
            
            q_time_str = q[driver].get('best_time', '')
            q_time = parse_timedelta_to_seconds(q_time_str)
            
            if not q_time or q_time <= 0 or q_time > 120:
                continue
            
            # 殘差 = Q 時間 - FP2 Quali Sim 時間
            # 正數 = Q 比 FP2 慢（需要加大預測時間）
            # 負數 = Q 比 FP2 快（這是正常的，因為 Q 有更好的賽道條件）
            residual = q_time - fp2_time
            
            team_residuals[team].append({
                'year': year,
                'race': race_name,
                'driver': driver,
                'fp2_time': fp2_time,
                'q_time': q_time,
                'residual': residual,
                'year_weight': year_weight
            })
    
    # 計算每個車隊的調整因子
    results = {}
    global_residuals = []
    global_weights = []
    
    for team, entries in team_residuals.items():
        if len(entries) < 5:
            continue
        
        residuals = [e['residual'] for e in entries]
        weights = [e['year_weight'] for e in entries]
        
        global_residuals.extend(residuals)
        global_weights.extend(weights)
    
    # 計算全局加權平均殘差
    total_weight = sum(global_weights)
    global_mean_residual = sum(r * w for r, w in zip(global_residuals, global_weights)) / total_weight if total_weight > 0 else 0
    
    print(f"\n全局加權平均殘差: {global_mean_residual:.3f}s (Q - FP2 Quali Sim)")
    
    for team, entries in team_residuals.items():
        if len(entries) < 5:
            continue
        
        residuals = [e['residual'] for e in entries]
        weights = [e['year_weight'] for e in entries]
        
        # 加權平均
        total_weight = sum(weights)
        mean_residual = sum(r * w for r, w in zip(residuals, weights)) / total_weight if total_weight > 0 else 0
        
        # 加權標準差
        weighted_var = sum(w * (r - mean_residual) ** 2 for r, w in zip(residuals, weights)) / total_weight if total_weight > 0 else 0
        std_residual = weighted_var ** 0.5
        
        # 相對於全局平均的調整量
        # 如果這個車隊的殘差比全局高，需要更大的調整
        relative_adjustment = mean_residual - global_mean_residual
        
        # 標準差調整：高標準差表示不穩定，需要額外調整
        # 但只在殘差為正時添加（即 Q 比 FP2 慢的情況）
        std_adjustment = 0.0
        if std_residual > 8.0:  # 全局 std 約 8.0
            std_adjustment = (std_residual - 8.0) * 0.1
        
        # 總調整量
        total_adjustment = max(0, relative_adjustment + std_adjustment)
        
        results[team] = {
            'sample_count': len(entries),
            'mean_residual': mean_residual,
            'std_residual': std_residual,
            'global_mean': global_mean_residual,
            'relative_adjustment': relative_adjustment,
            'std_adjustment': std_adjustment,
            'total_adjustment': total_adjustment
        }
    
    return results


def save_results(factors: Dict[str, dict], output_path: str):
    """保存結果到 JSON 文件"""
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'fp2_q_training_data_2022_2025.json',
            'description': '車隊 FP2→Q 預測殘差調整因子（僅 Quali Sim 圈）',
            'formula': 'adjusted_prediction = base_prediction + total_adjustment',
            'note': '正的 mean_residual 表示 Q 通常比 FP2 Quali Sim 慢'
        },
        'team_factors': factors
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n調整因子已保存到: {output_path}")


def main():
    # 載入訓練數據
    training_file = Path(__file__).parent / "training_data" / "fp2_q_training_data_2022_2025.json"
    data = load_training_data(str(training_file))
    
    # 計算殘差調整因子
    print("\n計算車隊預測殘差調整因子（僅使用 Quali Sim 圈）...")
    factors = calculate_residual_adjustment(data)
    
    # 保存結果
    output_path = Path(__file__).parent / "training_data" / "team_residual_adjustment.json"
    save_results(factors, str(output_path))
    
    # 打印報告
    print("\n" + "=" * 90)
    print("車隊 FP2→Q 預測殘差調整因子報告 (年份加權)")
    print("=" * 90)
    print(f"\n{'車隊':<20} {'樣本':>6} {'平均殘差':>10} {'標準差':>10} {'相對調整':>10} {'總調整':>10}")
    print("-" * 80)
    
    # 按總調整值排序
    sorted_factors = sorted(factors.items(), key=lambda x: x[1]['total_adjustment'], reverse=True)
    
    for team, info in sorted_factors:
        print(f"{team:<20} {info['sample_count']:>6} "
              f"{info['mean_residual']:>+10.3f} {info['std_residual']:>10.3f} "
              f"{info['relative_adjustment']:>+10.3f} {info['total_adjustment']:>+10.3f}")
    
    print("-" * 80)
    print("\n說明:")
    print("  - 平均殘差: Q時間 - FP2 Quali Sim 時間 的加權平均值")
    print("  - 正數 = Q 通常比 FP2 Quali Sim 慢（需要加大預測）")
    print("  - 負數 = Q 通常比 FP2 Quali Sim 快（正常情況）")
    print("  - 總調整: 相對於全局平均的額外調整量")


if __name__ == "__main__":
    main()
