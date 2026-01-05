#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
車隊 FP2 燃油習慣學習腳本

方案 B: 從歷史 FP2→Q 數據學習各車隊的「典型 FP2 燃油量」

核心邏輯:
1. 燃油係數是物理常數 (~0.032 s/kg)
2. Q 燃油量固定 (~12 kg)
3. 從 FP2→Q 改善量反推各車隊的典型 FP2 燃油量

公式:
  improvement = fp2_time - q_time
  estimated_fp2_fuel = Q_FUEL + improvement / FUEL_COEF
  
作者: GitHub Copilot
日期: 2026-01-04
"""

import json
import os
import re
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import statistics


# ===== 物理常數 =====
FUEL_COEF = 0.032  # 秒/公斤 (燃油重量對圈速的影響)
Q_FUEL = 12  # 公斤 (Q 賽典型燃油量)

# ===== 車隊名稱標準化映射 =====
# 處理車隊更名：將舊名稱統一映射到新名稱
TEAM_NAME_MAPPING = {
    # 2024-2025 Racing Bulls 車隊演變
    # AlphaTauri (2022-2023) → RB (2024 初期) → Racing Bulls (2024-2025)
    'Alfa Romeo': 'Kick Sauber',
    'Sauber': 'Kick Sauber',
    'Alfa Romeo Racing': 'Kick Sauber',
    'AlphaTauri': 'Racing Bulls',
    'Scuderia AlphaTauri': 'Racing Bulls',
    'RB': 'Racing Bulls',  # 🔧 修正: RB 是 Racing Bulls 的 2024 年名稱
    'RB F1 Team': 'Racing Bulls',
    'Visa Cash App RB': 'Racing Bulls',
    # 2023 年更名
    'Aston Martin Aramco': 'Aston Martin',
    'Aston Martin Aramco Cognizant F1 Team': 'Aston Martin',
    # 保持原名（標準化拼寫）
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
    """
    標準化車隊名稱
    
    將舊車隊名稱映射到新名稱，確保訓練數據一致性
    例如: Alfa Romeo (2022-2023) → Kick Sauber (2024+)
    """
    # 先去除前後空白
    team = team.strip()
    
    # 檢查映射表
    if team in TEAM_NAME_MAPPING:
        return TEAM_NAME_MAPPING[team]
    
    # 如果沒有找到，嘗試模糊匹配
    team_lower = team.lower()
    for old_name, new_name in TEAM_NAME_MAPPING.items():
        if old_name.lower() in team_lower or team_lower in old_name.lower():
            return new_name
    
    # 找不到映射，返回原名稱
    return team


def parse_timedelta_to_seconds(time_str: str) -> Optional[float]:
    """將 timedelta 字串轉換為秒數"""
    if not time_str or time_str == 'NaT':
        return None
    
    # 格式: "0 days 00:01:30.558000"
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


def extract_fp2_q_pairs(data: List[dict]) -> List[dict]:
    """
    提取 FP2→Q 配對數據
    
    只使用「低輪胎壽命」的圈作為 Quali Sim 圈
    (tire_age_avg <= 3 表示新胎)
    """
    pairs = []
    
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
            if fp2_time is None or fp2_time <= 0:
                continue
            
            # 過濾異常值 (圈速 > 2 分鐘可能是異常)
            if fp2_time > 120:
                continue
            
            # 獲取輪胎壽命 (None 時預設為 10，表示非 Quali Sim)
            tire_age = fp2_info.get('tire_age_avg')
            if tire_age is None or not isinstance(tire_age, (int, float)):
                tire_age = 10
            
            # 獲取車隊（標準化名稱）
            team = fp2_info.get('team', 'Unknown')
            team = normalize_team_name(team)  # 🔧 標準化車隊名稱
            
            # 獲取 Q 賽最佳圈速
            q_info = q_results[driver]
            q_time_str = q_info.get('best_time')
            q_time = parse_timedelta_to_seconds(q_time_str)
            
            if q_time is None or q_time <= 0:
                continue
            
            # 計算改善量
            improvement = fp2_time - q_time
            
            # 過濾異常改善量 (負值表示 FP2 比 Q 快，不合理)
            # 或改善量過大 (> 10 秒，可能是測試圈)
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
                'is_quali_sim': tire_age <= 3  # 新胎 = 可能是 Quali Sim
            })
    
    print(f"提取 {len(pairs)} 個有效 FP2→Q 配對")
    return pairs


def learn_team_fuel_habits(pairs: List[dict]) -> Dict[str, dict]:
    """
    學習各車隊的 FP2 燃油習慣
    
    改進版: 分別計算 Quali Sim 圈和一般圈的統計
    """
    team_data = defaultdict(lambda: {'quali_sim': [], 'all': []})
    
    for pair in pairs:
        team = pair['team']
        improvement = pair['improvement']
        is_quali_sim = pair['is_quali_sim']
        
        # 只使用合理的改善量
        if -0.5 <= improvement <= 8:
            team_data[team]['all'].append(improvement)
            if is_quali_sim:
                team_data[team]['quali_sim'].append(improvement)
    
    team_habits = {}
    
    for team, samples in team_data.items():
        all_samples = samples['all']
        qs_samples = samples['quali_sim']
        
        if len(all_samples) < 10:  # 至少需要 10 個樣本
            continue
        
        # 計算全部樣本的平均
        all_avg = statistics.mean(all_samples)
        all_std = statistics.stdev(all_samples) if len(all_samples) > 1 else 0
        
        # 計算 Quali Sim 圈的平均 (如果有足夠樣本)
        if len(qs_samples) >= 5:
            qs_avg = statistics.mean(qs_samples)
            qs_std = statistics.stdev(qs_samples) if len(qs_samples) > 1 else 0
        else:
            qs_avg = None
            qs_std = None
        
        # 反推燃油量
        estimated_fp2_fuel_all = Q_FUEL + all_avg / FUEL_COEF
        estimated_fp2_fuel_qs = Q_FUEL + qs_avg / FUEL_COEF if qs_avg else None
        
        team_habits[team] = {
            'sample_count': len(all_samples),
            'quali_sim_count': len(qs_samples),
            # 全部樣本統計
            'all_avg_improvement': round(all_avg, 3),
            'all_std_improvement': round(all_std, 3),
            'all_estimated_fuel_kg': round(estimated_fp2_fuel_all, 1),
            # Quali Sim 圈統計
            'qs_avg_improvement': round(qs_avg, 3) if qs_avg else None,
            'qs_std_improvement': round(qs_std, 3) if qs_std else None,
            'qs_estimated_fuel_kg': round(estimated_fp2_fuel_qs, 1) if estimated_fp2_fuel_qs else None,
            # 用於預測的校正值 (嚴格僅使用 Quali Sim，無回退)
            'fuel_correction_seconds': round(qs_avg, 3) if qs_avg else None,
            'estimated_fp2_fuel_kg': round(estimated_fp2_fuel_qs, 1) if estimated_fp2_fuel_qs else None,
            # 標記是否有有效的 Quali Sim 數據
            'has_quali_sim_data': qs_avg is not None
        }
    
    return team_habits


def calculate_improvement_stats(pairs: List[dict], team_habits: Dict[str, dict]) -> Dict[str, dict]:
    """
    計算使用車隊校正後的預測準確度提升
    
    比較三種模式:
    1. 原始: 假設固定 58kg 燃油差異
    2. 車隊校正: 使用車隊特定的校正值
    3. 僅 Quali Sim: 只使用 Quali Sim 圈進行評估
    """
    
    original_errors = []
    corrected_errors = []
    qs_only_errors = []
    
    for pair in pairs:
        team = pair['team']
        if team not in team_habits:
            continue
        
        actual_improvement = pair['improvement']
        is_quali_sim = pair['is_quali_sim']
        
        # 車隊校正值
        team_correction = team_habits[team]['fuel_correction_seconds']
        
        # 原始預測: 假設 58kg 燃油差異 (70kg - 12kg)
        original_predicted = 58 * FUEL_COEF  # 1.856s
        original_error = abs(actual_improvement - original_predicted)
        original_errors.append(original_error)
        
        # 車隊校正預測
        corrected_error = abs(actual_improvement - team_correction)
        corrected_errors.append(corrected_error)
        
        # 僅 Quali Sim 圈的評估
        if is_quali_sim:
            qs_only_errors.append(corrected_error)
    
    if not original_errors:
        return {}
    
    result = {
        'total_samples': len(original_errors),
        'quali_sim_samples': len(qs_only_errors),
        'original_mae': round(statistics.mean(original_errors), 3),
        'corrected_mae': round(statistics.mean(corrected_errors), 3),
        'improvement_seconds': round(statistics.mean(original_errors) - statistics.mean(corrected_errors), 3),
        'improvement_percent': round((statistics.mean(original_errors) - statistics.mean(corrected_errors)) / statistics.mean(original_errors) * 100, 1)
    }
    
    if qs_only_errors:
        result['qs_only_mae'] = round(statistics.mean(qs_only_errors), 3)
    
    return result


def save_team_habits(team_habits: Dict[str, dict], output_path: str):
    """儲存車隊燃油習慣到 JSON"""
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'fuel_coefficient_s_per_kg': FUEL_COEF,
            'q_fuel_kg': Q_FUEL,
            'description': '車隊 FP2 燃油習慣學習結果'
        },
        'team_habits': team_habits
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"車隊燃油習慣已儲存到: {output_path}")


def print_team_habits_report(team_habits: Dict[str, dict], stats: Dict[str, float]):
    """列印車隊燃油習慣報告"""
    print("\n" + "=" * 100)
    print("車隊 FP2 燃油習慣分析報告 (方案 B)")
    print("=" * 100)
    
    # 按估計燃油量排序
    sorted_teams = sorted(team_habits.items(), key=lambda x: x[1]['estimated_fp2_fuel_kg'])
    
    print(f"\n{'車隊':<25} {'樣本':>6} {'QS圈':>6} {'全部改善':>10} {'QS改善':>10} {'估計燃油':>10} {'校正值':>10}")
    print("-" * 100)
    
    for team, h in sorted_teams:
        qs_imp = f"{h['qs_avg_improvement']:.3f}s" if h['qs_avg_improvement'] else "N/A"
        print(f"{team:<25} {h['sample_count']:>6} {h['quali_sim_count']:>6} "
              f"{h['all_avg_improvement']:>9.3f}s {qs_imp:>10} "
              f"{h['estimated_fp2_fuel_kg']:>9.1f}kg {h['fuel_correction_seconds']:>9.3f}s")
    
    print("-" * 100)
    
    # 統計摘要
    all_fuels = [h['estimated_fp2_fuel_kg'] for h in team_habits.values()]
    qs_fuels = [h['qs_estimated_fuel_kg'] for h in team_habits.values() if h['qs_estimated_fuel_kg']]
    
    print(f"\n燃油量統計:")
    print(f"  全部樣本估計: {min(all_fuels):.1f}kg ~ {max(all_fuels):.1f}kg (平均 {statistics.mean(all_fuels):.1f}kg)")
    if qs_fuels:
        print(f"  Quali Sim 估計: {min(qs_fuels):.1f}kg ~ {max(qs_fuels):.1f}kg (平均 {statistics.mean(qs_fuels):.1f}kg)")
    
    if stats:
        print(f"\n預測準確度改善分析:")
        print(f"  總樣本數: {stats['total_samples']}")
        print(f"  Quali Sim 樣本數: {stats['quali_sim_samples']}")
        print(f"  原始 MAE (假設 58kg): {stats['original_mae']:.3f}s")
        print(f"  校正後 MAE (車隊特定): {stats['corrected_mae']:.3f}s")
        print(f"  改善幅度: {stats['improvement_seconds']:.3f}s ({stats['improvement_percent']:.1f}%)")
        if 'qs_only_mae' in stats:
            print(f"  僅 Quali Sim 圈 MAE: {stats['qs_only_mae']:.3f}s")


def main():
    """主程式"""
    # 路徑設定
    training_data_path = 'training_data/fp2_q_training_data_2022_2025.json'
    output_path = 'training_data/team_fuel_habits.json'
    
    # 載入數據
    data = load_training_data(training_data_path)
    
    # 提取 FP2→Q 配對
    pairs = extract_fp2_q_pairs(data)
    
    # 學習車隊燃油習慣
    team_habits = learn_team_fuel_habits(pairs)
    
    # 計算改善統計
    stats = calculate_improvement_stats(pairs, team_habits)
    
    # 儲存結果
    save_team_habits(team_habits, output_path)
    
    # 列印報告
    print_team_habits_report(team_habits, stats)
    
    return team_habits, stats


if __name__ == '__main__':
    main()
