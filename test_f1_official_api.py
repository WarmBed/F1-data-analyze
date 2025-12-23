#!/usr/bin/env python3
"""測試 F1 官方 Live Timing API 數據結構"""

import requests
import json

# F1 官方 Live Timing 靜態 JSON API
# https://livetiming.formula1.com/static/{year}/{meeting_key}/{session_key}/{topic}.json

base_url = "https://livetiming.formula1.com/static"
year = 2024
meeting_key = 1243  # Abu Dhabi GP
session_key = 9601  # Race

print("="*70)
print("F1 官方 Live Timing API 數據結構分析")
print("="*70)
print(f"賽事: 2024 Abu Dhabi GP")
print(f"Meeting Key: {meeting_key}")
print(f"Session Key: {session_key}")
print("="*70)

topics = [
    "TimingData",
    "TimingAppData", 
    "LapSeries",
    "CarData.z",
    "Position.z",
    "SessionInfo",
    "DriverList",
    "WeatherData",
    "TrackStatus",
    "RaceControlMessages"
]

for topic in topics:
    url = f"{base_url}/{year}/{meeting_key}/{session_key}/{topic}.json"
    print(f"\n📡 {topic}")
    print(f"   URL: {url}")
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            print(f"   ✅ 成功! 大小: {len(r.content):,} bytes")
            
            # 嘗試解析 JSON
            try:
                data = r.json()
                
                if isinstance(data, dict):
                    print(f"   類型: Dictionary")
                    keys = list(data.keys())
                    print(f"   Keys ({len(keys)}): {keys[:10]}")
                    
                    # 特殊處理 LapSeries - 可能包含 mini-sector 數據
                    if topic == "LapSeries" and keys:
                        first_driver = keys[0] if not keys[0].startswith('_') else keys[1] if len(keys) > 1 else None
                        if first_driver:
                            laps = data[first_driver]
                            print(f"   車手 {first_driver} 圈數: {len(laps)}")
                            if laps:
                                first_lap = laps[0] if isinstance(laps, list) else laps
                                print(f"   第一圈 Keys: {list(first_lap.keys()) if isinstance(first_lap, dict) else 'Not a dict'}")
                                
                elif isinstance(data, list):
                    print(f"   類型: List")
                    print(f"   長度: {len(data)}")
                    if len(data) > 0:
                        first_item = data[0]
                        if isinstance(first_item, dict):
                            print(f"   第一項 Keys: {list(first_item.keys())[:10]}")
                        
            except json.JSONDecodeError:
                print(f"   ⚠️  二進制數據 (可能是 .z 壓縮格式)")
                
        else:
            print(f"   ❌ HTTP {r.status_code}")
            
    except requests.Timeout:
        print(f"   ❌ 請求超時")
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")

print("\n" + "="*70)
print("✅ F1 官方 API 提供以下數據主題:")
print("="*70)
print("1. TimingData - 計時數據 (位置、差距、圈速)")
print("2. TimingAppData - App 數據 (扇區時間、輪胎等)")
print("3. LapSeries - 圈速序列 (可能包含 mini-sector)")
print("4. CarData.z - 車輛遙測 (速度、轉速、油門等)")
print("5. Position.z - 位置數據 (X, Y, Z 座標)")
print("6. SessionInfo - 賽事資訊")
print("7. DriverList - 車手列表")
print("8. WeatherData - 天氣數據")
print("9. TrackStatus - 賽道狀態")
print("10. RaceControlMessages - 賽會訊息")
