"""
測試 FastF1 是否提供 Z 軸（高度）數據

檢查項目：
1. 位置數據 (pos_data) 的欄位
2. 遙測數據 (telemetry) 的欄位
3. Session 和 Lap 物件的可用屬性
"""

import fastf1
import pandas as pd

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

print("=" * 80)
print("FastF1 Z 軸高度數據檢查報告")
print("=" * 80)

try:
    # 載入 2024 日本站正賽數據
    print("\n[步驟 1] 載入 2024 日本站正賽數據...")
    session = fastf1.get_session(2024, 'Japan', 'R')
    session.load()
    print("✓ 數據載入成功")
    
    # 檢查 Session 物件屬性
    print("\n[步驟 2] 檢查 Session 物件屬性...")
    session_attrs = dir(session)
    z_related = [attr for attr in session_attrs if 'z' in attr.lower() or 'alt' in attr.lower() or 'elev' in attr.lower() or 'height' in attr.lower()]
    print(f"Session 物件中與高度相關的屬性: {z_related}")
    
    # 獲取最快圈的車手
    print("\n[步驟 3] 獲取最快圈遙測數據...")
    fastest_lap = session.laps.pick_fastest()
    driver = fastest_lap['Driver']
    print(f"最快圈車手: {driver}")
    
    # 檢查 Lap 物件屬性
    print("\n[步驟 4] 檢查 Lap 物件屬性...")
    lap_attrs = dir(fastest_lap)
    lap_z_related = [attr for attr in lap_attrs if 'z' in attr.lower() or 'alt' in attr.lower() or 'elev' in attr.lower() or 'height' in attr.lower() or 'pos' in attr.lower()]
    print(f"Lap 物件中與位置/高度相關的屬性: {lap_z_related}")
    
    # 獲取遙測數據
    print("\n[步驟 5] 獲取遙測數據並檢查欄位...")
    telemetry = fastest_lap.get_telemetry()
    print(f"\n遙測數據欄位:")
    for col in telemetry.columns:
        print(f"  - {col}")
    
    # 檢查是否有 X, Y, Z 欄位
    print("\n[步驟 6] 檢查座標欄位...")
    has_x = 'X' in telemetry.columns
    has_y = 'Y' in telemetry.columns
    has_z = 'Z' in telemetry.columns
    
    print(f"  X 欄位存在: {has_x}")
    print(f"  Y 欄位存在: {has_y}")
    print(f"  Z 欄位存在: {has_z}")
    
    if has_x and has_y and has_z:
        print("\n🎉 FastF1 提供完整的 X, Y, Z 座標數據！")
        print("\n[步驟 7] 分析 Z 軸數據...")
        
        # 清理數據
        z_data = telemetry['Z'].dropna()
        print(f"\n  Z 軸數據統計:")
        print(f"    資料點數: {len(z_data)}")
        print(f"    最小高度: {z_data.min():.2f} m")
        print(f"    最大高度: {z_data.max():.2f} m")
        print(f"    平均高度: {z_data.mean():.2f} m")
        print(f"    高度變化: {z_data.max() - z_data.min():.2f} m")
        print(f"    中位數: {z_data.median():.2f} m")
        print(f"    標準差: {z_data.std():.2f} m")
        
        # 顯示前 10 個數據點
        print(f"\n  前 10 個座標數據點:")
        print(telemetry[['X', 'Y', 'Z', 'Speed', 'Distance']].head(10).to_string())
        
        # 檢查 X, Y 數據
        x_data = telemetry['X'].dropna()
        y_data = telemetry['Y'].dropna()
        print(f"\n  X 軸範圍: {x_data.min():.2f} ~ {x_data.max():.2f}")
        print(f"  Y 軸範圍: {y_data.min():.2f} ~ {y_data.max():.2f}")
        
    elif has_x and has_y:
        print("\n⚠️  FastF1 只提供 X, Y 座標，沒有 Z 軸高度數據")
        print("\n[步驟 7] 分析 X, Y 數據...")
        print(f"  X 軸範圍: {telemetry['X'].min():.2f} ~ {telemetry['X'].max():.2f}")
        print(f"  Y 軸範圍: {telemetry['Y'].min():.2f} ~ {telemetry['Y'].max():.2f}")
        
    else:
        print("\n❌ FastF1 不提供座標數據 (X, Y, Z)")
    
    # 檢查是否有 pos_data 或類似方法
    print("\n[步驟 8] 檢查位置數據方法...")
    if hasattr(fastest_lap, 'get_pos_data'):
        print("  ✓ 發現 get_pos_data() 方法")
        try:
            pos_data = fastest_lap.get_pos_data()
            print(f"\n  位置數據欄位:")
            for col in pos_data.columns:
                print(f"    - {col}")
        except Exception as e:
            print(f"  ✗ 調用 get_pos_data() 失敗: {e}")
    else:
        print("  ✗ 沒有 get_pos_data() 方法")
    
    # 檢查 Session 是否有賽道數據
    print("\n[步驟 9] 檢查 Session 賽道數據...")
    if hasattr(session, 'get_circuit_info'):
        print("  ✓ 發現 get_circuit_info() 方法")
    else:
        print("  ✗ 沒有 get_circuit_info() 方法")
    
except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("檢查完成")
print("=" * 80)
