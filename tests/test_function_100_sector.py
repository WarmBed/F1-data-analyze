"""
快速測試 Function 100 的 Sector 邊界提取
"""

import sys
sys.path.insert(0, 'CLI_modules')

from cli.analyzer.historical_flags_analysis import extract_track_position_with_speed
import fastf1

print("="*60)
print("測試 extract_track_position_with_speed 函數")
print("="*60)

# 設定緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

# 載入 2024 年巴西 GP 正賽
print("\n載入 2024 年巴西 GP 正賽...")
session = fastf1.get_session(2024, 'Brazil', 'R')
session.load()

print("會話載入成功\n")

# 調用函數
result = extract_track_position_with_speed(session)

print("\n" + "="*60)
print("函數返回結果分析")
print("="*60)

print(f"\nposition_records 數量: {len(result.get('position_records', []))}")
print(f"track_bounds 存在: {result.get('track_bounds') is not None}")
print(f"elevation_profile 存在: {result.get('elevation_profile') is not None}")
print(f"sector_boundaries 存在: {'sector_boundaries' in result}")
print(f"sector_boundaries 數量: {len(result.get('sector_boundaries', []))}")

if result.get('sector_boundaries'):
    print("\nSector 邊界詳細資訊:")
    for boundary in result['sector_boundaries']:
        print(f"  - {boundary['name']}: {boundary['distance_m']:.1f}m")
        print(f"    座標: ({boundary['position_x']:.1f}, {boundary['position_y']:.1f})")
        if boundary.get('elevation'):
            print(f"    高程: {boundary['elevation']:.1f}")
        print(f"    時間: {boundary['sector_time']:.3f}s")
else:
    print("\n⚠️  未找到 sector_boundaries！")

print("\n" + "="*60)
