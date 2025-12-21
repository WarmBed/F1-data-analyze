"""
手動查詢 ANT T6 遙測數據 - 診斷異常值問題
"""
import fastf1
import pandas as pd

# 載入數據
fastf1.Cache.enable_cache('cache')
session = fastf1.get_session(2025, 'Abu Dhabi', 'FP2')
session.load()

# 獲取 ANT 的所有圈數
ant_laps = session.laps.pick_driver('ANT')
print('=== ANT 總圈數 ===')
print(f'總圈數: {len(ant_laps)}')
print(f'圈數範圍: {ant_laps["LapNumber"].min()} - {ant_laps["LapNumber"].max()}')

# 獲取彎道資訊
circuit_info = session.get_circuit_info()
corners = circuit_info.corners
t6 = corners[corners['Number'] == 6].iloc[0]
t6_distance = t6['Distance']
print(f'\n=== T6 彎道資訊 ===')
print(f'T6 距離位置: {t6_distance:.1f} m')
print(f'T6 角度: {t6.get("Angle", "N/A")}')

# 分析每一圈在 T6 的速度
print(f'\n=== ANT 每圈 T6 速度 (+-20m 範圍) ===')
print(f'{"Lap":>4} | {"MinSpeed":>10} | {"MaxSpeed":>10} | {"Range":>8} | 狀態')
print('-' * 55)

speeds_data = []
for idx, lap in ant_laps.iterrows():
    try:
        tel = lap.get_telemetry()
        if tel is None or tel.empty:
            continue
        
        # ±20m 範圍
        nearby = tel[(tel['Distance'] >= t6_distance - 20) & (tel['Distance'] <= t6_distance + 20)]
        if nearby.empty:
            continue
        
        min_speed = nearby['Speed'].min()
        max_speed = nearby['Speed'].max()
        
        speeds_data.append({
            'Lap': int(lap['LapNumber']),
            'MinSpeed': min_speed,
            'MaxSpeed': max_speed,
            'SpeedRange': max_speed - min_speed
        })
        
        # 標記異常圈
        if min_speed > 100:
            flag = '!!! MIN > 100'
        elif max_speed > 150:
            flag = '!! MAX > 150'
        else:
            flag = 'OK'
            
        print(f'{int(lap["LapNumber"]):4d} | {min_speed:10.1f} | {max_speed:10.1f} | {max_speed-min_speed:8.1f} | {flag}')
        
    except Exception as e:
        print(f'{int(lap["LapNumber"]):4d} | ERROR: {e}')

print(f'\n=== 統計摘要 ===')
if speeds_data:
    df = pd.DataFrame(speeds_data)
    print(f'有效圈數: {len(df)}')
    print(f'')
    print(f'MinSpeed 統計:')
    print(f'  - 最小: {df["MinSpeed"].min():.1f} km/h')
    print(f'  - 最大: {df["MinSpeed"].max():.1f} km/h')
    print(f'  - 平均: {df["MinSpeed"].mean():.1f} km/h')
    print(f'  - 中位數: {df["MinSpeed"].median():.1f} km/h')
    print(f'')
    print(f'MaxSpeed 統計:')
    print(f'  - 最小: {df["MaxSpeed"].min():.1f} km/h')
    print(f'  - 最大: {df["MaxSpeed"].max():.1f} km/h')
    print(f'  - 平均: {df["MaxSpeed"].mean():.1f} km/h')
    
    # 找出異常圈
    anomalies = df[df['MinSpeed'] > 100]
    if not anomalies.empty:
        print(f'\n=== 異常圈（MinSpeed > 100 km/h）===')
        for _, row in anomalies.iterrows():
            print(f'  Lap {row["Lap"]}: MinSpeed={row["MinSpeed"]:.1f}, MaxSpeed={row["MaxSpeed"]:.1f}')
        
        # 深入分析第一個異常圈
        first_anomaly_lap = int(anomalies.iloc[0]['Lap'])
        print(f'\n=== 深入分析 Lap {first_anomaly_lap} 的 T6 區域 ===')
        
        lap_data = ant_laps[ant_laps['LapNumber'] == first_anomaly_lap].iloc[0]
        tel = lap_data.get_telemetry()
        nearby = tel[(tel['Distance'] >= t6_distance - 30) & (tel['Distance'] <= t6_distance + 30)]
        
        print(f'T6 中心距離: {t6_distance:.1f} m')
        print(f'搜尋範圍: {t6_distance - 30:.1f} ~ {t6_distance + 30:.1f} m')
        print(f'')
        print(f'遙測數據點:')
        print(f'{"Distance":>10} | {"Speed":>10} | {"Throttle":>10} | {"Brake":>8}')
        print('-' * 50)
        for _, row in nearby.iterrows():
            print(f'{row["Distance"]:10.1f} | {row["Speed"]:10.1f} | {row.get("Throttle", "N/A"):>10} | {row.get("Brake", "N/A"):>8}')
    else:
        print(f'\n=== 沒有異常圈 ===')
