#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
賽道 FP2→Q 調整因子學習腳本

從 2022-2025 的歷史數據學習各賽道的 FP2→Q 調整因子。

不同賽道的 FP2→Q 轉化特性不同:
- 有些賽道 FP2 很難跑出代表性圈速（如 Singapore）
- 有些賽道 FP2 和 Q 差異很大（如 Japan）

輸出:
  training_data/track_adjustment_factors.json

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


def extract_track_fp2_q_data(data: List[dict]) -> Dict[str, List[dict]]:
    """
    提取每個賽道的 FP2→Q 數據
    """
    track_data = defaultdict(list)
    
    for race in data:
        track = race['metadata']['race']
        year = race['metadata']['year']
        
        # 年份權重
        year_weights = {2025: 2.0, 2024: 1.5, 2023: 1.0, 2022: 0.7}
        year_weight = year_weights.get(year, 1.0)
        
        fp2 = race.get('practice_sessions', {}).get('FP2', {}).get('driver_data', {})
        q = race.get('qualifying', {}).get('results', {})
        
        for driver, fp2_info in fp2.items():
            if driver not in q:
                continue
            
            fp2_time = fp2_info.get('best_lap_time', 0)
            if not fp2_time or fp2_time <= 0 or fp2_time > 120:
                continue
            
            # 獲取輪胎壽命（用於識別 Quali Sim）
            tire_age = fp2_info.get('tire_age_avg')
            is_quali_sim = tire_age is not None and tire_age <= 3
            
            q_time_str = q[driver].get('best_time', '') or ''
            q_time = parse_timedelta_to_seconds(q_time_str)
            
            if not q_time or q_time <= 0 or q_time > 120:
                continue
            
            delta = q_time - fp2_time
            
            track_data[track].append({
                'year': year,
                'driver': driver,
                'fp2_time': fp2_time,
                'q_time': q_time,
                'delta': delta,
                'is_quali_sim': is_quali_sim,
                'year_weight': year_weight
            })
    
    return track_data


def calculate_track_adjustment_factors(track_data: Dict[str, List[dict]]) -> Dict[str, dict]:
    """
    計算賽道調整因子
    
    對於每個賽道:
    1. 計算 FP2→Q 差異的加權平均值和標準差
    2. 與全局基準比較，計算調整因子
    """
    results = {}
    
    # 計算全局基準
    all_deltas = []
    all_weights = []
    for track, entries in track_data.items():
        for e in entries:
            all_deltas.append(e['delta'])
            all_weights.append(e['year_weight'])
    
    # 加權全局平均
    total_weight = sum(all_weights)
    global_mean = sum(d * w for d, w in zip(all_deltas, all_weights)) / total_weight if total_weight > 0 else 0
    
    print(f"\n全局加權平均差異: {global_mean:.3f}s")
    
    for track, entries in track_data.items():
        if len(entries) < 10:
            continue
        
        # 加權平均
        track_weight = sum(e['year_weight'] for e in entries)
        track_mean = sum(e['delta'] * e['year_weight'] for e in entries) / track_weight if track_weight > 0 else 0
        
        # 加權標準差
        weighted_var = sum(e['year_weight'] * (e['delta'] - track_mean) ** 2 for e in entries) / track_weight if track_weight > 0 else 0
        track_std = weighted_var ** 0.5
        
        # 只使用 Quali Sim 圈的數據
        qs_entries = [e for e in entries if e['is_quali_sim']]
        if len(qs_entries) >= 5:
            qs_weight = sum(e['year_weight'] for e in qs_entries)
            qs_mean = sum(e['delta'] * e['year_weight'] for e in qs_entries) / qs_weight if qs_weight > 0 else 0
        else:
            qs_mean = track_mean
        
        # 賽道調整因子 = 賽道平均 - 全局平均
        # 正數 = 這個賽道 FP2→Q 進步較少，需要加慢預測
        # 負數 = 這個賽道 FP2→Q 進步較多，需要加快預測
        track_adjustment = track_mean - global_mean
        
        results[track] = {
            'sample_count': len(entries),
            'quali_sim_count': len(qs_entries),
            'all_mean_delta': track_mean,
            'all_std_delta': track_std,
            'qs_mean_delta': qs_mean,
            'global_mean': global_mean,
            'track_adjustment': track_adjustment,
        }
    
    return results


def save_track_factors(factors: Dict[str, dict], output_path: str):
    """保存賽道因子到 JSON 文件"""
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'fp2_q_training_data_2022_2025.json',
            'description': '賽道 FP2→Q 調整因子（從歷史數據學習）',
            'formula': 'adjusted_prediction = base_prediction + track_adjustment',
        },
        'track_factors': factors
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n賽道調整因子已保存到: {output_path}")


def main():
    # 載入訓練數據
    training_file = Path(__file__).parent / "training_data" / "fp2_q_training_data_2022_2025.json"
    data = load_training_data(str(training_file))
    
    # 提取賽道數據
    print("\n提取賽道 FP2→Q 數據...")
    track_data = extract_track_fp2_q_data(data)
    
    total_samples = sum(len(entries) for entries in track_data.values())
    print(f"提取 {total_samples} 個樣本，涵蓋 {len(track_data)} 個賽道")
    
    # 計算賽道因子
    print("\n計算賽道調整因子...")
    factors = calculate_track_adjustment_factors(track_data)
    
    # 保存結果
    output_path = Path(__file__).parent / "training_data" / "track_adjustment_factors.json"
    save_track_factors(factors, str(output_path))
    
    # 打印報告
    print("\n" + "=" * 90)
    print("賽道 FP2→Q 調整因子報告 (年份加權)")
    print("=" * 90)
    print(f"\n{'賽道':<20} {'樣本':>6} {'QS圈':>6} {'平均Δ':>10} {'標準差':>10} {'調整值':>10}")
    print("-" * 80)
    
    # 按調整值排序
    sorted_factors = sorted(factors.items(), key=lambda x: x[1]['track_adjustment'], reverse=True)
    
    for track, info in sorted_factors:
        print(f"{track:<20} {info['sample_count']:>6} {info['quali_sim_count']:>6} "
              f"{info['all_mean_delta']:>+10.3f} {info['all_std_delta']:>10.3f} "
              f"{info['track_adjustment']:>+10.3f}")
    
    print("-" * 80)
    print("\n說明:")
    print("  - 平均Δ: Q時間 - FP2時間 的平均值（負值 = Q比FP2快）")
    print("  - 調整值: 與全局平均的差異（正值 = 需要加慢預測，負值 = 需要加快預測）")


if __name__ == "__main__":
    main()
