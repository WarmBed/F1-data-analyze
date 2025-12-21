"""驗證煞車分析 JSON 結構"""
import json

json_file = "json/brake_performance_2025_China_R.json"

try:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 80)
    print("煞車分析 JSON 驗證")
    print("=" * 80)
    
    print(f"\nSuccess: {data.get('success')}")
    print(f"Function ID: {data.get('function_id')}")
    print(f"Message: {data.get('message')}")
    
    if 'data' in data:
        print("\n數據結構:")
        print(f"  Keys: {list(data['data'].keys())}")
        
        if 'brake_zones' in data['data']:
            brake_zones = data['data']['brake_zones']
            print(f"\n  煞車區域數量: {len(brake_zones)}")
            
            if brake_zones:
                first_zone = brake_zones[0]
                print(f"\n  第一個煞車區域結構:")
                for key in first_zone.keys():
                    print(f"    - {key}: {type(first_zone[key]).__name__}")
        
        if 'drivers_performance' in data['data']:
            drivers = data['data']['drivers_performance']
            print(f"\n  車手數量: {len(drivers)}")
            
            if drivers:
                print(f"\n  前 3 位車手:")
                for i, driver_data in enumerate(drivers[:3], 1):
                    driver = driver_data.get('driver', 'N/A')
                    avg_brake_force = driver_data.get('avg_brake_force', 'N/A')
                    max_brake_force = driver_data.get('max_brake_force', 'N/A')
                    print(f"    {i}. {driver}: 平均煞車力 {avg_brake_force}, 最大煞車力 {max_brake_force}")
    
    print("\n✅ JSON 結構正常！")

except FileNotFoundError:
    print(f"❌ 找不到檔案: {json_file}")
except Exception as e:
    print(f"❌ 讀取失敗: {e}")
    import traceback
    traceback.print_exc()
