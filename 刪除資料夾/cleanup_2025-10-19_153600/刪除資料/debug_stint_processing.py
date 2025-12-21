import json

# 讀取 JSON 數據
with open('json/tire_strategy_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers_analysis = data.get('drivers_analysis', {})

print("=" * 80)
print("模擬 tire_analysis_mdi.py 的數據處理邏輯")
print("=" * 80)

for driver_code in sorted(list(drivers_analysis.keys())[:5]):  # 只看前5個車手
    print(f"\n{'='*70}")
    print(f"車手: {driver_code}")
    print(f"{'='*70}")
    
    driver_data = drivers_analysis[driver_code]
    
    # 模擬 _process_tire_strategy_data 中的邏輯
    stint_data = (
        driver_data.get("stint_analysis")
        or driver_data.get("corrected_stint_analysis")
        or driver_data.get("original_stint_analysis")
        or driver_data.get("stints")
        or []
    )
    
    print(f"找到 {len(stint_data)} 個 stint")
    
    for index, stint in enumerate(stint_data, start=1):
        print(f"\n  Stint {index}:")
        print(f"    原始數據: {stint}")
        
        # 模擬第 627-638 行的邏輯
        stint_number = (
            stint.get("stint_number")
            or stint.get("stint")
            or index
        )
        start_lap = (
            stint.get("start_lap")
            or stint.get("lap_start")
            or stint.get("startLap")
            or 1
        )
        end_lap = (
            stint.get("end_lap")
            or stint.get("lap_end")
            or stint.get("endLap")
            or start_lap
        )
        
        print(f"    處理後:")
        print(f"      stint_number = {stint_number}")
        print(f"      start_lap = {start_lap}")
        print(f"      end_lap = {end_lap}")
        
        # 檢查是否會觸發警告
        if end_lap <= start_lap:
            print(f"    ⚠️ 會觸發警告: end_lap ({end_lap}) <= start_lap ({start_lap})")
