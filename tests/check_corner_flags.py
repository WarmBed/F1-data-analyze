#!/usr/bin/env python3
"""檢查彎道旗幟統計"""

import json

with open('json/historical_flags_Japan_2022-2025_20251109_152903.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

corner_analysis = data['data']['corner_analysis']

print('🚩 彎道旗幟統計:\n')
for corner_key in sorted(corner_analysis.keys(), key=lambda x: int(x[1:]) if x[1:].isdigit() else 0):
    corner = corner_analysis[corner_key]
    yearly = corner.get('yearly_breakdown', {})
    
    total_yellow = 0
    total_double_yellow = 0
    total_red = 0
    
    for year_data in yearly.values():
        total_yellow += year_data.get('yellow', 0)
        total_double_yellow += year_data.get('double_yellow', 0)
        total_red += year_data.get('red', 0)
    
    if total_yellow > 0 or total_double_yellow > 0 or total_red > 0:
        flags = []
        if total_yellow > 0:
            flags.append(f'Yellow: {total_yellow:.1f}')
        if total_double_yellow > 0:
            flags.append(f'D-Yellow: {total_double_yellow:.1f}')
        if total_red > 0:
            flags.append(f'Red: {total_red:.1f}')
        
        status = '🔴🟡' if (total_red > 0 and (total_yellow > 0 or total_double_yellow > 0)) else ('🔴' if total_red > 0 else '🟡')
        print(f'{status} {corner_key}: {" | ".join(flags)}')
