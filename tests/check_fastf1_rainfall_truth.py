#!/usr/bin/env python3
"""深入分析 FastF1 降雨數據的真實性"""

import json

# 讀取 JSON 檔案
json_file = r"json\enhanced_rain_analysis_2025_United States_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("2025 F1 美國站 - FastF1 降雨數據真實性分析")
print("=" * 70)

# 分析每圈的降雨狀態
print("\n[逐圈降雨狀態檢查]")
print("-" * 70)

rain_laps = []
no_rain_laps = []

lap_weather_data = data.get('lap_weather_data', {})

for lap_num, lap_data in lap_weather_data.items():
    rainfall = lap_data.get('weather', {}).get('rainfall', None)
    
    if rainfall is True:
        rain_laps.append(lap_num)
    elif rainfall is False:
        no_rain_laps.append(lap_num)
    else:
        print(f"⚠️  圈 {lap_num}: rainfall 數據缺失或異常 (值: {rainfall})")

print(f"\n📊 統計結果:")
print(f"  ☔ 有降雨的圈數: {len(rain_laps)} 圈")
print(f"  ☀️  無降雨的圈數: {len(no_rain_laps)} 圈")
print(f"  📈 總檢查圈數: {len(lap_weather_data)} 圈")

# 顯示有降雨的圈次詳細資訊
if rain_laps:
    print(f"\n☔ 【有降雨的圈次詳細資訊】")
    print("-" * 70)
    
    for lap_num in rain_laps[:10]:  # 最多顯示前 10 圈
        lap_data = lap_weather_data[lap_num]
        time = lap_data.get('time', 'N/A')
        air_temp = lap_data.get('temperature', {}).get('air_temp', 'N/A')
        track_temp = lap_data.get('temperature', {}).get('track_temp', 'N/A')
        humidity = lap_data.get('humidity', 'N/A')
        rainfall = lap_data.get('weather', {}).get('rainfall', 'N/A')
        
        print(f"\n圈 {lap_num}:")
        print(f"  ⏰ 時間: {time}")
        print(f"  🌡️  氣溫: {air_temp}°C")
        print(f"  🏁 賽道溫度: {track_temp}°C")
        print(f"  💧 濕度: {humidity}%")
        print(f"  ☔ Rainfall: {rainfall} (FastF1 原始值)")
    
    if len(rain_laps) > 10:
        print(f"\n... 還有 {len(rain_laps) - 10} 圈有降雨記錄")
else:
    print(f"\n❌ 【沒有任何圈次記錄到降雨】")
    print("FastF1 的 'rainfall' 欄位在所有圈次中都是 False")

# 檢查原始數據點
print("\n" + "=" * 70)
print("[原始氣象數據點分析]")
print("-" * 70)

summary = data.get('summary', {})
print(f"  📡 總氣象數據點: {summary.get('weather_data_points', 'N/A')}")
print(f"  🌧️  原始降雨數據點: {summary.get('original_rain_points', 'N/A')}")
print(f"  📊 原始降雨百分比: {summary.get('original_rain_percentage', 'N/A')}%")

# 結論
print("\n" + "=" * 70)
print("[最終結論]")
print("-" * 70)

if len(rain_laps) > 0:
    print(f"✅ FastF1 確實記錄到降雨")
    print(f"   共有 {len(rain_laps)} 圈的 'rainfall' 欄位為 True")
    print(f"   降雨圈次: {', '.join(rain_laps)}")
else:
    print(f"❌ FastF1 沒有記錄到降雨")
    print(f"   所有 {len(no_rain_laps)} 圈的 'rainfall' 欄位都是 False")
    print(f"   但 summary 顯示有 {summary.get('rain_laps', 0)} 圈降雨")
    print(f"   這可能是分析算法的問題，而非 FastF1 原始數據")

print("=" * 70)
