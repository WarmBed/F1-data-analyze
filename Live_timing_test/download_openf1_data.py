"""
使用 OpenF1 API 獲取 2023-2024 年歷史數據
OpenF1 提供排位賽和正賽的結果數據
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

# 輸出目錄
OUTPUT_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze/json/historical_data")
OUTPUT_DIR.mkdir(exist_ok=True)

# OpenF1 API 基礎 URL
OPENF1_BASE = "https://api.openf1.org/v1"

def api_request(url, params, retries=3, delay=2):
    """帶重試的 API 請求"""
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            print(f"    API 返回 {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"    超時，重試 {attempt + 1}/{retries}")
        except Exception as e:
            print(f"    錯誤: {e}, 重試 {attempt + 1}/{retries}")
        
        if attempt < retries - 1:
            time.sleep(delay)
    return []

def get_sessions(year: int, session_type: str = None):
    """獲取指定年份的所有 sessions"""
    url = f"{OPENF1_BASE}/sessions"
    params = {"year": year}
    if session_type:
        params["session_type"] = session_type
    
    return api_request(url, params)

def get_position_data(session_key: int):
    """獲取指定 session 的最終位置數據"""
    url = f"{OPENF1_BASE}/position"
    params = {"session_key": session_key}
    
    return api_request(url, params)

def get_drivers(session_key: int):
    """獲取指定 session 的車手信息"""
    url = f"{OPENF1_BASE}/drivers"
    params = {"session_key": session_key}
    
    return api_request(url, params)

def extract_final_positions(position_data: list, drivers_data: list):
    """從位置數據中提取最終排名"""
    if not position_data:
        return []
    
    # 建立車手信息字典
    driver_info = {}
    for d in drivers_data:
        driver_num = d.get('driver_number')
        if driver_num:
            driver_info[driver_num] = {
                'name_acronym': d.get('name_acronym', ''),
                'full_name': d.get('full_name', ''),
                'team_name': d.get('team_name', '')
            }
    
    # 按車手分組，取最後的位置
    final_positions = {}
    for p in position_data:
        driver_num = p.get('driver_number')
        position = p.get('position')
        if driver_num and position:
            final_positions[driver_num] = position
    
    # 組合結果
    results = []
    for driver_num, position in final_positions.items():
        info = driver_info.get(driver_num, {})
        results.append({
            'driver_number': driver_num,
            'driver_code': info.get('name_acronym', f"#{driver_num}"),
            'driver_name': info.get('full_name', ''),
            'team': info.get('team_name', ''),
            'position': position
        })
    
    # 按位置排序
    results.sort(key=lambda x: x['position'])
    return results

def download_year_data(year: int):
    """下載指定年份的數據"""
    print(f"\n{'='*60}")
    print(f"開始下載 {year} 年數據 (OpenF1 API)")
    print(f"{'='*60}")
    
    year_data = {
        'year': year,
        'races': []
    }
    
    # 獲取排位賽 sessions
    print(f"\n正在獲取 {year} 排位賽 sessions...")
    q_sessions = get_sessions(year, "Qualifying")
    print(f"  找到 {len(q_sessions)} 場排位賽")
    
    # 獲取正賽 sessions
    print(f"正在獲取 {year} 正賽 sessions...")
    r_sessions = get_sessions(year, "Race")
    print(f"  找到 {len(r_sessions)} 場正賽")
    
    # 按 meeting_key 組織數據
    meetings = {}
    
    for s in q_sessions:
        meeting_key = s.get('meeting_key')
        if meeting_key not in meetings:
            meetings[meeting_key] = {
                'meeting_key': meeting_key,
                'location': s.get('location', ''),
                'country_name': s.get('country_name', ''),
                'date_start': s.get('date_start', ''),
                'q_session_key': None,
                'r_session_key': None
            }
        meetings[meeting_key]['q_session_key'] = s.get('session_key')
        meetings[meeting_key]['location'] = s.get('location', '')
        
    for s in r_sessions:
        meeting_key = s.get('meeting_key')
        if meeting_key not in meetings:
            meetings[meeting_key] = {
                'meeting_key': meeting_key,
                'location': s.get('location', ''),
                'country_name': s.get('country_name', ''),
                'date_start': s.get('date_start', ''),
                'q_session_key': None,
                'r_session_key': None
            }
        meetings[meeting_key]['r_session_key'] = s.get('session_key')
    
    # 處理每個 meeting
    meeting_list = sorted(meetings.values(), key=lambda x: x.get('date_start', ''))
    
    for idx, meeting in enumerate(meeting_list):
        location = meeting.get('location', 'Unknown')
        print(f"\n[{idx+1}/{len(meeting_list)}] {location}")
        
        race_data = {
            'meeting_key': meeting.get('meeting_key'),
            'location': location,
            'country': meeting.get('country_name', ''),
            'qualifying': None,
            'race': None
        }
        
        # 獲取排位賽結果
        q_session_key = meeting.get('q_session_key')
        if q_session_key:
            print(f"  獲取排位賽... (session_key: {q_session_key})")
            pos_data = get_position_data(q_session_key)
            drivers_data = get_drivers(q_session_key)
            q_results = extract_final_positions(pos_data, drivers_data)
            if q_results:
                race_data['qualifying'] = q_results
                print(f"    ✓ 排位賽: {len(q_results)} 名車手")
                if q_results:
                    print(f"    Pole: {q_results[0]['driver_code']}")
            else:
                print(f"    ✗ 無排位賽數據")
        
        # 獲取正賽結果
        r_session_key = meeting.get('r_session_key')
        if r_session_key:
            print(f"  獲取正賽... (session_key: {r_session_key})")
            pos_data = get_position_data(r_session_key)
            drivers_data = get_drivers(r_session_key)
            r_results = extract_final_positions(pos_data, drivers_data)
            if r_results:
                race_data['race'] = r_results
                print(f"    ✓ 正賽: {len(r_results)} 名車手")
                if r_results:
                    print(f"    冠軍: {r_results[0]['driver_code']}")
            else:
                print(f"    ✗ 無正賽數據")
        
        year_data['races'].append(race_data)
    
    return year_data

def save_data(data: dict, filename: str):
    """保存數據到 JSON"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✓ 已保存: {filepath}")

def main():
    print("="*60)
    print("F1 歷史數據下載器 (OpenF1 API)")
    print("下載 2023-2024 年排位賽和正賽結果")
    print("="*60)
    
    all_data = {}
    
    for year in [2023, 2024]:
        year_data = download_year_data(year)
        all_data[year] = year_data
        
        # 保存每年的數據
        save_data(year_data, f"openf1_{year}_results.json")
    
    # 保存合併數據
    save_data(all_data, "openf1_2023_2024_combined.json")
    
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
