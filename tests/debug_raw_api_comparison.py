"""
比較 FastF1 遙測數據來源：
1. session.laps.get_telemetry() - 處理過的數據
2. 原始 car_data API - 未處理的數據

調查採樣頻率問題是來自 FastF1 處理還是原始 API
"""
import fastf1
import pandas as pd
from fastf1 import api

# 載入數據
fastf1.Cache.enable_cache('cache')
session = fastf1.get_session(2025, 'Abu Dhabi', 'FP2')
session.load()

# T6 位置
circuit_info = session.get_circuit_info()
corners = circuit_info.corners
t6 = corners[corners['Number'] == 6].iloc[0]
t6_distance = t6['Distance']

print(f'T6 中心距離: {t6_distance:.1f} m')
print()

# 獲取 ANT 的圈數資訊
ant_laps = session.laps.pick_driver('ANT')
print(f'ANT 總圈數: {len(ant_laps)}')

# 分析特定異常圈：Lap 20, 25, 26
target_laps = [20, 25, 26, 28]  # 28 是正常圈作為對比

for lap_num in target_laps:
    print()
    print('=' * 70)
    print(f'=== Lap {lap_num} ===')
    print('=' * 70)
    
    lap_data = ant_laps[ant_laps['LapNumber'] == lap_num]
    if lap_data.empty:
        print('無數據')
        continue
    
    lap = lap_data.iloc[0]
    
    # 方法 1: FastF1 處理後的遙測
    print('\n【方法 1】FastF1 get_telemetry() 處理後數據:')
    try:
        tel = lap.get_telemetry()
        if tel is not None and not tel.empty:
            # T6 區域
            nearby = tel[(tel['Distance'] >= t6_distance - 30) & (tel['Distance'] <= t6_distance + 30)]
            print(f'  T6 區域數據點: {len(nearby)}')
            print(f'  Speed 範圍: {nearby["Speed"].min():.1f} - {nearby["Speed"].max():.1f} km/h')
            print(f'  採樣頻率估算: {len(tel) / (tel["Distance"].max() / 1000):.1f} 點/km')
            
            # 顯示彎心區數據
            core = tel[(tel['Distance'] >= t6_distance - 10) & (tel['Distance'] <= t6_distance + 10)]
            print(f'  彎心區(±10m)數據點: {len(core)}')
            if not core.empty:
                print(f'  彎心區 Speed: {core["Speed"].min():.1f} - {core["Speed"].max():.1f} km/h')
    except Exception as e:
        print(f'  錯誤: {e}')
    
    # 方法 2: 使用原始 car_data（未經 FastF1 處理）
    print('\n【方法 2】原始 car_data（未處理）:')
    try:
        # 從 session 獲取原始 car_data
        # ANT 的車號是 87
        driver_number = '87'  # Antonelli
        
        # 獲取該圈的時間範圍
        lap_start = lap.get('LapStartTime')
        lap_end = lap.get('Time')
        
        if pd.notna(lap_start) and pd.notna(lap_end):
            # 從 session 的原始數據中提取
            if hasattr(session, 'car_data') and driver_number in session.car_data:
                car_data = session.car_data[driver_number]
                
                # 篩選該圈的數據
                lap_car_data = car_data[(car_data['Time'] >= lap_start) & (car_data['Time'] <= lap_end)]
                
                print(f'  該圈原始數據點總數: {len(lap_car_data)}')
                print(f'  Speed 列存在: {"Speed" in lap_car_data.columns}')
                
                if 'Speed' in lap_car_data.columns:
                    print(f'  Speed 範圍: {lap_car_data["Speed"].min():.1f} - {lap_car_data["Speed"].max():.1f} km/h')
                    
                    # 計算採樣頻率
                    if len(lap_car_data) > 1:
                        time_diff = (lap_car_data['Time'].iloc[-1] - lap_car_data['Time'].iloc[0]).total_seconds()
                        freq = len(lap_car_data) / time_diff if time_diff > 0 else 0
                        print(f'  採樣頻率: {freq:.1f} Hz')
            else:
                print(f'  car_data 不存在或無 driver {driver_number}')
        else:
            print(f'  LapStartTime 或 Time 為空')
            
    except Exception as e:
        print(f'  錯誤: {e}')
    
    # 方法 3: 檢查 position_data（位置數據）
    print('\n【方法 3】position_data（位置數據）:')
    try:
        if hasattr(session, 'pos_data') and driver_number in session.pos_data:
            pos_data = session.pos_data[driver_number]
            
            if pd.notna(lap_start) and pd.notna(lap_end):
                lap_pos_data = pos_data[(pos_data['Time'] >= lap_start) & (pos_data['Time'] <= lap_end)]
                print(f'  該圈位置數據點: {len(lap_pos_data)}')
                
                if len(lap_pos_data) > 1:
                    time_diff = (lap_pos_data['Time'].iloc[-1] - lap_pos_data['Time'].iloc[0]).total_seconds()
                    freq = len(lap_pos_data) / time_diff if time_diff > 0 else 0
                    print(f'  位置採樣頻率: {freq:.1f} Hz')
        else:
            print(f'  pos_data 不存在')
            
    except Exception as e:
        print(f'  錯誤: {e}')

print()
print('=' * 70)
print('=== 結論 ===')
print('=' * 70)
print('''
如果方法 1 和方法 2 的數據點數差異很大，問題可能在 FastF1 的處理。
如果方法 2 的原始數據本身就很少，問題在 F1 官方 API 的採樣。
''')
