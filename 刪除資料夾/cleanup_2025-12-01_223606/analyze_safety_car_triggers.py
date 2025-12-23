"""
分析安全車觸發原因
檢查安全車部署前的黃旗、事故位置等資訊
"""

import fastf1
import pandas as pd
from datetime import timedelta

fastf1.Cache.enable_cache('f1_analysis_cache')

def analyze_safety_car_deployment(session, minutes_before=3):
    """分析安全車部署前的旗幟訊息"""
    messages = session.race_control_messages
    
    # 找出所有安全車部署訊息
    safety_car_msgs = messages[
        messages['Message'].str.contains('SAFETY CAR DEPLOYED', case=False, na=False)
    ]
    
    # 找出所有 VSC 訊息
    vsc_msgs = messages[
        (messages['Message'].str.contains('VIRTUAL SAFETY CAR', case=False, na=False)) |
        (messages['Message'].str.contains('VSC DEPLOYED', case=False, na=False))
    ]
    
    return safety_car_msgs, vsc_msgs, messages

# 測試案例：選擇多個賽事
test_cases = [
    (2024, 'Japan', 'R'),
    (2022, 'Japan', 'R'),
    (2024, 'Monaco', 'R'),
    (2024, 'Brazil', 'R'),
    (2024, 'Saudi Arabia', 'R'),
    (2023, 'Singapore', 'R'),
]

print("=" * 100)
print("SAFETY CAR & VSC TRIGGER ANALYSIS")
print("Finding yellow flags and incidents that triggered Safety Car deployment")
print("=" * 100)

for year, race, session_type in test_cases:
    print(f"\n{'=' * 100}")
    print(f"RACE: {year} {race} - {session_type}")
    print("=" * 100)
    
    try:
        session = fastf1.get_session(year, race, session_type)
        session.load()
        
        sc_msgs, vsc_msgs, all_messages = analyze_safety_car_deployment(session)
        
        # 分析安全車
        if len(sc_msgs) > 0:
            print(f"\n*** Found {len(sc_msgs)} SAFETY CAR deployment(s) ***")
            
            for idx, sc_msg in sc_msgs.iterrows():
                sc_time = sc_msg['Time']
                sc_message = sc_msg['Message']
                
                print(f"\n--- SAFETY CAR DEPLOYED at {sc_time} ---")
                print(f"    Message: {sc_message}")
                
                # 查找安全車前 3 分鐘的所有訊息
                time_window_start = sc_time - timedelta(minutes=3)
                messages_before = all_messages[
                    (all_messages['Time'] >= time_window_start) & 
                    (all_messages['Time'] < sc_time)
                ]
                
                print(f"\n    Events in 3 minutes BEFORE Safety Car:")
                print(f"    {'-' * 90}")
                
                if len(messages_before) == 0:
                    print("    No messages found")
                else:
                    for msg_idx, msg in messages_before.iterrows():
                        time_diff = (sc_time - msg['Time']).total_seconds()
                        flag = msg['Flag'] if pd.notna(msg['Flag']) else 'NO FLAG'
                        category = msg['Category'] if pd.notna(msg['Category']) else 'N/A'
                        message = msg['Message']
                        
                        # 高亮關鍵事件
                        marker = ""
                        if 'YELLOW' in flag.upper():
                            marker = " <-- YELLOW FLAG"
                        elif 'SECTOR' in message.upper() and 'YELLOW' in message.upper():
                            marker = " <-- YELLOW IN SECTOR"
                        elif 'TURN' in message.upper():
                            marker = " <-- TURN MENTIONED"
                        elif 'SPUN' in message.upper() or 'STOPPED' in message.upper():
                            marker = " <-- INCIDENT"
                        elif 'CAR' in message.upper() and ('OFF' in message.upper() or 'RETIRED' in message.upper()):
                            marker = " <-- CAR ISSUE"
                        
                        print(f"    [-{int(time_diff)}s] [{flag:15}] {message}{marker}")
        else:
            print("\n   No Safety Car deployments")
        
        # 分析 VSC
        if len(vsc_msgs) > 0:
            print(f"\n*** Found {len(vsc_msgs)} VSC deployment(s) ***")
            
            for idx, vsc_msg in vsc_msgs.iterrows():
                vsc_time = vsc_msg['Time']
                vsc_message = vsc_msg['Message']
                
                print(f"\n--- VSC DEPLOYED at {vsc_time} ---")
                print(f"    Message: {vsc_message}")
                
                # 查找 VSC 前 2 分鐘的訊息
                time_window_start = vsc_time - timedelta(minutes=2)
                messages_before = all_messages[
                    (all_messages['Time'] >= time_window_start) & 
                    (all_messages['Time'] < vsc_time)
                ]
                
                print(f"\n    Events in 2 minutes BEFORE VSC:")
                print(f"    {'-' * 90}")
                
                if len(messages_before) == 0:
                    print("    No messages found")
                else:
                    for msg_idx, msg in messages_before.tail(10).iterrows():
                        time_diff = (vsc_time - msg['Time']).total_seconds()
                        flag = msg['Flag'] if pd.notna(msg['Flag']) else 'NO FLAG'
                        message = msg['Message']
                        
                        marker = ""
                        if 'YELLOW' in flag.upper():
                            marker = " <-- YELLOW FLAG"
                        elif 'TURN' in message.upper():
                            marker = " <-- TURN MENTIONED"
                        elif 'STOPPED' in message.upper():
                            marker = " <-- CAR STOPPED"
                        
                        print(f"    [-{int(time_diff)}s] [{flag:15}] {message}{marker}")
        else:
            print("\n   No VSC deployments")
    
    except Exception as e:
        print(f"   ERROR: {e}")

print("\n" + "=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
print("\nKEY FINDINGS:")
print("1. Safety Car messages contain 'SAFETY CAR DEPLOYED' but NO turn/corner info")
print("2. Trigger can be found in yellow flags BEFORE deployment")
print("3. Yellow flags DO contain sector information (e.g., 'YELLOW IN TRACK SECTOR 11')")
print("4. Some incident messages contain 'AT TURN X' information")
print("=" * 100)
