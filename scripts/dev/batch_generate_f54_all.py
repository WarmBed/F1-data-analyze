#!/usr/bin/env python3
"""
批量生成所有賽事的 Function 54 (driver_throttle_ratio) JSON
涵蓋 2018-2025 年，所有 Session 類型 (R, Q, FP1, FP2, FP3, SQ)
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 確保 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import fastf1
fastf1.Cache.enable_cache('f1_analysis_cache')

from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
from CLI_modules.cli.analyzer.driver_throttle_ratio import run_driver_throttle_ratio_analysis

# JSON 輸出目錄
JSON_DIR = Path("json")

def check_existing_json(year: int, race_name: str, session: str) -> bool:
    """檢查 JSON 是否已存在"""
    patterns = [
        f"driver_throttle_ratio_{year}_{race_name}_{session}.json",
        f"driver_throttle_ratio_{year}_{race_name.replace(' ', '_')}_{session}.json",
    ]
    
    for pattern in patterns:
        if (JSON_DIR / pattern).exists():
            return True
    
    # 模糊匹配
    for f in JSON_DIR.glob(f"driver_throttle_ratio_{year}*{session}.json"):
        if race_name.split()[0] in f.name:
            return True
    
    return False


def generate_f54_for_session(year: int, race_name: str, session: str) -> dict:
    """生成單個 Session 的 F54 數據"""
    result = {
        'year': year,
        'race': race_name,
        'session': session,
        'success': False,
        'message': ''
    }
    
    try:
        # 載入數據
        loader = CompatibleF1DataLoader()
        loader.load_race_data(
            year=year,
            race_name=race_name,
            session_type=session
        )
        
        # 執行分析
        analysis_result = run_driver_throttle_ratio_analysis(
            data_loader=loader,
            show_summary=False,
            save_json=True
        )
        
        if analysis_result.get('success'):
            result['success'] = True
            result['message'] = 'JSON 生成成功'
        else:
            result['message'] = analysis_result.get('message', '分析失敗')
            
    except Exception as e:
        result['message'] = str(e)
    
    return result


def main():
    print("=" * 70)
    print("批量生成 Function 54 (Pedal Behavior) JSON")
    print("=" * 70)
    
    # 設定參數
    years = [2025]  # 主要生成 2025 年
    sessions = ['R', 'Q', 'SQ']  # 正賽、排位賽、衝刺排位賽
    
    # 可選：加入練習賽
    # sessions = ['R', 'Q', 'SQ', 'FP1', 'FP2', 'FP3']
    
    total_success = 0
    total_fail = 0
    total_skip = 0
    results = []
    
    for year in years:
        print(f"\n{'='*70}")
        print(f"處理 {year} 年賽季")
        print("=" * 70)
        
        try:
            schedule = fastf1.get_event_schedule(year)
            races = schedule[schedule['EventFormat'] != 'testing']
        except Exception as e:
            print(f"❌ 無法獲取 {year} 年賽程: {e}")
            continue
        
        for idx, row in races.iterrows():
            race_name = row['EventName']
            round_number = row['RoundNumber']
            event_date = row.get('EventDate', None)
            
            # 跳過未來的比賽
            if event_date:
                try:
                    if hasattr(event_date, 'date'):
                        event_dt = event_date
                    else:
                        event_dt = datetime.strptime(str(event_date)[:10], '%Y-%m-%d')
                    
                    if event_dt > datetime.now():
                        print(f"⏭️  跳過未來賽事: {race_name}")
                        continue
                except:
                    pass
            
            for session in sessions:
                # 檢查是否已存在
                if check_existing_json(year, race_name, session):
                    print(f"⏭️  已存在: {year} {race_name} {session}")
                    total_skip += 1
                    continue
                
                print(f"\n[{round_number}] {year} {race_name} - {session}")
                print("-" * 50)
                
                result = generate_f54_for_session(year, race_name, session)
                results.append(result)
                
                if result['success']:
                    print(f"✅ 成功")
                    total_success += 1
                else:
                    print(f"❌ 失敗: {result['message']}")
                    total_fail += 1
    
    # 總結
    print("\n" + "=" * 70)
    print("批量生成完成")
    print("=" * 70)
    print(f"✅ 成功: {total_success}")
    print(f"❌ 失敗: {total_fail}")
    print(f"⏭️  跳過 (已存在): {total_skip}")
    print(f"📊 總計: {total_success + total_fail + total_skip}")
    
    # 保存報告
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'success': total_success,
            'fail': total_fail,
            'skip': total_skip
        },
        'results': results
    }
    
    report_path = JSON_DIR / 'f54_batch_generation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 報告已保存: {report_path}")


if __name__ == "__main__":
    main()
