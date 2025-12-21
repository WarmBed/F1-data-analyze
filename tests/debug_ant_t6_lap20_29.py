"""
深入分析 ANT Lap 20-29 的 T6 遙測數據
"""
import fastf1
import pandas as pd

# 載入數據
fastf1.Cache.enable_cache('cache')
session = fastf1.get_session(2025, 'Abu Dhabi', 'FP2')
session.load()

# 獲取 ANT 的所有圈數
ant_laps = session.laps.pick_driver('ANT')

# 獲取彎道資訊
circuit_info = session.get_circuit_info()
corners = circuit_info.corners
t6 = corners[corners['Number'] == 6].iloc[0]
t6_distance = t6['Distance']

print(f'T6 中心距離: {t6_distance:.1f} m')
print(f'搜尋範圍: ±20m = {t6_distance - 20:.1f} ~ {t6_distance + 20:.1f} m')
print()

# 分析 Lap 20-29
target_laps = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]

for lap_num in target_laps:
    lap_data = ant_laps[ant_laps['LapNumber'] == lap_num]
    if lap_data.empty:
        print(f'=== Lap {lap_num}: 無數據 ===\n')
        continue
    
    lap = lap_data.iloc[0]
    
    # 基本資訊
    print(f'=== Lap {lap_num} ===')
    print(f'LapTime: {lap.get("LapTime", "N/A")}')
    print(f'IsAccurate: {lap.get("IsAccurate", "N/A")}')
    print(f'PitOutTime: {lap.get("PitOutTime", "N/A")}')
    print(f'PitInTime: {lap.get("PitInTime", "N/A")}')
    print(f'TrackStatus: {lap.get("TrackStatus", "N/A")}')
    
    try:
        tel = lap.get_telemetry()
        if tel is None or tel.empty:
            print('遙測數據: 無\n')
            continue
        
        # ±30m 範圍（更寬的範圍看完整圖景）
        nearby = tel[(tel['Distance'] >= t6_distance - 30) & (tel['Distance'] <= t6_distance + 30)]
        
        if nearby.empty:
            print('T6 區域無數據點\n')
            continue
        
        min_speed = nearby['Speed'].min()
        max_speed = nearby['Speed'].max()
        
        print(f'T6 區域 (±30m):')
        print(f'  數據點數: {len(nearby)}')
        print(f'  MinSpeed: {min_speed:.1f} km/h')
        print(f'  MaxSpeed: {max_speed:.1f} km/h')
        print(f'  Range: {max_speed - min_speed:.1f} km/h')
        
        # 判斷是否正常過彎
        if min_speed > 100:
            print(f'  狀態: 🚨 沒有過彎！')
        elif max_speed > 150:
            print(f'  狀態: ⚠️ 可能採樣到加速區')
        else:
            print(f'  狀態: ✅ 正常')
        
        print()
        print('  遙測詳細數據:')
        print(f'  {"Dist":>8} | {"Speed":>7} | {"Thr":>5} | {"Brk":>5} | 相對位置')
        print('  ' + '-' * 55)
        
        for _, row in nearby.iterrows():
            dist = row['Distance']
            speed = row['Speed']
            throttle = row.get('Throttle', 0)
            brake = row.get('Brake', 0)
            
            # 相對於 T6 中心的位置
            relative = dist - t6_distance
            if relative < -10:
                pos = '入彎區'
            elif relative > 10:
                pos = '出彎區'
            else:
                pos = '>>> 彎心 <<<'
            
            print(f'  {dist:8.1f} | {speed:7.1f} | {throttle:5.0f} | {brake:5.0f} | {pos}')
        
    except Exception as e:
        print(f'錯誤: {e}')
    
    print()
    print('=' * 60)
    print()
