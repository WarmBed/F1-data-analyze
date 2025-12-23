#!/usr/bin/env python3
"""
測試 FastF1 Distance 欄位的實際意義
"""

import fastf1

# 啟用快取
fastf1.Cache.enable_cache('cache')

# 載入 2024 日本站正賽數據
print("正在載入 2024 日本站正賽數據...")
session = fastf1.get_session(2024, 'Japan', 'R')
session.load()

# 獲取 Verstappen 的最速圈
ver_laps = session.laps.pick_driver('VER')
fastest = ver_laps.pick_fastest()

# 獲取遙測數據並添加 Distance
print("正在獲取遙測數據...")
telemetry = fastest.get_car_data().add_distance()

print(f'\n{"="*60}')
print(f'Distance 欄位解析')
print(f'{"="*60}')
print(f'賽道: Japan (Suzuka)')
print(f'車手: VER')
print(f'圈數: {fastest["LapNumber"]}')
print(f'\nDistance 數據範圍:')
print(f'  最小值: {telemetry["Distance"].min():.1f} m')
print(f'  最大值: {telemetry["Distance"].max():.1f} m')
print(f'  總長度: {telemetry["Distance"].max() - telemetry["Distance"].min():.1f} m')
print(f'\nSuzuka 賽道實際長度: 5,807 m')

# 顯示前5個和後5個數據點
print(f'\n前5個數據點 (起點):')
print(telemetry[['Distance', 'Speed']].head())

print(f'\n後5個數據點 (終點):')
print(telemetry[['Distance', 'Speed']].tail())

print(f'\n{"="*60}')
print(f'📝 結論: Distance 是從單圈起點開始的累積距離')
print(f'{"="*60}')
print(f'✅ Distance 代表車輛在賽道上的位置 (單位: 公尺)')
print(f'✅ 起點距離通常接近 0m (或很小的數值)')
print(f'✅ 終點距離接近賽道總長度 (~5,807m)')
print(f'✅ 可用於定位特定賽道位置 (如直線段、彎道)')
print(f'✅ FastF1 透過積分速度數據計算累積距離')
