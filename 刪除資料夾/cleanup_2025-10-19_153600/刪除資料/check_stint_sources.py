import json

# 讀取 JSON 數據
with open('json/tire_strategy_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['drivers_analysis']

print("=" * 80)
print("檢查所有可能的 stint 數據來源")
print("=" * 80)

for driver in sorted(drivers.keys())[:3]:  # 只檢查前3個車手
    print(f"\n{'='*60}")
    print(f"車手: {driver}")
    print(f"{'='*60}")
    
    driver_data = drivers[driver]
    
    # 檢查所有可能的 stint 數據字段
    possible_fields = [
        'corrected_stint_analysis',
        'original_stint_analysis', 
        'stint_analysis',
        'stints'
    ]
    
    for field in possible_fields:
        if field in driver_data:
            print(f"\n✅ 找到字段: {field}")
            stints = driver_data[field]
            print(f"   Stint 數量: {len(stints)}")
            
            for i, stint in enumerate(stints):
                start = stint.get('start_lap', 'N/A')
                end = stint.get('end_lap', 'N/A')
                length = stint.get('length', 'N/A')
                compound = stint.get('compound', 'N/A')
                
                marker = "⚠️" if start == end else "✓"
                print(f"   {marker} Stint {i+1}: start={start}, end={end}, length={length}, compound={compound}")
        else:
            print(f"❌ 無字段: {field}")
    
    # 檢查其他可能包含 stint 的頂層鍵
    print(f"\n所有頂層鍵: {list(driver_data.keys())}")
