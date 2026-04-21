"""測試 RPM API 返回的數據結構"""
import requests
import json

# 模擬 RPM 跨賽事比較的 API 請求
api_url = "http://localhost:8000/api/v2/analysis/cross-event-comparison"
params = {
    "driver1": "VER",
    "year1": 2024,
    "race1": "Japan",
    "session1": "R",
    "lap1": 1,
    "driver2": "LEC",
    "year2": 2024,
    "race2": "Japan",
    "session2": "R",
    "lap2": 1,
    "analysis_type": "rpm"
}

print("=" * 80)
print("🌐 測試 RPM API 數據結構")
print("=" * 80)
print(f"\nURL: {api_url}")
print(f"參數: {json.dumps(params, indent=2)}\n")

try:
    response = requests.post(api_url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    print(f"✅ API 響應狀態: {response.status_code}\n")
    print(f"📦 返回數據的頂層鍵值:")
    print(f"   {list(data.keys())}\n")
    
    # 檢查 success 和 data
    if data.get("success"):
        print(f"✅ API 返回 success=True")
        api_data = data.get("data", {})
        print(f"\n📦 data 的頂層鍵值:")
        print(f"   {list(api_data.keys())}\n")
    else:
        print(f"❌ API 返回 success=False")
        print(f"   message: {data.get('message')}")
        api_data = {}
    
    # 檢查是否有遙測數據
    if "results" in api_data and "telemetry_comparison" in api_data["results"]:
        telemetry = api_data["results"]["telemetry_comparison"]
        print(f"✅ 找到 results.telemetry_comparison\n")
        print(f"🔍 telemetry_comparison 的鍵值:")
        print(f"   {list(telemetry.keys())}\n")
        
        # 檢查 RPM 數據
        if "RPM" in telemetry:
            rpm_data = telemetry["RPM"]
            print(f"✅ 找到 RPM 數據")
            print(f"   RPM 的鍵值: {list(rpm_data.keys())}\n")
            
            # 檢查是否有時間數據
            time_keys = [k for k in rpm_data.keys() if 'time' in k.lower()]
            print(f"⏱️  包含 'time' 的鍵值:")
            print(f"   {time_keys}\n")
            
            # 檢查數據長度
            print("📊 數據長度統計:")
            for key in ['driver1_data', 'driver2_data', 'distance']:
                if key in rpm_data:
                    value = rpm_data[key]
                    if isinstance(value, list):
                        print(f"   - {key}: {len(value)} 個數據點")
            
            # 特別檢查時間數據
            print("\n⏱️  時間數據檢查:")
            for key in ['driver1_time', 'driver2_time', 'driver1_time_seconds', 'driver2_time_seconds']:
                if key in rpm_data:
                    value = rpm_data[key]
                    if isinstance(value, list):
                        print(f"   ✅ {key}: {len(value)} 個數據點")
                        if value:
                            print(f"      範圍: {min(value):.2f} - {max(value):.2f} 秒")
                    else:
                        print(f"   ⚠️  {key}: 存在但不是 List，類型={type(value)}")
                else:
                    print(f"   ❌ {key}: 不存在")
            
            # 顯示完整的鍵值列表
            print(f"\n📋 RPM 數據完整鍵值列表:")
            for key in sorted(rpm_data.keys()):
                value = rpm_data[key]
                if isinstance(value, list):
                    print(f"   - {key}: List[{len(value)}]")
                elif isinstance(value, dict):
                    print(f"   - {key}: Dict (keys: {list(value.keys())})")
                else:
                    print(f"   - {key}: {type(value).__name__} = {value}")
        else:
            print(f"❌ telemetry_comparison 中沒有 'RPM' 鍵值")
            print(f"   可用的遙測類型: {list(telemetry.keys())}")
    
    elif "rpm_data" in api_data:
        rpm_data = api_data["rpm_data"]
        print(f"🔍 rpm_data 的鍵值:")
        print(f"   {list(rpm_data.keys())}\n")
        
        # 檢查是否有時間數據
        time_keys = [k for k in rpm_data.keys() if 'time' in k.lower()]
        print(f"⏱️  包含 'time' 的鍵值:")
        print(f"   {time_keys}\n")
        
        # 檢查數據長度
        print("📊 數據長度統計:")
        for key in ['distance', 'driver1_rpm', 'driver2_rpm']:
            if key in rpm_data:
                print(f"   - {key}: {len(rpm_data[key])} 個數據點")
        
        # 特別檢查時間數據
        print("\n⏱️  時間數據檢查:")
        for key in ['driver1_time_seconds', 'driver2_time_seconds']:
            if key in rpm_data:
                value = rpm_data[key]
                print(f"   ✅ {key}: {len(value)} 個數據點")
                if value:
                    print(f"      範圍: {min(value):.2f} - {max(value):.2f} 秒")
            else:
                print(f"   ❌ {key}: 不存在於返回數據中")
        
        # 顯示完整的鍵值列表
        print(f"\n📋 rpm_data 完整鍵值列表:")
        for key in sorted(rpm_data.keys()):
            value = rpm_data[key]
            if isinstance(value, list):
                print(f"   - {key}: List[{len(value)}]")
            elif isinstance(value, dict):
                print(f"   - {key}: Dict (keys: {list(value.keys())})")
            else:
                print(f"   - {key}: {type(value).__name__} = {value}")
    
    else:
        print("❌ 返回數據中沒有 'rpm_data' 鍵值")
        if api_data:
            print(f"\n完整 data 內容:")
            print(json.dumps(api_data, indent=2, ensure_ascii=False)[:1000])
                
except requests.exceptions.RequestException as e:
    print(f"❌ API 請求失敗: {e}")
except json.JSONDecodeError as e:
    print(f"❌ JSON 解析失敗: {e}")
    print(f"響應內容: {response.text[:500]}")

print("\n" + "=" * 80)
