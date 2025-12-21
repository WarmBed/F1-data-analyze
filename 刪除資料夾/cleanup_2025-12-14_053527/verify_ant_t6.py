#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""驗證 ANT T6 中位數過濾結果"""

import json

with open('json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json', encoding='utf-8') as f:
    data = json.load(f)

# 找 ANT 的數據
drivers = [d for d in data['mode_a_unified']['drivers'] if d['driver'] == 'ANT']

if drivers:
    ant = drivers[0]
    t6 = ant['corners'].get('T6_low_speed', {})
    
    print("=" * 50)
    print("ANT T6 (low_speed) 統計結果 - 中位數過濾後")
    print("=" * 50)
    print(f"  中位數: {t6.get('median_speed', 'N/A')} km/h")
    print(f"  平均速: {t6.get('mean_speed', 'N/A')} km/h")
    print(f"  最小值: {t6.get('min_speed', 'N/A')} km/h")
    print(f"  最大值: {t6.get('max_speed', 'N/A')} km/h")
    print(f"  有效圈: {t6.get('valid_laps', 'N/A')}")
    print(f"  過濾圈: {t6.get('filtered_laps', 'N/A')}")
    print(f"  原始速度: {t6.get('speeds_raw', [])}")
    
    # 檢查是否還有異常值 (> 150 km/h 的低速彎)
    speeds = t6.get('speeds_raw', [])
    outliers = [s for s in speeds if s > 150]
    if outliers:
        print(f"\n  [警告] 仍有異常值: {outliers}")
    else:
        print(f"\n  [成功] 無異常值 (所有值 < 150 km/h)")
else:
    print("ANT 車手未找到")

print("\n" + "=" * 50)
