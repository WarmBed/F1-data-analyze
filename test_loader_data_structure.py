#!/usr/bin/env python3
"""Check actual data structure from loader"""
import sys
import os
import json

os.chdir(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")
sys.path.insert(0, r"c:\Users\mike2\OneDrive\Code\F1-data-analyze")

from modules.gui.race_analysis.start_reaction import StartReactionDataLoader

loader = StartReactionDataLoader(2025, "Abu_Dhabi", "R")
data = loader.load_data()

print("=" * 60)
print("Data Structure Check")
print("=" * 60)

if data:
    print(f"\nTop-level keys: {list(data.keys())}")
    
    drivers = data.get('drivers', [])
    print(f"\nNumber of drivers: {len(drivers)}")
    
    if drivers:
        print("\nFirst driver structure:")
        first_driver = drivers[0]
        for key, value in first_driver.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("All Drivers Summary (sorted by 0-20 km/h time)")
        print("=" * 60)
        # 使用正確的鍵名 (t20 起步反應, t50 加速)
        for d in sorted(drivers, key=lambda x: x.get('t20', 999)):
            name = d.get('name', 'N/A')
            t20 = d.get('t20', 0)
            t50 = d.get('t50', 0)
            pos_delta = d.get('position_delta', 0)
            grid = d.get('grid', 0)
            lap1_pos = d.get('lap1_pos', 0)
            print(f"  {name:5s}: 0-20={t20:6.3f}s, 0-50={t50:6.3f}s, Grid={grid:2d}->Lap1={lap1_pos:2d} ({pos_delta:+d})")
else:
    print("No data returned!")
