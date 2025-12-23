"""
測試 Safety Car 事件檢測和 Sector 資訊提取
使用 FastF1 直接讀取 race_control_messages
"""
import fastf1
import pandas as pd

# 設定緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

# 選擇一場有 Safety Car 的比賽（2021 Bahrain 有紅旗）
year = 2021
race = "Bahrain"
session_type = "R"

print(f"載入 {year} {race} {session_type} 賽事數據...")
session = fastf1.get_session(year, race, session_type)
session.load()

# 獲取 race control messages
race_control = session.race_control_messages

if race_control is not None and not race_control.empty:
    print(f"\n總共有 {len(race_control)} 筆 race control messages")
    
    # 找出所有包含 "SAFETY" 的訊息
    safety_messages = race_control[race_control['Message'].str.contains('SAFETY', case=False, na=False)]
    
    print(f"\n找到 {len(safety_messages)} 筆包含 'SAFETY' 的訊息:\n")
    print("=" * 100)
    
    for idx, row in safety_messages.iterrows():
        print(f"\nLap {row['Lap']}, Time {row['Time']}")
        print(f"Message: {row['Message']}")
        print(f"Category: {row.get('Category', 'N/A')}")
        print(f"Status: {row.get('Status', 'N/A')}")
        print("-" * 100)
    
    # 額外檢查 RED FLAG, YELLOW FLAG
    print("\n\n檢查其他重要旗幟...")
    print("=" * 100)
    
    for flag_type in ['RED FLAG', 'YELLOW', 'VIRTUAL SAFETY']:
        flag_messages = race_control[race_control['Message'].str.contains(flag_type, case=False, na=False)]
        print(f"\n{flag_type}: 找到 {len(flag_messages)} 筆")
        
        if len(flag_messages) > 0:
            print("前 3 筆:")
            for idx, row in flag_messages.head(3).iterrows():
                print(f"  Lap {row['Lap']}: {row['Message']}")
else:
    print("無法載入 race_control_messages")
