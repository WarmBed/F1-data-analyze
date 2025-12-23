#!/usr/bin/env python3
"""
生成 2025 Abu Dhabi Live Timing Throttle 95% 分析報告
"""

import json
import glob
from pathlib import Path
from collections import defaultdict

def analyze_throttle_95_from_live_timing():
    """分析 Live Timing 數據中的 throttle 95% 占比"""
    
    print("="*80)
    print("2025 Abu Dhabi GP - Throttle 95% 分析報告")
    print("="*80)
    
    # 查找 2025 Abu Dhabi 相關的 JSON 檔案
    json_dir = Path("json")
    
    # 可能的檔案模式
    patterns = [
        "*2025*Abu*Dhabi*.json",
        "*2025*Abu_Dhabi*.json",
        "*throttle*2025*.json",
        "driver_throttle_ratio_2025*.json"
    ]
    
    found_files = []
    for pattern in patterns:
        found_files.extend(json_dir.glob(pattern))
    
    if not found_files:
        print("\n❌ 找不到 2025 Abu Dhabi 的數據檔案")
        print("\n建議執行:")
        print('python f1_analysis_modular_main.py -f 54 -y 2025 -r "Abu Dhabi" -s R --threshold 0.95')
        return
    
    print(f"\n找到 {len(found_files)} 個相關檔案:")
    for f in found_files:
        print(f"  - {f.name}")
    
    # 使用功能 54 的 throttle ratio 檔案
    throttle_file = None
    for f in found_files:
        if "throttle" in f.name.lower():
            throttle_file = f
            break
    
    if not throttle_file:
        throttle_file = found_files[0]
    
    print(f"\n使用檔案: {throttle_file.name}")
    
    try:
        with open(throttle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n" + "="*80)
        print("每位車手每圈的 Throttle 95% 分析")
        print("="*80)
        
        # 處理標準 Function 54 格式 (有 'data' 包裝層)
        if 'data' in data:
            drivers = data['data'].get('analysis', {}).get('drivers', [])
        else:
            drivers = data.get('analysis', {}).get('drivers', [])
        
        if not drivers:
            print("❌ 數據格式不符或無車手數據")
            print(f"數據結構: {list(data.keys())}")
            return
        
        # 分析每位車手
        for driver in drivers:
            driver_code = driver.get('driver_code', 'N/A')
            team = driver.get('team', 'N/A')
            laps = driver.get('laps', [])
            
            print(f"\n{'='*80}")
            print(f"車手: {driver_code} ({team})")
            print(f"{'='*80}")
            
            if not laps:
                print("  無圈速數據")
                continue
            
            # 表頭
            print(f"{'Lap':<6} {'Lap Time':<10} {'Throttle 95%':<14} {'Avg Throttle':<14} {'Full Duration':<15}")
            print("-"*80)
            
            total_ratio = 0
            valid_laps = 0
            
            for lap in laps:
                lap_num = lap.get('lap_number', 'N/A')
                lap_time = lap.get('lap_time_formatted', lap.get('lap_time_seconds', 'N/A'))
                
                # full_throttle_ratio 即為 >= threshold 的占比
                # 如果使用 --threshold 0.95，這就是 95% 的占比
                throttle_95_ratio = lap.get('full_throttle_ratio')
                avg_throttle = lap.get('average_throttle')
                full_duration = lap.get('full_throttle_duration_s')
                
                if throttle_95_ratio is not None:
                    throttle_95_percent = throttle_95_ratio * 100
                    total_ratio += throttle_95_percent
                    valid_laps += 1
                else:
                    throttle_95_percent = None
                
                # 格式化輸出
                lap_time_str = f"{lap_time:.3f}s" if isinstance(lap_time, (int, float)) else str(lap_time)
                throttle_str = f"{throttle_95_percent:.2f}%" if throttle_95_percent is not None else "N/A"
                avg_str = f"{avg_throttle*100:.2f}%" if avg_throttle is not None else "N/A"
                dur_str = f"{full_duration:.2f}s" if full_duration is not None else "N/A"
                
                print(f"{lap_num:<6} {lap_time_str:<10} {throttle_str:<14} {avg_str:<14} {dur_str:<15}")
            
            # 統計摘要
            if valid_laps > 0:
                avg_ratio = total_ratio / valid_laps
                print("-"*80)
                print(f"統計摘要: 有效圈數={valid_laps}, 平均 Throttle 95% = {avg_ratio:.2f}%")
        
        # 全場統計
        print("\n" + "="*80)
        print("全場統計 - Top 5 平均 Throttle 95%")
        print("="*80)
        
        driver_averages = []
        for driver in drivers:
            driver_code = driver.get('driver_code', 'N/A')
            laps = driver.get('laps', [])
            
            ratios = [lap['full_throttle_ratio'] * 100 
                     for lap in laps 
                     if lap.get('full_throttle_ratio') is not None]
            
            if ratios:
                avg = sum(ratios) / len(ratios)
                driver_averages.append((driver_code, avg, len(ratios)))
        
        driver_averages.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n{'排名':<6} {'車手':<8} {'平均 Throttle 95%':<20} {'圈數':<8}")
        print("-"*80)
        for i, (driver, avg, count) in enumerate(driver_averages[:5], 1):
            print(f"{i:<6} {driver:<8} {avg:.2f}%{' '*14} {count:<8}")
        
        print("\n" + "="*80)
        print("✅ 報告生成完成")
        print("="*80)
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 解析錯誤: {e}")
    except Exception as e:
        print(f"\n❌ 處理錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_throttle_95_from_live_timing()
