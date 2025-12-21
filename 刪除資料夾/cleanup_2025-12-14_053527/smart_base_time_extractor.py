"""
智能 base_time 提取器 - 處理 SC、黃旗、異常圈

過濾條件：
1. 跳過 Formation Lap（Lap 1）
2. 跳過 Safety Car 期間的圈（圈速 > 120s）
3. 跳過異常圈（圈速 > 平均 + 3σ）
4. 使用 Lap 4-15 的正常圈速中位數
"""

import fastf1
import numpy as np
import pandas as pd
from typing import Tuple


def extract_base_time_robust(year: int, race: str, driver: str = "VER", 
                             session_type: str = 'R') -> Tuple[float, dict]:
    """
    智能提取 base_time，自動處理 SC、黃旗等異常情況
    
    Args:
        year: 年份
        race: 賽事名稱
        driver: 車手代碼
        session_type: 會話類型（'R' = Race）
    
    Returns:
        (base_time, info_dict)
        
    info_dict 包含：
        - base_time: 基礎圈速
        - sample_count: 使用樣本數
        - sc_laps: SC/黃旗圈列表 ← 新增
        - sc_laps_removed: 移除的 SC 圈數
        - outliers_removed: 移除的 outlier 圈數
        - used_laps: 使用的圈號列表
        
    過濾邏輯：
        1. 使用 Lap 4-15（跳過開場混亂）
        2. 過濾 > 120s 的圈（SC/黃旗）
        3. 過濾 outliers（> mean + 3σ）
        4. 返回中位數
    """
    
    print(f"\n{'='*80}")
    print(f"智能 base_time 提取 - {year} {race} {driver}")
    print(f"{'='*80}")
    
    # 載入數據
    fastf1.Cache.enable_cache('f1_analysis_cache')
    session = fastf1.get_session(year, race, session_type)
    session.load()
    
    laps = session.laps.pick_driver(driver)
    
    # 定義 Safety Car 門檻
    sc_threshold = 120.0
    
    # 步驟 1: 選擇 Lap 4-15（跳過開場 + 避免進站影響）
    candidate_laps = laps[(laps['LapNumber'] >= 4) & (laps['LapNumber'] <= 15)].copy()
    candidate_laps['LapTimeSeconds'] = candidate_laps['LapTime'].dt.total_seconds()
    
    initial_count = len(candidate_laps)
    print(f"\n步驟 1: 選擇 Lap 4-15")
    print(f"  候選圈數: {initial_count}")
    
    # 步驟 1.5: 偵測整場比賽的 SC/黃旗圈（用於後續預測時跳過）
    all_laps = laps.copy()
    all_laps['LapTimeSeconds'] = all_laps['LapTime'].dt.total_seconds()
    sc_laps_all = all_laps[all_laps['LapTimeSeconds'] >= sc_threshold]['LapNumber'].tolist()
    
    print(f"\n步驟 1.5: 偵測全場 SC/黃旗圈（> {sc_threshold}s）")
    print(f"  全場 SC 圈數: {len(sc_laps_all)}")
    if len(sc_laps_all) > 0:
        print(f"  SC 圈列表: {[int(lap) for lap in sc_laps_all]}")
    
    # 步驟 2: 過濾 Safety Car / 黃旗圈（> 120s）
    non_sc_laps = candidate_laps[candidate_laps['LapTimeSeconds'] < sc_threshold].copy()
    sc_laps_removed = initial_count - len(non_sc_laps)
    
    print(f"\n步驟 2: 過濾 Safety Car/黃旗圈（> {sc_threshold}s）")
    print(f"  移除圈數: {sc_laps_removed}")
    print(f"  剩餘圈數: {len(non_sc_laps)}")
    
    if sc_laps_removed > 0:
        removed = candidate_laps[candidate_laps['LapTimeSeconds'] >= sc_threshold]
        for _, lap in removed.iterrows():
            print(f"    ⚠️  Lap {int(lap['LapNumber'])}: {lap['LapTimeSeconds']:.3f}s (SC/黃旗)")
    
    # 步驟 3: 過濾統計 outliers（> mean + 3σ）
    if len(non_sc_laps) > 3:
        mean_time = non_sc_laps['LapTimeSeconds'].mean()
        std_time = non_sc_laps['LapTimeSeconds'].std()
        outlier_threshold = mean_time + 3 * std_time
        
        clean_laps = non_sc_laps[non_sc_laps['LapTimeSeconds'] < outlier_threshold].copy()
        outliers_removed = len(non_sc_laps) - len(clean_laps)
        
        print(f"\n步驟 3: 過濾統計 outliers（> mean + 3σ = {outlier_threshold:.3f}s）")
        print(f"  移除圈數: {outliers_removed}")
        print(f"  剩餘圈數: {len(clean_laps)}")
        
        if outliers_removed > 0:
            removed = non_sc_laps[non_sc_laps['LapTimeSeconds'] >= outlier_threshold]
            for _, lap in removed.iterrows():
                print(f"    ⚠️  Lap {int(lap['LapNumber'])}: {lap['LapTimeSeconds']:.3f}s (outlier)")
    else:
        clean_laps = non_sc_laps
    
    # 步驟 4: 計算 base_time（中位數）
    if len(clean_laps) < 3:
        # 退回策略：使用所有 < 120s 的圈
        print(f"\n⚠️  清理後圈數不足（{len(clean_laps)}），退回使用所有 < {sc_threshold}s 的圈")
        clean_laps = laps[laps['LapTime'].dt.total_seconds() < sc_threshold].copy()
        clean_laps['LapTimeSeconds'] = clean_laps['LapTime'].dt.total_seconds()
    
    base_time = clean_laps['LapTimeSeconds'].median()
    min_time = clean_laps['LapTimeSeconds'].min()
    max_time = clean_laps['LapTimeSeconds'].max()
    mean_time = clean_laps['LapTimeSeconds'].mean()
    
    print(f"\n步驟 4: 計算 base_time")
    print(f"  使用圈數: {len(clean_laps)}")
    print(f"  圈速範圍: {min_time:.3f}s - {max_time:.3f}s")
    print(f"  平均: {mean_time:.3f}s")
    print(f"  中位數: {base_time:.3f}s ← base_time")
    
    # 列出使用的圈
    print(f"\n使用的圈:")
    for _, lap in clean_laps.iterrows():
        lap_num = int(lap['LapNumber'])
        lap_time = lap['LapTimeSeconds']
        print(f"  Lap {lap_num}: {lap_time:.3f}s")
    
    # 返回資訊
    info = {
        'base_time': base_time,
        'sample_count': len(clean_laps),
        'min_time': min_time,
        'max_time': max_time,
        'mean_time': mean_time,
        'sc_laps': [int(lap) for lap in sc_laps_all],  # ← 新增：全場 SC 圈列表
        'sc_laps_removed': sc_laps_removed,
        'outliers_removed': outliers_removed if len(non_sc_laps) > 3 else 0,
        'used_laps': clean_laps['LapNumber'].tolist()
    }
    
    print(f"\n{'='*80}")
    print(f"base_time 提取完成: {base_time:.3f}s")
    print(f"{'='*80}\n")
    
    return base_time, info


if __name__ == '__main__':
    # 測試案例
    test_cases = [
        (2025, "Japan", "VER"),
        (2024, "Mexico", "VER"),
    ]
    
    for year, race, driver in test_cases:
        try:
            base_time, info = extract_base_time_robust(year, race, driver)
            print(f"\n📊 {year} {race} 結果:")
            print(f"   Base Time: {base_time:.3f}s")
            print(f"   樣本數: {info['sample_count']}")
            print(f"   SC 移除: {info['sc_laps_removed']} 圈")
            print(f"   Outlier 移除: {info['outliers_removed']} 圈")
        except Exception as e:
            print(f"\n❌ 錯誤 {year} {race}: {e}")
        
        print("\n" + "="*80 + "\n")
