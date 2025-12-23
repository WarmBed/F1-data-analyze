#!/usr/bin/env python3
"""
測試 Open-Meteo API - 2025 美國大獎賽（COTA）天氣預報
Test Open-Meteo API for 2025 US GP weather forecast
"""

import datetime as dt
import requests

# Circuit of the Americas (Austin, Texas)
LAT = 30.1328
LON = -97.6411
RACE_DAY = dt.date(2025, 10, 19)

print("=" * 60)
print("🏁 2025 US Grand Prix Weather Forecast")
print("📍 Circuit of the Americas, Austin, Texas")
print(f"📅 Race Day: {RACE_DAY}")
print("=" * 60)

# 查詢參數
params = {
    "latitude": LAT,
    "longitude": LON,
    "hourly": "temperature_2m,precipitation,precipitation_probability,cloudcover,windspeed_10m,winddirection_10m",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours",
    "timezone": "auto",
    "forecast_days": 16
}

try:
    print("\n🌐 正在查詢 Open-Meteo API...")
    response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    print("✅ 資料取得成功！")
    
    # 每日摘要
    print("\n" + "=" * 60)
    print("📊 每日天氣摘要 (Daily Summary)")
    print("=" * 60)
    daily = data.get("daily", {})
    for i, date_str in enumerate(daily.get("time", [])):
        date = dt.date.fromisoformat(date_str)
        # 只顯示賽事週末前後 (10/18-10/20)
        if abs((date - RACE_DAY).days) <= 1:
            tmax = daily['temperature_2m_max'][i]
            tmin = daily['temperature_2m_min'][i]
            precip_sum = daily['precipitation_sum'][i]
            precip_hours = daily['precipitation_hours'][i]
            
            race_marker = "🏁 " if date == RACE_DAY else "   "
            print(f"{race_marker}{date} ({['一','二','三','四','五','六','日'][date.weekday()]}):")
            print(f"   🌡️  溫度: {tmin:.1f}°C ~ {tmax:.1f}°C")
            print(f"   🌧️  降雨: {precip_sum:.1f} mm ({precip_hours:.0f} 小時)")
    
    # 逐小時預報（只顯示正賽日前後24小時）
    print("\n" + "=" * 60)
    print(f"⏰ 逐小時預報 (Race Day ±12h)")
    print("=" * 60)
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    
    race_window_start = dt.datetime.combine(RACE_DAY, dt.time(0, 0))
    race_window_end = dt.datetime.combine(RACE_DAY, dt.time(23, 59))
    
    for i, time_str in enumerate(times):
        timestamp = dt.datetime.fromisoformat(time_str)
        
        # 只顯示正賽日當天
        if race_window_start <= timestamp <= race_window_end:
            temp = hourly['temperature_2m'][i]
            precip = hourly['precipitation'][i]
            precip_prob = hourly['precipitation_probability'][i]
            cloud = hourly['cloudcover'][i]
            wind = hourly['windspeed_10m'][i]
            wind_dir = hourly['winddirection_10m'][i]
            
            # 格式化輸出
            time_local = timestamp.strftime("%H:%M")
            print(f"{time_local} | ", end="")
            print(f"🌡️ {temp:5.1f}°C | ", end="")
            print(f"🌧️ {precip:4.1f}mm ({precip_prob:3.0f}%) | ", end="")
            print(f"☁️ {cloud:3.0f}% | ", end="")
            print(f"💨 {wind:4.1f} km/h @ {wind_dir:3.0f}°")
    
    print("\n" + "=" * 60)
    print("✅ 預報查詢完成！")
    print("=" * 60)
    
except requests.exceptions.RequestException as e:
    print(f"❌ API 請求失敗: {e}")
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
