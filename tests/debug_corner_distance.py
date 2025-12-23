"""
調查彎道距離問題
"""
import fastf1
import numpy as np

fastf1.Cache.enable_cache('f1_analysis_cache')

print('=' * 70)
print('鈴鹿賽道彎道距離調查')
print('=' * 70)

session = fastf1.get_session(2024, 'Japan', 'R')
session.load()

fastest_lap = session.laps.pick_fastest()
telemetry = fastest_lap.get_telemetry()

track_length = telemetry['Distance'].max()
print(f'\n賽道長度: {track_length:.2f} m ({track_length/1000:.3f} km)')

# 預定義的鈴鹿 18 個彎道
suzuka_corners = [
    {'number': 1, 'distance_pct': 0.048},
    {'number': 2, 'distance_pct': 0.120},
    {'number': 3, 'distance_pct': 0.168},
    {'number': 4, 'distance_pct': 0.216},
    {'number': 5, 'distance_pct': 0.264},
    {'number': 6, 'distance_pct': 0.312},
    {'number': 7, 'distance_pct': 0.360},
    {'number': 8, 'distance_pct': 0.408},
    {'number': 9, 'distance_pct': 0.456},
    {'number': 10, 'distance_pct': 0.504},
    {'number': 11, 'distance_pct': 0.552},
    {'number': 12, 'distance_pct': 0.600},
    {'number': 13, 'distance_pct': 0.648},
    {'number': 14, 'distance_pct': 0.696},
    {'number': 15, 'distance_pct': 0.744},
    {'number': 16, 'distance_pct': 0.792},
    {'number': 17, 'distance_pct': 0.840},
    {'number': 18, 'distance_pct': 0.888},
]

print('\n彎道位置計算:')
print(f"{'彎道':<6} {'百分比':<10} {'距離(m)':<12} {'距離(km)':<10}")
print('-' * 45)

for corner in suzuka_corners:
    distance_m = corner['distance_pct'] * track_length
    distance_km = distance_m / 1000
    print(f"T{corner['number']:<5} {corner['distance_pct']:<10.3f} {distance_m:<12.2f} {distance_km:<10.3f}")

print(f'\n問題分析:')
print(f'如果圖表只顯示到 T11（約 3.15km），可能的原因:')
print(f'1. X 軸最大值設定錯誤（應該是 {track_length/1000:.3f} km）')
print(f'2. 彎道標記的 X 座標計算使用了錯誤的比例')
print(f'3. 繪圖區域寬度計算問題')

# 檢查 demo 文件中的數據傳遞
print(f'\n請檢查 demo_fastf1_z_elevation.py 中:')
print(f'1. self.distance 的最大值是否為 {track_length/1000:.3f} km')
print(f'2. self.elevation_chart.set_data() 接收的 distance 範圍')
print(f'3. paintEvent() 中的 x_scale 計算是否正確')
