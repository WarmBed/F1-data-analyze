"""
檢查 Bottom 5 最差預測賽道的天氣狀況
比較 2022-2024 訓練數據 vs 2025 驗證數據
"""

import json
import glob
from pathlib import Path
from collections import defaultdict

# Bottom 5 賽道映射
bottom_5_tracks = {
    10: "Canada",
    15: "Netherlands", 
    16: "Italy",
    17: "Azerbaijan",
    12: "Great Britain"
}

spearman_scores = {
    "Canada": -0.305,
    "Netherlands": -0.186,
    "Italy": -0.118,
    "Azerbaijan": 0.107,
    "Great Britain": 0.194
}

def extract_weather_from_json(json_file):
    """從 JSON 提取天氣資訊"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    weather_info = {
        'year': data.get('metadata', {}).get('year', 'Unknown'),
        'race': data.get('metadata', {}).get('race', 'Unknown'),
    }
    
    # 提取 Qualifying 天氣
    q_weather = data.get('qualifying', {}).get('weather', {})
    if q_weather:
        weather_info['q_rainfall'] = q_weather.get('rainfall', False)
        
        # 安全處理 None 值
        air_temp = q_weather.get('air_temp_avg')
        track_temp = q_weather.get('track_temp_avg')
        humidity = q_weather.get('humidity_avg')
        
        weather_info['q_air_temp'] = round(air_temp, 1) if air_temp is not None else 0
        weather_info['q_track_temp'] = round(track_temp, 1) if track_temp is not None else 0
        weather_info['q_humidity'] = round(humidity, 1) if humidity is not None else 0
    
    # 提取 FP3 天氣
    practice_sessions = data.get('practice_sessions', {})
    fp3_weather = practice_sessions.get('FP3', {}).get('weather', {})
    if fp3_weather:
        weather_info['fp3_rainfall'] = fp3_weather.get('rainfall', False)
        
        fp3_air = fp3_weather.get('air_temp_avg')
        fp3_track = fp3_weather.get('track_temp_avg')
        
        weather_info['fp3_air_temp'] = round(fp3_air, 1) if fp3_air is not None else 0
        weather_info['fp3_track_temp'] = round(fp3_track, 1) if fp3_track is not None else 0
    
    return weather_info

def main():
    print("="*80)
    print("Bottom 5 賽道天氣調查報告")
    print("="*80)
    print("\n比較 2022-2024 訓練數據 vs 2025 驗證數據的天氣差異\n")
    
    # 收集所有天氣數據
    weather_by_track = defaultdict(lambda: {'2022-2024': [], '2025': []})
    
    # 掃描所有 JSON 檔案
    json_dir = Path("json/predictionJSON")
    all_files = list(json_dir.glob("fp_q_data_*.json"))
    
    print(f"[INFO] 找到 {len(all_files)} 個 JSON 檔案\n")
    
    for json_file in all_files:
        try:
            weather = extract_weather_from_json(json_file)
            year = weather.get('year')
            race_num = weather.get('race')
            
            # 只處理 Bottom 5 賽道
            if race_num not in bottom_5_tracks:
                continue
            
            track_name = bottom_5_tracks[race_num]
            
            if year in [2022, 2023, 2024]:
                weather_by_track[track_name]['2022-2024'].append(weather)
            elif year == 2025:
                weather_by_track[track_name]['2025'].append(weather)
                
        except Exception as e:
            print(f"[ERROR] 處理 {json_file.name} 失敗: {e}")
            continue
    
    # 生成報告
    for track_name in sorted(bottom_5_tracks.values()):
        spearman = spearman_scores.get(track_name, 0)
        
        print("="*80)
        print(f"賽道: {track_name} (Spearman: {spearman:.3f})")
        print("="*80)
        
        training_data = weather_by_track[track_name]['2022-2024']
        validation_data = weather_by_track[track_name]['2025']
        
        if not training_data and not validation_data:
            print("⚠️  無天氣數據\n")
            continue
        
        # 2022-2024 訓練數據
        print("\n【2022-2024 訓練數據】")
        if training_data:
            print(f"  樣本數: {len(training_data)}")
            
            # 統計降雨
            rain_sessions = [w for w in training_data if w.get('q_rainfall') or w.get('fp3_rainfall')]
            rain_rate = len(rain_sessions) / len(training_data) * 100
            
            print(f"  降雨場次: {len(rain_sessions)}/{len(training_data)} ({rain_rate:.1f}%)")
            
            # 平均溫度
            avg_air_temp = sum(w.get('q_air_temp', 0) for w in training_data) / len(training_data)
            avg_track_temp = sum(w.get('q_track_temp', 0) for w in training_data) / len(training_data)
            
            print(f"  平均氣溫: {avg_air_temp:.1f}°C")
            print(f"  平均賽道溫度: {avg_track_temp:.1f}°C")
            
            # 列出所有場次
            for w in sorted(training_data, key=lambda x: x.get('year', 0)):
                year = w.get('year')
                rain_q = "☔" if w.get('q_rainfall') else "☀️"
                rain_fp3 = "☔" if w.get('fp3_rainfall') else "☀️"
                air = w.get('q_air_temp', 0)
                track = w.get('q_track_temp', 0)
                print(f"    {year}: Q={rain_q} FP3={rain_fp3} 氣溫={air:.1f}°C 賽道={track:.1f}°C")
        else:
            print("  ⚠️  無訓練數據")
        
        # 2025 驗證數據
        print("\n【2025 驗證數據】")
        if validation_data:
            for w in validation_data:
                rain_q = "☔ 雨戰" if w.get('q_rainfall') else "☀️ 乾地"
                rain_fp3 = "☔" if w.get('fp3_rainfall') else "☀️"
                air = w.get('q_air_temp', 0)
                track = w.get('q_track_temp', 0)
                humidity = w.get('q_humidity', 0)
                
                print(f"  排位賽: {rain_q}")
                print(f"  FP3: {rain_fp3}")
                print(f"  氣溫: {air:.1f}°C")
                print(f"  賽道溫度: {track:.1f}°C")
                print(f"  濕度: {humidity:.1f}%")
        else:
            print("  ⚠️  無 2025 數據")
        
        # 天氣差異分析
        print("\n【天氣差異分析】")
        if training_data and validation_data:
            val = validation_data[0]  # 2025 數據
            
            # 降雨差異
            train_rain_rate = len([w for w in training_data if w.get('q_rainfall')]) / len(training_data) * 100
            val_is_rain = val.get('q_rainfall', False)
            
            if val_is_rain and train_rain_rate < 20:
                print(f"  ⚠️  2025 下雨但訓練數據大多乾地 (訓練降雨率 {train_rain_rate:.1f}%)")
                print(f"  → 模型未學習到雨戰特徵，預測失效機率高")
            elif not val_is_rain and train_rain_rate > 80:
                print(f"  ⚠️  2025 乾地但訓練數據大多雨戰 (訓練降雨率 {train_rain_rate:.1f}%)")
                print(f"  → 模型過度學習雨戰特徵，乾地預測失效")
            else:
                print(f"  ✅ 降雨條件一致 (訓練 {train_rain_rate:.1f}% vs 2025 {'雨' if val_is_rain else '乾'})")
            
            # 溫度差異
            avg_train_air = sum(w.get('q_air_temp', 0) for w in training_data) / len(training_data)
            val_air = val.get('q_air_temp', 0)
            temp_diff = val_air - avg_train_air
            
            if abs(temp_diff) > 10:
                print(f"  ⚠️  氣溫差異大: 2025 ({val_air:.1f}°C) vs 訓練平均 ({avg_train_air:.1f}°C) = {temp_diff:+.1f}°C")
                print(f"  → 溫度影響輪胎性能，可能導致預測失準")
            else:
                print(f"  ✅ 氣溫相近: 2025 ({val_air:.1f}°C) vs 訓練平均 ({avg_train_air:.1f}°C) = {temp_diff:+.1f}°C")
        else:
            print("  ⚠️  數據不足，無法比較")
        
        print()
    
    # 總結
    print("\n" + "="*80)
    print("總結與建議")
    print("="*80)
    
    # 統計有雨戰的賽道
    rain_affected = []
    for track_name in bottom_5_tracks.values():
        val_data = weather_by_track[track_name]['2025']
        train_data = weather_by_track[track_name]['2022-2024']
        
        if val_data and train_data:
            val_rain = val_data[0].get('q_rainfall', False)
            train_rain_rate = len([w for w in train_data if w.get('q_rainfall')]) / len(train_data) * 100
            
            if val_rain != (train_rain_rate > 50):  # 天氣條件不一致
                rain_affected.append(track_name)
    
    if rain_affected:
        print(f"\n⚠️  受天氣影響的賽道 ({len(rain_affected)}/{len(bottom_5_tracks)}):")
        for track in rain_affected:
            print(f"   - {track}")
        print("\n建議:")
        print("   1. 添加降雨特徵到模型 (rainfall, humidity)")
        print("   2. 分別訓練乾地/雨戰模型")
        print("   3. 收集更多雨戰訓練數據")
    else:
        print("\n✅ Bottom 5 賽道天氣條件大致一致")
        print("\n結論:")
        print("   天氣差異不是主要原因，過擬合問題更嚴重")
        print("   建議優先解決:")
        print("   - 使用相對特徵 (gap to P1)")
        print("   - 增強正則化")
        print("   - 擴充訓練數據")

if __name__ == "__main__":
    main()
