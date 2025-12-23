#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查 Function 96/97/99 的刷新狀態"""

import json
from pathlib import Path
from datetime import datetime, timezone

print("=" * 80)
print("檢查 Las Vegas 賽後刷新狀態")
print("=" * 80)

# 1. 檢查 Season Calendar
print("\n1️⃣ Season Calendar (Function 99)")
print("-" * 80)

calendar_files = sorted(Path("json").glob("season_calendar_multi_year*.json"), 
                       key=lambda p: p.stat().st_mtime, reverse=True)

if calendar_files:
    latest_calendar = calendar_files[0]
    file_mtime = datetime.fromtimestamp(latest_calendar.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age_hours = (now - file_mtime).total_seconds() / 3600
    
    print(f"📁 檔案: {latest_calendar.name}")
    print(f"🕐 修改時間: {file_mtime} (UTC)")
    print(f"⏰ 檔案年齡: {age_hours:.1f} 小時")
    print(f"🔄 刷新間隔: 168 小時 (7 天)")
    print(f"✅ 狀態: {'新鮮' if age_hours < 168 else '過期'}")
    
    # 讀取內容檢查 Las Vegas 狀態
    data = json.loads(latest_calendar.read_text(encoding='utf-8'))
    year_2025_events = data['data'].get('2025', [])  # 是 list，不是 dict
    vegas_events = [e for e in year_2025_events if e.get('location') == 'Las Vegas']
    
    if vegas_events:
        vegas = vegas_events[0]
        print(f"\n🏁 Las Vegas 賽事狀態:")
        print(f"   - Round: {vegas['round']}")
        print(f"   - is_completed: {vegas['is_completed']}")
        print(f"   - race_date_utc: {vegas['race_date_utc']}")
        
        race_dt = datetime.fromisoformat(vegas['race_date_utc'].replace('Z', '+00:00'))
        hours_since_race = (now - race_dt).total_seconds() / 3600
        
        print(f"   - 賽後經過: {hours_since_race:.1f} 小時")
        print(f"   - 應該觸發: {'❌ 是的！需要立即刷新' if vegas['is_completed'] == False else '✅ 已標記完成'}")
else:
    print("❌ 找不到 Season Calendar 檔案")

# 2. 檢查 Championship Standings
print("\n\n2️⃣ Championship Standings (Function 97)")
print("-" * 80)

standings_files = sorted(Path("json").glob("championship_standings_2025*.json"), 
                        key=lambda p: p.stat().st_mtime, reverse=True)

if standings_files:
    latest_standings = standings_files[0]
    file_mtime = datetime.fromtimestamp(latest_standings.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age_hours = (now - file_mtime).total_seconds() / 3600
    
    print(f"📁 檔案: {latest_standings.name}")
    print(f"🕐 修改時間: {file_mtime} (UTC)")
    print(f"⏰ 檔案年齡: {age_hours:.1f} 小時")
    
    # 讀取內容
    data = json.loads(latest_standings.read_text(encoding='utf-8'))
    resolved_round = data['metadata']['resolved_round']
    generated_at = data['metadata']['generated_at']
    
    print(f"🏆 最新回合: Round {resolved_round}")
    print(f"📅 生成時間: {generated_at}")
    
    # 計算是否應該觸發賽後加速
    if latest_calendar:
        calendar_data = json.loads(latest_calendar.read_text(encoding='utf-8'))
        year_2025_events = calendar_data['data'].get('2025', [])
        vegas_list = [e for e in year_2025_events if e.get('location') == 'Las Vegas']
        if vegas_list:
            vegas = vegas_list[0]
        race_dt = datetime.fromisoformat(vegas['race_date_utc'].replace('Z', '+00:00'))
        hours_since_race = (now - race_dt).total_seconds() / 3600
        
        print(f"\n🔍 賽後加速模式檢查:")
        print(f"   - Las Vegas 賽後經過: {hours_since_race:.1f} 小時")
        print(f"   - 應該啟用 6 小時刷新: {'✅ 是 (0-72小時內)' if 0 <= hours_since_race <= 72 else '❌ 否'}")
        print(f"   - 當前檔案年齡: {age_hours:.1f} 小時")
        print(f"   - 應該觸發刷新: {'❌ 是的！檔案過期' if age_hours > 6 and 0 <= hours_since_race <= 72 else '✅ 不需要'}")
else:
    print("❌ 找不到 Championship Standings 檔案")

# 3. 檢查 Weather Forecast
print("\n\n3️⃣ Weather Forecast (Function 96)")
print("-" * 80)

weather_files = sorted(Path("json").glob("race_weather_forecast_2025_Las_Vegas*.json"), 
                      key=lambda p: p.stat().st_mtime, reverse=True)

if weather_files:
    latest_weather = weather_files[0]
    file_mtime = datetime.fromtimestamp(latest_weather.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age_hours = (now - file_mtime).total_seconds() / 3600
    
    print(f"📁 檔案: {latest_weather.name}")
    print(f"🕐 修改時間: {file_mtime} (UTC)")
    print(f"⏰ 檔案年齡: {age_hours:.1f} 小時")
    print(f"🔄 刷新間隔: 24 小時")
    print(f"✅ 狀態: {'新鮮' if age_hours < 24 else '過期'}")
else:
    print("❌ 找不到 Las Vegas Weather Forecast 檔案")

print("\n" + "=" * 80)
print("檢查完成")
print("=" * 80)
