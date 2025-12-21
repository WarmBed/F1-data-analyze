#!/usr/bin/env python3
"""
測試 API 是否正確傳輸帶有時間戳的 JSON 數據
"""

import requests
import json

def test_api_time_series():
    """測試 Function 13 API 端點是否包含時間序列數據"""
    
    print("=" * 60)
    print("測試 API 時間序列數據傳輸")
    print("=" * 60)
    
    # API 端點 (使用 v2)
    url = "http://localhost:8000/api/v2/analysis/execute"
    
    # 請求參數
    params = {
        'function_id': '13',
        'year': 2025,
        'race': 'Japan',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',
        'lap1': 1,
        'lap2': 1
    }
    
    print(f"\n📡 發送 API 請求:")
    print(f"   URL: {url}")
    print(f"   參數: {json.dumps(params, indent=4)}")
    
    try:
        # 發送請求
        print(f"\n⏳ 正在請求...")
        response = requests.post(url, params=params, timeout=30)
        
        print(f"\n✅ HTTP 狀態碼: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API 請求失敗")
            print(f"   響應內容: {response.text[:500]}")
            return False
        
        # 解析 JSON
        data = response.json()
        
        print(f"\n📦 API 響應結構:")
        print(f"   success: {data.get('success')}")
        print(f"   message: {data.get('message')}")
        
        # 檢查數據結構
        result_data = data.get('data', {})
        if not result_data:
            print(f"❌ 響應中沒有 'data' 欄位")
            return False
        
        print(f"\n📊 數據結構:")
        print(f"   data 鍵值: {list(result_data.keys())}")
        
        # 檢查 results
        results = result_data.get('results', {})
        if not results:
            print(f"❌ 響應中沒有 'results' 欄位")
            return False
        
        print(f"   results 鍵值: {list(results.keys())}")
        
        # 檢查 telemetry_comparison
        telemetry_comp = results.get('telemetry_comparison', {})
        if not telemetry_comp:
            print(f"❌ 沒有找到 telemetry_comparison 數據")
            return False
        
        print(f"   telemetry_comparison 鍵值: {list(telemetry_comp.keys())}")
        
        # 檢查 Speed 數據
        speed_data = telemetry_comp.get('Speed', {})
        if not speed_data:
            print(f"❌ 沒有找到 Speed 數據")
            return False
        
        print(f"\n🔍 Speed 數據鍵值: {list(speed_data.keys())}")
        
        # 檢查時間序列欄位
        has_driver1_time = 'driver1_time_seconds' in speed_data
        has_driver2_time = 'driver2_time_seconds' in speed_data
        
        print(f"\n⏱️  時間序列檢查:")
        print(f"   driver1_time_seconds 存在: {has_driver1_time}")
        print(f"   driver2_time_seconds 存在: {has_driver2_time}")
        
        if has_driver1_time:
            time_array = speed_data.get('driver1_time_seconds', [])
            print(f"   driver1_time_seconds 長度: {len(time_array)}")
            if len(time_array) > 0:
                print(f"   前5個數值: {time_array[:5]}")
        
        if has_driver2_time:
            time_array = speed_data.get('driver2_time_seconds', [])
            print(f"   driver2_time_seconds 長度: {len(time_array)}")
            if len(time_array) > 0:
                print(f"   前5個數值: {time_array[:5]}")
        
        # 驗證結果
        if has_driver1_time and has_driver2_time:
            print(f"\n✅ API 成功傳輸時間序列數據!")
            return True
        else:
            print(f"\n❌ API 響應中缺少時間序列數據")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 無法連接到 API 服務器")
        print(f"   請確認 API 服務器正在運行: python refactored_api.py")
        return False
        
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_api_time_series()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 測試通過: API 正確傳輸時間序列數據")
    else:
        print("💥 測試失敗: API 未傳輸時間序列數據")
    print("=" * 60)
    
    exit(0 if success else 1)
