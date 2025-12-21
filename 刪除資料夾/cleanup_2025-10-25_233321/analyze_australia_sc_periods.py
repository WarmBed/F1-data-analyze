"""
詳細分析 2025 Australia R 的 Safety Car Periods
"""
import fastf1

fastf1.Cache.enable_cache('f1_analysis_cache')

session = fastf1.get_session(2025, 'Australia', 'R')
session.load()

race_control = session.race_control_messages

# 篩選 Safety Car DEPLOYED 和 IN THIS LAP 訊息
sc_deployed = race_control[
    (race_control['Message'].str.contains('SAFETY CAR DEPLOYED', case=False, na=False)) &
    (~race_control['Message'].str.contains('VIRTUAL', case=False, na=False))
]

sc_ending = race_control[
    race_control['Message'].str.contains('SAFETY CAR IN THIS LAP', case=False, na=False)
]

print("=" * 80)
print("2025 Australia R - Safety Car Periods 配對分析")
print("=" * 80)

print("\n【DEPLOYED 訊息】")
for idx, row in sc_deployed.iterrows():
    print(f"  Lap {row['Lap']:2d} | {row['Time']} | {row['Message']}")

print("\n【IN THIS LAP 訊息】")
for idx, row in sc_ending.iterrows():
    print(f"  Lap {row['Lap']:2d} | {row['Time']} | {row['Message']}")

print("\n" + "=" * 80)
print("配對結果預測")
print("=" * 80)

deployed_laps = sc_deployed['Lap'].tolist()
ending_laps = sc_ending['Lap'].tolist()

if len(deployed_laps) == len(ending_laps):
    print(f"\n✅ 可以完美配對 {len(deployed_laps)} 個 Safety Car Period(s):\n")
    
    for i, (start, end) in enumerate(zip(deployed_laps, ending_laps), 1):
        duration = end - start
        print(f"  Period {i}: Lap {start} → Lap {end} (持續 {duration} 圈)")
        
        # 找出這段時間內的其他重要訊息
        period_messages = race_control[
            (race_control['Lap'] >= start) & 
            (race_control['Lap'] <= end) &
            (~race_control['Message'].str.contains('SAFETY CAR INFRINGEMENT', case=False, na=False))
        ]
        
        # 找可能的原因
        reasons = []
        for _, msg_row in period_messages.iterrows():
            msg = msg_row['Message'].upper()
            if any(kw in msg for kw in ['YELLOW', 'ACCIDENT', 'CRASH', 'DEBRIS', 'STOPPED']):
                reasons.append(f"    • Lap {msg_row['Lap']}: {msg_row['Message'][:60]}...")
        
        if reasons:
            print(f"    可能原因:")
            for reason in reasons[:3]:  # 只顯示前3個
                print(reason)
        print()
else:
    print(f"⚠️  配對數量不一致！")
    print(f"   DEPLOYED: {len(deployed_laps)} 筆")
    print(f"   ENDING:   {len(ending_laps)} 筆")
