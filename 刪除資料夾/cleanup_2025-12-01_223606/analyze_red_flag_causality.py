"""
分析紅旗與黃旗的因果關係
檢查每次紅旗前後的黃旗事件，找出可能的觸發原因
"""

import fastf1
import pandas as pd
from datetime import timedelta

fastf1.Cache.enable_cache('f1_analysis_cache')

def analyze_flags_before_red(session, minutes_before=5):
    """分析紅旗前 N 分鐘的旗幟訊息"""
    messages = session.race_control_messages
    
    # 找出所有紅旗（排除終點旗）
    red_flags = messages[
        (messages['Flag'].str.contains('RED', case=False, na=False)) &
        (~messages['Message'].str.contains('CHEQUERED', case=False, na=False))
    ]
    
    return red_flags, messages

# 測試案例：已知有紅旗的賽事
test_cases = [
    (2022, 'Japan', 'R', '2 red flags'),
    (2022, 'Monaco', 'R', '2 red flags'),
    (2024, 'Monaco', 'R', '1 red flag'),
    (2024, 'Brazil', 'R', '1 red flag'),
]

print("=" * 100)
print("RED FLAG CAUSALITY ANALYSIS")
print("Investigating yellow flags before each red flag")
print("=" * 100)

for year, race, session_type, note in test_cases:
    print(f"\n{'=' * 100}")
    print(f"RACE: {year} {race} - {session_type} ({note})")
    print("=" * 100)
    
    try:
        session = fastf1.get_session(year, race, session_type)
        session.load()
        
        red_flags, all_messages = analyze_flags_before_red(session)
        
        if len(red_flags) == 0:
            print("   No red flags found (excluding chequered)")
            continue
        
        for idx, red_flag in red_flags.iterrows():
            red_time = red_flag['Time']
            red_message = red_flag['Message']
            
            print(f"\n--- RED FLAG at {red_time} ---")
            print(f"    Message: {red_message}")
            
            # 查找紅旗前 5 分鐘的所有訊息
            time_window_start = red_time - timedelta(minutes=5)
            messages_before = all_messages[
                (all_messages['Time'] >= time_window_start) & 
                (all_messages['Time'] < red_time)
            ]
            
            print(f"\n    Events in 5 minutes BEFORE red flag:")
            print(f"    {'-' * 90}")
            
            if len(messages_before) == 0:
                print("    No messages found")
            else:
                for msg_idx, msg in messages_before.iterrows():
                    time_diff = (red_time - msg['Time']).total_seconds()
                    flag = msg['Flag'] if pd.notna(msg['Flag']) else 'NO FLAG'
                    category = msg['Category'] if pd.notna(msg['Category']) else 'N/A'
                    message = msg['Message']
                    
                    # 高亮黃旗和安全車
                    marker = ""
                    if 'YELLOW' in flag.upper():
                        marker = " <-- YELLOW FLAG"
                    elif 'SAFETY CAR' in message.upper():
                        marker = " <-- SAFETY CAR"
                    elif 'VSC' in message.upper():
                        marker = " <-- VSC"
                    
                    print(f"    [-{int(time_diff)}s] [{flag:15}] {message}{marker}")
            
            # 查找紅旗後 2 分鐘的訊息（瞭解後續處理）
            time_window_end = red_time + timedelta(minutes=2)
            messages_after = all_messages[
                (all_messages['Time'] > red_time) & 
                (all_messages['Time'] <= time_window_end)
            ]
            
            print(f"\n    Events in 2 minutes AFTER red flag:")
            print(f"    {'-' * 90}")
            
            if len(messages_after) > 0:
                for msg_idx, msg in messages_after.head(10).iterrows():
                    time_diff = (msg['Time'] - red_time).total_seconds()
                    flag = msg['Flag'] if pd.notna(msg['Flag']) else 'NO FLAG'
                    message = msg['Message']
                    print(f"    [+{int(time_diff)}s] [{flag:15}] {message}")
    
    except Exception as e:
        print(f"   ERROR: {e}")

print("\n" + "=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
