"""
生成歷年 Yellow Flag 統計數據（以日本站為例）
分析每個彎道的 Yellow Flag 頻率
"""
import fastf1
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 啟用緩存
cache_dir = Path('f1_analysis_cache')
cache_dir.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(cache_dir))

def get_suzuka_corners():
    """
    獲取鈴鹿賽道的 18 個彎道資訊
    使用 FastF1 官方數據
    """
    try:
        # 使用最近的賽季獲取彎道數據
        session = fastf1.get_session(2024, 'Japan', 'R')
        session.load()
        
        circuit_info = session.get_circuit_info()
        if hasattr(circuit_info, 'corners') and len(circuit_info.corners) > 0:
            corners = []
            for _, corner in circuit_info.corners.iterrows():
                corners.append({
                    "number": int(corner['Number']),
                    "x": float(corner['X']),
                    "y": float(corner['Y']),
                    "distance": float(corner['Distance']),
                    "angle": float(corner.get('Angle', 0))
                })
            return corners
    except Exception as e:
        print(f"⚠️ 無法獲取官方彎道數據: {e}")
    
    return []

def find_nearest_corner(distance_m, corners):
    """
    根據距離找到最近的彎道
    
    Args:
        distance_m: 事件發生的距離（公尺）
        corners: 彎道列表
    
    Returns:
        最近的彎道編號，如果距離太遠則返回 None
    """
    if not corners:
        return None
    
    min_dist = float('inf')
    nearest_corner = None
    
    for corner in corners:
        dist = abs(corner['distance'] - distance_m)
        if dist < min_dist:
            min_dist = dist
            nearest_corner = corner['number']
    
    # 如果距離超過 200 公尺，認為不在彎道附近
    if min_dist > 200:
        return None
    
    return nearest_corner

def analyze_yellow_flags_for_year(year, race='Japan', session_type='R'):
    """
    分析單一年份的 Yellow Flag 數據
    
    Args:
        year: 年份
        race: 賽事名稱
        session_type: 會話類型（R=正賽, Q=排位賽, FP1/2/3=練習賽）
    
    Returns:
        該年份的 Yellow Flag 統計數據
    """
    try:
        print(f"\n分析 {year} {race} {session_type}...")
        
        # 載入會話
        session = fastf1.get_session(year, race, session_type)
        session.load()
        
        # 獲取賽道控制訊息
        messages = session.race_control_messages
        
        if messages is None or len(messages) == 0:
            print(f"  ⚠️ 無賽道控制訊息")
            return None
        
        # 篩選 Yellow Flag 相關訊息
        yellow_flags = messages[
            messages['Message'].str.contains('YELLOW', case=False, na=False) |
            messages['Flag'].str.contains('YELLOW', case=False, na=False)
        ]
        
        if len(yellow_flags) == 0:
            print(f"  ℹ️ 無 Yellow Flag 事件")
            return {
                "year": year,
                "race": race,
                "session": session_type,
                "yellow_flag_count": 0,
                "events": []
            }
        
        # 獲取彎道數據
        corners = get_suzuka_corners()
        
        # 獲取賽道長度
        fastest_lap = session.laps.pick_fastest()
        if fastest_lap is not None:
            telemetry = fastest_lap.get_telemetry()
            track_length = telemetry['Distance'].max()
        else:
            track_length = 5807.0  # 鈴鹿賽道標準長度
        
        # 分析每個 Yellow Flag 事件
        events = []
        for idx, flag in yellow_flags.iterrows():
            event = {
                "time": str(flag.get('Time', '')),
                "lap": int(flag.get('Lap', 0)) if not pd.isna(flag.get('Lap')) else None,
                "message": str(flag.get('Message', '')),
                "flag": str(flag.get('Flag', '')),
                "sector": int(flag.get('Sector', 0)) if not pd.isna(flag.get('Sector')) else None,
                "category": str(flag.get('Category', ''))
            }
            
            # 嘗試定位彎道
            # 方法1: 從訊息中提取彎道編號
            corner_number = None
            message_text = event['message'].upper()
            
            # 檢查訊息中是否提到 TURN/T 加數字
            import re
            corner_match = re.search(r'T(?:URN)?\s*(\d+)', message_text)
            if corner_match:
                corner_number = int(corner_match.group(1))
            
            # 方法2: 使用 Sector 推測大致區域
            if corner_number is None and event['sector']:
                sector = event['sector']
                # 鈴鹿賽道 3 個 Sector 的大致彎道分佈
                if sector == 1:
                    # Sector 1: T1-T6 (約前 1/3)
                    sector_corners = [1, 2, 3, 4, 5, 6]
                elif sector == 2:
                    # Sector 2: T7-T12 (約中間 1/3)
                    sector_corners = [7, 8, 9, 10, 11, 12]
                else:
                    # Sector 3: T13-T18 (約後 1/3)
                    sector_corners = [13, 14, 15, 16, 17, 18]
                
                event['possible_corners'] = sector_corners
            
            if corner_number:
                event['corner'] = corner_number
            
            events.append(event)
        
        result = {
            "year": year,
            "race": race,
            "session": session_type,
            "yellow_flag_count": len(events),
            "events": events,
            "track_length_m": float(track_length)
        }
        
        print(f"  ✅ 找到 {len(events)} 個 Yellow Flag 事件")
        return result
        
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

