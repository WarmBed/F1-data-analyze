"""
深入調查仍然異常的圈次（Lap 1, 16, 25, 26, 29）
"""
import fastf1
import pandas as pd

fastf1.Cache.enable_cache('cache')
session = fastf1.get_session(2025, 'Abu Dhabi', 'FP2')
session.load()

# T6 位置
circuit_info = session.get_circuit_info()
corners = circuit_info.corners
t6 = corners[corners['Number'] == 6].iloc[0]
t6_distance = t6['Distance']

print(f"T6 中心距離: {t6_distance:.1f} m")
print()

# ANT 數據
ant_laps = session.laps.pick_drivers('ANT')
driver_number = '12'  # ANT 的車號
car_data = session.car_data[driver_number]

# 異常圈次
anomaly_laps = [1, 16, 25, 26, 29]

for lap_num in anomaly_laps:
    print('=' * 70)
    print(f'=== Lap {lap_num} ===')
    print('=' * 70)
    
    lap_data = ant_laps[ant_laps['LapNumber'] == lap_num]
    if lap_data.empty:
        print('無圈數數據')
        continue
    
    lap = lap_data.iloc[0]
    
    # 獲取 telemetry 時間區間
    tel = lap.get_telemetry()
    if tel is None or tel.empty:
        print('無遙測數據')
        continue
    
    # 彎道區域
    tolerance = 20
    nearby = tel[
        (tel['Distance'] >= t6_distance - tolerance) &
        (tel['Distance'] <= t6_distance + tolerance)
    ]
    
    print(f'\n【FastF1 get_telemetry() 在 T6 區域】')
    print(f'  數據點數: {len(nearby)}')
    if not nearby.empty:
        print(f'  Speed 範圍: {nearby["Speed"].min():.1f} - {nearby["Speed"].max():.1f} km/h')
        print(f'  Distance 範圍: {nearby["Distance"].min():.1f} - {nearby["Distance"].max():.1f} m')
        
        # 獲取時間區間
        if 'SessionTime' in nearby.columns:
            time_min = nearby['SessionTime'].min()
            time_max = nearby['SessionTime'].max()
            print(f'  SessionTime 區間: {time_min} - {time_max}')
        
        # 從 car_data 獲取原始數據
        print(f'\n【原始 car_data 在相同時間區間】')
        if 'SessionTime' in car_data.columns and 'SessionTime' in nearby.columns:
            time_buffer = pd.Timedelta(seconds=0.5)
            raw_nearby = car_data[
                (car_data['SessionTime'] >= time_min - time_buffer) &
                (car_data['SessionTime'] <= time_max + time_buffer)
            ]
            print(f'  數據點數: {len(raw_nearby)}')
            if not raw_nearby.empty and 'Speed' in raw_nearby.columns:
                print(f'  Speed 範圍: {raw_nearby["Speed"].min():.1f} - {raw_nearby["Speed"].max():.1f} km/h')
                
                # 列出所有速度
                speeds = raw_nearby['Speed'].values
                print(f'  所有速度值: {speeds}')
    
    # 檢查該圈是否是特殊圈
    print(f'\n【圈次特性】')
    print(f'  LapTime: {lap["LapTime"]}')
    print(f'  Compound: {lap.get("Compound", "N/A")}')
    print(f'  IsAccurate: {lap.get("IsAccurate", "N/A")}')
    print(f'  TrackStatus: {lap.get("TrackStatus", "N/A")}')
    
    # 檢查是否是進站圈
    pit_in = lap.get('PitInTime')
    pit_out = lap.get('PitOutTime')
    if pd.notna(pit_in) or pd.notna(pit_out):
        print(f'  [!] 進站相關圈 - PitIn: {pit_in}, PitOut: {pit_out}')
    
    print()
