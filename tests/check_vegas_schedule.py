#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查 2025 拉斯維加斯站賽程"""

import fastf1
import pandas as pd
from datetime import datetime
import pytz

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

print("=== 正在載入 2025 賽季賽程 ===\n")
schedule = fastf1.get_event_schedule(2025)

# 查找拉斯維加斯站
print("=== 搜尋拉斯維加斯站 ===")
vegas = schedule[schedule['Location'] == 'Las Vegas']

if len(vegas) == 0:
    print("⚠️ 未找到拉斯維加斯站，嘗試搜尋所有美國站...")
    usa_races = schedule[schedule['Country'] == 'USA']
    print(f"\n找到 {len(usa_races)} 場美國站:")
    print(usa_races[['RoundNumber', 'EventName', 'Location', 'EventDate']].to_string())
else:
    print(f"✅ 找到拉斯維加斯站 (第 {vegas.iloc[0]['RoundNumber']} 站)")
    print(f"賽事名稱: {vegas.iloc[0]['EventName']}")
    print(f"賽事日期: {vegas.iloc[0]['EventDate']}")
    print(f"賽事格式: {vegas.iloc[0]['EventFormat']}")
    
    # 列出所有場次時間
    print("\n=== 完整賽程時間表 ===")
    for i in range(1, 6):
        session_col = f'Session{i}'
        session_date_col = f'Session{i}Date'
        if session_col in vegas.columns and session_date_col in vegas.columns:
            session_name = vegas.iloc[0][session_col]
            session_date = vegas.iloc[0][session_date_col]
            if not pd.isna(session_name):
                print(f"{session_name}: {session_date}")
    
    # 檢查正賽時間
    print("\n=== 正賽時間分析 ===")
    race_date = vegas.iloc[0]['Session5Date']  # 通常正賽是 Session5
    print(f"正賽時間 (UTC): {race_date}")
    
    # 轉換為台灣時間
    if not pd.isna(race_date):
        taipei_tz = pytz.timezone('Asia/Taipei')
        race_date_utc = race_date.replace(tzinfo=pytz.UTC)
        race_date_taipei = race_date_utc.astimezone(taipei_tz)
        print(f"正賽時間 (台灣): {race_date_taipei}")
        
        # 計算距離現在的時間
        now = datetime.now(pytz.UTC)
        time_diff = (race_date_utc - now).total_seconds() / 3600
        print(f"當前時間 (UTC): {now}")
        print(f"時間差距: {time_diff:.1f} 小時")
        
        if time_diff > 0:
            print(f"⏰ 比賽尚未開始，還有 {time_diff:.1f} 小時")
        else:
            print(f"✅ 比賽已結束，已過 {abs(time_diff):.1f} 小時")

# 嘗試載入拉斯維加斯站數據
print("\n=== 嘗試載入賽事數據 ===")
try:
    event = fastf1.get_event(2025, 'Las Vegas')
    print(f"✅ 成功載入賽事: {event['EventName']}")
    print(f"賽事日期: {event['EventDate']}")
    
    # 嘗試載入正賽數據
    print("\n=== 嘗試載入正賽場次 ===")
    session = fastf1.get_session(2025, 'Las Vegas', 'R')
    print(f"場次: {session.name}")
    print(f"日期: {session.date}")
    
    # 嘗試載入數據
    print("\n=== 嘗試載入遙測數據 ===")
    session.load()
    print(f"✅ 數據載入成功!")
    print(f"圈數: {len(session.laps)}")
    print(f"車手數: {len(session.drivers)}")
    
except Exception as e:
    print(f"❌ 無法載入數據: {e}")

print("\n=== 檢查完成 ===")
