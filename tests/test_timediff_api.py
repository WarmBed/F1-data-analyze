"""
測試 API Timediff 跨賽事比較功能
"""
import requests
import json

def test_timediff_api():
    """測試 API 是否正確返回 Timediff 數據"""
    
    print("=" * 60)
    print("🧪 測試 API Timediff 跨賽事比較功能")
    print("=" * 60)
    
    # API 端點（修正：加上 /analysis 前綴）
    url = "http://localhost:8000/api/v2/analysis/cross-event-comparison"
    
    # 測試參數：比較兩場不同賽事的同一車手（使用 query 參數）
    params = {
        "year1": 2024,
        "race1": "Japan",
        "session1": "R",
        "driver1": "VER",
        "lap1": 30,
        
        "year2": 2024,
        "race2": "Bahrain",
        "session2": "R",
        "driver2": "VER",
        "lap2": 30,
        
        "force_refresh": False
    }
    
    print(f"\n📤 發送請求到: {url}")
    print(f"📋 參數:")
    print(f"   事件1: {params['year1']} {params['race1']} {params['session1']} - {params['driver1']} Lap {params['lap1']}")
    print(f"   事件2: {params['year2']} {params['race2']} {params['session2']} - {params['driver2']} Lap {params['lap2']}")
    
    try:
        response = requests.post(url, params=params, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ API 回應成功 (狀態碼: {response.status_code})")
            
            # 檢查數據結構
            if "data" in data:
                result = data["data"]
                
                # 檢查 telemetry_comparison
                if "telemetry_comparison" in result:
                    telemetry_comp = result["telemetry_comparison"]
                    print(f"\n📊 telemetry_comparison keys: {list(telemetry_comp.keys())}")
                    
                    # 檢查 Timediff
                    if "Timediff" in telemetry_comp:
                        timediff = telemetry_comp["Timediff"]
                        print(f"\n✅ Timediff 已添加")
                        print(f"   - name: {timediff.get('name')}")
                        print(f"   - time 點數: {len(timediff.get('time', []))}")
                        print(f"   - time_difference 點數: {len(timediff.get('time_difference', []))}")
                        print(f"   - distance_gap 點數: {len(timediff.get('distance_gap', []))}")
                        
                        # 顯示時間差範圍
                        time_diff_data = timediff.get('time_difference', [])
                        if time_diff_data:
                            print(f"   - 時間差範圍: {min(time_diff_data):.2f} ~ {max(time_diff_data):.2f} s")
                        
                        # 顯示距離差範圍
                        distance_gap_data = timediff.get('distance_gap', [])
                        if distance_gap_data:
                            print(f"   - 距離差範圍: {min(distance_gap_data):.2f} ~ {max(distance_gap_data):.2f} m")
                    else:
                        print(f"\n❌ Timediff 未找到")
                        print(f"   可用的 keys: {list(telemetry_comp.keys())}")
                    
                    # 檢查其他 Diff
                    for diff_key in ["Speeddiff", "Distancediff"]:
                        if diff_key in telemetry_comp:
                            print(f"✅ {diff_key} 已添加 ({len(telemetry_comp[diff_key].get('distance', []))} 點)")
                
                # 檢查 time_difference 欄位
                if "time_difference" in result:
                    time_diff_field = result["time_difference"]
                    if time_diff_field:
                        print(f"\n✅ time_difference 欄位已更新")
                        print(f"   - time 點數: {len(time_diff_field.get('time', []))}")
                        print(f"   - time_difference 點數: {len(time_diff_field.get('time_difference', []))}")
                    else:
                        print(f"\n⚠️  time_difference 欄位為空")
                
                # 保存測試結果
                with open("test_timediff_api_result.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 完整回應已保存到: test_timediff_api_result.json")
                
            else:
                print(f"\n❌ 回應中沒有 'data' 欄位")
                print(f"回應內容: {data}")
        
        else:
            print(f"\n❌ API 回應失敗 (狀態碼: {response.status_code})")
            print(f"錯誤訊息: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 無法連接到 API 服務器")
        print(f"   請確認 API 服務器正在運行: python refactored_api.py")
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_timediff_api()
    print("\n" + "=" * 60)
