#!/usr/bin/env python3
"""快速測試修正後的 _calculate_max_speed_for_year 函數"""

import sys
sys.path.insert(0, 'CLI_modules')

from cli.analyzer.historical_flags_analysis import _calculate_max_speed_for_year

print("測試 2025 巴西正賽最高速度計算...")
print("=" * 60)

max_speed = _calculate_max_speed_for_year(2025, 'Brazil', 'R')

print("=" * 60)
print(f"\n✅ 結果: {max_speed:.1f} km/h")
print(f"\n預期結果: 336.0 km/h (LAW, Lap 22)")
print(f"舊版結果: 333.0 km/h (HAD, Lap 40 - 只檢查最速圈)")
