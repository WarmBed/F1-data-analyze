"""
診斷：追蹤傳遞給 Chart Widget 的實際數據
檢查 start=3, end=3 這種值是從哪裡來的
"""
import json

# 讀取 JSON 數據
with open('json/tire_strategy_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers_analysis = data.get('drivers_analysis', {})

print("=" * 80)
print("追蹤數據流向：JSON → MDI → Chart Widget")
print("=" * 80)

# 模擬 MDI 的 _process_tire_strategy_data
print("\n[步驟 1] MDI 處理數據 (_process_tire_strategy_data)")
print("-" * 80)

processed_data = {}

for driver_code in sorted(list(drivers_analysis.keys())[:3]):  # 只看前3個車手
    driver_data = drivers_analysis[driver_code]
    stint_data = driver_data.get("stint_analysis", [])
    
    driver_info = {"driver": driver_code, "stints": []}
    
    for index, stint in enumerate(stint_data, start=1):
        # 使用修復後的邏輯
        start_lap = stint.get("start_lap")
        if start_lap is None:
            start_lap = stint.get("lap_start")
            if start_lap is None:
                start_lap = 1
        
        end_lap = stint.get("end_lap")
        if end_lap is None or end_lap <= 0:
            end_lap = stint.get("lap_end")
            if end_lap is None or end_lap <= 0:
                length = stint.get("length")
                if length is not None and length > 0:
                    end_lap = start_lap + length - 1
                else:
                    end_lap = start_lap
        
        stint_info = {
            "stint_number": int(stint.get("stint_number", index)),
            "compound": stint.get("compound", "UNKNOWN"),
            "start_lap": int(start_lap),
            "end_lap": int(end_lap),
            "laps": stint.get("length", 0)
        }
        
        driver_info["stints"].append(stint_info)
        print(f"{driver_code} Stint {stint_info['stint_number']}: start={stint_info['start_lap']}, end={stint_info['end_lap']}")
    
    processed_data[driver_code] = driver_info

# 模擬 _prepare_tire_chart_data
print("\n[步驟 2] MDI 準備圖表數據 (_prepare_tire_chart_data)")
print("-" * 80)

chart_data = {
    "drivers_analyzed": list(processed_data.keys()),
    "tire_analysis": {k: {"stint_analysis": v["stints"]} for k, v in processed_data.items()},
    "all_drivers_tire_strategy": {k: {"stint_analysis": v["stints"]} for k, v in processed_data.items()}
}

print(f"準備了 {len(chart_data['drivers_analyzed'])} 個車手的數據")

# 模擬 Chart Widget 的 update_data
print("\n[步驟 3] Chart Widget 接收數據 (update_data)")
print("-" * 80)

tire_analysis = chart_data.get('tire_analysis', {})
drivers_analyzed = chart_data.get('drivers_analyzed', [])

all_drivers_stint_data = {}

for driver in drivers_analyzed:
    if driver in tire_analysis:
        driver_data = tire_analysis[driver]
        driver_stints = driver_data.get('stint_analysis', [])
        
        print(f"\n{driver}:")
        for i, stint in enumerate(driver_stints):
            # 檢查 fastest_lap 計算
            if 'fastest_lap' not in stint:
                fastest_lap = (stint['start_lap'] + stint['end_lap']) // 2
                print(f"  Stint {i+1}: start={stint['start_lap']}, end={stint['end_lap']}, fastest_lap={fastest_lap}")
            
            # 檢查是否會觸發警告
            if stint['end_lap'] <= stint['start_lap']:
                print(f"  ⚠️ 會觸發警告: start={stint['start_lap']}, end={stint['end_lap']}")

print("\n" + "=" * 80)
print("結論:")
print("-" * 80)
print("✅ 如果上面沒有警告，說明修復有效")
print("❌ 如果仍有警告，說明問題在其他地方")
print("=" * 80)
