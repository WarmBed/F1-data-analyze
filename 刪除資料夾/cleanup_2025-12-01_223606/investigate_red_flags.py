#!/usr/bin/env python3
"""調查紅旗訊息是否包含 TURN 資訊"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

# 調查多個賽季和賽事
races_to_check = [
    (2022, 'Japan', 'R'),      # 已知有紅旗
    (2022, 'Monaco', 'R'),     # 街道賽
    (2022, 'Saudi Arabia', 'R'), # 多次紅旗
    (2023, 'Monaco', 'R'),     
    (2023, 'Singapore', 'R'),  
    (2024, 'Monaco', 'R'),
    (2024, 'Brazil', 'R'),     # 多次紅旗
    (2024, 'Las Vegas', 'R'),
]

print("=" * 80)
print("RED FLAG Investigation: Do they contain TURN/CORNER info?")
print("=" * 80)

total_red_flags = 0
red_flags_with_turn = 0

for year, race, session_type in races_to_check:
    try:
        print(f"{'=' * 60}")
        print(f"Location: {year} {race} - {session_type}")
        print(f"{'=' * 60}")
        
        session = fastf1.get_session(year, race, session_type)
        session.load()
        
        messages = session.race_control_messages
        
        # 過濾紅旗訊息
        red_flags = messages[messages['Flag'].str.contains('RED', case=False, na=False)]
        
        if len(red_flags) == 0:
            print("   No red flags found")
            continue
        
        print(f"   Found {len(red_flags)} red flag messages:\n")
        
        for idx, row in red_flags.iterrows():
            total_red_flags += 1
            message = row['Message']
            time = row['Time']
            
            # 檢查訊息中是否包含 TURN 或 CORNER
            has_turn = 'TURN' in message.upper() or 'CORNER' in message.upper()
            
            if has_turn:
                red_flags_with_turn += 1
                print(f"   [HAS TURN] [{time}] {message}")
            else:
                print(f"   [NO TURN]  [{time}] {message}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        continue

print("\n" + "=" * 80)
print("STATISTICS")
print("=" * 80)
print(f"Total red flags: {total_red_flags}")
print(f"With TURN/CORNER info: {red_flags_with_turn} ({red_flags_with_turn/total_red_flags*100 if total_red_flags > 0 else 0:.1f}%)")
print(f"Without location info: {total_red_flags - red_flags_with_turn} ({(total_red_flags - red_flags_with_turn)/total_red_flags*100 if total_red_flags > 0 else 0:.1f}%)")

if red_flags_with_turn == 0:
    print("\nCONCLUSION: Red flag messages do NOT contain specific corner locations")
    print("   -> Red flags are track-wide stop signals, not corner-specific")
else:
    print(f"\nWARNING: Found {red_flags_with_turn} red flag messages with location info")
