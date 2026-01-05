#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
賽道演進效應學習腳本

Q 賽通常比 FP2 有更好的賽道條件（更多橡膠積累），導致:
1. Q 時賽道抓地力更高
2. 所有車手的圈速都會比 FP2 快
3. 這個「賽道演進效應」可以從歷史數據中學習

計算方式:
- 對每個賽道，計算所有車手的「Q時間 - FP2時間」的中位數
- 中位數代表賽道演進效應（不受個別車手異常值影響）

輸出:
  training_data/track_evolution_factors.json

作者: GitHub Copilot
日期: 2026-01-05
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


def calculate_track_evolution(data: List[dict]) -> Dict[str, dict]:
    """
    計算賽道演進效應
    
    使用中位數來排除異常值（如某些車手的 FP2 Long Run 圈速）
    """
    track_deltas = defaultdict(list)
    
    # 年份權重
    year_weights = {2025: 2.0, 2024: 1.5, 2023: 1.0, 2022: 0.7}
    
    for race in data:
        year = race['metadata']['year']
        track = race['metadata']['race']
        year_weight = year_weights.get(year, 1.0)
        
        fp2 = race.get('practice_sessions', {}).get('FP2', {}).get('driver_data', {})
        q = race.get('qualifying', {}).get('results', {})
        
        for driver, fp2_info in fp2.items():
            fp2_time = fp2_info.get('best_lap_time', 0)
            if not fp2_time or fp2_time <= 0 or fp2_time > 120:
                continue
            
            if driver not in q:
                continue
            
            q_time_str = q[driver].get('best_time', '')
            q_time = parse_timedelta_to_seconds(q_time_str)
            
            if not q_time or q_time <= 0 or q_time > 120:
                continue
            
            # Delta = Q - FP2 (負值表示 Q 比 FP2 快)
            delta = q_time - fp2_time
            
            # 排除極端異常值 (超過 ±30 秒)
            if abs(delta) > 30:
                continue
            
            track_deltas[track].append({
                'year': year,
                'driver': driver,
                'delta': delta,
                'year_weight': year_weight
            })
    
    # 計算每個賽道的演進效應
    results = {}
    all_medians = []
    
    for track, entries in track_deltas.items():
        if len(entries) < 10:
            continue
        
        deltas = [e['delta'] for e in entries]
        weights = [e['year_weight'] for e in entries]
        
        # 使用中位數（不受異常值影響）
        median_delta = statistics.median(deltas)
        all_medians.append(median_delta)
        
        # 計算加權平均
        total_weight = sum(weights)
        weighted_mean = sum(d * w for d, w in zip(deltas, weights)) / total_weight if total_weight > 0 else 0
        
        # 標準差
        std_delta = statistics.stdev(deltas) if len(deltas) > 1 else 0
        
        results[track] = {
            'sample_count': len(entries),
            'median_delta': median_delta,
            'weighted_mean_delta': weighted_mean,
            'std_delta': std_delta
        }
    
    # 計算全局中位數（用作基準）
    global_median = statistics.median(all_medians) if all_medians else 0
    print(f"\n全局賽道演進中位數: {global_median:.3f}s")
    
    # 添加相對於全局的調整
    for track, info in results.items():
        # 賽道演進調整 = 賽道中位數 - 全局中位數
        # 正數 = 這個賽道演進效應較弱（Q 比 FP2 慢）
        # 負數 = 這個賽道演進效應較強（Q 比 FP2 快很多）
        info['global_median'] = global_median
        info['evolution_adjustment'] = info['median_delta'] - global_median
    
    return results


def save_results(factors: Dict[str, dict], output_path: str):
    """保存結果到 JSON 文件"""
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'fp2_q_training_data_2022_2025.json',
            'description': '賽道演進效應因子（FP2→Q 的中位數差異）',
            'formula': 'track_evolution_effect = median(Q_time - FP2_time) for all drivers',
            'note': '負值表示 Q 比 FP2 快（正常情況），正值表示 Q 比 FP2 慢（異常）'
        },
        'track_factors': factors
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n賽道演進因子已保存到: {output_path}")


def main():
    # 載入訓練數據
    training_file = Path(__file__).parent / "training_data" / "fp2_q_training_data_2022_2025.json"
    data = load_training_data(str(training_file))
    
    # 計算賽道演進效應
    print("\n計算賽道演進效應（使用中位數）...")
    factors = calculate_track_evolution(data)
    
    # 保存結果
    output_path = Path(__file__).parent / "training_data" / "track_evolution_factors.json"
    save_results(factors, str(output_path))
    
    # 打印報告
    print("\n" + "=" * 90)
    print("賽道演進效應報告 (中位數)")
    print("=" * 90)
    print(f"\n{'賽道':<20} {'樣本':>6} {'中位Δ':>10} {'加權平均Δ':>12} {'標準差':>10} {'演進調整':>10}")
    print("-" * 80)
    
    # 按演進調整排序（演進效應弱→強）
    sorted_factors = sorted(factors.items(), key=lambda x: x[1]['evolution_adjustment'], reverse=True)
    
    for track, info in sorted_factors:
        print(f"{track:<20} {info['sample_count']:>6} "
              f"{info['median_delta']:>+10.3f} {info['weighted_mean_delta']:>+12.3f} "
              f"{info['std_delta']:>10.3f} {info['evolution_adjustment']:>+10.3f}")
    
    print("-" * 80)
    print("\n說明:")
    print("  - 中位Δ: Q時間 - FP2時間 的中位數（負值 = Q 比 FP2 快）")
    print("  - 演進調整: 相對於全局中位數的偏差")
    print("  - 正值 = 賽道演進效應較弱，負值 = 賽道演進效應較強")


if __name__ == "__main__":
    main()
