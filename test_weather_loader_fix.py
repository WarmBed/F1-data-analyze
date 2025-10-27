#!/usr/bin/env python3
"""
測試修正後的 Weather DataLoader
"""
import sys
import json
from pathlib import Path

# 載入 DataLoader
sys.path.insert(0, '.')
from modules.gui.weather_timeline.weather_timeline_data_loader import WeatherTimelineDataLoader

def test_weather_loader():
    """測試天氣載入器"""
    print("\n🧪 測試修正後的 Weather DataLoader...\n")
    
    # 初始化 DataLoader
    loader = WeatherTimelineDataLoader(year='2025', event='Brazil')
    print("✅ DataLoader 初始化成功")
    
    # 讀取 JSON 檔案
    json_file = Path('json/weather/race_weather_forecast_2025_São Paulo_R.json')
    with open(json_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"\n📄 JSON 檔案: {json_file.name}")
    print(f"📊 頂層鍵值: {list(raw_data.keys())}")
    
    # 測試驗證
    print("\n🔍 開始驗證...")
    is_valid = loader._validate_data_format(raw_data)
    print(f"✅ 驗證結果: {is_valid}")
    
    # 測試轉換
    if is_valid:
        print("\n🔄 開始轉換...")
        transformed = loader._transform_data_for_display(raw_data)
        print("✅ 轉換成功")
        
        forecast_days = transformed.get("forecast_days", [])
        print(f"\n📊 結果統計:")
        print(f"  - forecast_days 數量: {len(forecast_days)}")
        print(f"  - event_name: {transformed.get('event_name')}")
        print(f"  - location: {transformed.get('location')}")
        print(f"  - year: {transformed.get('year')}")
        print(f"  - event: {transformed.get('event')}")
        
        # 顯示第一天資料
        if forecast_days:
            day1 = forecast_days[0]
            print(f"\n📅 第一天資料:")
            print(f"  - 日期: {day1.get('date')}")
            print(f"  - 標籤: {day1.get('label')}")
            summary = day1.get('summary', {})
            print(f"  - 溫度: {summary.get('temperature_min')}~{summary.get('temperature_max')}°C")
            print(f"  - 降雨: {summary.get('precipitation_sum')} mm")
            print(f"  - 雲量: {summary.get('cloudcover_mean')}%")
            print(f"  - 風向: {summary.get('winddirection_cardinal')}")
    else:
        print("❌ 驗證失敗")
        return False
    
    print("\n✅ 測試通過！")
    return True

if __name__ == "__main__":
    success = test_weather_loader()
    sys.exit(0 if success else 1)
