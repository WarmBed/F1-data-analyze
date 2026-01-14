#!/usr/bin/env python3
"""
批量生成 2025 年所有賽事的 Function 54 (driver_throttle_ratio) JSON
"""

import sys
import os

# 確保 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import fastf1
fastf1.Cache.enable_cache('f1_analysis_cache')

from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
from CLI_modules.cli.analyzer.driver_throttle_ratio import run_driver_throttle_ratio_analysis

def main():
    # 獲取 2025 賽程
    schedule = fastf1.get_event_schedule(2025)
    races = schedule[schedule['EventFormat'] != 'testing']
    
    # 只處理正賽 (R)
    session_type = 'R'
    
    success_count = 0
    fail_count = 0
    
    for idx, row in races.iterrows():
        race_name = row['EventName']
        round_number = row['RoundNumber']
        
        print(f"\n{'='*60}")
        print(f"[{round_number}/24] {race_name} - {session_type}")
        print('='*60)
        
        try:
            # 載入數據
            loader = CompatibleF1DataLoader()
            loader.load_race_data(
                year=2025,
                race_name=race_name,
                session_type=session_type
            )
            
            # 執行分析
            result = run_driver_throttle_ratio_analysis(
                data_loader=loader,
                show_summary=False,
                save_json=True
            )
            
            if result.get('success'):
                print(f"✅ 成功生成 JSON")
                success_count += 1
            else:
                print(f"❌ 分析失敗: {result.get('message')}")
                fail_count += 1
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"完成! 成功: {success_count}, 失敗: {fail_count}")
    print('='*60)

if __name__ == "__main__":
    main()
