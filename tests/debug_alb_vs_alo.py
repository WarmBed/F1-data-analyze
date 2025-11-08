"""深入分析 ALB vs ALO 的遙測數據，找出加速數據缺失原因"""
import fastf1
import pandas as pd
import numpy as np

# 載入 Azerbaijan 2025 R
print("=" * 80)
print("🔍 深入分析 ALB vs ALO 遙測數據")
print("=" * 80)

fastf1.Cache.enable_cache('f1_analysis_cache')
session = fastf1.get_session(2025, 'Azerbaijan', 'R')
print("📡 載入會話數據...")
session.load()

# 獲取兩位車手
drivers = ['ALB', 'ALO']
colors = {'ALB': 'Williams', 'ALO': 'Aston Martin'}

for driver_code in drivers:
    print(f"\n{'=' * 80}")
    print(f"🏎️  {driver_code} ({colors[driver_code]})")
    print("=" * 80)
    
    # 獲取車手的所有圈
    driver_laps = session.laps.pick_driver(driver_code)
    
    if driver_laps.empty:
        print(f"❌ 找不到 {driver_code} 的圈數數據")
        continue
    
    # 找最速圈
    valid_laps = driver_laps[driver_laps['LapTime'].notna()]
    if valid_laps.empty:
        print(f"❌ {driver_code} 沒有有效圈速")
        continue
    
    fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
    lap_number = int(fastest_lap['LapNumber'])
    lap_time = fastest_lap['LapTime']
    
    print(f"\n📊 最速圈資訊:")
    print(f"  圈數: Lap {lap_number}")
    print(f"  圈速: {lap_time}")
    
    # 獲取遙測數據
    try:
        fastest_lap_obj = driver_laps[driver_laps['LapNumber'] == lap_number].iloc[0]
        telemetry = fastest_lap_obj.get_car_data().add_distance()
        
        print(f"\n📡 遙測數據統計:")
        print(f"  總數據點: {len(telemetry)}")
        print(f"  速度範圍: {telemetry['Speed'].min():.1f} - {telemetry['Speed'].max():.1f} km/h")
        print(f"  距離範圍: {telemetry['Distance'].min():.1f} - {telemetry['Distance'].max():.1f} m")
        
        # 找最高速度點
        max_speed_idx = telemetry['Speed'].idxmax()
        max_speed = telemetry.loc[max_speed_idx, 'Speed']
        max_speed_distance = telemetry.loc[max_speed_idx, 'Distance']
        
        print(f"\n🎯 最高速度點:")
        print(f"  速度: {max_speed:.1f} km/h")
        print(f"  位置: {max_speed_distance:.1f} m")
        
        # 分析從最高速度點向前的速度分佈
        print(f"\n🔍 從最高速度點向前 500 個數據點的速度分佈:")
        
        max_speed_pos = telemetry.index.get_loc(max_speed_idx)
        start_pos = max(0, max_speed_pos - 500)
        
        speed_before_max = telemetry.iloc[start_pos:max_speed_pos + 1]['Speed']
        
        # 統計速度區間
        speed_bins = [0, 100, 150, 200, 250, 300, 350]
        speed_counts = pd.cut(speed_before_max, bins=speed_bins).value_counts().sort_index()
        
        print("\n  速度區間分佈:")
        for interval, count in speed_counts.items():
            if count > 0:
                print(f"    {interval}: {count} 個數據點")
        
        # 檢查是否有 100-150 km/h 的數據
        has_100_150 = len(speed_before_max[speed_before_max <= 150]) > 0
        has_100 = len(speed_before_max[speed_before_max <= 100]) > 0
        
        print(f"\n  ✅ 有 ≤100 km/h 的點: {has_100} ({len(speed_before_max[speed_before_max <= 100])} 個)")
        print(f"  ✅ 有 ≤150 km/h 的點: {has_100_150} ({len(speed_before_max[speed_before_max <= 150])} 個)")
        
        # 找到最低速度點
        min_speed_before_max = speed_before_max.min()
        min_speed_idx = speed_before_max.idxmin()
        min_speed_distance = telemetry.loc[min_speed_idx, 'Distance']
        
        print(f"\n  📉 最高速度點之前的最低速度:")
        print(f"    速度: {min_speed_before_max:.1f} km/h")
        print(f"    位置: {min_speed_distance:.1f} m")
        print(f"    速度增益: {max_speed - min_speed_before_max:.1f} km/h")
        
        # 分析參考直線段位置（假設是 VER 的主直線段）
        # 根據之前的輸出，VER 的參考範圍大約是 5285m - 5485m
        reference_start = 5285.0
        reference_end = 5485.0
        
        print(f"\n🎯 參考直線段分析 ({reference_start:.0f}m - {reference_end:.0f}m):")
        
        # 檢查最高速度點是否在參考範圍內
        in_core = reference_start <= max_speed_distance <= reference_end
        print(f"  最高速度點在核心範圍: {in_core}")
        
        # 擴展範圍 ±200m
        extended_start = reference_start - 200
        extended_end = reference_end + 200
        in_extended = extended_start <= max_speed_distance <= extended_end
        print(f"  最高速度點在擴展範圍 (±200m): {in_extended}")
        
        if in_extended:
            offset = ""
            if max_speed_distance < reference_start:
                offset = f"(核心範圍前 {reference_start - max_speed_distance:.1f}m)"
            elif max_speed_distance > reference_end:
                offset = f"(核心範圍後 {max_speed_distance - reference_end:.1f}m)"
            print(f"    位置偏移: {offset}")
        
        # 分析擴展範圍內的數據
        mask = (telemetry['Distance'] >= extended_start) & (telemetry['Distance'] <= extended_end)
        range_telemetry = telemetry[mask]
        
        if not range_telemetry.empty:
            print(f"\n  擴展範圍內的數據:")
            print(f"    數據點數量: {len(range_telemetry)}")
            print(f"    速度範圍: {range_telemetry['Speed'].min():.1f} - {range_telemetry['Speed'].max():.1f} km/h")
            
            # 檢查範圍內是否有低速點
            range_has_100 = len(range_telemetry[range_telemetry['Speed'] <= 100]) > 0
            range_has_150 = len(range_telemetry[range_telemetry['Speed'] <= 150]) > 0
            
            print(f"    範圍內有 ≤100 km/h: {range_has_100} ({len(range_telemetry[range_telemetry['Speed'] <= 100])} 個)")
            print(f"    範圍內有 ≤150 km/h: {range_has_150} ({len(range_telemetry[range_telemetry['Speed'] <= 150])} 個)")
            
            # 找範圍內最高速度點之前的最低速度
            range_max_speed_idx = range_telemetry['Speed'].idxmax()
            range_max_speed_pos = range_telemetry.index.get_loc(range_max_speed_idx)
            
            range_before_max = range_telemetry.iloc[:range_max_speed_pos + 1]
            if not range_before_max.empty:
                range_min_speed = range_before_max['Speed'].min()
                print(f"    範圍內最高速度點之前的最低速度: {range_min_speed:.1f} km/h")
                print(f"    範圍內速度增益: {range_telemetry['Speed'].max() - range_min_speed:.1f} km/h")
                
                # 關鍵判斷：能否計算加速數據
                can_calculate = False
                reason = ""
                
                if range_has_100:
                    can_calculate = True
                    reason = "範圍內有 ≤100 km/h 的點"
                elif range_has_150:
                    can_calculate = True
                    reason = "範圍內有 ≤150 km/h 的點"
                elif range_telemetry['Speed'].max() - range_min_speed >= 50:
                    can_calculate = True
                    reason = f"速度增益 {range_telemetry['Speed'].max() - range_min_speed:.1f} km/h >= 50 km/h"
                else:
                    reason = f"速度增益 {range_telemetry['Speed'].max() - range_min_speed:.1f} km/h < 50 km/h (不足)"
                
                print(f"\n  ⚙️  能否計算加速數據: {can_calculate}")
                print(f"    原因: {reason}")
        else:
            print(f"\n  ❌ 擴展範圍內沒有數據點！")
            print(f"    這表示車手的最高速度點不在參考直線段附近")
        
    except Exception as e:
        print(f"\n❌ 獲取遙測數據失敗: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 分析完成")
print("=" * 80)
