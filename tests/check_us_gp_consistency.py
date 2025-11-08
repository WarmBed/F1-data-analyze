#!/usr/bin/env python3
"""
檢查 United States GP 的各模組數據一致性
"""

import json
from pathlib import Path


def check_ideal_lap_ranking():
    """檢查 Ideal Lap Ranking 數據"""
    files = list(Path("json").glob("ideal_lap_ranking_2025_*United*States*.json"))
    if not files:
        files = list(Path("json").glob("ideal_lap_ranking_2025_*united*states*.json"))
    
    if not files:
        print("❌ 找不到 Ideal Lap Ranking (United States) 檔案")
        return None
    
    filepath = files[0]
    print(f"📄 {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    analysis_result = data.get('analysis_result', {})
    ranking = analysis_result.get('ranking', [])
    
    ver_data = next((d for d in ranking if d.get('driver') == 'VER'), None)
    
    if ver_data:
        fastest_lap = ver_data.get('fastest_lap_time')
        ideal_lap = ver_data.get('ideal_lap_time')
        
        print(f"   Metadata Race: {metadata.get('race')}")
        print(f"   VER 最速圈: {fastest_lap:.3f}s ({fastest_lap/60:.0f}:{fastest_lap%60:06.3f})")
        print(f"   VER 理想圈: {ideal_lap:.3f}s ({ideal_lap/60:.0f}:{ideal_lap%60:06.3f})")
        
        return {
            'race': metadata.get('race'),
            'ver_fastest': fastest_lap,
            'ver_ideal': ideal_lap
        }
    
    return None


def check_detailed_lap_analysis():
    """檢查 Detailed Lap Analysis 數據"""
    files = list(Path("json").glob("detailed_laptime_analysis_2025_*United*States*.json"))
    if not files:
        files = list(Path("json").glob("detailed_laptime_analysis_2025_*united*states*.json"))
    
    if not files:
        print("❌ 找不到 Detailed Lap Analysis (United States) 檔案")
        return None
    
    filepath = files[0]
    print(f"\n📄 {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    all_drivers = data.get('all_drivers_detailed_laptime', {})
    ver_data = all_drivers.get('VER', {})
    laps = ver_data.get('detailed_laps', [])
    
    if laps:
        valid_laps = [l for l in laps if l.get('lap_time_seconds') is not None]
        if valid_laps:
            fastest_lap = min(valid_laps, key=lambda x: x.get('lap_time_seconds', 999))
            fastest_time = fastest_lap.get('lap_time_seconds')
            
            print(f"   Metadata Race: {metadata.get('race')}")
            print(f"   VER 最速圈: {fastest_time:.3f}s ({fastest_time/60:.0f}:{fastest_time%60:06.3f})")
            print(f"   圈號: {fastest_lap.get('lap_number')}")
            print(f"   總圈數: {len(laps)}")
            
            return {
                'race': metadata.get('race'),
                'ver_fastest': fastest_time,
                'total_laps': len(laps)
            }
    
    print("   ⚠️ 沒有有效的圈數數據")
    return None


def check_throttle_ratio():
    """檢查 Throttle Ratio 數據"""
    files = list(Path("json").glob("throttle_ratio_2025_*united*states*.json"))
    if not files:
        files = list(Path("json").glob("throttle_ratio_2025_*United*States*.json"))
    
    if not files:
        print("❌ 找不到 Throttle Ratio (United States) 檔案")
        return None
    
    filepath = files[0]
    print(f"\n📄 {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    analysis = data.get('analysis', {})
    drivers = analysis.get('drivers', [])
    
    ver_driver = next((d for d in drivers if d.get('driver_code') == 'VER'), None)
    
    if ver_driver:
        laps = ver_driver.get('laps', [])
        valid_laps = [l for l in laps if l.get('lap_time_seconds') is not None]
        
        if valid_laps:
            fastest_lap = min(valid_laps, key=lambda x: x.get('lap_time_seconds', 999))
            fastest_time = fastest_lap.get('lap_time_seconds')
            
            print(f"   Metadata Race: {metadata.get('race')}")
            print(f"   VER 最速圈: {fastest_time:.3f}s ({fastest_time/60:.0f}:{fastest_time%60:06.3f})")
            print(f"   總圈數: {len(laps)}")
            
            return {
                'race': metadata.get('race'),
                'ver_fastest': fastest_time,
                'total_laps': len(laps)
            }
    
    return None


def main():
    print("="*80)
    print("United States GP 數據一致性檢查")
    print("="*80)
    print()
    
    ideal_lap = check_ideal_lap_ranking()
    detailed_lap = check_detailed_lap_analysis()
    throttle = check_throttle_ratio()
    
    print("\n" + "="*80)
    print("🔍 比對結果")
    print("="*80)
    
    if ideal_lap and detailed_lap:
        time_diff = abs(ideal_lap['ver_fastest'] - detailed_lap['ver_fastest'])
        
        print(f"\n⏱️  VER 最速圈時間比對:")
        print(f"   Ideal Lap Ranking: {ideal_lap['ver_fastest']:.3f}s")
        print(f"   Detailed Lap Analysis: {detailed_lap['ver_fastest']:.3f}s")
        print(f"   時間差: {time_diff:.3f}s")
        
        if time_diff > 1.0:
            print(f"   ❌ 時間差異過大！可能來自不同賽事的數據")
            print(f"   💡 建議：重新生成 Detailed Lap Analysis 數據")
            print(f"      命令: python f1_analysis_modular_main.py -f 28 -y 2025 -r \"United States\" -s R")
        elif time_diff > 0.1:
            print(f"   ⚠️  有小幅差異（可能是計算方式不同）")
        else:
            print(f"   ✅ 時間一致！")
    
    if ideal_lap and throttle:
        time_diff = abs(ideal_lap['ver_fastest'] - throttle['ver_fastest'])
        
        print(f"\n⏱️  VER 最速圈時間比對 (Throttle):")
        print(f"   Ideal Lap Ranking: {ideal_lap['ver_fastest']:.3f}s")
        print(f"   Throttle Ratio: {throttle['ver_fastest']:.3f}s")
        print(f"   時間差: {time_diff:.3f}s")
        
        if time_diff > 1.0:
            print(f"   ❌ 時間差異過大！可能來自不同賽事的數據")
            print(f"   💡 建議：重新生成 Throttle Ratio 數據")
            print(f"      命令: python f1_analysis_modular_main.py -f 54 -y 2025 -r \"United States\" -s R")
        elif time_diff > 0.1:
            print(f"   ⚠️  有小幅差異（可能是計算方式不同）")
        else:
            print(f"   ✅ 時間一致！")


if __name__ == "__main__":
    main()