def aggregate_corner_statistics(yearly_data, corners):
    """
    彙總每個彎道的 Yellow Flag 統計
    
    Args:
        yearly_data: 歷年數據列表
        corners: 彎道列表
    
    Returns:
        每個彎道的統計數據
    """
    corner_stats = defaultdict(lambda: {
        "corner_number": 0,
        "total_yellow_flags": 0,
        "years_with_incidents": [],
        "events": []
    })
    
    # 初始化所有彎道
    for corner in corners:
        corner_num = corner['number']
        corner_stats[corner_num]['corner_number'] = corner_num
        corner_stats[corner_num]['distance'] = corner['distance']
        corner_stats[corner_num]['x'] = corner['x']
        corner_stats[corner_num]['y'] = corner['y']
    
    # 統計每個事件
    for year_data in yearly_data:
        if year_data is None:
            continue
        
        year = year_data['year']
        for event in year_data['events']:
            corner_num = event.get('corner')
            
            if corner_num and 1 <= corner_num <= 18:
                corner_stats[corner_num]['total_yellow_flags'] += 1
                if year not in corner_stats[corner_num]['years_with_incidents']:
                    corner_stats[corner_num]['years_with_incidents'].append(year)
                corner_stats[corner_num]['events'].append({
                    "year": year,
                    "message": event['message'],
                    "time": event['time']
                })
            
            # 如果只知道可能的彎道範圍
            elif 'possible_corners' in event:
                for corner_num in event['possible_corners']:
                    # 分配權重（不確定的事件）
                    corner_stats[corner_num]['total_yellow_flags'] += 0.5
    
    # 轉換為列表並排序
    result = []
    for corner_num in sorted(corner_stats.keys()):
        stats = corner_stats[corner_num]
        stats['incident_rate'] = stats['total_yellow_flags'] / len(yearly_data) if yearly_data else 0
        result.append(stats)
    
    return result

def main():
    """主程式"""
    print("=" * 70)
    print("生成歷年 Yellow Flag 統計數據（日本站 - 鈴鹿賽道）")
    print("=" * 70)
    
    # 獲取彎道資訊
    print("\n獲取鈴鹿賽道彎道資訊...")
    corners = get_suzuka_corners()
    if not corners:
        print("無法獲取彎道資訊")
        return
    print(f"獲取到 {len(corners)} 個彎道")
    
    # 分析歷年數據（2018-2024）
    years = [2018, 2019, 2023, 2024]  # 跳過 2020-2022（疫情期間部分賽事取消）
    
    yearly_data = []
    for year in years:
        data = analyze_yellow_flags_for_year(year, 'Japan', 'R')
        if data:
            yearly_data.append(data)
    
    # 彙總統計
    print("\n彙總彎道統計...")
    corner_statistics = aggregate_corner_statistics(yearly_data, corners)
    
    # 構建最終 JSON
    output = {
        "metadata": {
            "circuit": "Suzuka International Racing Course",
            "country": "Japan",
            "analysis_type": "Yellow Flag Statistics",
            "years_analyzed": years,
            "total_sessions": len(yearly_data),
            "generated_at": datetime.now().isoformat()
        },
        "corners": corners,
        "corner_statistics": corner_statistics,
        "yearly_data": yearly_data,
        "summary": {
            "total_yellow_flags": sum(d['yellow_flag_count'] for d in yearly_data),
            "most_dangerous_corner": max(corner_statistics, key=lambda x: x['total_yellow_flags'])['corner_number'] if corner_statistics else None,
            "average_yellow_flags_per_race": sum(d['yellow_flag_count'] for d in yearly_data) / len(yearly_data) if yearly_data else 0
        }
    }
    
    # 儲存 JSON
    output_dir = Path('json')
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'yellow_flag_statistics_japan_suzuka.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n數據已儲存: {output_file}")
    print(f"\n統計摘要:")
    print(f"   - 分析年份: {len(yearly_data)} 年")
    print(f"   - 總 Yellow Flag 事件: {output['summary']['total_yellow_flags']}")
    print(f"   - 平均每場: {output['summary']['average_yellow_flags_per_race']:.1f}")
    if output['summary']['most_dangerous_corner']:
        print(f"   - 最危險彎道: T{output['summary']['most_dangerous_corner']}")
    
    print("\n彎道危險度排名（前 5）:")
    sorted_corners = sorted(corner_statistics, key=lambda x: x['total_yellow_flags'], reverse=True)
    for i, corner in enumerate(sorted_corners[:5], 1):
        if corner['total_yellow_flags'] > 0:
            print(f"   {i}. T{corner['corner_number']}: {corner['total_yellow_flags']:.1f} 次 Yellow Flag")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    import pandas as pd
    main()
