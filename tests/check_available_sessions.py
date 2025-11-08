#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查特定賽道/年份的可用 Session
"""
import fastf1
import sys

def check_sessions(year, race):
    """檢查指定賽事的所有可用 Session"""
    try:
        print(f"\n{'='*70}")
        print(f"檢查 {year} {race} 的可用 Session")
        print(f"{'='*70}")
        
        # 獲取賽事
        event = fastf1.get_event(year, race)
        
        print(f"\n賽事名稱: {event.EventName}")
        print(f"賽事日期: {event.EventDate}")
        print(f"賽事格式: {event.EventFormat}")
        
        # 列出所有可用的 Session
        print(f"\n可用的 Sessions:")
        sessions = []
        
        for session_name in ['FP1', 'FP2', 'FP3', 'Qualifying', 'Sprint', 'Sprint Shootout', 'Race']:
            try:
                session = fastf1.get_session(year, race, session_name)
                session.load(telemetry=False, laps=False, weather=False)
                sessions.append(session_name)
                print(f"  ✅ {session_name}")
            except Exception as e:
                print(f"  ❌ {session_name} - {str(e)[:50]}")
        
        print(f"\n總結: 共 {len(sessions)} 個可用 Session")
        print(f"可用列表: {', '.join(sessions)}")
        
        return sessions
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        return []

if __name__ == "__main__":
    # 啟用緩存
    fastf1.Cache.enable_cache('cache')
    
    tracks = [
        ('Austria', [2022, 2023, 2024]),
        ('Brazil', [2022, 2023, 2024]),
        ('Qatar', [2022, 2023, 2024]),
        ('China', [2019, 2024])  # 測試 2019 (最後一次) 和 2024
    ]
    
    results = {}
    
    for track, years in tracks:
        results[track] = {}
        for year in years:
            print(f"\n{'#'*70}")
            sessions = check_sessions(year, track)
            results[track][year] = sessions
    
    # 總結報告
    print(f"\n\n{'='*70}")
    print("總結報告")
    print(f"{'='*70}")
    
    for track, year_data in results.items():
        print(f"\n【{track}】")
        for year, sessions in year_data.items():
            has_fp3 = 'FP3' in sessions
            status = '✅ 有 FP3' if has_fp3 else '⚠️  無 FP3 (可能是 Sprint 週末)'
            print(f"  {year}: {status}")
            if not has_fp3 and sessions:
                print(f"       可用: {', '.join(sessions)}")
