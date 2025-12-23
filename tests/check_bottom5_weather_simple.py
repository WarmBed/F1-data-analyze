"""
Bottom 5 賽道天氣快速調查
直接讀取 2025 JSON 數據的天氣欄位
"""

import json
from pathlib import Path

# Bottom 5 賽道
tracks = {
    10: ("Canada", -0.305),
    15: ("Netherlands", -0.186),
    16: ("Italy", -0.118),
    17: ("Azerbaijan", 0.107),
    12: ("Great Britain", 0.194)
}

print("="*80)
print("Bottom 5 賽道 2025 天氣狀況調查")
print("="*80)
print()

for race_num, (track_name, spearman) in sorted(tracks.items(), key=lambda x: x[1]):
    print(f"\n{'='*80}")
    print(f"{track_name} (Race #{race_num}, Spearman: {spearman:.3f})")
    print(f"{'='*80}")
    
    # 尋找 2025 數據
    json_dir = Path("json/predictionJSON")
    files = list(json_dir.glob(f"fp_q_data_2025_{race_num}_*.json"))
    
    if not files:
        print("⚠️  找不到 2025 數據")
        continue
    
    # 讀取最新檔案
    latest_file = sorted(files)[-1]
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取天氣資訊
        q_weather = data.get('qualifying', {}).get('weather', {})
        fp3_weather = data.get('practice_sessions', {}).get('FP3', {}).get('weather', {})
        
        if q_weather:
            rainfall_q = q_weather.get('rainfall', False)
            air_temp = q_weather.get('air_temp_avg', 0)
            track_temp = q_weather.get('track_temp_avg', 0)
            humidity = q_weather.get('humidity_avg', 0)
            
            print(f"\n【排位賽天氣】")
            print(f"  降雨: {'☔ 是 (雨戰！)' if rainfall_q else '☀️ 否 (乾地)'}")
            print(f"  氣溫: {air_temp:.1f}°C")
            print(f"  賽道溫度: {track_temp:.1f}°C")
            print(f"  濕度: {humidity:.1f}%")
            
            if rainfall_q:
                print(f"\n  ⚠️  這是雨戰！模型可能未學習到雨戰特徵")
        
        if fp3_weather:
            rainfall_fp3 = fp3_weather.get('rainfall', False)
            print(f"\n【FP3 天氣】")
            print(f"  降雨: {'☔ 是' if rainfall_fp3 else '☀️ 否'}")
        
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")

print("\n" + "="*80)
print("總結")
print("="*80)

# 統計降雨
rain_tracks = []
for race_num, (track_name, spearman) in tracks.items():
    json_dir = Path("json/predictionJSON")
    files = list(json_dir.glob(f"fp_q_data_2025_{race_num}_*.json"))
    
    if files:
        try:
            with open(sorted(files)[-1], 'r', encoding='utf-8') as f:
                data = json.load(f)
            q_weather = data.get('qualifying', {}).get('weather', {})
            if q_weather.get('rainfall', False):
                rain_tracks.append(track_name)
        except:
            pass

if rain_tracks:
    print(f"\n⚠️  有降雨的賽道: {', '.join(rain_tracks)}")
    print(f"\n結論:")
    print(f"  - {len(rain_tracks)}/{len(tracks)} 個 Bottom 5 賽道有雨")
    print(f"  - 雨戰可能是模型失效的主要原因之一")
    print(f"  - 建議: 添加降雨特徵或分開訓練乾地/雨戰模型")
else:
    print(f"\n✅ Bottom 5 賽道都是乾地")
    print(f"\n結論:")
    print(f"  - 天氣不是主要原因")
    print(f"  - 問題在於過擬合和絕對時間特徵")
    print(f"  - 建議: 使用相對特徵 (gap to P1) + 增強正則化")
