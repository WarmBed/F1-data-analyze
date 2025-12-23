#!/usr/bin/env python3
"""
深度檢查 2018 英國站 FP3 的位置數據
"""

import fastf1
import pandas as pd

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

print("=" * 60)
print("深度檢查：2018 Great Britain FP3 位置數據")
print("=" * 60)

try:
    # 載入會話
    print("\n📥 正在載入會話數據...")
    session = fastf1.get_session(2018, 'Great Britain', 'FP3')
    session.load(telemetry=True, laps=True, weather=False)
    print("✅ 會話數據載入成功")
    
    # 檢查單圈數據
    laps = session.laps
    print(f"\n📊 單圈統計:")
    print(f"   總單圈數: {len(laps)}")
    print(f"   單圈欄位: {list(laps.columns)[:10]}...")  # 顯示前 10 個欄位
    
    # 檢查是否有最速圈
    fastest = laps.pick_fastest()
    if fastest is None or pd.isna(fastest.get('LapTime')):
        print("❌ 沒有有效的最速圈")
    else:
        print(f"   最速圈: {fastest['Driver']} - {fastest['LapTime']}")
        
        # 獲取遙測數據
        print(f"\n📡 正在載入遙測數據...")
        tel = fastest.get_telemetry()
        print(f"✅ 遙測數據載入成功")
        print(f"   遙測形狀: {tel.shape}")
        print(f"   遙測欄位: {list(tel.columns)}")
        
        # 檢查位置數據
        print(f"\n📍 位置數據檢查:")
        has_x = 'X' in tel.columns
        has_y = 'Y' in tel.columns
        print(f"   有 X 欄位: {has_x}")
        print(f"   有 Y 欄位: {has_y}")
        
        if has_x and has_y:
            x_nulls = tel['X'].isna().sum()
            y_nulls = tel['Y'].isna().sum()
            total_points = len(tel)
            
            print(f"\n   X 資料:")
            print(f"      總點數: {total_points}")
            print(f"      空值數: {x_nulls}")
            print(f"      有效率: {((total_points - x_nulls) / total_points * 100):.1f}%")
            print(f"      樣本值: {tel['X'].dropna().head(5).tolist()}")
            
            print(f"\n   Y 資料:")
            print(f"      總點數: {total_points}")
            print(f"      空值數: {y_nulls}")
            print(f"      有效率: {((total_points - y_nulls) / total_points * 100):.1f}%")
            print(f"      樣本值: {tel['Y'].dropna().head(5).tolist()}")
            
            # 檢查是否所有值都是 NaN
            if x_nulls == total_points and y_nulls == total_points:
                print(f"\n❌ 位置數據全部為 NaN（無有效數據）")
            elif x_nulls > total_points * 0.5 or y_nulls > total_points * 0.5:
                print(f"\n⚠️  位置數據缺失率過高（超過 50%）")
            else:
                print(f"\n✅ 位置數據完整且有效")
        else:
            print(f"\n❌ 缺少 X 或 Y 欄位")
    
    # 檢查其他車手
    print(f"\n👥 檢查所有車手的位置數據:")
    drivers = laps['Driver'].unique()
    print(f"   車手數量: {len(drivers)}")
    
    position_data_count = 0
    for driver in drivers[:5]:  # 檢查前 5 名車手
        driver_laps = laps[laps['Driver'] == driver]
        if len(driver_laps) > 0:
            try:
                lap = driver_laps.iloc[0]
                tel = lap.get_telemetry()
                if 'X' in tel.columns and 'Y' in tel.columns:
                    x_valid = tel['X'].notna().sum()
                    y_valid = tel['Y'].notna().sum()
                    if x_valid > 0 and y_valid > 0:
                        position_data_count += 1
                        print(f"   ✅ {driver}: X={x_valid}/{len(tel)}, Y={y_valid}/{len(tel)}")
                    else:
                        print(f"   ❌ {driver}: 無有效位置數據")
                else:
                    print(f"   ❌ {driver}: 無 X/Y 欄位")
            except Exception as e:
                print(f"   ⚠️  {driver}: 無法載入遙測 ({str(e)[:50]})")
    
    print(f"\n📊 總結:")
    print(f"   有位置數據的車手: {position_data_count} / {min(5, len(drivers))}")
    
    if position_data_count == 0:
        print(f"\n❌ 結論: 2018 Great Britain FP3 確實沒有有效的位置數據")
    else:
        print(f"\n✅ 結論: 2018 Great Britain FP3 有位置數據，可能是 CLI 處理邏輯問題")

except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
