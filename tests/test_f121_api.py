"""測試 F121 API 端點"""
import requests
import json

# API 端點
API_URL = "http://localhost:8000/api/v2/analysis/execute"

# 測試參數
params = {
    "function_id": "121",
    "year": 2025,
    "race": "Abu Dhabi",
    "session": "R"
}

print("=" * 80)
print("F121 API 測試")
print("=" * 80)
print()

print("【請求資訊】")
print(f"  URL: {API_URL}")
print(f"  參數:")
for key, value in params.items():
    print(f"    • {key}: {value}")
print()

print("【發送請求】")
print("  ⏳ 正在調用 API...")

try:
    response = requests.post(API_URL, params=params, timeout=60)
    
    print(f"  ✓ 響應狀態碼: {response.status_code}")
    print()
    
    if response.status_code == 200:
        print("【響應數據】")
        data = response.json()
        
        # 顯示基本資訊
        print(f"  ✅ 分析成功: {data.get('success', False)}")
        print(f"  Function ID: {data.get('function_id')}")
        print(f"  年份: {data.get('year')}")
        print(f"  賽事: {data.get('race')}")
        print(f"  會話: {data.get('session')}")
        print()
        
        # 顯示車手數據
        drivers = data.get('drivers', [])
        print(f"  總車手數: {len(drivers)}")
        
        if drivers:
            print()
            print("  【車手數據範例 - HAM】")
            ham = next((d for d in drivers if d['driver'] == 'HAM'), None)
            if ham:
                print(f"    • 總圈數: {ham.get('total_laps')}")
                print(f"    • 有效速度圈數: {ham.get('valid_speed_laps')}")
                print(f"    • 絕對最高速度: {ham.get('absolute_max_speed_kmh')} km/h (圈數 {ham.get('absolute_max_speed_lap')})")
                
                speed_stats = ham.get('speed_stats', {})
                print(f"    • 速度中位數: {speed_stats.get('median')} km/h")
                print(f"    • 速度標準差: {speed_stats.get('std_dev', 0):.2f} km/h")
                
                accel_stats = ham.get('acceleration_100_300_stats', {})
                print(f"    • 加速 100→300 (中位數): {accel_stats.get('median')} s")
                
                time_stats = ham.get('time_to_max_speed_stats', {})
                print(f"    • 推算到最高速 (中位數): {time_stats.get('median')} s")
            else:
                print("    ⚠️ 找不到 HAM 數據")
        
        print()
        print("【主直線資訊】")
        main_straight = data.get('main_straight', {})
        if main_straight:
            print(f"  • 起點距離: {main_straight.get('start_distance', 0):.2f} m")
            print(f"  • 終點距離: {main_straight.get('end_distance', 0):.2f} m")
            print(f"  • 直線長度: {main_straight.get('length', 0):.2f} m")
        
        print()
        print("=" * 80)
        print("✅ API 測試成功")
        print("=" * 80)
        
    else:
        print("【錯誤響應】")
        print(f"  狀態碼: {response.status_code}")
        print(f"  內容: {response.text[:500]}")
        print()
        print("=" * 80)
        print("❌ API 測試失敗")
        print("=" * 80)

except requests.exceptions.ConnectionError:
    print()
    print("=" * 80)
    print("❌ 連接錯誤")
    print("=" * 80)
    print()
    print("API 服務器未運行或無法連接到 http://localhost:8000")
    print()
    print("請先啟動 API 服務器:")
    print("  python refactored_api.py")
    print()
    print("或使用已部署的服務:")
    print("  https://api.f1telemetrystationpro.org")
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ 發生錯誤")
    print("=" * 80)
    print(f"  錯誤類型: {type(e).__name__}")
    print(f"  錯誤訊息: {e}")
    print()
    import traceback
    print("詳細錯誤:")
    traceback.print_exc()
