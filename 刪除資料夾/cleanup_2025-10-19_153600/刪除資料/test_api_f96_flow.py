#!/usr/bin/env python3
"""
測試 API Function 96 完整流程
驗證：
1. 緩存搜尋是否找到 race_weather_forecast_2025_Singapore_R.json
2. 如果找不到，API 是否調用 CLI
3. JSON 格式是否符合標準
"""

import requests
import json
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_cache_search():
    """測試緩存搜尋"""
    print("=" * 60)
    print("測試 1: API 緩存搜尋")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE}/api/v2/analysis/execute",
        params={
            "function_id": "96",
            "year": 2025,
            "race": "Singapore Grand Prix",
            "session": "R"
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"成功: {data.get('success')}")
        print(f"來源: {data.get('source')}")  # ← 關鍵：應該是 "cache" 或 "cli"
        print(f"訊息: {data.get('message')}")
        
        if 'data' in data:
            metadata = data['data'].get('metadata', {})
            print(f"\n元數據:")
            print(f"  - 功能 ID: {metadata.get('function_id')}")
            print(f"  - 賽事: {metadata.get('event_name')}")
            print(f"  - 分析類型: {metadata.get('analysis_type')}")
    else:
        print(f"錯誤: {response.text}")

def test_json_structure():
    """測試本地 JSON 格式"""
    print("\n" + "=" * 60)
    print("測試 2: 本地 JSON 結構驗證")
    print("=" * 60)
    
    json_file = Path("json/weather/race_weather_forecast_2025_Singapore_R.json")
    
    if not json_file.exists():
        print(f"❌ 檔案不存在: {json_file}")
        return
    
    print(f"✅ 檔案存在: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n頂層鍵:")
    for key in data.keys():
        print(f"  - {key}")
    
    if 'metadata' in data:
        metadata = data['metadata']
        print(f"\nmetadata 鍵:")
        for key in metadata.keys():
            print(f"  - {key}: {metadata.get(key)}")
    
    if 'data' in data:
        data_section = data['data']
        print(f"\ndata 結構:")
        print(f"  - coordinates: {bool(data_section.get('coordinates'))}")
        print(f"  - forecast: {bool(data_section.get('forecast'))}")
        
        if 'forecast' in data_section:
            forecast = data_section['forecast']
            days = forecast.get('days', [])
            print(f"  - forecast.days 數量: {len(days)}")
            if days:
                print(f"  - 第一天: {days[0].get('date')} ({days[0].get('label')})")

def test_cache_patterns():
    """測試緩存搜尋模式"""
    print("\n" + "=" * 60)
    print("測試 3: 緩存搜尋模式生成")
    print("=" * 60)
    
    from api.services.cache_service import F1AnalysisCacheService
    
    cache_service = F1AnalysisCacheService(json_dir="json/")
    
    # 測試 token 生成
    race_tokens = cache_service._build_race_search_tokens("Singapore Grand Prix")
    
    print(f"賽事名稱: 'Singapore Grand Prix'")
    print(f"生成的搜尋 tokens ({len(race_tokens)} 個):")
    for i, token in enumerate(race_tokens, 1):
        print(f"  {i}. '{token}'")
    
    # 檢查是否包含 "Singapore"
    if "Singapore" in race_tokens:
        print(f"\n✅ 包含 'Singapore' (大寫開頭)")
    else:
        print(f"\n❌ 不包含 'Singapore' (大寫開頭)")

if __name__ == "__main__":
    test_json_structure()
    test_cache_patterns()
    test_cache_search()
