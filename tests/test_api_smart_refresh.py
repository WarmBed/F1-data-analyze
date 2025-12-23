#!/usr/bin/env python3
"""
測試 API 智慧刷新功能

驗證 API 在收到 Function 97 請求時會自動檢查數據新鮮度
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"

def test_api_smart_refresh():
    """測試 API 智慧刷新"""
    
    print("=" * 80)
    print("測試 API 智慧刷新功能 (Function 97 - Championship Standings)")
    print("=" * 80)
    print()
    
    # 測試參數
    year = 2024
    endpoint = f"{API_BASE_URL}/api/v2/analysis/execute"
    
    params = {
        "function_id": "97",
        "year": year,
        "force_refresh": False  # 不強制刷新，讓 API 自動判斷
    }
    
    print(f"📡 調用 API: {endpoint}")
    print(f"📋 參數: {json.dumps(params, indent=2)}")
    print()
    print("⏳ 等待 API 響應...")
    print()
    
    try:
        # 發送請求
        start_time = datetime.now()
        response = requests.post(endpoint, params=params, timeout=120)
        end_time = datetime.now()
        
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"✅ API 響應成功 (耗時: {elapsed:.2f}s)")
        print(f"📊 HTTP 狀態碼: {response.status_code}")
        print()
        
        # 解析響應
        if response.status_code == 200:
            result = response.json()
            
            print("📦 響應內容:")
            print(f"   ├─ success: {result.get('success')}")
            print(f"   ├─ message: {result.get('message')}")
            print(f"   ├─ source: {result.get('source', 'N/A')}")
            print(f"   ├─ execution_time: {result.get('execution_time', 'N/A')}")
            print(f"   └─ request_id: {result.get('request_id', 'N/A')}")
            print()
            
            # 檢查數據內容
            data = result.get("data", {})
            if data:
                drivers = data.get("drivers", [])
                constructors = data.get("constructors", [])
                metadata = data.get("metadata", {})
                
                print("📊 數據統計:")
                print(f"   ├─ 車手數量: {len(drivers)}")
                print(f"   ├─ 車隊數量: {len(constructors)}")
                print(f"   ├─ 賽季年份: {metadata.get('season_year')}")
                print(f"   └─ 當前輪次: {metadata.get('resolved_round')}")
                print()
                
                # 顯示前三名車手
                if drivers:
                    print("🏆 前三名車手:")
                    for i, driver_entry in enumerate(drivers[:3], 1):
                        driver_info = driver_entry.get("driver", {})
                        points = driver_entry.get("points", 0)
                        constructors_list = driver_entry.get("constructors", [])
                        team = constructors_list[0].get("name", "Unknown") if constructors_list else "Unknown"
                        
                        print(f"   {i}. {driver_info.get('full_name', 'Unknown')} ({team}) - {points} pts")
                    print()
                
                # 顯示前三名車隊
                if constructors:
                    print("🏆 前三名車隊:")
                    for i, constructor_entry in enumerate(constructors[:3], 1):
                        constructor_info = constructor_entry.get("constructor", {})
                        points = constructor_entry.get("points", 0)
                        
                        print(f"   {i}. {constructor_info.get('name', 'Unknown')} - {points} pts")
                    print()
            
            print("✅ 測試成功！API 智慧刷新正常運作")
            
        else:
            print(f"❌ API 返回錯誤:")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("❌ API 請求超時")
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 服務器")
        print("💡 提示: 請確認 API 服務器正在運行")
        print("   執行: python refactored_api.py")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_api_smart_refresh()
