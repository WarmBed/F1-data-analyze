import json

# 讀取 JSON 數據
with open('json/tire_strategy_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['drivers_analysis']

print("=" * 80)
print("檢查 stint_analysis 中 start_lap == end_lap 的情況")
print("=" * 80)

found_issues = []

for driver in sorted(drivers.keys()):
    driver_data = drivers[driver]
    stint_analysis = driver_data.get('stint_analysis', [])
    
    for stint in stint_analysis:
        start = stint.get('start_lap')
        end = stint.get('end_lap')
        length = stint.get('length', 'N/A')
        stint_num = stint.get('stint_number', 'N/A')
        compound = stint.get('compound', 'N/A')
        
        if start == end:
            found_issues.append({
                'driver': driver,
                'stint_number': stint_num,
                'start_lap': start,
                'end_lap': end,
                'length': length,
                'compound': compound
            })
            print(f"{driver} - Stint {stint_num}: start={start}, end={end}, length={length}, compound={compound}")

print("\n" + "=" * 80)
print(f"總共發現 {len(found_issues)} 個 start == end 的問題")
print("=" * 80)

# 檢查是否有 corrected_stint_analysis
print("\n檢查是否有 corrected_stint_analysis:")
for driver in sorted(drivers.keys()):
    driver_data = drivers[driver]
    if 'corrected_stint_analysis' in driver_data:
        print(f"{driver}: 有 corrected_stint_analysis")
        corrected = driver_data['corrected_stint_analysis']
        for stint in corrected:
            start = stint.get('start_lap')
            end = stint.get('end_lap')
            if start == end:
                print(f"  ⚠️ Stint {stint.get('stint_number')}: start={start}, end={end}")
