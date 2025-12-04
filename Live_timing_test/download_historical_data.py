"""
下載 2023-2024 年歷史數據
使用 FastF1 的 session.results 來獲取排位賽和正賽結果
避免 Ergast API (已廢棄) 的問題
"""

import fastf1
import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# 設定緩存
CACHE_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze/f1_analysis_cache")
CACHE_DIR.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

# 輸出目錄
OUTPUT_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze/json/historical_data")
OUTPUT_DIR.mkdir(exist_ok=True)

def get_race_schedule(year: int):
    """獲取賽季賽程"""
    try:
        schedule = fastf1.get_event_schedule(year)
        # 過濾正式比賽 (排除測試)
        races = schedule[schedule['EventFormat'].isin(['conventional', 'sprint_shootout', 'sprint_qualifying', 'sprint'])]
        return races
    except Exception as e:
        print(f"  獲取 {year} 賽程失敗: {e}")
        return None

def download_session_results(year: int, event_name: str, session_type: str):
    """
    下載特定 session 的結果
    session_type: 'Q' for Qualifying, 'R' for Race
    """
    try:
        session = fastf1.get_session(year, event_name, session_type)
        # 只載入基本結果，不載入遙測
        session.load(telemetry=False, weather=False, messages=False)
        
        results = session.results
        if results is None or results.empty:
            return None
            
        data = []
        for _, row in results.iterrows():
            driver_data = {
                'driver_code': row.get('Abbreviation', ''),
                'driver_name': f"{row.get('FirstName', '')} {row.get('LastName', '')}",
                'team': row.get('TeamName', ''),
                'position': int(row.get('Position', 0)) if pd.notna(row.get('Position')) else 0,
                'grid_position': int(row.get('GridPosition', 0)) if pd.notna(row.get('GridPosition')) else 0,
            }
            
            # 對於排位賽，position 就是排位結果
            # 對於正賽，position 是最終名次，grid_position 是發車位
            if session_type == 'Q':
                driver_data['q_position'] = driver_data['position']
            else:
                driver_data['finish_position'] = driver_data['position']
                driver_data['status'] = row.get('Status', '')
                
            data.append(driver_data)
            
        return data
        
    except Exception as e:
        print(f"    下載 {year} {event_name} {session_type} 失敗: {e}")
        return None

def download_year_data(year: int):
    """下載指定年份的所有數據"""
    print(f"\n{'='*60}")
    print(f"開始下載 {year} 年數據")
    print(f"{'='*60}")
    
    schedule = get_race_schedule(year)
    if schedule is None:
        return {}
        
    year_data = {
        'year': year,
        'races': []
    }
    
    # 對於過去的年份，直接處理所有比賽
    from datetime import datetime
    
    # 簡單判斷：2023 和 2024 已完成的比賽
    if year <= 2024:
        # 直接使用所有賽事
        completed_races = schedule
        # 對於 2024，只取到目前為止的比賽
        if year == 2024:
            # 保守起見，取 RoundNumber <= 24 (2024全年)
            completed_races = schedule[schedule['RoundNumber'] <= 24]
    
    print(f"找到 {len(completed_races)} 場已完成的比賽")
    
    for idx, (_, event) in enumerate(completed_races.iterrows()):
        event_name = event['EventName']
        round_number = event['RoundNumber']
        
        print(f"\n[{idx+1}/{len(completed_races)}] {event_name} (Round {round_number})")
        
        race_data = {
            'round': int(round_number),
            'event_name': event_name,
            'date': str(event['EventDate']),
            'qualifying': None,
            'race': None
        }
        
        # 下載排位賽結果
        print(f"  下載排位賽...")
        q_data = download_session_results(year, event_name, 'Q')
        if q_data:
            race_data['qualifying'] = q_data
            print(f"    ✓ 排位賽: {len(q_data)} 名車手")
        else:
            print(f"    ✗ 排位賽數據失敗")
            
        # 下載正賽結果
        print(f"  下載正賽...")
        r_data = download_session_results(year, event_name, 'R')
        if r_data:
            race_data['race'] = r_data
            winner = next((d for d in r_data if d['finish_position'] == 1), None)
            if winner:
                print(f"    ✓ 正賽: 冠軍 {winner['driver_code']}")
        else:
            print(f"    ✗ 正賽數據失敗")
            
        year_data['races'].append(race_data)
        
    return year_data

def save_data(data: dict, filename: str):
    """保存數據到 JSON"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✓ 已保存: {filepath}")

def main():
    import pandas as pd
    
    print("="*60)
    print("F1 歷史數據下載器")
    print("下載 2023-2024 年排位賽和正賽結果")
    print("="*60)
    
    all_data = {}
    
    for year in [2023, 2024]:
        year_data = download_year_data(year)
        all_data[year] = year_data
        
        # 保存每年的數據
        save_data(year_data, f"fastf1_{year}_results.json")
        
    # 保存合併數據
    save_data(all_data, "fastf1_2023_2024_combined.json")
    
    # 統計摘要
    print("\n" + "="*60)
    print("下載完成摘要")
    print("="*60)
    
    for year, data in all_data.items():
        races = data.get('races', [])
        q_count = sum(1 for r in races if r.get('qualifying'))
        r_count = sum(1 for r in races if r.get('race'))
        print(f"{year}: {len(races)} 場比賽, Q數據 {q_count}, R數據 {r_count}")

if __name__ == '__main__':
    main()
