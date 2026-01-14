#!/usr/bin/env python3
"""測試 Color Palette API (Function 98) 是否正常工作"""

import requests
import certifi

def test_color_api():
    url = "https://localhost:8000/api/v2/analysis/execute"
    params = {"function_id": 98, "year": 2025}
    
    try:
        print("🔍 測試 API 端點...")
        print(f"URL: {url}")
        print(f"參數: {params}")
        print()
        
        response = requests.post(
            url, 
            params=params,
            headers={"Accept": "application/json"},
            timeout=10,
            verify=certifi.where()
        )
        
        print(f"✅ HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            
            outer_data = data.get("data", {})
            inner_data = outer_data.get("data", outer_data)
            teams = inner_data.get("teams", {})
            drivers = inner_data.get("drivers", {})
            
            print(f"✅ 車隊數量: {len(teams)}")
            print(f"✅ 車手數量: {len(drivers)}")
            
            if teams:
                print(f"\n📋 前 3 個車隊:")
                for i, (team_slug, team_info) in enumerate(list(teams.items())[:3]):
                    print(f"  - {team_slug}: {team_info.get('name', 'N/A')} ({team_info.get('color', 'N/A')})")
            
            if drivers:
                print(f"\n📋 前 3 個車手:")
                for i, (driver_code, driver_info) in enumerate(list(drivers.items())[:3]):
                    print(f"  - {driver_code}: {driver_info.get('name', 'N/A')} ({driver_info.get('color', 'N/A')})")
            
            print("\n🎉 API 運作正常！")
            return True
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
            print(f"回應: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API 請求超時（10 秒）")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 連線錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 發生錯誤: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    test_color_api()
