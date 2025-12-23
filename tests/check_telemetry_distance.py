"""檢查 FastF1 telemetry Distance 欄位"""
import fastf1
import numpy as np

fastf1.Cache.enable_cache('f1_analysis_cache')

session = fastf1.get_session(2024, 'Japan', 'R')
session.load()

fastest_lap = session.laps.pick_fastest()
telemetry = fastest_lap.get_telemetry()

print('檢查 telemetry Distance 欄位:')
print(f'資料點數: {len(telemetry)}')
print(f'Distance 最小值: {telemetry["Distance"].min():.2f} m')
print(f'Distance 最大值: {telemetry["Distance"].max():.2f} m')
print(f'Distance 範圍: {telemetry["Distance"].max() - telemetry["Distance"].min():.2f} m')
print()
print('前 5 個點:')
print(telemetry[['Distance', 'X', 'Y', 'Z']].head())
print()
print('後 5 個點:')
print(telemetry[['Distance', 'X', 'Y', 'Z']].tail())
