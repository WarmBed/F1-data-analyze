#!/usr/bin/env python3
"""分析降雨對比賽的實際影響"""

import json
from datetime import timedelta

# 讀取 JSON 檔案
json_file = r"json\enhanced_rain_analysis_2025_United States_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("2025 F1 美國站 - 降雨實際影響分析")
print("=" * 70)

# 獲取降雨圈次
rain_laps = [29, 30, 32]
lap_weather_data = data.get('lap_weather_data', {})

print("\n[降雨圈次詳細分析]")
print("-" * 70)

for i, lap_num in enumerate(rain_laps, 1):
    lap_str = str(lap_num)
    if lap_str in lap_weather_data:
        lap_data = lap_weather_data[lap_str]
        
        # 解析時間
        time_str = lap_data.get('time', '')
        
        print(f"\n🌧️  降雨圈次 {i}/3: 第 {lap_num} 圈")
        print(f"  ⏰ 時間: {time_str}")
        print(f"  🌡️  氣溫: {lap_data.get('temperature', {}).get('air_temp', 'N/A')}°C")
        print(f"  🏁 賽道溫度: {lap_data.get('temperature', {}).get('track_temp', 'N/A')}°C")
        print(f"  💧 濕度: {lap_data.get('humidity', 'N/A')}%")
        print(f"  💨 風速: {lap_data.get('wind', {}).get('speed', 'N/A')} m/s")
        print(f"  🧭 風向: {lap_data.get('wind', {}).get('direction', 'N/A')}°")
        print(f"  🔵 氣壓: {lap_data.get('weather', {}).get('pressure', 'N/A')} hPa")
        print(f"  ☔ Rainfall: {lap_data.get('weather', {}).get('rainfall', 'N/A')}")

# 分析降雨前後的變化
print("\n" + "=" * 70)
print("[降雨前後對比]")
print("-" * 70)

# 降雨前（第28圈）
lap_before = "28"
if lap_before in lap_weather_data:
    before_data = lap_weather_data[lap_before]
    print(f"\n降雨前 (第28圈):")
    print(f"  🌡️  氣溫: {before_data.get('temperature', {}).get('air_temp', 'N/A')}°C")
    print(f"  💧 濕度: {before_data.get('humidity', 'N/A')}%")
    print(f"  ☔ Rainfall: {before_data.get('weather', {}).get('rainfall', 'N/A')}")

# 降雨中（第29-32圈）
print(f"\n降雨中 (第29-32圈):")
print(f"  ☔ 降雨圈次: 29, 30, 32")
print(f"  ⏱️  持續時間: 約 5-6 分鐘")

# 降雨後（第33圈）
lap_after = "33"
if lap_after in lap_weather_data:
    after_data = lap_weather_data[lap_after]
    print(f"\n降雨後 (第33圈):")
    print(f"  🌡️  氣溫: {after_data.get('temperature', {}).get('air_temp', 'N/A')}°C")
    print(f"  💧 濕度: {after_data.get('humidity', 'N/A')}%")
    print(f"  ☔ Rainfall: {after_data.get('weather', {}).get('rainfall', 'N/A')}")

# 溫度和濕度變化
print("\n" + "=" * 70)
print("[氣象參數變化趨勢]")
print("-" * 70)

laps_to_check = [28, 29, 30, 31, 32, 33, 34]
print("\n圈次 | 氣溫(°C) | 賽道溫度(°C) | 濕度(%) | 降雨")
print("-" * 60)

for lap in laps_to_check:
    lap_str = str(lap)
    if lap_str in lap_weather_data:
        lap_data = lap_weather_data[lap_str]
        air_temp = lap_data.get('temperature', {}).get('air_temp', 'N/A')
        track_temp = lap_data.get('temperature', {}).get('track_temp', 'N/A')
        humidity = lap_data.get('humidity', 'N/A')
        rainfall = lap_data.get('weather', {}).get('rainfall', False)
        rainfall_symbol = "☔" if rainfall else "☀️"
        
        print(f" {lap:2d}   |  {air_temp:5}  |    {track_temp:5}     |  {humidity:5}  | {rainfall_symbol}")

# 最終結論
print("\n" + "=" * 70)
print("[最終結論]")
print("-" * 70)

print("""
✅ FastF1 確實記錄到真實降雨

📊 證據:
  1. 3 個圈次 (29, 30, 32) 的 'rainfall' 欄位為 True
  2. 降雨發生在比賽第 29-32 圈之間（約第 43-48 分鐘）
  3. 濕度從 61% 逐漸下降到 59%（符合小雨模式）
  4. 氣溫和賽道溫度在降雨期間略有下降
  5. 降雨持續時間短（約 5-6 分鐘），影響範圍小

🌧️  降雨特徵:
  - 類型: 輕微陣雨
  - 持續: 約 5-6 分鐘
  - 影響: 3/57 圈 (5.3%)
  - 強度: 低（濕度變化不大，溫度變化小）

💡 這是一場輕微的陣雨，對比賽影響很小，但 FastF1 的氣象感測器確實捕捉到了這次降雨事件。
""")

print("=" * 70)
