import json

# 讀取 JSON 數據
with open('json/tire_strategy_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['drivers_analysis']

print("=" * 80)
print("檢查 stint 數據中是否有 null, 0, 或 False 值")
print("=" * 80)

problematic_stints = []

for driver in sorted(drivers.keys()):
    driver_data = drivers[driver]
    stint_analysis = driver_data.get('stint_analysis', [])
    
    for i, stint in enumerate(stint_analysis, start=1):
        start = stint.get('start_lap')
        end = stint.get('end_lap')
        length = stint.get('length')
        
        # 檢查是否有異常值
        issues = []
        if start is None:
            issues.append("start_lap 是 None")
        if end is None:
            issues.append("end_lap 是 None")
        if start == 0:
            issues.append("start_lap 是 0")
        if end == 0:
            issues.append("end_lap 是 0")
        if length == 0:
            issues.append("length 是 0")
        if start and end and start > end:
            issues.append(f"start ({start}) > end ({end})")
        
        if issues:
            problematic_stints.append({
                'driver': driver,
                'stint_num': i,
                'start_lap': start,
                'end_lap': end,
                'length': length,
                'issues': issues
            })
            print(f"{driver} - Stint {i}:")
            print(f"  start_lap={start}, end_lap={end}, length={length}")
            print(f"  問題: {', '.join(issues)}")
            print()

if not problematic_stints:
    print("\n✅ 沒有發現任何異常的 stint 數據！")
else:
    print(f"\n⚠️ 總共發現 {len(problematic_stints)} 個有問題的 stint")

# 額外檢查：打印幾個正常的 stint 來對比
print("\n" + "=" * 80)
print("正常 stint 數據範例（VER 車手）:")
print("=" * 80)
ver_stints = drivers.get('VER', {}).get('stint_analysis', [])
for i, stint in enumerate(ver_stints, start=1):
    print(f"Stint {i}: start={stint.get('start_lap')}, end={stint.get('end_lap')}, length={stint.get('length')}")
