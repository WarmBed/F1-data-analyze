#!/usr/bin/env python3
"""檢查賽事名稱與賽道名稱的映射"""

import fastf1

# 獲取 2025 賽季賽程
schedule = fastf1.get_event_schedule(2025)

print("=" * 80)
print("2025 F1 賽季 - 賽事名稱 vs 賽道名稱映射")
print("=" * 80)
print(f"{'賽事名稱':<30s} {'賽道位置':<30s} {'國家':<15s}")
print("-" * 80)

for _, event in schedule.iterrows():
    event_name = event['EventName']
    location = event['Location']
    country = event['Country']
    
    # 只顯示正賽和衝刺賽
    if 'Grand Prix' in event_name or 'Sprint' in event_name:
        print(f"{event_name:<30s} {location:<30s} {country:<15s}")

print("=" * 80)
