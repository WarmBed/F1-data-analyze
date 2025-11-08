"""測試通過外網 API 調用 Function 34（煞車分析）"""
import requests
import json
import time

# 外網 API 網址
API_URL = "https://api.f1telemetrystationpro.org/analyze"

# 測試參數
payload = {
    "function_id": "34",
    "year": 2025,
    "race": "China",
    "session": "R"
}

print("=" * 80)
print("測試外網 API - Function 34（煞車分析）")
print("=" * 80)
print(f"\nAPI URL: {API_URL}")
print(f"請求參數:")
for key, value in payload.items():
    print(f"  {key}: {value}")

print("\n發送請求...")
start_time = time.time()

try:
    response = requests.post(API_URL, json=payload, timeout=300)
    elapsed_time = time.time() - start_time
    
    print(f"\n請求完成！耗時: {elapsed_time:.2f} 秒")
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n" + "=" * 80)
        print("API 響應:")
        print("=" * 80)
        
        print(f"\nSuccess: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Function ID: {data.get('function_id')}")
        
        if 'data' in data:
            print("\n數據結構:")
            print(f"  Keys: {list(data['data'].keys())}")
            
            if 'driver_brakes' in data['data']:
                drivers = data['data']['driver_brakes']
                print(f"\n  車手數量: {len(drivers)}")
                
                if drivers:
                    print(f"\n  前 5 位車手:")
                    for i, driver_data in enumerate(drivers[:5], 1):
                        driver = driver_data.get('driver', 'N/A')
                        total_brakes = driver_data.get('total_brakes', 'N/A')
                        avg_pressure = driver_data.get('avg_brake_pressure', 'N/A')
                        print(f"    {i}. {driver}: 煞車次數 {total_brakes}, 平均煞車壓力 {avg_pressure}")
            
            if 'reference_brake_zone' in data['data']:
                ref_zone = data['data']['reference_brake_zone']
                print(f"\n  參考煞車區域:")
                print(f"    區域名稱: {ref_zone.get('zone_name', 'N/A')}")
                print(f"    起始距離: {ref_zone.get('start_distance', 'N/A')}m")
                print(f"    結束距離: {ref_zone.get('end_distance', 'N/A')}m")
        
        print("\n✅ API 調用成功！")
        
        # 保存響應到檔案
        output_file = "test_api_brake_response.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n響應已保存到: {output_file}")
        
    else:
        print(f"\n❌ API 返回錯誤: {response.status_code}")
        print(f"響應內容: {response.text}")

except requests.exceptions.Timeout:
    print(f"\n❌ 請求超時（超過 300 秒）")
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ 連接失敗: {e}")
except Exception as e:
    print(f"\n❌ 發生錯誤: {e}")
    import traceback
    traceback.print_exc()
