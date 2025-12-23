"""
測試 API Timediff 計算功能
驗證跨賽事時間差異是否正確添加到 API 回應中
"""

import requests
import json

# API 端點
API_URL = "http://localhost:8000/api/v1/analysis/telemetry-comparison/cross-event"

# 測試參數：VER vs LEC 跨賽事比較
params = {
    "driver1": "VER",
    "year1": 2024,
    "race1": "Japan",
    "session1": "R",
    "lap1": 21,
    "driver2": "LEC",
    "year2": 2024,
    "race2": "Bahrain",
    "session2": "R",
    "lap2": 21
}

print("=" * 80)
print("🧪 測試 API Timediff 計算功能")
print("=" * 80)
print(f"車手1: {params['driver1']} - {params['year1']} {params['race1']} {params['session1']} Lap {params['lap1']}")
print(f"車手2: {params['driver2']} - {params['year2']} {params['race2']} {params['session2']} Lap {params['lap2']}")
print()

try:
    print("📡 發送 API 請求...")
    response = requests.post(API_URL, json=params, timeout=180)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API 請求成功")
        print()
        
        # 檢查 telemetry_comparison
        if "telemetry_comparison" in data:
            telemetry_comp = data["telemetry_comparison"]
            print(f"📊 telemetry_comparison keys: {list(telemetry_comp.keys())}")
            print()
            
            # 檢查 Speeddiff
            if "Speeddiff" in telemetry_comp:
                speeddiff = telemetry_comp["Speeddiff"]
                print("✅ Speeddiff 已添加")
                print(f"   - distance 點數: {len(speeddiff.get('distance', []))}")
                print(f"   - speed_difference 點數: {len(speeddiff.get('speed_difference', []))}")
            
            # 檢查 Distancediff
            if "Distancediff" in telemetry_comp:
                distancediff = telemetry_comp["Distancediff"]
                print("✅ Distancediff 已添加")
                print(f"   - distance 點數: {len(distancediff.get('distance', []))}")
                print(f"   - distance_difference 點數: {len(distancediff.get('distance_difference', []))}")
            
            # 🆕 檢查 Timediff
            if "Timediff" in telemetry_comp:
                timediff = telemetry_comp["Timediff"]
                print("✅ Timediff 已添加")
                print(f"   - time 點數: {len(timediff.get('time', []))}")
                print(f"   - time_difference 點數: {len(timediff.get('time_difference', []))}")
                
                # 檢查數據範圍
                time_data = timediff.get('time', [])
                time_diff_data = timediff.get('time_difference', [])
                
                if time_data and time_diff_data:
                    print(f"   - 時間範圍: {min(time_data):.2f} ~ {max(time_data):.2f} s")
                    print(f"   - 時間差範圍: {min(time_diff_data):.3f} ~ {max(time_diff_data):.3f} s")
                    
                    # 檢查額外欄位
                    if 'distance_gap' in timediff:
                        print(f"   - distance_gap 點數: {len(timediff['distance_gap'])}")
                    if 'driver1_distance' in timediff:
                        print(f"   - driver1_distance 點數: {len(timediff['driver1_distance'])}")
                    if 'driver2_distance' in timediff:
                        print(f"   - driver2_distance 點數: {len(timediff['driver2_distance'])}")
            else:
                print("❌ Timediff 未添加")
            
            print()
            
            # 檢查 time_difference 欄位
            if "time_difference" in data:
                time_diff = data["time_difference"]
                if time_diff:
                    print("✅ time_difference 欄位已更新")
                    print(f"   - time 點數: {len(time_diff.get('time', []))}")
                    print(f"   - time_difference 點數: {len(time_diff.get('time_difference', []))}")
                    if 'max_time_diff' in time_diff:
                        print(f"   - 最大時間差: {time_diff['max_time_diff']:.3f} s")
                    if 'min_time_diff' in time_diff:
                        print(f"   - 最小時間差: {time_diff['min_time_diff']:.3f} s")
                    if 'mean_time_diff' in time_diff:
                        print(f"   - 平均時間差: {time_diff['mean_time_diff']:.3f} s")
                else:
                    print("⚠️ time_difference 欄位為空")
            else:
                print("❌ time_difference 欄位不存在")
        else:
            print("❌ telemetry_comparison 不存在")
    else:
        print(f"❌ API 請求失敗: {response.status_code}")
        print(response.text)

except requests.exceptions.Timeout:
    print("⏰ 請求超時（180秒）")
except requests.exceptions.ConnectionError:
    print("❌ 連線錯誤：無法連接到 API 服務器")
    print("💡 提示：請確認 API 服務器是否運行中")
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("測試完成")
print("=" * 80)
