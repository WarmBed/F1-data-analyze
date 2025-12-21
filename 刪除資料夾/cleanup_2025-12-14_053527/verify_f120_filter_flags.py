#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""驗證 F120 JSON 中的過濾旗標"""

import json
from pathlib import Path

json_file = Path("json/F120_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json")

with open(json_file, encoding='utf-8') as f:
    data = json.load(f)

mode_a = data.get('mode_a_unified', {})
drivers = mode_a.get('drivers', [])

print("=== F120 過濾旗標驗證 ===\n")

# 統計過濾數據
filtered_drivers = []
for driver_info in drivers:
    driver = driver_info.get('driver', '')
    corners = driver_info.get('corners', {})
    
    for corner_key, corner_data in corners.items():
        entry_filtered = corner_data.get('entry_filtered', False)
        exit_filtered = corner_data.get('exit_filtered', False)
        
        # 驗證 GUI 相容欄位
        entry_50m = corner_data.get('entry_50m_speed')
        exit_50m = corner_data.get('exit_50m_speed')
        apex = corner_data.get('apex_speed')
        
        if entry_filtered or exit_filtered:
            filtered_drivers.append({
                'driver': driver,
                'corner': corner_key,
                'entry_filtered': entry_filtered,
                'exit_filtered': exit_filtered
            })

print(f"總車手數: {len(drivers)}")
print(f"過濾數據點數: {len(filtered_drivers)}")

if filtered_drivers:
    print("\n被過濾的車手:")
    for item in filtered_drivers:
        flags = []
        if item['entry_filtered']:
            flags.append('Entry')
        if item['exit_filtered']:
            flags.append('Exit')
        print(f"  🟣 {item['driver']} - {item['corner']} ({', '.join(flags)})")

# 驗證第一個車手的數據結構
if drivers:
    first_driver = drivers[0]
    first_corner_key = list(first_driver.get('corners', {}).keys())[0]
    first_corner = first_driver['corners'][first_corner_key]
    
    print(f"\n=== 數據結構驗證 ({first_driver['driver']} {first_corner_key}) ===")
    required_fields = ['entry_filtered', 'exit_filtered', 'entry_50m_speed', 'exit_50m_speed', 'apex_speed']
    for field in required_fields:
        value = first_corner.get(field)
        status = "✅" if value is not None else "❌"
        print(f"  {status} {field}: {value}")
