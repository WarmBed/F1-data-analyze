"""檢查 pos_data 和 telemetry 長度差異"""
import fastf1
import numpy as np

fastf1.Cache.enable_cache('f1_analysis_cache')

session = fastf1.get_session(2024, 'Japan', 'R')
session.load()

fastest_lap = session.laps.pick_fastest()
pos_data = fastest_lap.get_pos_data()
telemetry = fastest_lap.get_telemetry()

print('=' * 70)
print('pos_data vs telemetry 長度檢查')
print('=' * 70)

print(f'\npos_data 長度: {len(pos_data)}')
print(f'telemetry 長度: {len(telemetry)}')
print(f'min_len: {min(len(pos_data), len(telemetry))}')

print(f'\ntelemetry Distance 完整範圍:')
print(f'  最小值: {telemetry["Distance"].min():.2f}m')
print(f'  最大值: {telemetry["Distance"].max():.2f}m')

min_len = min(len(pos_data), len(telemetry))
distances_truncated = telemetry["Distance"].values[:min_len]

print(f'\n截取到 min_len={min_len} 後的 Distance 範圍:')
print(f'  最小值: {distances_truncated[0]:.2f}m')
print(f'  最大值: {distances_truncated[-1]:.2f}m')
print(f'  ⚠️ 損失: {telemetry["Distance"].max() - distances_truncated[-1]:.2f}m')

print(f'\n結論:')
if len(pos_data) < len(telemetry):
    print(f'  pos_data 較短！只有 {len(pos_data)} 個點')
    print(f'  telemetry 有 {len(telemetry)} 個點')
    print(f'  導致 distances 被截斷到 {distances_truncated[-1]:.2f}m')
else:
    print(f'  telemetry 較短！')
