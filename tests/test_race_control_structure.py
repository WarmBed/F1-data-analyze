"""
測試 race_control_messages 的實際欄位結構
檢查是否包含位置/距離/Sector 資訊，用於映射到彎道
"""
import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

# 測試 2024 Japan (有鈴鹿賽道的 official_corners 數據)
year = 2024
race = "Japan"
session_type = "R"

print(f"🏁 載入 {year} {race} {session_type} 賽事數據...")
print("=" * 70)

try:
    session = fastf1.get_session(year, race, session_type)
    session.load()
    
    # 1. 檢查 race_control_messages 的欄位
    print("\n📋 race_control_messages 欄位結構:")
    print("-" * 70)
    
    if hasattr(session, 'race_control_messages'):
        race_control = session.race_control_messages
        
        if race_control is not None and not race_control.empty:
            print(f"✅ 總共 {len(race_control)} 筆訊息")
            print(f"\n欄位列表: {list(race_control.columns)}")
            print(f"\n前 5 筆範例:")
            print(race_control.head())
            
            # 2. 找一筆 SAFETY CAR 或 YELLOW FLAG 的範例
            print("\n" + "=" * 70)
            print("🚨 尋找安全車/黃旗事件範例:")
            print("-" * 70)
            
            safety_events = race_control[
                race_control['Message'].str.contains('SAFETY|YELLOW|RED FLAG', case=False, na=False, regex=True)
            ]
            
            if not safety_events.empty:
                print(f"\n找到 {len(safety_events)} 筆事件:")
                for idx, row in safety_events.head(3).iterrows():
                    print(f"\n事件 {idx}:")
                    for col in race_control.columns:
                        print(f"  {col}: {row[col]}")
                    print("-" * 50)
            else:
                print("❌ 本場比賽未發現安全車/黃旗事件")
            
            # 3. 檢查是否有位置相關欄位
            print("\n" + "=" * 70)
            print("📍 位置相關欄位檢查:")
            print("-" * 70)
            
            position_related_columns = [
                'Sector', 'Distance', 'Position', 'Location', 'Corner',
                'TrackPosition', 'X', 'Y', 'Coordinates'
            ]
            
            found_position_cols = [col for col in position_related_columns if col in race_control.columns]
            
            if found_position_cols:
                print(f"✅ 找到位置相關欄位: {found_position_cols}")
            else:
                print(f"❌ 未找到位置相關欄位 (檢查範圍: {position_related_columns})")
                print(f"   實際欄位: {list(race_control.columns)}")
        else:
            print("❌ race_control_messages 為空")
    else:
        print("❌ session 沒有 race_control_messages 屬性")
    
    # 4. 檢查 laps 數據是否有 Distance/Position
    print("\n" + "=" * 70)
    print("📊 Laps 數據欄位檢查 (用於推算事件位置):")
    print("-" * 70)
    
    if hasattr(session, 'laps') and session.laps is not None:
        print(f"✅ Laps 欄位: {list(session.laps.columns)}")
        
        # 檢查是否有 Time 欄位可以用來映射
        if 'Time' in session.laps.columns and 'LapTime' in session.laps.columns:
            print("✅ 可以使用 Time 欄位映射事件到圈數和位置")
    
    # 5. 檢查 official_corners 資料
    print("\n" + "=" * 70)
    print("🏁 Official Corners 數據:")
    print("-" * 70)
    
    if hasattr(session, 'results') and session.results is not None:
        if not session.results.empty:
            first_driver = session.results.iloc[0]['Abbreviation']
            driver_laps = session.laps.pick_driver(first_driver)
            
            if hasattr(driver_laps, 'get_telemetry'):
                telemetry = driver_laps.iloc[0].get_telemetry()
                
                if telemetry is not None and 'Distance' in telemetry.columns:
                    print(f"✅ Telemetry 包含 Distance 欄位")
                    print(f"   Distance 範圍: {telemetry['Distance'].min():.0f}m - {telemetry['Distance'].max():.0f}m")
    
    print("\n" + "=" * 70)
    print("✅ 數據結構檢查完成")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
