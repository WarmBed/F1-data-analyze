#!/usr/bin/env python3
"""讀取 2025 美國站 Rain Analysis JSON"""

import json

# 讀取 JSON 檔案
json_file = r"json\enhanced_rain_analysis_2025_United States_R.json"

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 顯示結果
print("=" * 60)
print("2025 F1 美國站正賽 (Race) - 降雨分析報告")
print("=" * 60)

# 賽事資訊
print("\n[賽事資訊]")
print(f"  年份: {data['metadata']['year']}")
print(f"  賽事: {data['metadata']['race_name']}")
print(f"  賽段: {data['metadata']['session_type']}")
print(f"  分析時間: {data['metadata']['generated_at']}")

# 降雨狀態
print("\n[降雨分析結果]")
has_rain = data['summary']['rain_laps'] > 0
print(f"  ❓ 是否下雨: {'是 (YES)' if has_rain else '否 (NO)'}")
print(f"  💧 降雨圈數: {data['summary']['rain_laps']} 圈")
print(f"  � 降雨百分比: {data['summary']['rain_percentage']:.1f}%")
print(f"  🌧️  原始降雨數據點: {data['summary']['original_rain_points']} 個")
print(f"  📈 原始降雨百分比: {data['summary']['original_rain_percentage']:.1f}%")

# 詳細數據
print("\n[詳細數據]")
print(f"  ☔ 降雨圈數: {data['summary']['rain_laps']} 圈")
print(f"  ☀️  乾燥圈數: {data['summary']['total_laps'] - data['summary']['rain_laps']} 圈")
print(f"  🏎️  總圈數: {data['summary']['total_laps']} 圈")
print(f"  📡 氣象數據點: {data['summary']['weather_data_points']} 個")

# 降雨時間分析
print("\n[降雨時間分析]")
rain_timing = data['summary']['rain_timing_analysis']
print(f"  🏁 比賽開始: {rain_timing['race_start_time']}")
print(f"  🏁 比賽結束: {rain_timing['race_end_time']}")
print(f"  ☔ 降雨開始: {rain_timing['rain_start_time']}")
print(f"  ☔ 降雨結束: {rain_timing['rain_end_time']}")
print(f"  📊 比賽期間降雨: {rain_timing['rain_during_race']} 個數據點 ({rain_timing['rain_distribution']['during_race_percentage']:.1f}%)")

# 結論
print("\n[結論]")
has_rain = data['summary']['rain_laps'] > 0
if has_rain:
    print(f"  ✅ 2025 美國站正賽【有下雨】")
    print(f"  🌧️  降雨覆蓋了 {data['summary']['rain_laps']}/{data['summary']['total_laps']} 圈 ({data['summary']['rain_percentage']:.1f}%)")
    print(f"  ⏰ 降雨時段: {rain_timing['rain_start_time']} 至 {rain_timing['rain_end_time']}")
else:
    print(f"  ❌ 2025 美國站正賽【沒有下雨】")
    print(f"  ☀️  全部 {data['summary']['total_laps']} 圈都是乾燥狀態")

print("=" * 60)
