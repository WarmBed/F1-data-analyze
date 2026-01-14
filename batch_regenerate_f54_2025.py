#!/usr/bin/env python3
"""
批量重新生成 Function 54 (Throttle Ratio) JSON - 2025 全賽季

這個腳本會為 2025 賽季的所有賽事重新生成 throttle ratio JSON，
使用新的格式（包含 pedal_states 和 is_pit_lap）。

用法:
    python batch_regenerate_f54_2025.py [--session R|Q|FP1|FP2|FP3]
"""

import os
import sys
import time
import argparse
from pathlib import Path

# 設置編碼
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import fastf1
fastf1.Cache.enable_cache('f1_analysis_cache')


def get_2025_races():
    """獲取 2025 賽事列表 - 使用標準短名稱"""
    # 使用標準短名稱，與 API/GUI 一致
    return [
        "Australia",
        "China",
        "Japan",
        "Bahrain",
        "Saudi Arabia",
        "Miami",
        "Emilia Romagna",
        "Monaco",
        "Spain",
        "Canada",
        "Austria",
        "Great Britain",
        "Belgium",
        "Hungary",
        "Netherlands",
        "Italy",
        "Azerbaijan",
        "Singapore",
        "United States",
        "Mexico",
        "Brazil",
        "Las Vegas",
        "Qatar",
        "Abu Dhabi",
    ]


def run_f54_for_race(race_name: str, session: str = "R"):
    """執行 Function 54 分析"""
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
    
    print(f"\n{'='*60}")
    print(f"  處理: {race_name} ({session})")
    print(f"{'='*60}")
    
    try:
        # 初始化數據載入器
        data_loader = CompatibleF1DataLoader()
        data_loader.load_race_data(year=2025, race_name=race_name, session_type=session)
        
        # 執行分析
        mapper = F1AnalysisFunctionMapper(data_loader)
        result = mapper.execute_function_by_number(54)
        
        if result.get("success"):
            print(f"  成功: {race_name} {session}")
            return True
        else:
            print(f"  失敗: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"  錯誤: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="批量生成 F54 JSON (2025)")
    parser.add_argument("--session", "-s", default="R", 
                        choices=["R", "Q", "FP1", "FP2", "FP3"],
                        help="賽段類型 (預設: R)")
    parser.add_argument("--start", type=int, default=1,
                        help="從第幾場開始 (1-24)")
    parser.add_argument("--end", type=int, default=24,
                        help="到第幾場結束 (1-24)")
    args = parser.parse_args()
    
    races = get_2025_races()
    
    print(f"  2025 賽季 Function 54 批量生成")
    print(f"   賽段: {args.session}")
    print(f"   範圍: 第 {args.start} 場 到 第 {args.end} 場")
    print(f"   共 {min(args.end, len(races)) - args.start + 1} 場賽事")
    
    success_count = 0
    fail_count = 0
    
    start_time = time.time()
    
    for i, race in enumerate(races[args.start-1:args.end], args.start):
        print(f"\n[{i}/{min(args.end, len(races))}] ", end="")
        
        if run_f54_for_race(race, args.session):
            success_count += 1
        else:
            fail_count += 1
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"  完成!")
    print(f"     成功: {success_count}")
    print(f"     失敗: {fail_count}")
    print(f"     耗時: {elapsed/60:.1f} 分鐘")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
