#!/usr/bin/env python3
"""
測試外網 API 功能 47 端點
"""

import requests
import json

def test_f47_api():
    """測試功能 47 API 端點"""
    
    # API 配置
    url = "https://api.f1telemetrystationpro.org/analyze"
    payload = {
        "function_id": "47",
        "year": "2024",
        "race": "Japan",
        "session": "R"
    }
    
    print("=" * 60)
    print("🧪 測試外網 API - 功能 47 (全車手彎道性能分析)")
    print("=" * 60)
    print(f"\n📡 API URL: {url}")
    print(f"📦 Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("\n🔄 發送請求...\n")
    
    try:
        # 發送 POST 請求
        response = requests.post(url, json=payload, timeout=60)
        
        # 顯示響應狀態
        print(f"✅ HTTP Status Code: {response.status_code}")
        print(f"📊 Response Headers:")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('content-length', 'N/A')} bytes")
        
        # 解析 JSON 響應
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API 調用成功!")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Function ID: {data.get('function_id', 'N/A')}")
            print(f"   Year: {data.get('year', 'N/A')}")
            print(f"   Race: {data.get('race', 'N/A')}")
            print(f"   Session: {data.get('session', 'N/A')}")
            
            # 檢查數據結構
            if 'selected_corners' in data:
                corners = data['selected_corners']
                print(f"\n📍 Selected Corners:")
                for corner_type, info in corners.items():
                    print(f"   - {corner_type}: T{info.get('corner_number')} ({info.get('avg_apex_speed')} km/h)")
            
            if 'fastest_lap_analysis' in data:
                fla = data['fastest_lap_analysis']
                print(f"\n🏎️  Fastest Lap Analysis:")
                print(f"   Total Drivers: {fla.get('total_drivers', 0)}")
                
            print(f"\n✅ 功能 47 API 端點測試通過!")
            return True
            
        else:
            print(f"\n❌ API 返回錯誤")
            print(f"Response Body:\n{response.text[:1000]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 請求超時 (60秒)")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 連接錯誤: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_f47_api()
    print("\n" + "=" * 60)
    if success:
        print("🎉 測試結果: 通過")
    else:
        print("💥 測試結果: 失敗")
    print("=" * 60)
